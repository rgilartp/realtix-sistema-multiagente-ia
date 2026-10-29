"""Curaduría y datos por año gravable (B2): esquemas de `datos/`, base de conocimiento y scripts."""

import re
import shutil
import sys
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import pytest
import yaml

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts" / "curaduria"))

import comun  # noqa: E402
import doble_lectura  # noqa: E402
import marcar_verificado  # noqa: E402

DATOS = RAIZ / "datos"
KB = RAIZ / "knowledge_base"
ARCHIVOS = sorted(DATOS.rglob("*.yaml"))

pytestmark = pytest.mark.unit


def _yaml(ruta: str) -> dict:
    return yaml.safe_load((DATOS / ruta).read_text(encoding="utf-8"))


def _contiguos(rangos: list[dict]) -> bool:
    previo = None
    for rango in rangos:
        if previo is not None and (
            previo["hasta"] is None or rango["desde"] != previo["hasta"] + 1
        ):
            return False
        previo = rango
    return rangos[-1]["hasta"] is None


@pytest.mark.req("RF-IPU-05 · Citación de la norma")
@pytest.mark.parametrize("ruta", ARCHIVOS, ids=lambda p: p.name)
def test_cada_archivo_de_datos_lleva_su_fuente_y_su_verificacion(ruta: Path) -> None:
    datos = yaml.safe_load(ruta.read_text(encoding="utf-8"))
    assert datos["mes_consulta"] == "octubre de 2026"
    assert "verificado_por" in datos
    assert datos.get("fuente") or ruta.name == "uvt_smmlv.yaml"


@pytest.mark.req("RF-IPU-04 · Plazos y descuentos")
def test_ipu_2026_tiene_30_rangos_contiguos_y_6_tarifas_no_residenciales() -> None:
    datos = _yaml("tarifas/ipu_2026.yaml")
    rangos = datos["residencial_urbano"]
    assert len(rangos) == 30
    assert _contiguos(rangos[:-1] + [{**rangos[-1], "hasta": None}])
    tarifas = [Decimal(r["tarifa_por_mil"]) for r in rangos]
    assert tarifas == sorted(tarifas)
    assert len(datos["no_residencial"]) == 6


@pytest.mark.req("RF-IPU-04 · Plazos y descuentos")
def test_ejemplo_de_350_millones_cae_en_6_1_por_mil() -> None:
    rangos = _yaml("tarifas/ipu_2026.yaml")["residencial_urbano"]
    avaluo = 350_000_000
    rango = next(
        r for r in rangos if r["desde"] <= avaluo and (r["hasta"] is None or avaluo <= r["hasta"])
    )
    assert rango["tarifa_por_mil"] == "6.1"
    impuesto = (Decimal(avaluo) * Decimal(rango["tarifa_por_mil"]) / 1000).quantize(
        Decimal("1"), ROUND_HALF_UP
    )
    assert impuesto == Decimal("2135000")
    assert impuesto * Decimal("0.9") == Decimal("1921500")


@pytest.mark.req("RF-IPU-04 · Plazos y descuentos")
def test_ipu_2027_tiene_32_rangos_y_repite_los_29_primeros_de_2026() -> None:
    rangos_2027 = _yaml("tarifas/ipu_2027.yaml")["generales"]["residencial"]
    rangos_2026 = _yaml("tarifas/ipu_2026.yaml")["residencial_urbano"]
    assert len(rangos_2027) == 32
    assert _contiguos(rangos_2027)
    assert rangos_2027[-1]["tarifa_por_mil"] == "13.9"
    assert [(r["hasta"], r["tarifa_por_mil"]) for r in rangos_2027[:29]] == [
        (r["hasta"], r["tarifa_por_mil"]) for r in rangos_2026[:29]
    ]


@pytest.mark.req("RF-IPU-04 · Plazos y descuentos")
def test_ipu_2027_preferenciales_y_clubes() -> None:
    datos = _yaml("tarifas/ipu_2027.yaml")
    preferenciales = datos["preferenciales"]["residencial_urbano_y_rural_agropecuario"]
    assert [(p["estratos"], p["tarifa_por_mil"]) for p in preferenciales] == [
        ([1, 2], "1"),
        ([1, 2], "3"),
        ([3], "3"),
    ]
    clubes = datos["generales"]["dotacional_clubes_de_particulares"]["rangos"]
    assert len(clubes) == 10
    assert _contiguos([{"desde": c["desde"], "hasta": c["hasta"]} for c in clubes])


