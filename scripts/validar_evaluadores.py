"""Valida el juez y RAGAS con casos conocidos antes de la mini corrida (ADR-24, A4). Gasta tokens.

Caso con falla: la respuesta real a GEN-02 guardada en `docs/resumenes/b11.md` («Fallas
conocidas»), con las tres secciones del manual que cita como contexto. Dice «Para pagar o
presentar, debes hacerlo directamente en la Oficina Virtual Tributaria», que no está en el manual.
Caso fiel: la misma respuesta sin esa frase y con cada afirmación tal como la sustenta el manual.

Casos con datos de herramientas (ADR-25, después de F1): una consulta inventada de saldo, con un
resultado inventado de `estado_cuenta_predial` y la nota de mora del sistema, armada con el mismo
`caso_del_ensayo` de las corridas. La respuesta fiel usa un dato que solo da la herramienta (el
avalúo); una alterada cambia el saldo (que también está en la referencia), otra cambia el avalúo
(que solo da la herramienta) y otra agrega un requisito que no está en ninguna fuente.

Criterios (juez v3, ADR-25): el juez califica cada caso 3 veces, con el criterio de la tasa de la
meta (A3), y debe cumplir en las 3:
- GEN-02 con la frase inventada: no se supera y la frase está entre las afirmaciones sin fuente;
- GEN-02 fiel y el saldo fiel: se superan, con la lista vacía;
- el requisito inventado y el saldo o el avalúo alterados: con alucinación;
- RAGAS, una vez (ajuste 2 de Rodolfo): la fidelidad del caso con falla es menor que la del fiel,
  y la del fiel es 0,9 o más.
Los dos casos de GEN-02 son también la prueba inicial de RAGAS en español (A9): se miden las cuatro
métricas y el costo. Si algún criterio no se cumple, termina con código 1: es una parada.

Uso: uv run python scripts/validar_evaluadores.py
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import cargar_configuracion  # noqa: E402
from src.evaluacion.escenarios import RAIZ, cargar_escenarios, normalizar_texto  # noqa: E402
from src.evaluacion.juez import (  # noqa: E402
    CasoJuez,
    Juez,
    Veredicto,
    caso_del_ensayo,
    huella_del_juez,
    superado,
)
from src.evaluacion.ragas_eval import CasoRagas, EvaluadorRagas  # noqa: E402
from src.integrations.costos import costo_usd  # noqa: E402
from src.services.notas import NOTA_INTERESES_MORA  # noqa: E402

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

# Caso inventado con datos de una herramienta (no es de ningún escenario: A8).
FUENTE = "Datos de tu cuenta en RealSit"
PREGUNTA_SALDO = "¿Me queda algo por pagar del predial de mi casa?"
RESULTADO_INVENTADO = {
    "matricula": "50C-9999901",
    "anio_gravable": 2026,
    "avaluo_catastral": "$612.300.000",
    "valor_liquidado": "$4.817.000",
    "pagado": "$0",
    "saldo": "$4.817.000",
    "vencida": True,
    "fuentes_de_la_herramienta": ["Datos de tu cuenta en RealSit"],
}
REFERENCIA_SALDO = (
    "Sí. Según tus datos en RealSit, el predial de 2026 de tu predio tiene un saldo pendiente de "
    "$4.817.000 y la obligación está vencida. Los intereses de mora no se calculan aquí."
)
SALDO_FIEL = (
    "Sí. Tu predio, con un avalúo catastral de $612.300.000, tiene un saldo pendiente de "
    "$4.817.000 del predial de 2026, y la obligación ya está vencida."
)
SALDO_ALTERADO = SALDO_FIEL.replace("$4.817.000", "$4.871.000")
# El avalúo solo lo da la herramienta (no está en la referencia): aísla lo que aporta F1.
AVALUO_ALTERADO = SALDO_FIEL.replace("$612.300.000", "$621.300.000")
# Un requisito que no está en ninguna fuente (juez v3).
CON_REQUISITO = (
    f"{SALDO_FIEL} Para pagar, debes presentar también el certificado de tradición y libertad del "
    "predio."
)
FRASE_INVENTADA = (
    "Para pagar o presentar, debes hacerlo directamente en la Oficina Virtual Tributaria"
)
REPETICIONES = 3


def caso_con_herramienta(respuesta: str) -> CasoJuez:
    """El caso como lo arma una corrida: la respuesta con la nota que agrega el sistema."""
    escenario = {
        "respuesta_referencia": REFERENCIA_SALDO,
        "fuentes_esperadas": ["Datos de tu cuenta en RealSit"],
        "no_debe": [],
    }
    turno = {
        "usuario": PREGUNTA_SALDO,
        "respuesta": f"{respuesta}\n\n{NOTA_INTERESES_MORA}\n\nFuentes: {FUENTE}.",
        "meta": {
            "fuentes": [{"norma": "Datos de tu cuenta en RealSit"}],
            "herramientas": [
                {"herramienta": "estado_cuenta_predial", "resultado": RESULTADO_INVENTADO}
            ],
            "notas": [NOTA_INTERESES_MORA],
        },
    }
    return caso_del_ensayo(escenario, {"turnos": [turno]})


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


def lista_la_frase(afirmaciones: list[str], frase: str, minimo: float = 0.5) -> bool:
    """Alguna afirmación listada recoge la frase: comparte al menos la mitad de sus palabras de
    contenido (cuatro letras o más), sin importar tildes ni puntuación."""

    def palabras(texto: str) -> set[str]:
        return {p for p in re.findall(r"\w+", normalizar_texto(texto)) if len(p) >= 4}

    buscadas = palabras(frase)
    return any(len(buscadas & palabras(a)) >= minimo * len(buscadas) for a in afirmaciones)


def main() -> int:
    settings = cargar_configuracion()
    gen02 = next(e for e in cargar_escenarios() if e["id"] == "GEN-02")
    contextos = secciones_del_manual()
    assert len(contextos) == 3, "No se encontraron las tres secciones del manual"
    pregunta = gen02["turnos"][0]["usuario"]
    citadas = [f"{NORMA_MANUAL}, {s}" for s in SECCIONES]
    juez = Juez(settings)
    resultado: dict = {"repeticiones_del_juez": REPETICIONES, "juez": {}, "ragas": {}}
    tokens_juez = {"entrada": 0, "salida": 0}
    casos_juez = {
        nombre: CasoJuez(
            [{"contribuyente": pregunta, "asistente": respuesta}],
            str(gen02["respuesta_referencia"]).strip(),
            gen02["fuentes_esperadas"],
            gen02["no_debe"],
            contextos,
            citadas,
        )
        for nombre, respuesta in (("con_falla", CON_FALLA), ("fiel", FIEL))
    }
    casos_juez["herramienta_con_requisito"] = caso_con_herramienta(CON_REQUISITO)
    casos_juez["herramienta_alterada"] = caso_con_herramienta(SALDO_ALTERADO)
    casos_juez["herramienta_solo_alterada"] = caso_con_herramienta(AVALUO_ALTERADO)
    casos_juez["herramienta_fiel"] = caso_con_herramienta(SALDO_FIEL)
    for nombre, caso in casos_juez.items():
        resultado["juez"][nombre] = []
        for repeticion in range(1, REPETICIONES + 1):
            calificacion = juez.calificar(caso)
            tokens_juez["entrada"] += calificacion.entrada
            tokens_juez["salida"] += calificacion.salida
            v = calificacion.veredicto
            resultado["juez"][nombre].append(
                {**v.model_dump(), "alucinacion_marcada": calificacion.alucinacion_marcada}
            )
            print(
                f"Juez, {nombre} ({repeticion}): {v.veredicto}, alucinación {v.alucinacion}, "
                f"sin fuente {v.afirmaciones_sin_fuente}"
            )
    ragas = EvaluadorRagas(settings)
    casos = [
        CasoRagas(pregunta, r, contextos, str(gen02["respuesta_referencia"]).strip())
        for r in (CON_FALLA, FIEL)
    ]
    # Con herramientas, solo como información: el contexto es el de una corrida (F1).
    datos = [
        f"Dato de una herramienta del sistema: {d}"
        for d in casos_juez["herramienta_fiel"].datos_herramientas
    ] + [f"Nota del sistema: {NOTA_INTERESES_MORA}"]
    casos += [
        CasoRagas(PREGUNTA_SALDO, r, datos, REFERENCIA_SALDO) for r in (SALDO_ALTERADO, SALDO_FIEL)
    ]
    nombres = ("con_falla", "fiel", "herramienta_alterada", "herramienta_fiel")
    for nombre, puntajes in zip(nombres, ragas.evaluar_varios(casos), strict=True):
        resultado["ragas"][nombre] = puntajes
        print(f"RAGAS, {nombre}: {puntajes}")
    j, r = resultado["juez"], resultado["ragas"]

    def meta(v: dict) -> bool:  # la tasa de la meta (A3): sin alucinación y no «incorrecta»
        return superado(True, Veredicto.model_validate({k: v[k] for k in Veredicto.model_fields}))[
            0
        ]

    def en_todas(nombre: str, condicion) -> bool:  # noqa: ANN001
        return all(condicion(v) for v in j[nombre])

    criterios = {
        "juez_no_supera_la_falla_y_lista_la_frase": en_todas(
            "con_falla",
            lambda v: not meta(v) and lista_la_frase(v["afirmaciones_sin_fuente"], FRASE_INVENTADA),
        ),
        "juez_supera_la_fiel_sin_lista": en_todas(
            "fiel", lambda v: meta(v) and not v["afirmaciones_sin_fuente"]
        ),
        "juez_detecta_el_requisito_inventado": en_todas(
            "herramienta_con_requisito", lambda v: v["alucinacion"]
        ),
        "juez_detecta_el_dato_de_herramienta_alterado": en_todas(
            "herramienta_alterada", lambda v: v["alucinacion"]
        ),
        "juez_detecta_el_dato_solo_de_herramienta_alterado": en_todas(
            "herramienta_solo_alterada", lambda v: v["alucinacion"]
        ),
        "juez_supera_los_datos_de_herramienta_sin_lista": en_todas(
            "herramienta_fiel", lambda v: meta(v) and not v["afirmaciones_sin_fuente"]
        ),
        "ragas_fidelidad_menor_con_falla": (
            r["con_falla"]["faithfulness"] is not None
            and r["fiel"]["faithfulness"] is not None
            and r["con_falla"]["faithfulness"] < r["fiel"]["faithfulness"]
        ),
        "ragas_fidelidad_fiel_0_9": (r["fiel"]["faithfulness"] or 0) >= UMBRAL_FIDELIDAD,
        "ragas_cuatro_metricas": all(
            v is not None for n in ("con_falla", "fiel") for v in r[n].values()
        ),
    }
    costo_juez = costo_usd(settings.modelo_juez, tokens_juez["entrada"], tokens_juez["salida"])
    resultado["criterios"] = criterios
    resultado["huella_juez"] = huella_del_juez(settings)
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
