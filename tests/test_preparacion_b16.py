"""Preparación de B16 (sección 8.17): la corrida 3 exige el juez calibrado (A5, ADR-25)."""

from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
GUARDADA = RAIZ / "reports" / "calibracion" / "huella_juez.txt"
RNF16 = "RNF-16 · Tasa de respuestas correctas"


@pytest.mark.unit
@pytest.mark.req(RNF16, "RF-OBS-05 · Ejecución repetible de pruebas")
def test_la_huella_calibrada_es_la_del_juez_actual(entorno_valido) -> None:
    """Con la muestra de calibración exportada (B15), su huella debe ser la del juez actual (v3):
    si alguien cambia el juez, esta prueba falla antes de la corrida 3, que corre con
    `--exigir-huella` y se detendría."""
    if not GUARDADA.exists():
        pytest.skip("Sin muestra de calibración exportada (antes de fusionar B15).")
    from src.config import Settings
    from src.evaluacion.juez import VERSION, huella_del_juez

    assert VERSION == "juez.v3"
    assert GUARDADA.read_text(encoding="utf-8").strip() == huella_del_juez(Settings(_env_file=None))


@pytest.mark.unit
@pytest.mark.req(RNF16)
def test_la_corrida_3_documenta_que_exige_la_huella() -> None:
    """El comando de la corrida 3 en `scripts/evaluar.py` lleva `--exigir-huella`, y el guion
    detiene la corrida si la huella guardada no es la del juez actual."""
    texto = (RAIZ / "scripts" / "evaluar.py").read_text(encoding="utf-8")
    assert "--k 3" in texto and "--exigir-huella" in texto
    assert "El juez cambió desde la calibración (A5)" in texto
