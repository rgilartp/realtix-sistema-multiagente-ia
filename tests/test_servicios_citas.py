"""Verificador de citas sin modelo (F5 de la corrida 1), con normas y artículos inventados."""

import pytest

from src.services.citas import citas_sin_fuente, extraer_citas

F5 = "RF-IPU-05 · Citación de la norma"
GEN03 = "RF-GEN-03 · Respuesta sustentada en fuentes"


@pytest.mark.unit
@pytest.mark.req(F5)
def test_reconoce_las_citas_con_articulo_en_sus_formas_usuales() -> None:
    texto = (
        "Según la Ley 900 de 2091, art. 4, y el Decreto Distrital 77 de 2093 (arts. 2 y 9), "
        "con el Acuerdo 55, art. 1-1. La Resolución XYZ-000123 de 2094, art. 3, también."
    )
    citas = {(c.tipo, c.numero, c.anio, c.articulo) for c in extraer_citas(texto)}
    assert citas == {
        ("ley", "900", "2091", "4"),
        ("decreto", "77", "2093", "2"),
        ("decreto", "77", "2093", "9"),
        ("acuerdo", "55", None, "1-1"),
        ("resolucion", "xyz-000123", "2094", "3"),
    }
    assert extraer_citas("La Ley 900 de 2091 dice que…") == []  # sin artículo no se revisa


@pytest.mark.unit
@pytest.mark.req(F5, GEN03)
def test_una_cita_que_no_esta_en_las_fuentes_se_reporta() -> None:
    fragmentos = ["Ley 900 de 2091, art. 4", "Acuerdo 55 de 2090, art. 1"]
    texto = "Lo dice la Ley 900 de 2091, art. 13, y el Acuerdo 55, art. 1."
    assert citas_sin_fuente(texto, fragmentos) == ["ley 900 de 2091, art. 13"]
    assert citas_sin_fuente("Lo dice la Ley 900 de 2091, art. 4.", fragmentos) == []


@pytest.mark.unit
@pytest.mark.req(F5)
def test_sin_distrital_y_con_capitulo_coincide_con_el_encabezado() -> None:
    """Revisión externa: «Decreto 123 de 2001, art. 14» coincide con el encabezado «Decreto
    Distrital 123 de 2001, cap. I, art. 14», con la misma normalización de F3."""
    encabezado = ["Decreto Distrital 123 de 2001, cap. I, art. 14"]
    assert citas_sin_fuente("Ver el Decreto 123 de 2001, art. 14.", encabezado) == []
    assert citas_sin_fuente("Ver el Decreto 123 de 2001, art. 15.", encabezado) == [
        "decreto 123 de 2001, art. 15"
    ]


@pytest.mark.unit
@pytest.mark.req(F5)
def test_una_cita_que_solo_esta_en_una_nota_del_sistema_tiene_fuente() -> None:
    nota = "El pago incluye un recargo inventado (Ley 900 de 2091, arts. 7 y 8)."
    assert citas_sin_fuente("Hay un recargo (Ley 900 de 2091, art. 8).", [nota]) == []