@pytest.mark.req("RF-IPU-04 · Plazos y descuentos")
def test_sobretasa_de_alumbrado_2027() -> None:
    datos = _yaml("tarifas/sobretasa_alumbrado_2027.yaml")
    assert [t["valor_limite_uvt"] for t in datos["topes_uvt"]] == [600, 1200]
    assert [t["de_2027_a_2041"] for t in datos["tarifas_por_mil"]] == ["0", "0.4", "0.8", "1"]
    assert datos["vigencia_desde"] == 2027


@pytest.mark.req("RF-ICA-01 · Consultas conceptuales de ICA")
def test_ica_2027_tiene_447_actividades_con_tarifas_conocidas() -> None:
    datos = _yaml("tarifas/ica_2027.yaml")
    filas = datos["por_actividad"]
    assert len(filas) == 447
    assert len({f["ciiu"] for f in filas}) == 447
    assert {f["tarifa_por_mil"] for f in filas} == {"4", "7", "8", "10", "11", "12", "13", "19"}
    assert len(datos["progresiva_financiera"]) == 28


@pytest.mark.req("RF-ICA-01 · Consultas conceptuales de ICA")
def test_ica_2027_coincide_en_los_dos_sentidos_con_el_texto_digital() -> None:
    datos = _yaml("tarifas/ica_2027.yaml")
    fijas = {f["ciiu"]: f["tarifa_por_mil"] for f in datos["por_actividad"]}
    progresivas = {
        f["ciiu"]: (f["hasta_2027"], f["en_2028"], f["desde_2029"])
        for f in datos["progresiva_financiera"]
    }
    digital_fijas = doble_lectura.tarifas_regimen_legal()
    digital_progresivas = doble_lectura.progresivas_regimen_legal()
    assert fijas == digital_fijas  # el YAML tiene todo lo del texto y el texto, todo lo del YAML
    assert progresivas == digital_progresivas
    assert not set(fijas) & set(progresivas)
    assert len(fijas) + len(progresivas) == 475


# Filas que decidió Rodolfo en la parada de B2: prevalece la Resolución SDH-000265 de 2021.
DECIDIDAS_ICA_2026 = {
    "4111": "6.9",
    "4112": "6.9",
    "4311": "6.9",
    "4312": "6.9",
    "4321": "6.9",
    "4322": "6.9",
    "4329": "6.9",
    "39002": "6.9",
    "4330": "7.6",
    "4390": "7.6",
}
NOTA_PARA_EL_AGENTE = (
    "El art. 6 del Acuerdo 780 de 2020 nombra a los contratistas de construcción, constructores y "
    "urbanizadores en el grupo que sube a 8,66 por mil; la Secretaría de Hacienda clasificó esta "
    "actividad en la tarifa indicada, que es la que aplica."
)


@pytest.mark.req("RF-ICA-01 · Consultas conceptuales de ICA")
def test_ica_2026_arma_el_texto_vigente_con_sus_fuentes() -> None:
    datos = _yaml("tarifas/ica_2026.yaml")
    filas = datos["por_actividad"]
    assert datos["estado"] == "completa"
    assert len(filas) == 486
    assert len({f["ciiu"] for f in filas}) == 486
    por_codigo = {f["ciiu"]: f for f in filas}
    financieras = [f for f in filas if f["grupo_resolucion_265"] == "401"]
    assert len(financieras) == 28
    assert {f["tarifa_por_mil"] for f in financieras} == {"14"}
    assert por_codigo["5330"]["tarifa_por_mil"] == "11.04"
    assert por_codigo["2100"]["tarifa_por_mil"] == "12.14"
    assert por_codigo["58112"]["tarifa_por_mil"] == "8"
    assert por_codigo["58112"]["tarifa_condicionada"]["tarifa_por_mil"] == "4.14"
    simple = datos["regimen_simple_2026"]["tarifas_por_mil"]
    assert [t["tarifa_por_mil"] for t in simple] == ["12", "16", "30", "30", "16"]


