"""Tablas de la base de conocimiento: ninguna pierde filas y el cierre no corta la norma."""

import re
import sys
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts" / "curaduria"))

import convertir  # noqa: E402

KB = RAIZ / "knowledge_base"
NORMAS = sorted(r for r in KB.rglob("*.md") if r.parent.name.startswith("normativa_"))

pytestmark = [pytest.mark.unit, pytest.mark.req("RF-OBS-04 · Actualización de la base vectorial")]


def _markdown(html: str) -> str:
    return convertir.tabla_markdown(BeautifulSoup(html, "html.parser").table) or ""


def _articulos(texto: str) -> dict[str, str]:
    partes = re.split(r"(?m)^## Artículo ([\d.]+)$", texto)
    return dict(zip(partes[1::2], partes[2::2], strict=True))


def _tablas(texto: str) -> list[list[list[str]]]:
    """Tablas Markdown de un texto, cada una con su encabezado y sin la fila separadora."""
    resultado: list[list[list[str]]] = []
    actual: list[list[str]] = []
    for linea in [*texto.splitlines(), ""]:
        if linea.startswith("|"):
            celdas = [c.strip() for c in linea.strip().strip("|").split("|")]
            if not (any(celdas) and all(re.fullmatch(r"-+", c) for c in celdas if c)):
                actual.append(celdas)
        elif actual:
            resultado.append(actual)
            actual = []
    return resultado


def _filas(coleccion: str, archivo: str, articulo: int) -> list[list[list[str]]]:
    texto = (KB / coleccion / archivo).read_text(encoding="utf-8")
    return [t[1:] for t in _tablas(_articulos(texto)[str(articulo)])]


# ------------------------------------------------------------------ el conversor


def test_una_tabla_de_texto_conserva_todas_sus_filas() -> None:
    html = (
        "<table><tr><td>Sector de actividad</td><td>Descripción</td></tr>"
        "<tr><td>Industria</td><td>Procesamiento y conservación de carne</td></tr>"
        "<tr><td>Servicios</td><td>Actividades de centros de llamadas</td></tr></table>"
    )
    assert _markdown(html).splitlines() == [
        "| Sector de actividad | Descripción |",
        "|---|---|",
        "| Industria | Procesamiento y conservación de carne |",
        "| Servicios | Actividades de centros de llamadas |",
    ]


def test_una_tabla_de_porcentajes_no_junta_las_filas_que_se_repiten() -> None:
    html = (
        "<table><tr><td>Inversión</td><td>Año 1</td><td>Año 2</td></tr>"
        "<tr><td>Hasta 10</td><td>100%</td><td>100%</td></tr>"
        "<tr><td>Hasta 20</td><td>100%</td><td>100%</td></tr>"
        "<tr><td>Hasta 30</td><td>100%</td><td>50%</td></tr></table>"
    )
    lineas = _markdown(html).splitlines()
    assert lineas[0] == "| Inversión | Año 1 | Año 2 |"
    assert lineas[2:] == [
        "| Hasta 10 | 100% | 100% |",
        "| Hasta 20 | 100% | 100% |",
        "| Hasta 30 | 100% | 50% |",
    ]


def test_el_encabezado_de_dos_niveles_une_rotulo_y_subrotulo() -> None:
    html = (
        '<table><tr><td rowspan="2">Monto</td><td colspan="3">Años de la exención</td></tr>'
        "<tr><td>1</td><td>2</td><td>3</td></tr>"
        "<tr><td>Hasta 5</td><td>100%</td><td>50%</td><td>10%</td></tr></table>"
    )
    lineas = _markdown(html).splitlines()
    assert lineas[0] == "| Monto | Año 1 | Año 2 | Año 3 |"
    assert lineas[2:] == ["| Hasta 5 | 100% | 50% | 10% |"]


def test_la_celda_que_ocupa_dos_columnas_lleva_el_texto_solo_en_la_primera() -> None:
    html = (
        "<table><tr><td>Desde</td><td>Hasta</td><td>Tarifa</td></tr>"
        "<tr><td>$ 1</td><td>$ 100</td><td>5</td></tr>"
        '<tr><td colspan="2">Más de $ 100</td><td>6</td></tr></table>'
    )
    assert _markdown(html).splitlines()[-1] == "| Más de $ 100 | — | 6 |"


