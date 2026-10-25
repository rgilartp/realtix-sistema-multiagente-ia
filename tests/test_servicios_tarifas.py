"""Búsqueda única de tarifas del predial y del ICA (valores escritos a mano desde la norma)."""

from decimal import Decimal

import pytest

from src.services.datos_anuales import calendario, porcentaje_pronto_pago, smmlv, uvt
from src.services.errores import (
    ActividadNoReconocidaError,
    AnioSinDatosError,
    DatoNoPublicadoError,
)
from src.services.ica import PeriodoICA, buscar_tarifa_ica
from src.services.predial import buscar_tarifa_ipu, descuento_pronto_pago, valor_impuesto

SMMLV_2026 = 1_750_905


@pytest.mark.unit
@pytest.mark.req("RF-IPU-03 · Liquidación estimada")
@pytest.mark.parametrize(
    ("destino", "estrato", "avaluo", "tarifa", "valor"),
    [
        ("residencial", 4, 350_000_000, "6.1", 2_135_000),
        ("residencial", 4, 194_307_000, "5.5", 1_068_689),
        ("residencial", 4, 194_307_001, "5.6", 1_088_119),
        ("residencial", 2, 150_000_000, "1", 150_000),
        ("residencial", 3, 200_000_000, "3", 600_000),
        ("residencial", 3, 300_000_000, "5.9", 1_770_000),
        ("comercial", None, 300_000_000, "8", 2_400_000),
        ("lote", None, 50_000_000, "12", 600_000),
    ],
)
def test_predial_2026_valores_conocidos(destino, estrato, avaluo, tarifa, valor) -> None:
    resultado = buscar_tarifa_ipu(2026, destino, estrato, avaluo)
    assert resultado.tarifa_por_mil == Decimal(tarifa)
    assert resultado.obligado
    assert valor_impuesto(avaluo, resultado.tarifa_por_mil) == valor


@pytest.mark.unit
@pytest.mark.req("RF-IPU-03 · Liquidación estimada")
def test_limites_de_16_107_y_135_smmlv_en_2026() -> None:
    assert smmlv(2026) == SMMLV_2026
    # 16 SMMLV = 28.014.480: en 2026 «igual o menor» no paga (Decreto 639 de 2025, art. 207).
    assert not buscar_tarifa_ipu(2026, "residencial", 1, 28_014_480).obligado
    assert buscar_tarifa_ipu(2026, "residencial", 1, 28_014_481).tarifa_por_mil == Decimal(1)
    # 107 SMMLV = 187.346.835 (1 por mil); más de eso, 3 por mil.
    assert buscar_tarifa_ipu(2026, "residencial", 2, 187_346_835).tarifa_por_mil == Decimal(1)
    assert buscar_tarifa_ipu(2026, "residencial", 2, 187_346_836).tarifa_por_mil == Decimal(3)
    # 135 SMMLV = 236.372.175: hasta ahí 3 por mil; después, el rango general (5,7).
    assert buscar_tarifa_ipu(2026, "residencial", 3, 236_372_175).tarifa_por_mil == Decimal(3)
    assert buscar_tarifa_ipu(2026, "residencial", 3, 236_372_176).tarifa_por_mil == Decimal("5.7")
    assert buscar_tarifa_ipu(2026, "residencial", 2, 236_372_176).tarifa_por_mil == Decimal("5.7")


@pytest.mark.unit
@pytest.mark.req("RF-IPU-03 · Liquidación estimada")
def test_estrato_1_y_2_bajo_el_limite_no_estan_obligados() -> None:
    for estrato in (1, 2):
        r = buscar_tarifa_ipu(2026, "residencial", estrato, 25_000_000)
        assert not r.obligado
        assert r.tarifa_por_mil == 0
        assert valor_impuesto(25_000_000, r.tarifa_por_mil) == 0