@pytest.mark.req("RF-ICA-01 · Consultas conceptuales de ICA")
def test_ica_2026_aplica_la_decision_de_rodolfo_sobre_las_10_filas() -> None:
    datos = _yaml("tarifas/ica_2026.yaml")
    filas = datos["por_actividad"]
    por_codigo = {f["ciiu"]: f for f in filas}
    assert not [f for f in filas if f["tarifa_por_mil"] == "pendiente"]
    assert datos["decision_de_rodolfo"]["filas"] == sorted(DECIDIDAS_ICA_2026)
    for codigo, tarifa in DECIDIDAS_ICA_2026.items():
        fila = por_codigo[codigo]
        assert fila["tarifa_por_mil"] == tarifa
        assert fila["fuente_tarifa"] == (
            "Resolución SDH-000265 de 2021, art. 1 "
            "(clasificación oficial por CIIU de la Secretaría de Hacienda)"
        )
        assert fila["nota_para_el_agente"] == NOTA_PARA_EL_AGENTE
        assert "Rodolfo" in fila["decision"]
    for fila in filas:
        assert fila["fuente_tarifa"]
        assert Decimal(fila["tarifa_por_mil"]) > 0
        if fila["ciiu"] not in DECIDIDAS_ICA_2026:
            assert "nota_para_el_agente" not in fila


@pytest.mark.req("RF-ICA-01 · Consultas conceptuales de ICA")
def test_ica_2026_completa_el_grupo_truncado_del_4930() -> None:
    fila = next(f for f in _yaml("tarifas/ica_2026.yaml")["por_actividad"] if f["ciiu"] == "4930")
    assert fila["grupo_resolucion_265"] == "301"
    assert fila["tarifa_por_mil"] == "4.14"


@pytest.mark.req("RF-ICA-03 · Fechas de declaración")
def test_ica_2026_y_2027_dicen_que_periodos_cubren() -> None:
    en_2026 = _yaml("tarifas/ica_2026.yaml")["periodos_que_cubre"]
    en_2027 = _yaml("tarifas/ica_2027.yaml")["aplicacion"]["periodos_que_cubre"]
    assert "bimestres 1 a 5 de 2026" in en_2026["declarantes_bimestrales"]
    assert "bimestre 6 de 2026" in en_2027["declarantes_bimestrales"]
    assert "12 de febrero de 2027" in en_2027["declarantes_bimestrales"]
    assert "1 de enero de 2027" in en_2027["declarantes_anuales"]


@pytest.mark.req("RF-IPU-04 · Plazos y descuentos")
def test_calendario_2026_coincide_con_la_tabla_de_la_especificacion() -> None:
    esperado = {
        "predial_pronto_pago_10": ["2026-04-17"],
        "predial_facturas_expedidas_a_mas_tardar": ["2026-04-30"],
        "predial_sin_descuento": ["2026-07-10"],
        "spac_declaracion_inicial": ["2026-05-08"],
        "spac_cuotas": ["2026-06-05", "2026-08-14", "2026-10-02", "2026-12-04"],
        "ica_bimestral_comun_mayor_391_uvt": [
            "2026-04-10",
            "2026-06-12",
            "2026-08-21",
            "2026-10-09",
            "2026-12-11",
            "2027-02-12",
        ],
        "ica_anual_comun_hasta_391_uvt_y_preferencial": ["2027-02-26"],
    }
    plazos = {p["concepto"]: p["fechas"] for p in _yaml("calendario/2026.yaml")["plazos"]}
    assert plazos == esperado


@pytest.mark.req("RF-ICA-03 · Fechas de declaración")
def test_regimenes_ica_y_umbral_en_pesos() -> None:
    anios = {a["anio_gravable"]: a for a in _yaml("regimenes_ica.yaml")["anios"]}
    assert anios[2026]["umbral_uvt"] == anios[2027]["umbral_uvt"] == 391
    assert anios[2027]["sin_declaracion"]["ingresos_netos_menores_a_uvt"] == 1933
    uvt_2025 = next(u["valor"] for u in _yaml("uvt_smmlv.yaml")["uvt"] if u["anio"] == 2025)
    assert anios[2026]["umbral_pesos"] == 391 * uvt_2025 == 19_471_409
    # Sobretasa bomberil: ingresos netos superiores a 43.498 UVT (Res. SDH-000195 de 2025, art. 2).
    assert anios[2026]["sobretasa_bomberil"]["umbral_uvt"] == 43_498
    assert "art. 2" in anios[2026]["sobretasa_bomberil"]["fuente"]


