"""Prueba de humo con los modelos reales (B7): una sola ejecución, con tokens y costo.

Gasta tokens reales, así que solo corre con `REALTIX_PRUEBAS_REALES=1` (y la clave en `.env`); en
la CI se salta. Escribe `reports/b07_humo.json`, de donde salen la primera medición de latencia y el
gasto del resumen del bloque. No califica las respuestas: eso lo hace B12.
"""

import os
from pathlib import Path

import pytest

from src.evaluacion.humo import CON_RECUPERACION, LIBRES, ORQUESTADOR, SIMPLES, correr_humo

REALES = os.environ.get("REALTIX_PRUEBAS_REALES") == "1"
SALIDA = Path(__file__).resolve().parent.parent / "reports" / "b07_humo.json"


@pytest.mark.integration
@pytest.mark.skipif(not REALES, reason="Gasta tokens reales: REALTIX_PRUEBAS_REALES=1")
@pytest.mark.req(
    "RF-ORQ-05 · Modelo de razonamiento",
    "RF-SYS-06 · Aviso de interacción con IA (provisional)",
    "RNF-01 · Tiempo de respuesta",
)
def test_humo_con_modelos_reales() -> None:
    from src.container import Contenedor

    reporte = correr_humo(Contenedor().deps, SALIDA)
    resultados = {r["escenario"]: r for r in reporte["resultados"]}
    assert set(resultados) == {*SIMPLES, *CON_RECUPERACION, *ORQUESTADOR, *LIBRES}
    assert all(r["respuesta"] for r in resultados.values())
    # Ninguna consulta cayó por un error de la API (parámetros o salida estructurada).
    assert not [
        r["escenario"]
        for r in resultados.values()
        if r["motivo_escalamiento"] == "fallo de servicio"
    ]
    assert "inteligencia artificial" in resultados["AIA-02"]["respuesta"]
    assert resultados["FA-03"]["motivo_escalamiento"] == "fuera de alcance"
    modelos = reporte["resumen"]["tokens"]
    assert any(m.startswith("claude-sonnet-5-5") for m in modelos)
    assert any(m.startswith("claude-haiku-5-5") for m in modelos)
