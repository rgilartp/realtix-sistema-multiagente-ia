"""Análisis de sensibilidad de la relevancia de RAGAS (corrida 3): los 66 casos sin sesión con los
cuatro valores, con la respuesta sin la lista final «Fuentes:» ni las notas fijas del sistema. No
reemplaza la cifra oficial. Sin modelos de Anthropic; usa el evaluador de RAGAS (OpenAI).

    gunzip -k reports/corrida-3/resultados.jsonl.gz
    uv run python reports/corrida-3/sensibilidad_relevancia.py \
        reports/corrida-3/resultados.jsonl reports/corrida-3/sensibilidad_relevancia.jsonl
"""

import asyncio
import json
import math
import sys
from pathlib import Path

RAIZ = Path.cwd()
sys.path.insert(0, str(RAIZ))
from src.config import cargar_configuracion  # noqa: E402
from src.evaluacion.escenarios import cargar_escenarios  # noqa: E402
from src.evaluacion.ragas_eval import CasoRagas, EvaluadorRagas  # noqa: E402

METRICAS = ("context_precision", "context_recall", "faithfulness", "answer_relevancy")


def sin_anexos(respuesta: str, notas: list[str]) -> str:
    """Quita la lista final «Fuentes: …» y cada nota fija que el sistema agregó tal cual."""
    texto = respuesta
    i = texto.rfind("\n\nFuentes:")
    if i >= 0:
        texto = texto[:i]
    for nota in notas:
        texto = texto.replace(nota, "")
    return "\n\n".join(p.strip() for p in texto.split("\n\n") if p.strip())


def main() -> None:
    """Escribe una fila por caso con la relevancia oficial y la de la respuesta sin anexos."""
    resultados, salida = Path(sys.argv[1]), Path(sys.argv[2])
    escenarios = {e["id"]: e for e in cargar_escenarios()}
    oficiales = {
        (r["escenario"], r["ensayo"]): r
        for r in map(json.loads, (RAIZ / "reports/corrida-3/ragas.jsonl").open(encoding="utf-8"))
        if all(isinstance(r.get(m), float) and not math.isnan(r[m]) for m in METRICAS)
        and not escenarios[r["escenario"]].get("sesion")
    }
    ensayos = {
        (e["escenario"], e["ensayo"]): e
        for e in map(json.loads, resultados.open(encoding="utf-8"))
        if (e["escenario"], e["ensayo"]) in oficiales
    }
    evaluador = EvaluadorRagas(cargar_configuracion())
    metrica = evaluador.metricas["answer_relevancy"]

    async def todos() -> list[dict]:
        await evaluador.adaptar_al_espanol()
        filas = []
        for clave, ensayo in sorted(ensayos.items()):
            turno = ensayo["turnos"][0]
            notas = (turno.get("meta") or {}).get("notas") or []
            recortada = sin_anexos(turno.get("respuesta") or "", notas)
            caso = CasoRagas(turno["usuario"], recortada, [], "").anonimizado()
            try:
                puntaje = await metrica.ascore(user_input=caso.pregunta, response=caso.respuesta)
                valor: float | None = float(puntaje.value)
            except Exception as error:  # una métrica que falla queda vacía, como en la corrida
                valor = None
                print("sin resultado", clave, type(error).__name__)
            filas.append(
                {
                    "escenario": clave[0],
                    "ensayo": clave[1],
                    "oficial": oficiales[clave]["answer_relevancy"],
                    "sin_anexos": valor,
                }
            )
        return filas

    filas = asyncio.run(todos())
    lineas = "".join(json.dumps(f, ensure_ascii=False) + "\n" for f in filas)
    salida.write_text(lineas, encoding="utf-8")
    validas = [f for f in filas if f["sin_anexos"] is not None]
    oficial = sum(f["oficial"] for f in validas) / len(validas)
    nueva = sum(f["sin_anexos"] for f in validas) / len(validas)
    print(f"casos {len(filas)}, con resultado {len(validas)}")
    print(f"relevancia oficial {100 * oficial:.1f} %; sin anexos {100 * nueva:.1f} %")
    print(f"costo OpenAI US${evaluador.consumo.costo_usd()}")


if __name__ == "__main__":
    main()
