"""Curaduría (B2), segunda ronda: base limpia, tablas completas y vistas legibles."""

import re
import sys
from pathlib import Path

import pytest
import yaml

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts" / "curaduria"))

import contrastar_1084  # noqa: E402
import contrastar_rangos  # noqa: E402
import convertir  # noqa: E402

DATOS = RAIZ / "datos"
KB = RAIZ / "knowledge_base"
VISTAS = RAIZ / "docs" / "verificacion"
CATALOGO = yaml.safe_load((RAIZ / "scripts/curaduria/fuentes.yaml").read_text(encoding="utf-8"))

pytestmark = pytest.mark.unit


def _yaml(ruta: str) -> dict:
    return yaml.safe_load((DATOS / ruta).read_text(encoding="utf-8"))


def _norma(coleccion: str, archivo: str) -> str:
    return (KB / coleccion / archivo).read_text(encoding="utf-8")


def _articulo(texto: str, numero: int) -> str:
    inicio = texto.index(f"\n## Artículo {numero}\n")
    fin = texto.find("\n## Artículo ", inicio + 1)
    return texto[inicio : fin if fin != -1 else len(texto)]


# ---------------------------------------------------------------- base de conocimiento


@pytest.mark.req("RF-OBS-04 · Actualización de la base vectorial")
def test_la_base_de_conocimiento_no_trae_ruido_web() -> None:
    for ruta in KB.rglob("*.md"):
        texto = ruta.read_text(encoding="utf-8")
        for ruido in ("javascript:", "](", "![", "Ir al inicio", "Jurisprudencia Vigencia"):
            assert ruido not in texto, f"{ruta.name}: {ruido}"


@pytest.mark.req("RF-IPU-05 · Citación de la norma")
def test_las_normas_completas_empiezan_en_el_art_1_y_no_tienen_saltos() -> None:
    completas = [f for f in CATALOGO["fuentes"] if f["articulos"] == "todos"]
    assert completas
    for fuente in completas:
        texto = _norma(fuente["coleccion"], f"{fuente['id']}.md")
        numeros = [int(n) for n in re.findall(r"(?m)^## Artículo (\d+)$", texto)]
        assert numeros == list(range(1, len(numeros) + 1)), fuente["id"]


@pytest.mark.req("RF-IPU-05 · Citación de la norma")
def test_el_acuerdo_648_trae_el_art_1_con_las_tarifas_del_predial() -> None:
    texto = _norma("normativa_ipu", "acuerdo_648_2016.md")
    articulo = _articulo(texto, 1)
    assert "modifíquense las tarifas del impuesto predial unificado" in articulo
    assert "artículo 2°" in articulo


@pytest.mark.req("RF-IPU-05 · Citación de la norma")
def test_el_acuerdo_1084_sale_del_texto_digital_sin_errores_de_ocr() -> None:
    texto = _norma("normativa_ipu", "acuerdo_1084_2026.md")
    assert "Norma1.jsp?i=194513" in texto.splitlines()[2]
    articulo_15 = _articulo(texto, 15)
    assert "| Residenciales | 600 UVT |" in articulo_15
    assert "1200 UT" not in articulo_15 and "500 UVT" not in articulo_15
    assert "CONCEJO DE BOGOTÁ" not in texto and "ACUERDO No" not in texto
    assert not re.search(r"Artículo \d+[%”?*]", texto)
    articulos = [int(n) for n in re.findall(r"(?m)^## Artículo (\d+)$", texto)]
    assert articulos == [3, 4, 5, 7, 8, 10, 11, 12, 13, 14, 15, 16, 17, 18, 20, 27, 28, 35, 52]


