"""Base de conocimiento: texto ajeno, caracteres, tablas, notas de vigencia y artículos del ICA."""

import re
import sys
import unicodedata
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts" / "curaduria"))

import convertir  # noqa: E402

KB = RAIZ / "knowledge_base"
ARCHIVOS = sorted(KB.rglob("*.md"))
NORMAS = [r for r in ARCHIVOS if r.parent.name.startswith("normativa_")]

pytestmark = [pytest.mark.unit, pytest.mark.req("RF-OBS-04 · Actualización de la base vectorial")]


def _norma(coleccion: str, archivo: str) -> str:
    return (KB / coleccion / archivo).read_text(encoding="utf-8")


def _articulos(texto: str) -> list[tuple[str, str]]:
    partes = re.split(r"(?m)^## Artículo ([\d.]+)$", texto)
    return list(zip(partes[1::2], partes[2::2], strict=True))


def _articulo(texto: str, numero: int) -> str:
    return dict(_articulos(texto))[str(numero)]


def _tablas(texto: str) -> list[list[list[str]]]:
    """Tablas Markdown de un texto: cada una, con su encabezado, sin la fila separadora."""
    resultado: list[list[list[str]]] = []
    actual: list[list[str]] = []
    for linea in [*texto.splitlines(), ""]:
        if linea.startswith("|"):
            celdas = [c.strip() for c in linea.strip().strip("|").split("|")]
            if not all(re.fullmatch(r"-+", c) for c in celdas if c):
                actual.append(celdas)
        elif actual:
            resultado.append(actual)
            actual = []
    return resultado


# ---------------------------------------------------------------- texto ajeno y firmas


def test_ningun_archivo_trae_el_texto_conciliado_ni_la_sentencia() -> None:
    for ruta in ARCHIVOS:
        texto = ruta.read_text(encoding="utf-8")
        assert "TEXTO CONCILIADO" not in texto, ruta.name
        assert "SENTENCIA C-748" not in texto, ruta.name


def test_ningun_articulo_sin_tablas_pasa_de_15000_caracteres() -> None:
    for ruta in NORMAS:
        for numero, texto in _articulos(ruta.read_text(encoding="utf-8")):
            sin_tablas = "\n".join(
                linea for linea in texto.splitlines() if not linea.startswith("|")
            )
            assert len(sin_tablas) <= 15_000, (ruta.name, numero, len(sin_tablas))


def test_la_ley_1581_termina_en_el_art_30_y_el_art_26_no_arrastra_el_titulo_ix() -> None:
    texto = _norma("normativa_datos", "ley_1581_2012.md")
    art_30 = _articulo(texto, 30)
    assert art_30.strip().endswith("La presente ley rige a partir de su promulgación.")
    assert len(art_30) < 300
    art_26 = _articulo(texto, 26)
    assert "TÍTULO IX" not in art_26 and "INEXEQUIBLE" not in art_26
    assert "Certificación de antecedentes judiciales" not in texto


def test_el_ultimo_articulo_no_trae_nombres_ni_cargos_de_quienes_firman() -> None:
    for ruta in NORMAS:
        ultimo = _articulos(ruta.read_text(encoding="utf-8"))[-1][1].strip()
        assert convertir.recortar_cierre(ultimo) == ultimo, ruta.name


def test_el_cierre_conserva_la_formula_y_la_fecha_de_expedicion() -> None:
    texto = _norma("normativa_ipu", "decreto_474_2016.md")
    assert texto.rstrip().endswith(
        "Dado en Bogotá, D.C., a los 26 días del mes de octubre del año 2016"
    )
    assert "PUBLÍQUESE Y CÚMPLASE." in texto
    assert (
        _norma("normativa_ica", "acuerdo_1084_2026_ica.md")
        .rstrip()
        .endswith("Dada en Bogotá, D.C., a los 08 días del mes de octubre del año 2026.")
    )


def test_ningun_articulo_arrastra_encabezados_de_la_parte_siguiente() -> None:
    for ruta in NORMAS:
        for numero, texto in _articulos(ruta.read_text(encoding="utf-8")):
            ultima = [linea for linea in texto.strip().splitlines() if linea.strip()][-1]
            assert not re.match(r"(?i)^(T[ÍI]TULO|CAP[ÍI]TULO|SECCI[ÓO]N)\b", ultima), (
                ruta.name,
                numero,
            )
    art_45 = _articulo(_norma("normativa_ipu", "decreto_639_2025.md"), 45)
    assert "ESTAMPILLAS" not in art_45


# ---------------------------------------------------------- caracteres y pie de página