def test_la_primera_fila_con_celda_combinada_no_se_une_si_la_siguiente_trae_valores() -> None:
    html = (
        '<table><tr><td>AÑO</td><td colspan="2">DIARIOS</td></tr>'
        "<tr><td>$ 0</td><td>$ 15.000.000</td><td>0</td></tr>"
        "<tr><td>$ 15.000.001</td><td>$ 20.000.000</td><td>8</td></tr></table>"
    )
    assert len(_markdown(html).splitlines()) == 4


def test_una_celda_con_caracteres_de_formato_no_cambia_el_encabezado() -> None:
    html = "<table><tr><td>Año​</td><td>Predial​</td></tr><tr><td>1​</td><td>100%​</td></tr></table>"
    assert _markdown(html).splitlines() == ["| Año | Predial |", "|---|---|", "| 1 | 100% |"]


def test_un_rotulo_en_mayusculas_no_es_una_firma() -> None:
    assert not convertir._es_firma("PARÁGRAFO TRANSITORIO")
    assert not convertir._es_firma("PARÁGRAFO PRIMERO")
    assert convertir._es_firma("ERNESTO MACÍAS TOVAR")


def test_el_cierre_no_corta_en_el_encabezado_de_una_tabla_en_mayusculas() -> None:
    texto = (
        "Artículo 2°. Tarifas.\n"
        "| ESTRATO | BASE GRAVABLE DESDE | BASE GRAVABLE HASTA | TARIFA POR MIL |\n"
        "|---|---|---|---|\n"
        "| 1 | $ 1 | $ 100 | 5 |\n"
        "PARÁGRAFO TRANSITORIO\n"
        "Texto del parágrafo.\n"
        "PUBLÍQUESE Y CÚMPLASE.\n"
        "Dado en Bogotá, D.C., a los 8 días del mes de octubre del año 2026.\n"
        "El Presidente del Concejo,\n"
        "JUAN PÉREZ GÓMEZ\n"
    )
    cortado = convertir.recortar_cierre(texto)
    assert "| ESTRATO |" in cortado and "PARÁGRAFO TRANSITORIO" in cortado
    assert cortado.endswith("octubre del año 2026.")


# ------------------------------------------------------------ la base de conocimiento


def test_ninguna_tabla_de_la_base_queda_sin_filas_de_datos() -> None:
    for ruta in NORMAS:
        for tabla in _tablas(ruta.read_text(encoding="utf-8")):
            assert len(tabla) >= 2, (ruta.name, tabla[0][:3])


def test_ningun_encabezado_de_tabla_tiene_una_celda_de_mas_de_80_caracteres() -> None:
    for ruta in NORMAS:
        for tabla in _tablas(ruta.read_text(encoding="utf-8")):
            assert all(len(c) <= 80 for c in tabla[0]), (ruta.name, tabla[0][:2])


def test_el_acuerdo_1084_conserva_las_filas_de_sus_tablas() -> None:
    for coleccion, archivo in (
        ("normativa_ica", "acuerdo_1084_2026_ica.md"),
        ("normativa_ipu", "acuerdo_1084_2026.md"),
    ):
        art_3 = _filas(coleccion, archivo, 3)
        assert len(art_3[0]) == 78  # sectores de actividad
        assert [len(t) for t in art_3[1:3]] == [2, 1]  # descuento de 60 % y 80 %; Año / Predial
        assert len(art_3[2][0]) == 7
    ica = "acuerdo_1084_2026_ica.md"
    sectores, exencion = _filas("normativa_ica", ica, 1)[:2]
    assert len(sectores) == 92
    assert len(exencion) == 3 and all(len(f) == 12 for f in exencion)
    assert all(re.search(r"\d|^-$", c) for f in exencion for c in f[2:])
    encabezado = _tablas(_articulos((KB / "normativa_ica" / ica).read_text())["1"])[1][0]
    assert encabezado[2:] == [f"Año {n}" for n in range(1, 11)]