@pytest.mark.req("RF-ICA-01 · Consultas conceptuales de ICA")
def test_el_acuerdo_1084_del_ica_trae_los_arts_del_reparto() -> None:
    texto = _norma("normativa_ica", "acuerdo_1084_2026_ica.md")
    articulos = [int(n) for n in re.findall(r"(?m)^## Artículo (\d+)$", texto)]
    assert articulos == [1, 2, 3, 4, 7, 21, 24, 25, 26, 52]
    assert "| 3 (sic) | 30 |" in _articulo(texto, 24)


@pytest.mark.req("RF-ICA-03 · Fechas de declaración")
def test_la_resolucion_195_trae_las_tablas_de_fechas_que_estan_en_imagenes() -> None:
    ica = _articulo(_norma("normativa_ica", "resolucion_sdh_000195_2025_ica.md"), 1)
    predial = _norma("normativa_ipu", "resolucion_sdh_000195_2025.md")
    assert "Tabla en imagen en la fuente, transcrita" in ica
    assert "Tabla en imagen en la fuente, transcrita" in _articulo(predial, 5)
    assert "IMPUESTO DE VEHÍCULOS AUTOMOTORES" not in predial

    def fecha(iso: str) -> str:
        anio, mes, dia = iso.split("-")
        meses = "enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre"
        nombres = [*meses.split(), "diciembre"]
        return f"{int(dia)} de {nombres[int(mes) - 1]} de {anio}"

    plazos = {p["concepto"]: p["fechas"] for p in _yaml("calendario/2026.yaml")["plazos"]}
    for iso in plazos["ica_bimestral_comun_mayor_391_uvt"]:
        assert fecha(iso).replace("9 de", "09 de") in ica or fecha(iso) in ica, iso
    for iso in plazos["spac_cuotas"]:
        assert fecha(iso) in _articulo(predial, 5), iso


@pytest.mark.req("RF-IPU-05 · Citación de la norma")
def test_el_decreto_474_es_texto_anterior_y_remite_al_decreto_639() -> None:
    decreto = _norma("normativa_ipu", "decreto_474_2016.md")
    assert decreto.count("Texto anterior, no vigente") == 21
    assert "Decreto 639 de 2025 (Decreto Único Distrital Tributario), art. 217" in decreto
    compilado = _norma("normativa_ipu", "decreto_639_2025.md")
    articulos = [int(n) for n in re.findall(r"(?m)^## Artículo (\d+)$", compilado)]
    assert articulos == [43, 44, 45, 205, 206, 207, *range(217, 228), 231, 232, 233, 263]
    assert "Decreto 474 de 2016" in _articulo(compilado, 218)


@pytest.mark.req("RF-ICA-01 · Consultas conceptuales de ICA")
def test_la_ley_1819_del_ica_trae_los_arts_342_y_345() -> None:
    texto = _norma("normativa_ica", "ley_1819_2016_ica.md")
    assert "BASE GRAVABLE Y TARIFA" in _articulo(texto, 342)
    assert "DEFINICIÓN DE LA ACTIVIDAD DE SERVICIOS" in _articulo(texto, 345)


# ---------------------------------------------------------------- tablas de datos


@pytest.mark.req("RF-IPU-04 · Plazos y descuentos")
def test_ipu_2026_trae_los_clubes_del_art_3_y_dice_por_que_omite_otras_categorias() -> None:
    datos = _yaml("tarifas/ipu_2026.yaml")
    clubes = datos["clubes_destino_66"]
    assert len(clubes) == 10
    assert [c["tarifa_por_mil"] for c in clubes][0] == "6.5"
    assert [c["tarifa_por_mil"] for c in clubes][-1] == "9.15"
    assert clubes[-1]["hasta"] is None
    assert datos["contraste"]["rangos_clubes_destino_66"] == 10
    assert "Acuerdo 897 de 2023" in datos["otras_categorias_no_transcritas"]
    assert "residencial, comercial y lote" in datos["otras_categorias_no_transcritas"]