def test_ningun_caracter_de_formato_unicode_en_la_base() -> None:
    for ruta in ARCHIVOS:
        texto = ruta.read_text(encoding="utf-8")
        formato = [c for c in texto if unicodedata.category(c) == "Cf"]
        assert formato == [], (ruta.name, len(formato))


def test_la_resolucion_194_no_trae_el_pie_de_pagina() -> None:
    texto = _norma("normativa_ipu", "resolucion_000194_2025_rangos.md")
    for ruido in ("PBX", "haciendabogota", "Carrera 30", "NIT."):
        assert ruido not in texto


# ---------------------------------------------------------------- tablas


def test_ninguna_tabla_repite_el_encabezado_ni_tiene_filas_corridas() -> None:
    for ruta in NORMAS:
        for tabla in _tablas(ruta.read_text(encoding="utf-8")):
            encabezado, datos = tabla[0], tabla[1:]
            rotulos = " ".join(encabezado).lower()
            for fila in datos:
                con_texto = [c for c in fila if c]
                repetida = con_texto and all(c.lower() in rotulos for c in con_texto)
                assert not repetida, (ruta.name, fila)
                assert len(fila) == len(encabezado), (ruta.name, fila)
                # subtítulos como «b. Actividades Comerciales» y celdas que la fuente deja vacías
                if con_texto and not fila[0]:
                    assert len(con_texto) < len(fila), (ruta.name, fila)


def test_la_tabla_preferencial_del_art_20_tiene_el_encabezado_unido() -> None:
    texto = _articulo(_norma("normativa_ipu", "acuerdo_1084_2026.md"), 20)
    assert "| ESTRATO | BASE GRAVABLE DESDE | BASE GRAVABLE HASTA | TARIFA POR MIL |" in texto
    assert "| 1 y 2 | 16 SMMLV | 107 SMMLV | 1 |" in texto
    assert "| BASE GRAVABLE DESDE | BASE GRAVABLE HASTA | TARIFA POR MIL |" in texto
    assert "**Predios residenciales rurales**" in texto
    assert "| Desde | Hasta | Tarifa por mil |" in texto
    assert "| Más de $ 4.411.881.000 | — | 13,9 |" in texto
    assert "| Más de $ 4.411.881.000 | Más de $ 4.411.881.000 |" not in texto
    assert "Base gravable Desde | Base gravable Hasta | Tarifas por mil 2027" in texto


def test_el_acuerdo_648_conserva_categoria_y_destino_en_cada_fila() -> None:
    texto = _articulo(_norma("normativa_ipu", "acuerdo_648_2016.md"), 1)
    assert (
        "| Residencial rural | 61 | 6.5 | Más de 135 salarios mínimos legales mensuales vigentes |"
        in texto
    )
    assert "| Dotacionales | 66 | 5 | De propiedad de entes públicos |" in texto
    assert "| Rangos Desde | Rangos Hasta | Tarifas por mil |" in texto


def test_la_resolucion_265_trae_las_celdas_corregidas() -> None:
    texto = _norma("normativa_ica", "resolucion_sdh_000265_2021.md")
    assert (
        "| 103 | 2394 | Fabricación de cemento, cal y yeso | 11,04 | 11,04 | 11,04 | 11,04 |"
        in texto
    )
    assert (
        "| 103 | 2816 | Fabricación de equipo de elevación y manipulación | 11,04 | 11,04 |"
        in texto
    )
    assert "| 302 | 4312 | Preparación del terreno | 6,9 | 6,9 | 6,9 | 6,9 |" in texto
    assert not re.search(r"\d \d,\d\d|\d ,\d|,\d,\d", texto)
    assert texto.count("Agrupación") == 1
    assert "| 304 | 5330 |" in texto


# ---------------------------------------------------------------- notas de vigencia y artículos


@pytest.mark.parametrize(
    ("coleccion", "archivo", "frase"),
    [
        ("normativa_ipu", "acuerdo_105_2003.md", "rige desde el predial de 2027"),
        ("normativa_ipu", "acuerdo_648_2016.md", "Resolución SDH-000194 de 2025"),
        ("normativa_ipu", "acuerdo_648_2016.md", "art. 285 del Acuerdo 927 de 2024"),
        ("normativa_ipu", "acuerdo_780_2020.md", "son de 2020"),
        ("normativa_ica", "acuerdo_65_2002.md", "desde el bimestre 6 de 2026"),
        ("normativa_ica", "acuerdo_1084_2026_ica.md", "1 de enero de 2027"),
        ("normativa_ica", "acuerdo_1019_2025_ica.md", "todo el año gravable 2026"),
    ],
)
def test_los_archivos_que_mezclan_anios_dicen_para_cual_rige_cada_parte(
    coleccion: str, archivo: str, frase: str
) -> None:
    texto = _norma(coleccion, archivo)
    encabezado = texto.split("\n## Artículo ")[0]
    assert "**Vigencia por año gravable.**" in encabezado
    assert frase in encabezado


