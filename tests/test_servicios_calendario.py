"""Régimen y fechas del ICA, fechas del predial y horario de atención con festivos."""

from datetime import datetime, time
from zoneinfo import ZoneInfo

import pytest

from src.services.calendario_tributario import fechas_ica, fechas_predial, regimen_ica
from src.services.errores import AnioSinDatosError, DatoNoPublicadoError
from src.services.horario import Horario, RelojFijo

BOGOTA = ZoneInfo("America/Bogota")
UMBRAL_391_UVT = 19_471_409


# -- Régimen y fechas -----------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.req("RF-ICA-03 · Fechas de declaración")
def test_regimen_de_2026_parte_el_comun_por_el_umbral_de_391_uvt() -> None:
    mayor = regimen_ica(2026, "comun_anual", UMBRAL_391_UVT + 1)
    igual = regimen_ica(2026, "comun_bimestral", UMBRAL_391_UVT)
    assert (mayor.regimen, mayor.periodicidad) == ("comun_bimestral", "bimestral")
    assert (igual.regimen, igual.periodicidad) == ("comun_anual", "anual")
    assert mayor.umbral_en_pesos() == UMBRAL_391_UVT and mayor.umbral_uvt == 391


@pytest.mark.unit
@pytest.mark.req("RF-ICA-03 · Fechas de declaración")
def test_el_preferencial_viene_registrado_y_no_se_deduce_del_impuesto() -> None:
    pref = regimen_ica(2026, "preferencial", UMBRAL_391_UVT * 10)  # el impuesto no lo cambia
    assert (pref.regimen, pref.periodicidad) == ("preferencial", "anual")
    assert regimen_ica(2026, "comun_bimestral").periodicidad == "bimestral"
    with pytest.raises(ValueError):
        regimen_ica(2026, None)


@pytest.mark.unit
@pytest.mark.req("RF-ICA-03 · Fechas de declaración")
def test_regimen_de_2027_da_la_regla_en_uvt_y_falla_solo_al_pasar_a_pesos() -> None:
    regla = regimen_ica(2027, None)
    assert regla.umbral_uvt == 391 and regla.primer_ano_preferencial
    assert regla.sin_declaracion_ingresos_uvt == 1933 and "391 UVT" in regla.regla
    assert "Acuerdo 1084" in regla.fuente and "art. 26" in regla.fuente
    with pytest.raises(DatoNoPublicadoError):
        regla.umbral_en_pesos()
    assert regimen_ica(2027, "preferencial").periodicidad == "anual"


@pytest.mark.unit
@pytest.mark.req("RF-ICA-03 · Fechas de declaración")
def test_fechas_del_ica_de_2026_por_periodicidad() -> None:
    assert fechas_ica(2026, "bimestral") == [
        "2026-04-10", "2026-06-12", "2026-08-21", "2026-10-09", "2026-12-11", "2027-02-12",
    ]  # fmt: skip
    assert fechas_ica(2026, "anual") == ["2027-02-26"]
    with pytest.raises(AnioSinDatosError):
        fechas_ica(2027, "anual")


@pytest.mark.unit
@pytest.mark.req("RF-ICA-03 · Fechas de declaración")
def test_fechas_del_predial_de_2026() -> None:
    f = fechas_predial(2026)
    assert (f["pronto_pago"], f["sin_descuento"]) == ("2026-04-17", "2026-07-10")
    assert f["spac_cuotas"] == ["2026-06-05", "2026-08-14", "2026-10-02", "2026-12-04"]
    with pytest.raises(AnioSinDatosError):
        fechas_predial(2027)


# -- Horario --------------------------------------------------------------------------------------


def _hora(dia: int, hora: int, minuto: int, mes: int = 11) -> datetime:
    return datetime(2026, mes, dia, hora, minuto, tzinfo=BOGOTA)


@pytest.mark.unit
@pytest.mark.req("RNF-06 · Horario de atención")
@pytest.mark.parametrize(
    ("hora", "minuto", "dentro"),
    [(7, 59, False), (8, 0, True), (16, 59, True), (17, 0, False)],
)
def test_limites_del_horario_las_17_00_ya_son_fuera_de_horario(hora, minuto, dentro) -> None:
    assert Horario().en_horario(_hora(12, hora, minuto)) is dentro  # jueves 12 de noviembre


