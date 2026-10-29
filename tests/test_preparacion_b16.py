"""Preparación de B16 (sección 8.17): la corrida 3 exige el juez calibrado (A5, ADR-25)."""

import importlib.util
import sys
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


def _evaluar(raiz: Path, monkeypatch: pytest.MonkeyPatch, *argumentos: str) -> None:
    """Corre `main()` de `scripts/evaluar.py` con `RAIZ` en una carpeta temporal."""
    from src.config import Settings

    ruta = RAIZ / "scripts" / "evaluar.py"
    especificacion = importlib.util.spec_from_file_location("evaluar_b16", ruta)
    assert especificacion and especificacion.loader
    modulo = importlib.util.module_from_spec(especificacion)
    especificacion.loader.exec_module(modulo)
    monkeypatch.setattr(modulo, "RAIZ", raiz)
    monkeypatch.setattr(modulo, "cargar_configuracion", lambda: Settings(_env_file=None))
    monkeypatch.setattr(sys, "argv", ["evaluar.py", "--corrida", "prueba", "--local", *argumentos])
    modulo.main()


@pytest.mark.unit
@pytest.mark.req(RNF16, "RF-OBS-05 · Ejecución repetible de pruebas")
@pytest.mark.parametrize("argumentos", [("--k", "3"), ("--exigir-huella",)])
def test_la_corrida_3_se_detiene_sin_la_huella_calibrada(
    entorno_valido, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, argumentos: tuple[str, ...]
) -> None:
    """Con 3 ensayos (la corrida 3) o con `--exigir-huella`, el guion se detiene antes de llamar a
    ningún modelo si no hay huella calibrada o si no es la del juez actual."""
    with pytest.raises(SystemExit, match="No hay huella de la calibración"):
        _evaluar(tmp_path, monkeypatch, *argumentos)
    calibracion = tmp_path / "reports" / "calibracion"
    calibracion.mkdir(parents=True)
    (calibracion / "huella_juez.txt").write_text("otra\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="El juez cambió desde la calibración"):
        _evaluar(tmp_path, monkeypatch, *argumentos)
