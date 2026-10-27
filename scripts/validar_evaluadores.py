"""Valida el juez y RAGAS con casos conocidos antes de la mini corrida (ADR-24, A4). Gasta tokens.

Caso con falla: la respuesta real a GEN-02 guardada en `docs/resumenes/b11.md` («Fallas
conocidas»), con las tres secciones del manual que cita como contexto. Dice «Para pagar o
presentar, debes hacerlo directamente en la Oficina Virtual Tributaria», que no está en el manual.
Caso fiel: la misma respuesta sin esa frase y con cada afirmación tal como la sustenta el manual.

Criterios:
- juez: el caso con falla tiene alucinación o no es «correcta»; el fiel es correcta o parcialmente
  correcta, sin alucinación;
- RAGAS (ajuste 2 de Rodolfo): la fidelidad del caso con falla es menor que la del fiel, y la del
  fiel es 0,9 o más.
Los dos casos son también la prueba inicial de RAGAS en español (A9): se miden las cuatro métricas y
el costo. Si algún criterio no se cumple, termina con código 1: es una parada.

Uso: uv run python scripts/validar_evaluadores.py
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import cargar_configuracion  # noqa: E402
from src.evaluacion.escenarios import RAIZ, cargar_escenarios  # noqa: E402
from src.evaluacion.juez import CasoJuez, Juez  # noqa: E402
from src.evaluacion.ragas_eval import CasoRagas, EvaluadorRagas  # noqa: E402
from src.integrations.costos import costo_usd  # noqa: E402

MANUAL = RAIZ / "knowledge_base" / "plataforma_general" / "manual_ovt_simulada.md"
SECCIONES = (
    "Lo que el asistente no hace",
    "Cómo usar el asistente",
    "Cómo hablar con un funcionario",
)
CON_FALLA = (
    "No. El asistente no presenta declaraciones, no hace pagos y no modifica datos, según el "
    "manual de la OVT simulada. Solo puede orientarte con respuestas generales sobre el predial, "
    "el ICA, tus datos personales y el uso de la plataforma. Para pagar o presentar, debes "
    "hacerlo directamente en la Oficina Virtual Tributaria. Si lo necesitas, también puedes pedir "
    "que te atienda un funcionario."
)
FIEL = (
    "No. El asistente no presenta declaraciones, no hace pagos y no modifica datos, según el "
    "manual de la OVT simulada. Puede orientarte sobre el predial, el ICA, tus datos personales y "
    "el uso de la plataforma, y sus respuestas son orientativas. Si lo necesitas, también puedes "
    "pedir que te atienda un funcionario."
)
UMBRAL_FIDELIDAD = 0.9
NORMA_MANUAL = "Manual de uso de la OVT simulada (sintético)"


def secciones_del_manual() -> list[str]:
    """Las tres secciones como las entrega la API en `meta.contextos`: la cita y el texto."""
    texto = MANUAL.read_text(encoding="utf-8")
    salida = []
    for parte in re.split(r"(?m)^## ", texto):
        titulo, _, cuerpo = parte.partition("\n")
        if titulo.strip() in SECCIONES:
            salida.append(f"{NORMA_MANUAL}, {titulo.strip()}\n{cuerpo.strip()}")
    return salida


def main() -> int:
    settings = cargar_configuracion()
    gen02 = next(e for e in cargar_escenarios() if e["id"] == "GEN-02")
    contextos = secciones_del_manual()
    assert len(contextos) == 3, "No se encontraron las tres secciones del manual"
    pregunta = gen02["turnos"][0]["usuario"]
    citadas = [f"{NORMA_MANUAL}, {s}" for s in SECCIONES]
    juez = Juez(settings)
    resultado: dict = {"juez": {}, "ragas": {}}
    tokens_juez = {"entrada": 0, "salida": 0}
    for nombre, respuesta in (("con_falla", CON_FALLA), ("fiel", FIEL)):
        caso = CasoJuez(
            [{"contribuyente": pregunta, "asistente": respuesta}],
            str(gen02["respuesta_referencia"]).strip(),
            gen02["fuentes_esperadas"],
            gen02["no_debe"],
            contextos,
            citadas,
        )
        calificacion = juez.calificar(caso)
        tokens_juez["entrada"] += calificacion.entrada
        tokens_juez["salida"] += calificacion.salida
        resultado["juez"][nombre] = calificacion.veredicto.model_dump()
        v = calificacion.veredicto
        print(f"Juez, {nombre}: {v.veredicto}, alucinación {v.alucinacion}: {v.justificacion}")
    ragas = EvaluadorRagas(settings)
    casos = [
        CasoRagas(pregunta, r, contextos, str(gen02["respuesta_referencia"]).strip())
        for r in (CON_FALLA, FIEL)
    ]
    for nombre, puntajes in zip(("con_falla", "fiel"), ragas.evaluar_varios(casos), strict=True):
        resultado["ragas"][nombre] = puntajes
        print(f"RAGAS, {nombre}: {puntajes}")
    j, r = resultado["juez"], resultado["ragas"]
    criterios = {
        "juez_detecta_la_falla": j["con_falla"]["alucinacion"]
        or j["con_falla"]["veredicto"] != "correcta",
        "juez_aprueba_la_fiel": j["fiel"]["veredicto"] != "incorrecta"
        and not j["fiel"]["alucinacion"],
        "ragas_fidelidad_menor_con_falla": (
            r["con_falla"]["faithfulness"] is not None
            and r["fiel"]["faithfulness"] is not None
            and r["con_falla"]["faithfulness"] < r["fiel"]["faithfulness"]
        ),
        "ragas_fidelidad_fiel_0_9": (r["fiel"]["faithfulness"] or 0) >= UMBRAL_FIDELIDAD,
        "ragas_cuatro_metricas": all(v is not None for p in r.values() for v in p.values()),
    }
    costo_juez = costo_usd(settings.modelo_juez, tokens_juez["entrada"], tokens_juez["salida"])
    resultado["criterios"] = criterios
    resultado["costo_usd"] = {"juez": str(costo_juez), "ragas": str(ragas.consumo.costo_usd())}
    resultado["tokens"] = {"juez": tokens_juez, "ragas": ragas.consumo.por_modelo}
    salida = RAIZ / "reports" / "validacion_evaluadores.json"
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for nombre, ok in criterios.items():
        print(f"{'cumple' if ok else 'NO CUMPLE'}: {nombre}")
    total = costo_juez + ragas.consumo.costo_usd()
    print(f"Costo: juez US${costo_juez:.4f}, RAGAS US${ragas.consumo.costo_usd():.4f}")
    print(f"Total: US${total:.4f}")
    print(f"Resultado en {salida}")
    return 0 if all(criterios.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
