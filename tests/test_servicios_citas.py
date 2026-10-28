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


@pytest.mark.unit
@pytest.mark.req(F5)
def test_formas_reales_de_encabezado_paréntesis_capitulos_puntos_y_rangos() -> None:
    """Revisión independiente: paréntesis después del año, «caps.», artículos con puntos, rangos
    «N a M», «Decreto Ley» igual a «Decreto» y una cifra que no es artículo (normas inventadas)."""
    fuentes = [
        "Resolución XYZ-000001 de 2091 (rangos inventados), art. 2",
        "Decreto 5555 de 2092, caps. 25 y 26, art. 2.2.2.25.1.1",
        "Acuerdo 77 de 2093, arts. 13 a 15",
        "Decreto Ley 4321 de 2094, art. 9",
    ]
    texto = (
        "Lo dicen la Resolución XYZ-000001 de 2091, art. 2; el Decreto 5555 de 2092, art. "
        "2.2.2.25.1.1; el Acuerdo 77 de 2093, art. 14, y el Decreto 4321 de 2094, art. 9."
    )
    assert citas_sin_fuente(texto, fuentes) == []
    assert citas_sin_fuente("El Decreto 5555 de 2092, art. 2.2.2.25.1.2.", fuentes) == [
        "decreto 5555 de 2092, art. 2.2.2.25.1.2"
    ]
    assert [c.articulo for c in extraer_citas("Ley 900 de 2091, art. 14, 2093 es el año.")] == [
        "14"
    ]


@pytest.mark.unit
@pytest.mark.req(F5)
def test_un_fragmento_sustenta_su_norma_su_articulo_y_su_linea_de_fuente() -> None:
    """La norma que vale es la primera del encabezado (no la que compila), y la línea «Fuente»
    del texto (como en el glosario) también sustenta."""
    from src.services.citas import fuentes_de_fragmento

    compila = fuentes_de_fragmento(
        "Decreto 888 de 2095 (compilación inventada), arts. que compilan el Decreto 111 de 2090",
        "Artículo 224",
        "ARTÍCULO 224. Texto inventado.",
    )
    assert citas_sin_fuente("Decreto 888 de 2095, art. 224.", compila) == []
    assert citas_sin_fuente("Decreto 111 de 2090, art. 224.", compila) == [
        "decreto 111 de 2090, art. 224"
    ]
    glosario = fuentes_de_fragmento(
        "Glosario inventado", "Término", "Definición.\n\n**Fuente:** Ley 900 de 2091, art. 1."
    )
    assert citas_sin_fuente("Así lo define la Ley 900 de 2091, art. 1.", glosario) == []


@pytest.mark.unit
@pytest.mark.req(F5)
def test_normas_citadas_por_las_notas_para_la_lista_de_fuentes() -> None:
    from src.services.citas import normas_citadas

    texto = (
        "Se aproximan al múltiplo de mil (Decreto 807 de 1993, arts. 15 y 132). Avisos y tableros "
        "(Decreto 352 de 2002, arts. 57 a 59) y sobretasa (Resolución SDH-000195 de 2025, art. 2)."
    )
    assert normas_citadas(texto) == [
        "Decreto 807 de 1993, arts. 15 y 132",
        "Decreto 352 de 2002, arts. 57, 58 y 59",
        "Resolución SDH-000195 de 2025, art. 2",
    ]


@pytest.mark.unit
@pytest.mark.req(F5, "RF-ICA-02 · Estimación por actividad")
def test_la_lista_de_fuentes_suma_las_normas_de_las_notas_sin_repetir() -> None:
    from src.agents.agente import componer_texto
    from src.agents.herramientas import Resultado

    nota = "Se aproximan (Decreto 807 de 1993, art. 15) y hay mora (Ley 1 de 2020, art. 3)."
    resultado = Resultado({}, fuentes=("Ley 1 de 2020, arts. 3 y 4",), notas=(nota,))
    texto, fuentes = componer_texto("Respuesta.", [resultado], [], con_anexos=True)
    assert texto.endswith("Fuentes: Ley 1 de 2020, arts. 3 y 4; Decreto 807 de 1993, art. 15.")
    assert fuentes == ["Ley 1 de 2020, arts. 3 y 4"]  # las del contrato no cambian


@pytest.mark.unit
@pytest.mark.req("RF-ICA-02 · Estimación por actividad")
def test_la_tarifa_de_un_ciiu_trae_la_fuente_de_su_clasificacion() -> None:
    from src.services.ica import PeriodoICA, buscar_tarifa_ica

    de_2026 = buscar_tarifa_ica("6201", PeriodoICA(2026))
    assert any(f.startswith("Resolución SDH-000265 de 2021, art. 1") for f in de_2026.fuentes)
    assert de_2026.fuentes[0] == de_2026.fuente  # la de la tarifa, primero
    assert buscar_tarifa_ica("6201", PeriodoICA(2027)).fuentes == (
        buscar_tarifa_ica("6201", PeriodoICA(2027)).fuente,
    )
