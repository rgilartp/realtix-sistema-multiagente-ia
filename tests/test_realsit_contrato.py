"""Contrato del adaptador (Tabla 7) contra las dos implementaciones, y control de acceso."""

import pytest

from src.data.adapter import (
    PredioInaccesibleError,
    PredioNoAutorizadoError,
    PredioNoEncontradoError,
)
from src.data.models import CasoEscalado
from src.services.errores import ActividadNoReconocidaError

U03, U02 = "CC-1000000003", "CC-1000000002"
PREDIO_U03, PREDIO_U02A = "50C-9000301", "50C-9000201"


@pytest.mark.unit
@pytest.mark.req("RF-SYS-05 · Adaptador equivalente a RealSit")
def test_predios_del_contribuyente(adaptador) -> None:
    predios = adaptador.get_predios_contribuyente(U02)
    assert [p.matricula_catastral for p in predios] == ["50C-9000201", "50C-9000202"]
    assert all(p.id_contribuyente == U02 for p in predios)
    assert adaptador.get_predios_contribuyente("CC-0000000000") == []


@pytest.mark.unit
@pytest.mark.req("RF-AUT-02 · Restricción a predios propios")
def test_predio_ajeno_e_inexistente_dan_el_mismo_mensaje(adaptador) -> None:
    with pytest.raises(PredioNoAutorizadoError) as ajeno:
        adaptador.get_estado_cuenta(PREDIO_U02A, U03)
    with pytest.raises(PredioNoEncontradoError) as inexistente:
        adaptador.get_estado_cuenta("50C-0000000", U03)
    assert str(ajeno.value) == str(inexistente.value)
    assert PREDIO_U02A not in str(ajeno.value)
    assert isinstance(ajeno.value, PredioInaccesibleError)


@pytest.mark.unit
@pytest.mark.req("RF-AUT-02 · Restricción a predios propios")
@pytest.mark.parametrize(
    "metodo",
    ["get_estado_cuenta", "get_historial_pagos", "get_avaluo_catastral"],
)
def test_todo_metodo_con_predio_valida_la_propiedad(adaptador, metodo: str) -> None:
    with pytest.raises(PredioNoAutorizadoError):
        getattr(adaptador, metodo)(PREDIO_U02A, U03)
    with pytest.raises(PredioNoAutorizadoError):
        adaptador.get_obligaciones_vigentes(PREDIO_U02A, U03, "IPU")


@pytest.mark.unit
@pytest.mark.req("RF-IPU-02 · Estado de cuenta e historial")
def test_estado_cuenta_e_historial(adaptador) -> None:
    cuenta = adaptador.get_estado_cuenta(PREDIO_U03, U03)
    assert cuenta.contribuyente == U03
    assert cuenta.obligaciones_pendientes == 1
    assert cuenta.saldo_total_pendiente == 2_135_000
    assert [o.vigencia_fiscal for o in cuenta.obligaciones] == [2026, 2025, 2024, 2023]
    pagos = adaptador.get_historial_pagos(PREDIO_U03, U03)
    assert len(pagos) == 3  # 2023 a 2025 pagadas; 2026 vencida
    assert [p.fecha_pago for p in pagos] == sorted((p.fecha_pago for p in pagos), reverse=True)


@pytest.mark.unit
@pytest.mark.req("RF-IPU-02 · Estado de cuenta e historial")
def test_vigentes_son_pendientes_o_vencidas_de_cualquier_vigencia(adaptador) -> None:
    vigentes = adaptador.get_obligaciones_vigentes("50C-9000202", U02, "IPU")
    assert [(o.vigencia_fiscal, o.estado_pago) for o in vigentes] == [
        (2026, "VENCIDO"),
        (2025, "VENCIDO"),
    ]
    assert adaptador.get_obligaciones_vigentes(PREDIO_U02A, U02, "IPU") == []


@pytest.mark.unit
@pytest.mark.req("RF-IPU-02 · Estado de cuenta e historial")
def test_avaluo_por_vigencia_con_la_vigencia_de_la_configuracion(adaptador) -> None:
    assert adaptador.get_avaluo_catastral(PREDIO_U03, U03).avaluo_catastral == 350_000_000
    assert adaptador.get_avaluo_catastral(PREDIO_U03, U03).vigencia_fiscal == 2026
    anterior = adaptador.get_avaluo_catastral(PREDIO_U03, U03, vigencia=2025)
    assert anterior.avaluo_catastral == 333_333_000  # 350.000.000 / 1,05, a miles
    with pytest.raises(LookupError):
        adaptador.get_avaluo_catastral(PREDIO_U03, U03, vigencia=2022)


@pytest.mark.unit
@pytest.mark.req("RF-ICA-02 · Estimación por actividad")
def test_tarifa_ica_de_la_tabla_oficial_y_actividad_desconocida(adaptador) -> None:
    tarifa = adaptador.get_tarifa_ica("5611")
    assert str(tarifa.tarifa_por_mil) == "13.8"
    assert tarifa.fuente
    with pytest.raises(ActividadNoReconocidaError):
        adaptador.get_tarifa_ica("comercio_al_por_menor")


@pytest.mark.unit
@pytest.mark.req("RF-SYS-05 · Adaptador equivalente a RealSit")
def test_las_dos_implementaciones_responden_lo_mismo(base_sintetica, datos_sinteticos) -> None:
    from src.data.adapter import MockRealSitAdapter
    from src.data.memoria import RealSitEnMemoria

    sqlite, memoria = MockRealSitAdapter(base_sintetica), RealSitEnMemoria(datos_sinteticos)
    for predio in datos_sinteticos.predios[::7]:
        c = predio.id_contribuyente
        m = predio.matricula_catastral
        assert sqlite.get_estado_cuenta(m, c) == memoria.get_estado_cuenta(m, c)
        assert sqlite.get_historial_pagos(m, c) == memoria.get_historial_pagos(m, c)
        assert sqlite.get_avaluo_catastral(m, c) == memoria.get_avaluo_catastral(m, c)
        assert sqlite.get_predios_contribuyente(c) == memoria.get_predios_contribuyente(c)


@pytest.mark.unit
@pytest.mark.req("RF-SYS-02 · Alcance de solo lectura")
def test_registrar_caso_va_al_registro_propio_y_no_a_realsit(
    base_sintetica, datos_sinteticos
) -> None:
    from src.data.adapter import MockRealSitAdapter
    from src.data.memoria import RealSitEnMemoria

    casos: list[CasoEscalado] = []

    class Registro:
        def registrar_caso(self, caso: CasoEscalado) -> None:
            casos.append(caso)

    caso = CasoEscalado("CASO-1", "CONV-1", "resumen", 0.0, motivo="solicitud explícita")
    for impl in (
        MockRealSitAdapter(base_sintetica, Registro()),
        RealSitEnMemoria(datos_sinteticos, Registro()),
    ):
        assert impl.registrar_caso_escalado(caso).ok
    assert len(casos) == 2
    with pytest.raises(RuntimeError):
        MockRealSitAdapter(base_sintetica).registrar_caso_escalado(caso)
