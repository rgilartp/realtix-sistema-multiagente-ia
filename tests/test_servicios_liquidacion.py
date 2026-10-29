"""Liquidación del predial y estimación del ICA: valores escritos a mano, años sin dato y notas."""

from decimal import Decimal

import pytest
import yaml

from src.services import notas
from src.services.datos_anuales import RAIZ_DATOS, uvt
from src.services.errores import ActividadNoReconocidaError, DatoNoPublicadoError
from src.services.ica import PeriodoICA, estimar_ica
from src.services.predial import liquidar_predial

SMMLV_2026 = 1_750_905
LIMITE_16_SMMLV = 16 * SMMLV_2026  # 28.014.480


# -- Predial 2026 ---------------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.req("RF-IPU-03 · Liquidación estimada")
def test_ejemplo_de_la_seccion_4_4_con_valores_exactos() -> None:
    liq = liquidar_predial(2026, "residencial", 4, 350_000_000)
    assert liq.tarifa.tarifa_por_mil == Decimal("6.1")
    # Exactos, sin aproximar al mil (decisión de Rodolfo): la fracción de $500 queda a la vista.
    assert (liq.impuesto, liq.descuento, liq.total_con_descuento) == (2_135_000, 213_500, 1_921_500)
    assert liq.porcentaje_descuento == 10 and liq.fecha_descuento == "2026-04-17"
    assert liq.fecha_sin_descuento == "2026-07-10" and liq.sobretasa is None


@pytest.mark.unit
@pytest.mark.req("RF-IPU-03 · Liquidación estimada")
@pytest.mark.parametrize(
    ("estrato", "avaluo", "tarifa", "impuesto", "obligado"),
    [
        (2, 150_000_000, "1", 150_000, True),  # U09
        (3, 200_000_000, "3", 600_000, True),  # U10
        (1, 25_000_000, "0", 0, False),  # U11: no obligado
        (1, LIMITE_16_SMMLV, "0", 0, False),  # 16 SMMLV exactos: «igual o menor» no paga en 2026
        (1, LIMITE_16_SMMLV + 1, "1", 28_014, True),  # un peso más: paga 1 por mil
    ],
)
def test_preferenciales_de_2026(estrato, avaluo, tarifa, impuesto, obligado) -> None:
    liq = liquidar_predial(2026, "residencial", estrato, avaluo)
    assert (liq.tarifa.tarifa_por_mil, liq.impuesto, liq.tarifa.obligado) == (
        Decimal(tarifa),
        impuesto,
        obligado,
    )


@pytest.mark.unit
@pytest.mark.req("RF-IPU-03 · Liquidación estimada")
def test_el_limite_de_16_smmlv_de_2026_es_28_014_480() -> None:
    assert LIMITE_16_SMMLV == 28_014_480


@pytest.mark.unit
@pytest.mark.req("RF-IPU-03 · Liquidación estimada")
def test_toda_liquidacion_lleva_las_notas_obligatorias() -> None:
    for destino, estrato, avaluo in [
        ("residencial", 3, 200_000_000),
        ("residencial", 1, 25_000_000),
    ]:
        liq = liquidar_predial(2026, destino, estrato, avaluo)
        assert notas.NOTA_ESTIMACION in liq.notas
        assert notas.NOTA_APROXIMACION_PREDIAL in liq.notas
        assert notas.NOTA_LEY_1995 in liq.notas
    assert "no vinculante" in notas.NOTA_ESTIMACION
    assert "Ley 1995 de 2019" in notas.NOTA_LEY_1995 and "Ley 2294 de 2023" in notas.NOTA_LEY_1995
    assert notas.NOTA_APROXIMACION_PREDIAL == (
        "En la declaración y en los recibos de pago los valores se aproximan al múltiplo de mil "
        "más cercano (Decreto 807 de 1993, arts. 15 y 132), así que el valor a pagar puede variar "
        "levemente; el que cuenta es el de la factura o la declaración."
    )
    assert "arts. 15 y 132" not in notas.NOTA_APROXIMACION_ICA and "art. 15" in (
        notas.NOTA_APROXIMACION_ICA
    )


