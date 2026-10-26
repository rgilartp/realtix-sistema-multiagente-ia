"""Latencia de punta a punta por la API (B9, RNF-01 · Tiempo de respuesta).

Corre el primer turno de los 12 escenarios de la prueba de humo de B7 por `POST /chat/mensaje`, en
el modo de evaluación (el reloj y el escenario van en las cabeceras) y con el token de la OVT
simulada de cada usuario. Mide la duración desde el cliente, en ms, y guarda los tiempos por nodo,
los tokens y el costo. Meta de RNF-01: menos de 8 s en las consultas simples y menos de 15 s con
recuperación.
"""

import json
import logging
import time
import uuid
from collections.abc import Callable
from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml
from fastapi.testclient import TestClient

from src.api.acceso import emitir_token
from src.evaluacion.escenarios import DIR_ESCENARIOS
from src.evaluacion.humo import CON_RECUPERACION, ORQUESTADOR, SIMPLES, resumir, sesiones
from src.integrations.costos import costo_usd

registro = logging.getLogger(__name__)

META_MS = {"simple": 8000, "con_recuperacion": 15000, "orquestador": 15000}


def correr_por_api(
    cliente: TestClient,
    secreto: Any,
    al_avanzar: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    """Primer turno de cada escenario por la API; resultados y resumen por tipo."""
    usuarios = sesiones()
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
            cabeceras = {"X-Reloj-Simulado": escenario["reloj"], "X-Escenario-Id": id_escenario}
            contribuyente, _ = usuarios.get(escenario.get("sesion") or "", (None, []))
            if contribuyente:
                cabeceras["Authorization"] = f"Bearer {emitir_token(contribuyente, secreto)}"
            cuerpo = {
                "id_conversacion": f"latencia-{id_escenario}-{uuid.uuid4().hex[:8]}",
                "mensaje": escenario["turnos"][0]["usuario"],
            }
            inicio = time.perf_counter()
            respuesta = cliente.post("/api/v1/chat/mensaje", json=cuerpo, headers=cabeceras)
            duracion_ms = round((time.perf_counter() - inicio) * 1000, 1)
            datos = respuesta.json()
            meta = datos.get("meta", {})
            resultado = {
                "escenario": id_escenario,
                "id_conversacion": cuerpo["id_conversacion"],
                "tipo": tipo,
                "codigo_http": respuesta.status_code,
                "duracion_ms": duracion_ms,
                "estado": datos.get("estado"),
                "motivo_escalamiento": meta.get("motivo_escalamiento"),
                "tiempos_ms": meta.get("tiempos_ms"),
                "modelo_por_nodo": meta.get("modelo_por_nodo"),
                "tokens": meta.get("tokens"),
                "cumple_meta": duracion_ms < META_MS[tipo],
            }
            resultados.append(resultado)
            if al_avanzar:
                al_avanzar(resultado)
    return {"resultados": resultados, "resumen": resumir_api(resultados)}


def resumir_api(resultados: list[dict[str, Any]]) -> dict[str, Any]:
    """Mediana y máximo por tipo (como en B7) y cuántos cumplen la meta de RNF-01."""
    base = resumir([{**r, "tokens": [], "costo_usd": "0"} for r in resultados])
    for tipo, datos in base["latencia"].items():
        datos["meta_ms"] = META_MS[tipo]
        datos["cumplen"] = sum(r["cumple_meta"] for r in resultados if r["tipo"] == tipo)
    entrada = sum((r.get("tokens") or {}).get("entrada", 0) for r in resultados)
    salida = sum((r.get("tokens") or {}).get("salida", 0) for r in resultados)
    base["tokens"] = {"entrada": entrada, "salida": salida}
    base.pop("costo_total_usd", None)
    return base


def costo_de_interacciones(
    interacciones: list[dict[str, Any]], conversaciones: set[str]
) -> Decimal:
    """Costo de los turnos de la corrida, con el desglose por modelo del registro."""
    total = Decimal(0)
    for fila in interacciones:
        if fila["id_conversacion"] not in conversaciones:
            continue
        for modelo, t in ((fila.get("tokens") or {}).get("por_modelo") or {}).items():
            try:
                total += costo_usd(modelo, t["entrada"], t["salida"])
            except KeyError:  # un modelo sin precio no tumba una corrida pagada
                registro.warning("Modelo sin precio en el costo", extra={"modelo": modelo})
    return total


def guardar(reporte: dict[str, Any], salida: Path) -> None:
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(json.dumps(reporte, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