@pytest.mark.req("RF-IPU-04 · Plazos y descuentos")
@pytest.mark.skipif(
    not contrastar_rangos.PDF.exists(), reason="el PDF de la resolución no se versiona"
)
def test_ipu_2026_coincide_con_el_pdf_en_los_tres_articulos() -> None:
    resultado = contrastar_rangos.contrastar()
    assert resultado["filas"] == {"art_1": 30, "art_2": 6, "art_3": 10}
    assert resultado["diferencias"] == []


@pytest.mark.req("RF-IPU-04 · Plazos y descuentos")
def test_las_tablas_del_acuerdo_1084_coinciden_con_su_texto_digital() -> None:
    resultados = contrastar_1084.contrastar()
    assert len(resultados) == 9
    for resultado in resultados:
        assert resultado["diferencias"] == [], resultado["tabla"]
        assert resultado["filas_en_el_texto"] == resultado["filas_en_el_yaml"]


@pytest.mark.req("RF-ICA-01 · Consultas conceptuales de ICA")
def test_todos_los_ciiu_tienen_solo_digitos() -> None:
    codigos = [f["ciiu"] for f in _yaml("tarifas/ica_2026.yaml")["por_actividad"]]
    en_2027 = _yaml("tarifas/ica_2027.yaml")
    codigos += [f["ciiu"] for f in en_2027["por_actividad"]]
    codigos += [f["ciiu"] for f in en_2027["progresiva_financiera"]]
    assert codigos
    assert [c for c in codigos if not c.isdigit()] == []


@pytest.mark.req("RF-ICA-01 · Consultas conceptuales de ICA")
def test_ica_2026_corrige_los_dos_ciiu_mal_escritos_y_conserva_la_nota() -> None:
    por_codigo = {f["ciiu"]: f for f in _yaml("tarifas/ica_2026.yaml")["por_actividad"]}
    assert "«/ 8523»" in por_codigo["8523"]["nota"]
    assert por_codigo["8523"]["tarifa_por_mil"] == "7"
    assert "«85232/8551»" in por_codigo["85232"]["nota"]
    assert por_codigo["85232"]["tarifa_por_mil"] == "9.66"
    assert por_codigo["8551"]["tarifa_por_mil"] == "9.66"


@pytest.mark.req("RF-ICA-01 · Consultas conceptuales de ICA")
def test_ica_2026_explica_por_que_6515_y_6523_van_a_14_por_mil() -> None:
    datos = _yaml("tarifas/ica_2026.yaml")
    por_codigo = {f["ciiu"]: f for f in datos["por_actividad"]}
    for codigo in ("6515", "6523"):
        fila = por_codigo[codigo]
        assert fila["tarifa_por_mil"] == "14"
        assert "grupo 401" in fila["fuente_tarifa"]
        assert "trae 11,04" in fila["fuente_tarifa"]
        assert "13,1" not in fila["fuente_tarifa"]
    assert "6515 y 6523 van a 14 por mil" in datos["criterio_de_la_resolucion_265"]


@pytest.mark.req("RF-ICA-01 · Consultas conceptuales de ICA")
def test_ica_2026_trae_las_demas_actividades_del_texto_original() -> None:
    demas = {
        d["clase"]: d["tarifa_por_mil"] for d in _yaml("tarifas/ica_2026.yaml")["demas_actividades"]
    }
    assert demas == {"industriales": "11.04", "comerciales": "11.04", "servicios": "9.66"}


@pytest.mark.req("RF-ICA-03 · Fechas de declaración")
def test_ica_2026_dice_para_que_periodos_rigen_las_normas_derogadas() -> None:
    datos = _yaml("tarifas/ica_2026.yaml")
    texto = yaml.safe_dump(datos, allow_unicode=True)
    assert "rige_hasta" not in texto
    por_codigo = {f["ciiu"]: f for f in datos["por_actividad"]}
    assert "bimestres 1 a 5" in por_codigo["5330"]["rige_para"]
    assert "bimestres 1 a 5" in por_codigo["58112"]["tarifa_condicionada"]["rige_para"]
    assert "todo el año 2026" in datos["regimen_simple_2026"]["rige"]
    assert (
        "9 de octubre de 2026"
        in datos["periodos_que_cubre"]["entrada_en_vigencia_del_acuerdo_1084"]
    )