# -- Predial 2027 ---------------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.req("RF-IPU-03 · Liquidación estimada")
@pytest.mark.parametrize("estrato", [1, 2, 3])
def test_predial_2027_con_regla_en_smmlv_no_se_estima_sin_el_smmlv(estrato) -> None:
    with pytest.raises(DatoNoPublicadoError):
        liquidar_predial(2027, "residencial", estrato, 100_000_000)


@pytest.mark.unit
@pytest.mark.req("RF-IPU-03 · Liquidación estimada")
def test_limite_de_16_smmlv_de_2027_con_smmlv_inyectado_solo_en_la_prueba(monkeypatch) -> None:
    monkeypatch.setattr("src.services.predial.smmlv", lambda anio: 1_800_000)  # solo en la prueba
    monkeypatch.setattr("src.services.predial.uvt", lambda anio: 55_000)
    limite = 16 * 1_800_000
    por_debajo = liquidar_predial(2027, "residencial", 2, limite - 1)
    exacto = liquidar_predial(2027, "residencial", 2, limite)
    assert not por_debajo.tarifa.obligado and por_debajo.impuesto == 0
    assert por_debajo.sobretasa is None  # excluido del predial, sin sobretasa
    # Al contrario que en 2026, con 16 SMMLV exactos se paga 1 por mil (Acuerdo 1084, art. 20).
    assert exacto.tarifa.obligado and exacto.tarifa.tarifa_por_mil == Decimal("1")
    assert exacto.impuesto == 28_800


@pytest.mark.unit
@pytest.mark.req("RF-IPU-03 · Liquidación estimada")
def test_predial_2027_dice_que_el_descuento_aun_no_se_publica() -> None:
    liq = liquidar_predial(2027, "residencial", 4, 350_000_000)
    assert liq.descuento is None and liq.total_con_descuento is None
    assert liq.porcentaje_descuento is None and liq.fecha_descuento is None
    assert notas.NOTA_DESCUENTO_2027 in liq.notas and "aún no se publica" in liq.notas[3]
    assert notas.NOTA_IVIUR_2027 in liq.notas and notas.NOTA_LEY_1995 in liq.notas


@pytest.mark.unit
@pytest.mark.req("RF-IPU-03 · Liquidación estimada")
@pytest.mark.parametrize(
    ("destino", "estrato", "categoria", "tarifa"),
    [
        ("residencial", 4, "residencial_123_mas_de_20000_uvt_y_456", "0.4"),
        ("comercial", None, "comercial_financiero_industrial", "1"),
        ("lote", None, "dotacional_y_urbanizables", "0.8"),
    ],
)
def test_sobretasa_de_alumbrado_2027_sin_el_tope_cuando_falta_la_uvt(
    destino, estrato, categoria, tarifa
) -> None:
    liq = liquidar_predial(2027, destino, estrato, 500_000_000)
    assert liq.sobretasa is not None and liq.sobretasa.categoria == categoria
    assert liq.sobretasa.tarifa_por_mil == Decimal(tarifa)
    assert liq.sobretasa.valor == int(Decimal(500_000_000) * Decimal(tarifa) / 1000)
    assert liq.sobretasa.tope_uvt is None and notas.NOTA_TOPE_SOBRETASA in liq.notas


@pytest.mark.unit
@pytest.mark.req("RF-IPU-03 · Liquidación estimada")
def test_sobretasa_con_tope_cuando_la_uvt_esta_publicada(monkeypatch) -> None:
    monkeypatch.setattr("src.services.predial.uvt", lambda anio: 1_000)  # solo en la prueba
    liq = liquidar_predial(2027, "residencial", 4, 5_000_000_000)  # 0,4 por mil = 2.000.000
    assert liq.sobretasa is not None and liq.sobretasa.tope_aplicado
    assert liq.sobretasa.valor == 600 * 1_000  # tope de 600 UVT en residenciales
    assert notas.NOTA_TOPE_SOBRETASA not in liq.notas