@pytest.mark.req("RF-ICA-03 · Fechas de declaración")
def test_uvt_y_smmlv_salen_de_fuentes_oficiales_y_los_de_2027_siguen_pendientes() -> None:
    datos = _yaml("uvt_smmlv.yaml")
    vigentes = datos["uvt"][:2] + datos["smmlv"][:2]
    assert [x["valor"] for x in vigentes] == [49799, 52374, 1423500, 1750905]
    for x in vigentes:
        assert x["url"].startswith(
            ("https://normograma.dian.gov.co/", "https://normativa.colpensiones.gov.co/")
        )
    assert datos["uvt"][2]["valor"] == datos["smmlv"][2]["valor"] == "pendiente"
    assert "confirmar" not in yaml.safe_dump(datos, allow_unicode=True)


@pytest.mark.req("RF-IPU-05 · Citación de la norma")
def test_ipu_2026_cita_su_resolucion_y_el_contraste() -> None:
    datos = _yaml("tarifas/ipu_2026.yaml")
    assert "SDH-000194 de 2025" in datos["fuente"]
    assert datos["url"].endswith("Resolucion-000194-de-2025-SDH.pdf")
    assert datos["contraste"]["diferencias"] == 0


@pytest.mark.req("RF-IPU-05 · Citación de la norma")
def test_las_normas_corregidas_traen_sus_notas_de_vigencia() -> None:
    ley_1581 = (KB / "normativa_datos" / "ley_1581_2012.md").read_text(encoding="utf-8")
    articulos = [int(n) for n in re.findall(r"^## Artículo (\d+)$", ley_1581, re.MULTILINE)]
    assert articulos == list(range(1, 31))
    ley_14 = (KB / "normativa_ica" / "ley_14_1983.md").read_text(encoding="utf-8")
    assert "alcaldiabogota.gov.co/sisjur/normas/Norma1.jsp?i=267" in ley_14
    assert "Modificado por" in ley_14
    for archivo in ("normativa_ipu/decreto_474_2016.md", "normativa_ipu/decreto_807_1993_ipu.md"):
        assert "alcaldiabogota.gov.co" in (KB / archivo).read_text(encoding="utf-8")


def _articulo(texto: str, numero: int) -> str:
    inicio = texto.index(f"\n## Artículo {numero}\n")
    fin = texto.find("\n## Artículo ", inicio + 1)
    return texto[inicio : fin if fin != -1 else len(texto)]


@pytest.mark.req("RF-ICA-01 · Consultas conceptuales de ICA")
def test_la_ley_14_marca_como_no_vigentes_los_arts_33_y_36_y_remite_a_la_ley_1819() -> None:
    ley_14 = (KB / "normativa_ica" / "ley_14_1983.md").read_text(encoding="utf-8")
    for numero, referencia in ((33, "art. 342"), (36, "art. 345")):
        articulo = _articulo(ley_14, numero)
        assert "Texto anterior, no vigente" in articulo
        assert f"Ley 1819 de 2016, {referencia}" in articulo
    assert ley_14.count("Texto anterior, no vigente") == 2
    ley_1819 = (KB / "normativa_ica" / "ley_1819_2016_ica.md").read_text(encoding="utf-8")
    assert [n for n in (342, 345) if f"\n## Artículo {n}\n" in ley_1819] == [342, 345]
    assert "Ley 1819 de 2016" in ley_1819.splitlines()[0]


@pytest.mark.req("RF-OBS-04 · Actualización de la base vectorial")
@pytest.mark.parametrize(
    "coleccion", ["normativa_ipu", "normativa_ica", "normativa_datos", "plataforma_general"]
)
def test_cada_coleccion_lista_sus_fuentes_con_mes_de_consulta(coleccion: str) -> None:
    fuentes = yaml.safe_load((KB / coleccion / "fuentes.yaml").read_text(encoding="utf-8"))[
        "fuentes"
    ]
    assert fuentes
    for fuente in fuentes:
        assert fuente["mes_consulta"] == "octubre de 2026"
        assert (KB / coleccion / fuente["archivo"]).exists()
        assert fuente["url"] or fuente["origen"]


@pytest.mark.req("RF-IPU-05 · Citación de la norma")
def test_cada_norma_cargada_cita_su_fuente_y_tiene_articulos() -> None:
    for ruta in KB.glob("normativa_*/*.md"):
        texto = ruta.read_text(encoding="utf-8")
        assert texto.startswith("# "), ruta
        assert "Fuente: http" in texto, ruta
        assert "\n## Artículo " in texto, ruta


