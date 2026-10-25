"""Todo YAML de `datos/` trae los campos de la sección 4.3 de la especificación."""

from pathlib import Path

import pytest
import yaml

RAIZ = Path(__file__).resolve().parent.parent / "datos"
ARCHIVOS = sorted(RAIZ.rglob("*.yaml"))
CAMPOS = (
    "fuente",
    "url",
    "mes_consulta",
    "vigencia_desde",
    "vigencia_hasta",
    "verificado_por",
)


def test_hay_archivos_de_datos() -> None:
    assert len(ARCHIVOS) == 8


@pytest.mark.unit
@pytest.mark.req("RF-IPU-05 · Citación de la norma")
@pytest.mark.parametrize("ruta", ARCHIVOS, ids=lambda p: p.name)
def test_todo_yaml_de_datos_trae_los_campos_de_la_seccion_4_3(ruta: Path) -> None:
    datos = yaml.safe_load(ruta.read_text(encoding="utf-8"))
    faltantes = [campo for campo in CAMPOS if campo not in datos]
    assert not faltantes, f"{ruta.name} no trae {faltantes}"
    for campo in ("fuente", "url", "mes_consulta", "verificado_por"):
        assert str(datos[campo]).strip(), f"{ruta.name}: {campo} vacío"
    assert datos["vigencia_desde"] is not None