@pytest.mark.unit
@pytest.mark.req("RF-IPU-03 · Liquidación estimada")
def test_sin_la_uvt_la_sobretasa_de_estratos_1_a_3_no_tumba_la_liquidacion(monkeypatch) -> None:
    monkeypatch.setattr("src.services.predial.smmlv", lambda anio: 1_800_000)  # solo en la prueba
    liq = liquidar_predial(2027, "residencial", 3, 100_000_000)
    assert liq.impuesto == 300_000 and liq.sobretasa is None
    assert notas.NOTA_SOBRETASA_SIN_UVT in liq.notas


# -- ICA ------------------------------------------------------------------------------------------


def _ciiu(archivo: str, claves: tuple[str, ...]) -> set[str]:
    datos = yaml.safe_load((RAIZ_DATOS / "tarifas" / archivo).read_text(encoding="utf-8"))
    return {f["ciiu"] for clave in claves for f in datos.get(clave, [])}


@pytest.mark.unit
@pytest.mark.req("RF-ICA-02 · Estimación por actividad")
def test_estimacion_ica_2026_anual_es_una_proyeccion_del_ano_completo() -> None:
    est = estimar_ica("6201", 1_000_000_000, PeriodoICA(2026))
    assert est.proyeccion_anual and notas.NOTA_PROYECCION_ICA_ANUAL in est.notas
    assert "proyección del año completo" in notas.NOTA_PROYECCION_ICA_ANUAL
    assert est.impuesto == int(Decimal(1_000_000_000) * est.tarifa_por_mil / 1000)
    for nota in (
        notas.NOTA_ESTIMACION,
        notas.NOTA_APROXIMACION_ICA,
        notas.NOTA_AVISOS_Y_TABLEROS,
    ):
        assert nota in est.notas


@pytest.mark.unit
@pytest.mark.req("RF-ICA-02 · Estimación por actividad")
def test_la_nota_dice_cuando_aplican_avisos_y_tableros_y_la_sobretasa_bomberil() -> None:
    # Avisos y tableros: solo con vallas, avisos o tableros visibles (Decreto 352 de 2002, art. 57).
    assert "visibles desde el espacio público" in notas.NOTA_AVISOS_Y_TABLEROS
    assert "15 %" in notas.NOTA_AVISOS_Y_TABLEROS
    # Sobretasa bomberil: el código compara los ingresos del periodo con 43.498 UVT del año.
    umbral = 43_498 * uvt(2026)
    debajo = estimar_ica("6201", 900_000_000, PeriodoICA(2026))
    assert any(n.startswith("La sobretasa bomberil no se declara") for n in debajo.notas)
    assert any(f"{umbral:,}".replace(",", ".") in n for n in debajo.notas)
    encima = estimar_ica("6201", umbral + 1, PeriodoICA(2026, "bimestral", 3))
    assert any("también se declara la sobretasa bomberil" in n for n in encima.notas)
    justo = estimar_ica("6201", umbral, PeriodoICA(2026, "bimestral", 3))  # «superiores»: no
    assert any(n.startswith("La sobretasa bomberil no se declara") for n in justo.notas)
    # El bimestre 6 de 2026 usa la tabla de 2027, pero la regla y la UVT de 2026.
    sexto = estimar_ica("6201", umbral + 1, PeriodoICA(2026, "bimestral", 6))
    assert any("también se declara la sobretasa bomberil" in n for n in sexto.notas)
    # La nota cita las normas completas, para que el verificador de citas las acepte.
    from src.services.citas import citas_sin_fuente

    assert (
        citas_sin_fuente("Decreto 352 de 2002, arts. 57 a 59", [notas.NOTA_AVISOS_Y_TABLEROS]) == []
    )
    # 2027: sin el umbral o la UVT en la base no se dice si aplica, ni que el umbral no se ha
    # publicado (una norma que no está en la base puede haber cambiado la regla).
    sin_datos = estimar_ica("6201", 900_000_000, PeriodoICA(2027))
    assert any("no puede decir si la sobretasa bomberil se declara" in n for n in sin_datos.notas)
    assert not any("se publica" in n for n in sin_datos.notas)
    assert any("43.498 UVT" in n and "art. 2" in n for n in sin_datos.notas)  # la regla de 2026