@pytest.mark.unit
@pytest.mark.req("RNF-06 · Horario de atención")
def test_fines_de_semana_y_festivos_estan_fuera_de_horario() -> None:
    h = Horario()
    assert not h.en_horario(_hora(14, 10, 0))  # sábado
    assert not h.en_horario(_hora(16, 10, 0))  # lunes festivo (Independencia de Cartagena)
    assert not h.en_horario(_hora(25, 10, 0, mes=12))  # Navidad
    assert h.en_horario(_hora(17, 10, 0))  # martes hábil


@pytest.mark.unit
@pytest.mark.req("RNF-06 · Horario de atención")
def test_el_13_de_julio_de_2026_es_festivo_ley_2578() -> None:
    assert not Horario().en_horario(datetime(2026, 7, 13, 10, 0, tzinfo=BOGOTA))
    assert Horario().en_horario(datetime(2026, 7, 14, 10, 0, tzinfo=BOGOTA))


@pytest.mark.unit
@pytest.mark.req("RNF-07 · Aviso fuera de horario")
def test_el_viernes_13_de_noviembre_tras_las_5_pm_abre_el_martes_17_a_las_8() -> None:
    h = Horario()
    apertura = h.proxima_apertura(_hora(13, 17, 30))
    assert apertura == datetime(2026, 11, 17, 8, 0, tzinfo=BOGOTA)  # el lunes 16 es festivo
    aviso = h.aviso_fuera_de_horario(_hora(13, 17, 30))
    assert "martes 17 de noviembre de 2026 a las 8:00 a. m." in aviso
    assert "8:00 a. m. a 5:00 p. m." in aviso and "festivos" in aviso
    assert ".." not in aviso


@pytest.mark.unit
@pytest.mark.req("RNF-07 · Aviso fuera de horario")
@pytest.mark.parametrize(
    ("dia", "apertura"),
    [(8, "lunes 9 de noviembre"), (1, "martes 3 de noviembre")],  # domingos; el lunes 2 es festivo
)
def test_el_aviso_nombra_el_dia_de_la_semana_con_su_fecha(dia: int, apertura: str) -> None:
    # Las verificaciones de HOR-01 y HOR-02 buscan «día fecha de mes»: el día suelto no basta,
    # porque el aviso siempre dice «de lunes a viernes».
    aviso = Horario().aviso_fuera_de_horario(_hora(dia, 10, 0))
    assert f"Vuelvo a atender el {apertura} de 2026 a las 8:00 a. m." in aviso


@pytest.mark.unit
@pytest.mark.req("RNF-07 · Aviso fuera de horario")
def test_antes_de_abrir_el_mismo_dia_y_el_reloj_inyectado() -> None:
    reloj = RelojFijo(_hora(12, 6, 30))
    h = Horario(reloj=reloj)
    assert h.proxima_apertura() == _hora(12, 8, 0)  # sin argumento usa el reloj inyectado
    assert not h.en_horario()
    reloj.momento = _hora(12, 9, 0)
    assert h.en_horario()


@pytest.mark.unit
@pytest.mark.req("RNF-06 · Horario de atención")
def test_horario_con_zona_distinta_y_configuracion(entorno_valido) -> None:
    utc = datetime(2026, 11, 12, 13, 0, tzinfo=ZoneInfo("UTC"))  # 8:00 en Bogotá
    assert Horario().en_horario(utc)
    from src.config import cargar_configuracion

    h = Horario.desde_settings(cargar_configuracion(env_file=None), RelojFijo(utc))
    assert (h.inicio, h.fin) == (time(8, 0), time(17, 0)) and h.en_horario()
    with pytest.raises(ValueError):
        Horario(inicio=time(17, 0), fin=time(8, 0))


@pytest.mark.unit
@pytest.mark.req("RF-IPU-04 · Plazos y descuentos", "RF-ICA-03 · Fechas de declaración")
def test_una_fecha_igual_a_hoy_no_ha_pasado() -> None:
    from datetime import date

    from src.services.calendario_tributario import ya_paso

    hoy = date(2091, 3, 10)  # fechas inventadas
    assert not ya_paso("2091-03-11", hoy) and not ya_paso("2091-03-10", hoy)
    assert ya_paso("2091-03-09", hoy) and ya_paso(date(2091, 3, 9), hoy)