@pytest.mark.unit
@pytest.mark.req("RF-IPU-03 · Liquidación estimada")
def test_2027_con_regla_en_smmlv_falla_y_no_usa_el_de_2026() -> None:
    for estrato in (1, 2, 3):
        with pytest.raises(DatoNoPublicadoError):
            buscar_tarifa_ipu(2027, "residencial", estrato, 150_000_000)


@pytest.mark.unit
@pytest.mark.req("RF-IPU-03 · Liquidación estimada")
def test_2027_con_regla_en_pesos_responde() -> None:
    assert buscar_tarifa_ipu(2027, "residencial", 4, 350_000_000).tarifa_por_mil == Decimal("6.1")
    assert buscar_tarifa_ipu(2027, "comercial", None, 300_000_000).tarifa_por_mil == Decimal(8)
    assert buscar_tarifa_ipu(2027, "lote", None, 50_000_000).tarifa_por_mil == Decimal(12)


@pytest.mark.unit
@pytest.mark.parametrize("anio", [2023, 2024, 2025, 2028])
def test_anio_sin_datos_falla_con_error_explicito(anio: int) -> None:
    with pytest.raises(AnioSinDatosError):
        buscar_tarifa_ipu(anio, "residencial", 4, 350_000_000)
    with pytest.raises(AnioSinDatosError):
        calendario(anio)


@pytest.mark.unit
@pytest.mark.req("RF-IPU-04 · Plazos y descuentos")
def test_descuento_por_pronto_pago_del_calendario() -> None:
    assert porcentaje_pronto_pago(2026) == 10
    assert descuento_pronto_pago(2_135_000, 2026) == 213_500
    assert 2_135_000 - descuento_pronto_pago(2_135_000, 2026) == 1_921_500


@pytest.mark.unit
def test_uvt_y_smmlv_de_2027_no_estan_publicados() -> None:
    assert uvt(2025) == 49_799
    with pytest.raises(DatoNoPublicadoError):
        smmlv(2027)


@pytest.mark.unit
@pytest.mark.req("RF-ICA-02 · Estimación por actividad")
def test_ica_bimestres_de_2026_y_paragrafo_del_articulo_21() -> None:
    bim = lambda n: PeriodoICA(2026, "bimestral", n)  # noqa: E731
    for n in range(1, 6):
        assert buscar_tarifa_ica("5611", bim(n)).tarifa_por_mil == Decimal("13.8")
    assert buscar_tarifa_ica("5611", bim(6)).tarifa_por_mil == Decimal(12)
    assert buscar_tarifa_ica("5611", bim(6)).tabla == 2027


@pytest.mark.unit
@pytest.mark.req("RF-ICA-02 · Estimación por actividad")
def test_ica_anual_2026_contra_2027() -> None:
    assert buscar_tarifa_ica("6201", PeriodoICA(2026)).tarifa_por_mil == Decimal("9.66")
    assert buscar_tarifa_ica("6201", PeriodoICA(2027)).tarifa_por_mil == Decimal(10)
    # Un anual de 2026 no usa la tabla de 2027 aunque el bimestre 6 de 2026 sí.
    assert buscar_tarifa_ica("5611", PeriodoICA(2026)).tabla == 2026


@pytest.mark.unit
@pytest.mark.req("RF-ICA-02 · Estimación por actividad")
def test_ica_progresiva_financiera_por_anio() -> None:
    assert buscar_tarifa_ica("6411", PeriodoICA(2027)).tarifa_por_mil == Decimal(20)
    assert buscar_tarifa_ica("6411", PeriodoICA(2028)).tarifa_por_mil == Decimal(19)
    assert buscar_tarifa_ica("6411", PeriodoICA(2029)).tarifa_por_mil == Decimal(18)


@pytest.mark.unit
def test_ica_errores_explicitos() -> None:
    with pytest.raises(AnioSinDatosError):
        buscar_tarifa_ica("5611", PeriodoICA(2025))
    with pytest.raises(ActividadNoReconocidaError):
        buscar_tarifa_ica("0000", PeriodoICA(2026))
    with pytest.raises(ValueError):
        PeriodoICA(2026, "bimestral")