@pytest.mark.unit
@pytest.mark.req("RF-ICA-02 · Estimación por actividad")
def test_estimacion_ica_bimestral_y_de_2027_no_son_proyeccion() -> None:
    bimestral = PeriodoICA(2026, "bimestral", 3)
    assert not estimar_ica("6201", 100_000_000, bimestral).proyeccion_anual
    assert not estimar_ica("6201", 100_000_000, PeriodoICA(2027)).proyeccion_anual


@pytest.mark.unit
@pytest.mark.req("RF-ICA-02 · Estimación por actividad")
def test_ciiu_58112_en_2026_da_8_por_mil_o_4_14_si_cumple_el_acuerdo_98() -> None:
    est = estimar_ica("58112", 100_000_000, PeriodoICA(2026))
    assert est.tarifa_por_mil == Decimal("8") and est.impuesto == 800_000
    assert est.tarifa_condicionada == Decimal("4.14") and est.impuesto_condicionado == 414_000
    assert est.condicion and "Secretaría de Educación" in est.condicion
    assert "Acuerdo 98 de 2003" in est.fuente or "Acuerdo 65 de 2002" in est.fuente


@pytest.mark.unit
@pytest.mark.req("RF-ICA-02 · Estimación por actividad")
def test_ciiu_58112_en_2027_da_4_por_mil_sin_condicion() -> None:
    est = estimar_ica("58112", 100_000_000, PeriodoICA(2027))
    assert est.tarifa_por_mil == Decimal("4") and est.impuesto == 400_000
    assert est.tarifa_condicionada is None and est.impuesto_condicionado is None


@pytest.mark.unit
@pytest.mark.req("RF-ICA-02 · Estimación por actividad")
def test_los_37_codigos_de_2026_sin_fila_en_2027_no_se_reconocen() -> None:
    de_2026 = _ciiu("ica_2026.yaml", ("por_actividad",))
    de_2027 = _ciiu("ica_2027.yaml", ("por_actividad", "progresiva_financiera"))
    faltan = sorted(de_2026 - de_2027)
    assert len(faltan) == 37 and {"4511", "69101", "69102"} <= set(faltan)
    for codigo in faltan:
        with pytest.raises(ActividadNoReconocidaError):
            estimar_ica(codigo, 100_000_000, PeriodoICA(2027))
        estimar_ica(codigo, 100_000_000, PeriodoICA(2026))  # en 2026 sí existen


@pytest.mark.unit
@pytest.mark.req("RF-ICA-02 · Estimación por actividad")
def test_nunca_se_asigna_un_codigo_de_2027_por_parecido() -> None:
    # El 6910 sí existe en 2027, pero no se usa para 69101 ni 69102, aunque se le parezca.
    assert estimar_ica("6910", 1_000_000, PeriodoICA(2027)).ciiu == "6910"
    for codigo in ("69101", "69102", "69103"):
        with pytest.raises(ActividadNoReconocidaError):
            estimar_ica(codigo, 1_000_000, PeriodoICA(2027))
    with pytest.raises(ActividadNoReconocidaError):
        estimar_ica("69101", 1_000_000, PeriodoICA(2026, "bimestral", 6))  # bimestre 6: tabla 2027


@pytest.mark.unit
@pytest.mark.req("RF-ICA-02 · Estimación por actividad")
def test_los_ingresos_negativos_se_rechazan() -> None:
    with pytest.raises(ValueError):
        estimar_ica("6201", -1, PeriodoICA(2026))
