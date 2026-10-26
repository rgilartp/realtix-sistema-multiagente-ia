"""Prueba de humo con modelos reales y primera medición de latencia (B7, RNF-01).

Corre el primer turno de unos escenarios aprobados de B6 por el grafo real (Sonnet 5.5 en el
orquestador y Haiku 5.5 en los agentes), con el reloj de cada escenario, y registra la duración en
ms, los tokens por modelo y el costo de cada consulta. No califica las respuestas (eso es de B12):
solo muestra que el flujo completo funciona y cuánto tarda y cuesta.
"""

import json
import time
from collections.abc import Callable
from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml
from langchain_core.callbacks import get_usage_metadata_callback

from src.agents.dependencias import Dependencias
from src.agents.graph import configuracion_de_hilo, construir_grafo
from src.agents.state import entrada_de_turno
from src.evaluacion.escenarios import DIR_ESCENARIOS, RAIZ
from src.integrations.costos import usos_desde_metadatos

USUARIOS = RAIZ / "tests" / "fixtures" / "usuarios_prueba.yaml"
# Cinco consultas simples (datos del adaptador o de los servicios, o texto fijo) y cinco con
# recuperación (respuestas conceptuales desde los fragmentos), más dos del orquestador.
SIMPLES = ("IPU-01", "IPU-10", "ICA-05", "ICA-08", "AIA-02")
CON_RECUPERACION = ("IPU-04", "IPU-09", "ICA-01", "GEN-04", "GEN-07")
ORQUESTADOR = ("MULTI-03", "FA-03")


def _sesiones() -> dict[str, tuple[str, list[str]]]:
    usuarios = yaml.safe_load(USUARIOS.read_text(encoding="utf-8"))["usuarios"]
    return {
        u["id"]: (u["contribuyente_id"], [p["matricula"] for p in u["predios"]]) for u in usuarios
    }


def correr_escenario(
    deps: Dependencias, escenario: dict[str, Any], tipo: str, sesiones: dict[str, Any]
) -> dict[str, Any]:
    """Primer turno del escenario por el grafo real; duración, tokens, costo y resultado."""
    contribuyente, predios = sesiones.get(escenario.get("sesion") or "", (None, []))
    conversacion = f"humo-{escenario['id']}"
    grafo = construir_grafo(deps)
    entrada = entrada_de_turno(
        escenario["turnos"][0]["usuario"], conversacion, contribuyente, predios
    )
    with get_usage_metadata_callback() as uso:
        inicio = time.perf_counter()
        r = grafo.invoke(entrada, configuracion_de_hilo(conversacion, escenario["reloj"]))
        duracion_ms = round((time.perf_counter() - inicio) * 1000, 1)
    usos = usos_desde_metadatos(uso.usage_metadata)
    partes = r.get("respuestas_parciales", [])
    return {
        "escenario": escenario["id"],
        "tipo": tipo,
        "duracion_ms": duracion_ms,
        "categoria": r.get("categoria"),
        "escalado": bool(r.get("requiere_escalamiento")),
        "motivo_escalamiento": r.get("motivo_escalamiento"),
        "nivel_confianza": round(float(r.get("nivel_confianza") or 0), 3),
        "suficiencias": [p.get("suficiencia") for p in partes],
        "respuesta": r.get("respuesta_final", ""),
        "tokens": [{"modelo": u.modelo, "entrada": u.entrada, "salida": u.salida} for u in usos],
        "costo_usd": str(sum((u.costo_usd for u in usos), Decimal(0))),
    }


def correr_humo(
    deps: Dependencias,
    salida: Path | None = None,
    al_avanzar: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    """Corre los 12 escenarios y, si se da `salida`, guarda el reporte en JSON."""
    sesiones = _sesiones()
    resultados = []
    for tipo, ids in (
        ("simple", SIMPLES),
        ("con_recuperacion", CON_RECUPERACION),
        ("orquestador", ORQUESTADOR),
    ):
        for id_escenario in ids:
            escenario = yaml.safe_load(
                (DIR_ESCENARIOS / f"{id_escenario}.yaml").read_text(encoding="utf-8")
            )
            resultado = correr_escenario(deps, escenario, tipo, sesiones)
            resultados.append(resultado)
            if al_avanzar:
                al_avanzar(resultado)
    reporte = {"resultados": resultados, "resumen": resumir(resultados)}
    if salida:
        salida.parent.mkdir(parents=True, exist_ok=True)
        salida.write_text(json.dumps(reporte, ensure_ascii=False, indent=2) + "\n", "utf-8")
    return reporte


def _mediana(valores: list[float]) -> float:
    ordenados = sorted(valores)
    mitad = len(ordenados) // 2
    if len(ordenados) % 2:
        return ordenados[mitad]
    return round((ordenados[mitad - 1] + ordenados[mitad]) / 2, 1)


def resumir(resultados: list[dict[str, Any]]) -> dict[str, Any]:
    """Duración mediana y máxima por tipo, tokens por modelo y costo total."""
    por_tipo: dict[str, Any] = {}
    for tipo in sorted({r["tipo"] for r in resultados}):
        duraciones = [r["duracion_ms"] for r in resultados if r["tipo"] == tipo]
        por_tipo[tipo] = {
            "consultas": len(duraciones),
            "mediana_ms": _mediana(duraciones),
            "maximo_ms": max(duraciones),
        }
    tokens: dict[str, dict[str, int]] = {}
    for r in resultados:
        for t in r["tokens"]:
            acumulado = tokens.setdefault(t["modelo"], {"entrada": 0, "salida": 0})
            acumulado["entrada"] += t["entrada"]
            acumulado["salida"] += t["salida"]
    costo = sum((Decimal(r["costo_usd"]) for r in resultados), Decimal(0))
    return {"latencia": por_tipo, "tokens": tokens, "costo_total_usd": str(costo)}