@pytest.mark.req("RF-GEN-02 · Explicación en lenguaje sencillo")
def test_el_glosario_cita_la_norma_de_cada_termino() -> None:
    texto = (KB / "plataforma_general" / "glosario.md").read_text(encoding="utf-8")
    terminos = [t for t in texto.splitlines() if t.startswith("## ")]
    fuentes = [t for t in texto.splitlines() if t.startswith("**Fuente:**")]
    assert terminos
    assert len(terminos) == len(fuentes)
    assert "Documento sintético" in texto


@pytest.mark.req("RF-GEN-01 · Consultas transversales")
def test_el_manual_de_la_ovt_esta_rotulado_como_sintetico() -> None:
    texto = (KB / "plataforma_general" / "manual_ovt_simulada.md").read_text(encoding="utf-8")
    assert "Documento sintético" in texto
    assert "Entorno simulado de pruebas" in texto


@pytest.mark.req("RF-IPU-05 · Citación de la norma")
def test_el_corte_por_articulo_ignora_citas_y_encabezados_anidados() -> None:
    texto = (RAIZ / "tests" / "fixtures" / "norma_ejemplo.md").read_text(encoding="utf-8")
    cortes = comun.cortar_por_articulo(texto)
    assert [n for n, _ in cortes] == ["1", "2", "3", "4", "5"]
    assert "Texto citado" in dict(cortes)["2"]
    assert [n for n, _ in comun.filtrar_articulos(cortes, ["2", "5", "9"])] == ["2", "5"]


@pytest.mark.req("RF-IPU-05 · Citación de la norma")
def test_marcar_verificado_llena_el_nombre_y_marca_la_casilla(tmp_path: Path) -> None:
    (tmp_path / "datos" / "tarifas").mkdir(parents=True)
    (tmp_path / "docs").mkdir()
    shutil.copy(DATOS / "tarifas" / "ipu_2026.yaml", tmp_path / "datos" / "tarifas")
    (tmp_path / "datos" / "tarifas" / "tabla_pendiente.yaml").write_text(
        "estado: pendiente\nverificado_por: ''\n", encoding="utf-8"
    )
    (tmp_path / "docs" / "verificacion_curaduria.md").write_text(
        "- [ ] `datos/tarifas/ipu_2026.yaml` — predial.\n"
        "- [ ] `datos/tarifas/tabla_pendiente.yaml` — pendiente.\n",
        encoding="utf-8",
    )
    for _ in range(2):  # idempotente
        verificadas = marcar_verificado.marcar("Nombre Apellido", tmp_path)
    assert verificadas == ["datos/tarifas/ipu_2026.yaml"]
    ipu = yaml.safe_load((tmp_path / "datos/tarifas/ipu_2026.yaml").read_text(encoding="utf-8"))
    ica = yaml.safe_load(
        (tmp_path / "datos/tarifas/tabla_pendiente.yaml").read_text(encoding="utf-8")
    )
    assert ipu["verificado_por"] == "Nombre Apellido"
    assert ica["verificado_por"] == ""
    lineas = (tmp_path / "docs/verificacion_curaduria.md").read_text(encoding="utf-8").splitlines()
    assert (
        lineas[0]
        == "- [x] `datos/tarifas/ipu_2026.yaml` — predial. Verificado por Nombre Apellido."
    )
    assert lineas[1].startswith("- [ ] ")


@pytest.mark.req(
    "RF-GEN-02 · Explicación en lenguaje sencillo", "RF-ICA-02 · Estimación por actividad"
)
def test_el_glosario_dice_donde_encontrar_el_codigo_ciiu_con_su_fuente_oficial() -> None:
    texto = (KB / "plataforma_general" / "glosario.md").read_text(encoding="utf-8")
    entrada = texto.split("## Código CIIU (actividad económica)")[1].split("\n## ")[0]
    assert "casilla 46" in entrada and "IN-CAC-0237" in entrada
    assert "https://www.dian.gov.co/" in entrada
    # La regla de `ica.v2` que lo decía al pedir el código se revirtió: en la corrida 2b, el juez
    # marcó como afirmación sin fuente la casilla 46, que el agente del ICA no recupera (no ve el
    # glosario). Queda la entrada del glosario, que el agente general sí recupera.

    def plano(t: str) -> str:
        return " ".join(t.lower().split())

    assert "en el rut, la actividad principal va en la casilla 46." in plano(entrada)
