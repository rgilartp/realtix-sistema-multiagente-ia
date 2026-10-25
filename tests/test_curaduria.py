"""Curaduría y datos por año gravable (B2): esquemas de `datos/`, base de conocimiento y scripts."""

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
    assert len(datos["progresiva_financiera"]) == 11


@pytest.mark.req("RF-ICA-01 · Consultas conceptuales de ICA")
def test_ica_2027_coincide_con_el_texto_digital_del_regimen_legal() -> None:
    digital = doble_lectura.tarifas_regimen_legal()
    propia = {
        f["ciiu"]: f["tarifa_por_mil"] for f in _yaml("tarifas/ica_2027.yaml")["por_actividad"]
    }
    assert propia == digital


@pytest.mark.req("RF-ICA-01 · Consultas conceptuales de ICA")
def test_ica_2026_queda_pendiente_sin_valores_supuestos() -> None:
    datos = _yaml("tarifas/ica_2026.yaml")
    assert datos["estado"] == "pendiente"
    assert datos["por_actividad"] == []


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


@pytest.mark.req("RF-ICA-03 · Fechas de declaración")
def test_uvt_y_smmlv_de_2027_siguen_pendientes() -> None:
    datos = _yaml("uvt_smmlv.yaml")
    assert all(isinstance(x["valor"], int) for x in datos["uvt"][:2] + datos["smmlv"][:2])
    assert datos["uvt"][2]["valor"] == datos["smmlv"][2]["valor"] == "pendiente"


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
    shutil.copy(DATOS / "tarifas" / "ica_2026.yaml", tmp_path / "datos" / "tarifas")
    (tmp_path / "docs" / "verificacion_curaduria.md").write_text(
        "- [ ] `datos/tarifas/ipu_2026.yaml` — predial.\n"
        "- [ ] `datos/tarifas/ica_2026.yaml` — pendiente.\n",
        encoding="utf-8",
    )
    for _ in range(2):  # idempotente
        verificadas = marcar_verificado.marcar("Nombre Apellido", tmp_path)
    assert verificadas == ["datos/tarifas/ipu_2026.yaml"]
    ipu = yaml.safe_load((tmp_path / "datos/tarifas/ipu_2026.yaml").read_text(encoding="utf-8"))
    ica = yaml.safe_load((tmp_path / "datos/tarifas/ica_2026.yaml").read_text(encoding="utf-8"))
    assert ipu["verificado_por"] == "Nombre Apellido"
    assert ica["verificado_por"] == ""
    lineas = (tmp_path / "docs/verificacion_curaduria.md").read_text(encoding="utf-8").splitlines()
    assert (
        lineas[0]
        == "- [x] `datos/tarifas/ipu_2026.yaml` — predial. Verificado por Nombre Apellido."
    )
    assert lineas[1].startswith("- [ ] ")