def test_el_art_45_del_decreto_639_remite_a_los_incisos_derogados_y_a_la_ley_1995() -> None:
    art_45 = _articulo(_norma("normativa_ipu", "decreto_639_2025.md"), 45)
    assert "**Vigencia.**" in art_45
    assert "art. 285 del Acuerdo 927 de 2024" in art_45
    assert "Ley 1995 de 2019" in art_45


def test_las_erratas_de_la_fuente_del_decreto_639_se_dejan_como_estan() -> None:
    """La compilación de Hacienda (y el Régimen Legal en el Decreto 474) traen estas erratas."""
    compilado = _norma("normativa_ipu", "decreto_639_2025.md")
    art_207 = _articulo(compilado, 207)
    assert "IGUALO MENOR A 16 SMLMV N." in art_207 and "igualo menor a 16 SMLMV" in art_207
    assert "lijado" in _articulo(compilado, 45) and "lije" in _articulo(compilado, 205)
    assert "igualo menor a 16 SMLMV" in _articulo(
        _norma("normativa_ipu", "decreto_474_2016.md"), 17
    )


def test_el_art_205_del_decreto_639_esta_tambien_en_la_coleccion_del_ica() -> None:
    ica = _norma("normativa_ica", "decreto_639_2025_ica.md")
    assert [n for n, _ in _articulos(ica)] == ["205"]
    assert (
        _articulo(ica, 205).strip()
        == _articulo(_norma("normativa_ipu", "decreto_639_2025.md"), 205).strip()
    )
    assert "391 UVT" in _articulo(ica, 205)
    cambios = (RAIZ / "docs" / "cambios_para_documento.md").read_text(encoding="utf-8")
    assert "art. 205" in cambios and "fuera de la tabla" in cambios


def test_el_art_44_del_acuerdo_1019_esta_en_la_coleccion_del_ica() -> None:
    texto = _norma("normativa_ica", "acuerdo_1019_2025_ica.md")
    articulo = _articulo(texto, 44)
    assert "Texto anterior, no vigente" in articulo
    assert "| 3(sic) | 30 |" in articulo


def test_la_ley_14_trae_cada_capitulo_al_inicio_del_articulo_que_encabeza() -> None:
    texto = _norma("normativa_ica", "ley_14_1983.md")
    for numero, articulo in _articulos(texto):
        final = [linea for linea in articulo.strip().splitlines() if linea.strip()][3:][-3:]
        assert not any(re.match(r"CAP[ÍI]TULO\b", linea) for linea in final), numero
    assert (
        _articulo(texto, 32).lstrip().startswith("CAPÍTULO II\n\nImpuesto de Industria y Comercio")
    )
    assert _articulo(texto, 41).lstrip().startswith("CAPÍTULO III")
    assert len(re.findall(r"(?m)^CAPÍTULO [IVX]+$", texto)) >= 7


@pytest.mark.parametrize(
    ("coleccion", "archivo", "numero", "frases"),
    [
        ("normativa_ipu", "decreto_639_2025.md", 207, ["derogó el Acuerdo 77 de 2002", "art. 15"]),
        ("normativa_ica", "decreto_639_2025_ica.md", 205, ["art. 26", "1 de enero de 2027"]),
        ("normativa_ipu", "decreto_639_2025.md", 205, ["art. 26", "1 de enero de 2027"]),
    ],
)
def test_los_articulos_del_decreto_639_dicen_hasta_cuando_rigen(
    coleccion: str, archivo: str, numero: int, frases: list[str]
) -> None:
    articulo = _articulo(_norma(coleccion, archivo), numero)
    assert "**Vigencia.**" in articulo
    assert all(frase in articulo for frase in frases)


def test_el_acuerdo_648_y_el_105_dicen_que_rige_para_el_predial_de_2026_y_de_2027() -> None:
    encabezado_648 = _norma("normativa_ipu", "acuerdo_648_2016.md").split("\n## Artículo ")[0]
    assert "art. 20" in encabezado_648 and "reemplaza las tablas de su art. 1" in encabezado_648
    encabezado_105 = _norma("normativa_ipu", "acuerdo_105_2003.md").split("\n## Artículo ")[0]
    assert "Acuerdo 897 de 2023" in encabezado_105
    assert "Resolución SDH-000194 de 2025" in encabezado_105