@pytest.mark.req("RF-IPU-04 · Plazos y descuentos")
def test_la_sobretasa_trae_sus_reglas_y_el_texto_literal_de_cada_categoria() -> None:
    datos = _yaml("tarifas/sobretasa_alumbrado_2027.yaml")
    articulos = {r["articulo"] for r in datos["reglas"]}
    assert {"14, parágrafo", "11, parágrafo 1", "15, parágrafo"} <= articulos
    reglas = " ".join(r["regla"] for r in datos["reglas"])
    assert "SISBÉN" in reglas and "personas naturales" in reglas and "30 de noviembre" in reglas
    assert "arts. 3, 4, 5 y 8" in reglas
    assert "usos mixtos" in reglas and "art. 20" in reglas
    for tarifa in datos["tarifas_por_mil"]:
        assert tarifa["descripcion"].endswith(".")
        assert len(tarifa["categoria"]) < 60


@pytest.mark.req("RF-ICA-01 · Consultas conceptuales de ICA")
def test_ica_2027_trae_el_simple_y_las_demas_actividades_del_texto_digital() -> None:
    datos = _yaml("tarifas/ica_2027.yaml")
    simple = datos["regimen_simple_2027"]
    assert [(t["numeral"], t["tarifa_por_mil"]) for t in simple["tarifas_por_mil"]] == [
        ("1", "10"),
        ("2", "14"),
        ("3", "29"),
        ("3 (sic)", "30"),
        ("6", "14"),
    ]
    texto = _norma("normativa_ica", "acuerdo_65_2002.md")
    digital = {
        m.group(1): m.group(2)
        for m in re.finditer(r"(?m)^\| Demás actividades de (\w+) \|  \| (\d+) \|$", texto)
    }
    esperado = {
        "servicios": "10",
        "comerciales": "11",
        "industriales": "11",
    }
    propio = {d["clase"]: d["tarifa_por_mil"] for d in datos["demas_actividades"]}
    assert propio == esperado
    assert digital == {"servicios": "10", "comerciales": "11", "industriales": "11"}


@pytest.mark.req("RF-ICA-03 · Fechas de declaración")
def test_el_calendario_cita_el_art_1_para_la_fecha_del_ica_anual() -> None:
    plazos = {p["concepto"]: p for p in _yaml("calendario/2026.yaml")["plazos"]}
    assert plazos["ica_anual_comun_hasta_391_uvt_y_preferencial"]["articulo"] == 1


# ---------------------------------------------------------------- vistas


@pytest.mark.req("RF-IPU-05 · Citación de la norma")
def test_las_vistas_no_dejan_texto_tapado() -> None:
    vistas = sorted(VISTAS.glob("*.html"))
    assert len(vistas) >= 7
    for ruta in vistas:
        texto = ruta.read_text(encoding="utf-8")
        assert ".par>div{min-width:0;overflow-x:auto}" in texto, ruta.name
        celdas = re.search(r"td,th\{[^}]*\}", texto, re.DOTALL)
        assert celdas, ruta.name
        assert "anywhere" not in celdas.group(0), ruta.name  # parte números y palabras
        assert "overflow-wrap:break-word" in celdas.group(0), ruta.name
        assert "word-break:normal" in celdas.group(0), ruta.name
        assert ".n{white-space:nowrap}" in texto, ruta.name
        if "<pre>" in texto:
            assert "pre{white-space:pre-wrap;overflow-wrap:anywhere;margin:0}" in texto, ruta.name