def test_la_exencion_de_352_291_uvt_trae_los_diez_anios_en_el_encabezado() -> None:
    for coleccion, archivo in (
        ("normativa_ica", "acuerdo_1084_2026_ica.md"),
        ("normativa_ipu", "acuerdo_1084_2026.md"),
    ):
        texto = _articulos((KB / coleccion / archivo).read_text(encoding="utf-8"))["3"]
        encabezado = next(t[0] for t in _tablas(texto) if "Requisito de empleos" in t[0])
        assert encabezado[2:] == [f"Año {n}" for n in range(1, 11)]


def test_las_tablas_de_tarifas_del_decreto_352_conservan_todas_sus_filas() -> None:
    tablas = _filas("normativa_ipu", "decreto_352_2002_cap1.md", 25)
    assert [len(t) for t in tablas] == [6, 2, 4, 2, 3, 3, 3, 2]
    assert ["Rurales", "16%o", "(dieciséis por mil)"] in tablas[0]
    assert any("Alto Impacto" in f[0] for t in tablas for f in t)


def test_el_art_2_del_acuerdo_105_conserva_sus_tablas_y_el_texto_original() -> None:
    texto = (KB / "normativa_ipu" / "acuerdo_105_2003.md").read_text(encoding="utf-8")
    articulo = _articulos(texto)["2"]
    assert len(articulo) > 14_000
    filas = [len(t) - 1 for t in _tablas(articulo)]
    assert 32 in filas  # residenciales generales: 32 rangos
    assert 10 in filas  # clubes
    assert "El texto original del artículo era el siguiente:" in articulo


def test_la_resolucion_194_trae_transcritas_las_tablas_de_los_arts_2_y_3_sin_la_nota_al_pie() -> (
    None
):
    texto = (KB / "normativa_ipu" / "resolucion_000194_2025_rangos.md").read_text(encoding="utf-8")
    articulos = _articulos(texto)
    assert "dane.gov.co" not in texto
    for numero, filas in (("2", 6), ("3", 10)):
        assert "**Tabla transcrita.**" in articulos[numero]
        assert [len(t) - 1 for t in _tablas(articulos[numero])] == [filas]
    assert "| Comercial (62) | 9,5 | $ 363.264.001 | $ - |" in articulos["2"]
    assert articulos["4"].strip().endswith("PUBLÍQUESE Y CÚMPLASE")  # cierre sin firmas


def test_el_decreto_352_une_las_filas_partidas_y_pone_el_encabezado_del_art_55_en_la_tabla() -> (
    None
):
    texto = (KB / "normativa_ica" / "decreto_352_2002_cap2.md").read_text(encoding="utf-8")
    assert "constructores y urbanizadores; y presentación de películas" in texto
    assert not re.search(r"(?m)^\| urbanizadores;", texto)
    assert "| Rango de ingresos netos, desde | Rango de ingresos netos, hasta |" in texto
    assert "RANGO DE INGRESOS NETOS NÚMERO" not in texto
    assert "| $ 60.000.001 | $ 77.900.000 | 60 |" in texto


def test_las_vistas_muestran_la_categoria_literal_y_cada_fecha_en_su_linea() -> None:
    vistas = RAIZ / "docs" / "verificacion"
    ipu = (vistas / "ipu_2027.html").read_text(encoding="utf-8")
    assert "pequena_propiedad" not in ipu and "depositos_y_parqueaderos" not in ipu
    assert "Pequeña propiedad rural destinada a la producción agropecuaria" in ipu
    assert '<td class="n">135 SMMLV</td>' in ipu and "Más de 135 SMMLV" in ipu
    calendario = (vistas / "calendario_2026.html").read_text(encoding="utf-8")
    for fecha in ("2026-10-09", "2026-12-04", "2026-12-11", "2027-02-12"):
        assert f'<span class="n">{fecha}</span>' in calendario
    assert "Texto de los artículos de donde salen las fechas" in calendario