@pytest.mark.req("RF-IPU-05 · Citación de la norma")
def test_las_celdas_de_numeros_codigos_y_fechas_no_se_parten() -> None:
    texto = (VISTAS / "ica_2026.html").read_text(encoding="utf-8")
    assert '<td class="n">4111</td>' in texto  # código CIIU
    assert '<td class="n">13,1</td>' in texto  # tarifa con coma decimal
    assert not re.search(r"<td>\d+\.\d{1,2}</td>", texto)
    assert '<th class="n">CIIU</th>' in texto
    calendario = (VISTAS / "calendario_2026.html").read_text(encoding="utf-8")
    assert '<td class="n">10 de abril de 2026</td>' in calendario
    assert "18 de septiembre de 2026" in calendario and "15 de enero de 2027" in calendario
    regimenes = (VISTAS / "regimenes_y_uvt.html").read_text(encoding="utf-8")
    assert '<td class="n">49.799</td>' in regimenes and '<td class="n">1.750.905</td>' in regimenes
    assert '<a href="https://normograma.dian.gov.co/' in regimenes
    assert "Res. DIAN 000193 de 2024" in regimenes
    assert (
        "https://normograma.dian.gov.co/dian/compilacion/docs/resolucion_dian_0193_2024.htm</td>"
        not in regimenes
    )


@pytest.mark.req("RF-IPU-05 · Citación de la norma")
def test_los_extractos_de_la_fuente_muestran_sus_tablas_como_tablas_html() -> None:
    for vista in ("ica_2026.html", "ipu_2026.html"):
        texto = (VISTAS / vista).read_text(encoding="utf-8")
        assert "<pre>" not in texto, vista
        assert "| Desde |" not in texto and "|---|" not in texto, vista
    ipu = (VISTAS / "ipu_2026.html").read_text(encoding="utf-8")
    assert "Tarifas preferenciales de 2026" in ipu
    assert "Decreto 639 de 2025, art. 207" in ipu and "Acuerdo 780 de 2020, art. 3" in ipu
    sobretasa = (VISTAS / "sobretasa_alumbrado_2027.html").read_text(encoding="utf-8")
    assert "Residenciales" in sobretasa and "Demás predios" in sobretasa


@pytest.mark.req("RF-ICA-01 · Consultas conceptuales de ICA")
def test_la_vista_del_ica_2026_corta_el_texto_original_en_el_art_3() -> None:
    texto = (VISTAS / "ica_2026.html").read_text(encoding="utf-8")
    inicio = texto.index("Art. 3 del Acuerdo 65, texto original")
    fin = texto.index("Acuerdo 780 de 2020, arts. 6 y 7", inicio)
    extracto = texto[inicio:fin]
    assert "Artículo 4" not in extracto and "Artículo 5" not in extracto
    assert "Resolución 265, 2024" in texto and "Demás actividades" in texto


@pytest.mark.req("RF-ICA-03 · Fechas de declaración")
def test_la_vista_de_regimenes_cita_las_dos_fuentes_de_cada_anio() -> None:
    texto = (VISTAS / "regimenes_y_uvt.html").read_text(encoding="utf-8")
    assert "fuentes secundarias" not in texto
    for fuente in (
        "resolucion_dian_0193_2024",
        "resolucion_dian_0238_2025",
        "decreto_1572_2024",
        "decreto_1469_2025",
    ):
        assert fuente in texto


def test_convertir_limpia_enlaces_imagenes_y_tablas_vacias() -> None:
    html = (
        b'<p>Texto <a href="x.html#1">con enlace</a> y <a href="javascript:f()">Jurisprudencia'
        b' Vigencia</a><img src="a.png"></p><table><tr><td></td></tr></table>'
        b"<table><tr><th>A</th><th>B</th></tr><tr><td>1</td><td>2</td></tr></table>"
    )
    texto = convertir.limpiar(convertir._html_a_texto(html))
    assert "Texto con enlace y" in texto
    assert "javascript" not in texto and "Jurisprudencia" not in texto and "![" not in texto
    assert "| A | B |" in texto and "| 1 | 2 |" in texto
