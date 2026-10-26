"""Usuarios de prueba: el valor escrito a mano, la función de dominio y la base deben coincidir.

El fixture se escribió desde la norma, sin llamar a ninguna función del repositorio; si el
esperado saliera de la misma función que se prueba, la prueba no probaría nada.
"""

from decimal import Decimal
from pathlib import Path

import pytest
import yaml

from src.data.models import ESTADOS_VIGENTES
from src.services.errores import DatoNoPublicadoError
from src.services.ica import PeriodoICA, buscar_tarifa_ica
from src.services.predial import buscar_tarifa_ipu, descuento_pronto_pago

FIXTURE = Path(__file__).parent / "fixtures" / "usuarios_prueba.yaml"
USUARIOS = yaml.safe_load(FIXTURE.read_text(encoding="utf-8"))["usuarios"]
PREDIOS = [(u["id"], u["contribuyente_id"], p) for u in USUARIOS for p in u["predios"]]
CON_COPIA = [c for c in PREDIOS if "obligaciones" in c[2] or "pagos" in c[2]]
GRUPOS = {
    "aviso_ia", "acceso", "ipu", "ica", "general", "ocr", "fuera_de_alcance",
    "multiagente", "escalamiento", "ambiguas_varios_turnos", "horario", "robustez",
}  # fmt: skip


def _id(caso) -> str:
    return f"{caso[0]}-{caso[2]['matricula']}"


@pytest.mark.unit
@pytest.mark.req("RF-AUT-01 · Verificación de identidad")
def test_son_12_usuarios_y_cubren_todos_los_grupos_de_escenarios() -> None:
    assert [u["id"] for u in USUARIOS] == [f"U{n:02d}" for n in range(1, 13)]
    assert all(u["cubre"] for u in USUARIOS)
    assert set().union(*(set(u["cubre"]) for u in USUARIOS)) == GRUPOS


@pytest.mark.unit
@pytest.mark.req("RF-IPU-03 · Liquidación estimada")
def test_hay_preferenciales_de_estratos_1_a_3_y_el_caso_de_16_smmlv() -> None:
    por_tarifa = {
        p["ipu_2026"]["tarifa_por_mil"] for _, _, p in PREDIOS if p["estrato"] in (1, 2, 3)
    }
    assert {"1", "3", "0"} <= por_tarifa
    u09 = next(p for u, _, p in PREDIOS if u == "U09")
    u10 = next(p for u, _, p in PREDIOS if u == "U10")
    assert 16 * 1_750_905 < u09["avaluo_2026"] <= 107 * 1_750_905 and u09["estrato"] in (1, 2)
    assert u10["avaluo_2026"] <= 135 * 1_750_905 and u10["estrato"] == 3


@pytest.mark.unit
@pytest.mark.req("RF-IPU-03 · Liquidación estimada")
@pytest.mark.parametrize("caso", PREDIOS, ids=_id)
def test_ipu_2026_escrito_a_mano_igual_a_la_funcion_y_a_la_base(caso, datos_sinteticos) -> None:
    _, contribuyente, predio = caso
    esperado = predio["ipu_2026"]
    regla = buscar_tarifa_ipu(2026, predio["destino"], predio["estrato"], predio["avaluo_2026"])
    assert regla.tarifa_por_mil == Decimal(esperado["tarifa_por_mil"])
    assert regla.obligado == (esperado["estado"] != "NO_OBLIGADO")
    assert esperado["valor"] == round(predio["avaluo_2026"] * regla.tarifa_por_mil / 1000)
    assert esperado["descuento"] == descuento_pronto_pago(esperado["valor"], 2026)
    assert esperado["base"] == predio["avaluo_2026"]
    assert esperado["fuente"]

    en_base = next(
        o
        for o in datos_sinteticos.obligaciones
        if o.matricula_catastral == predio["matricula"]
        and o.tipo_tributo == "IPU"
        and o.vigencia_fiscal == 2026
    )
    assert en_base.base_gravable == esperado["base"]
    assert en_base.tarifa_por_mil == Decimal(esperado["tarifa_por_mil"])
    assert en_base.valor_liquidado == esperado["valor"]
    assert en_base.descuento_pronto_pago == esperado["descuento"]
    assert en_base.estado_pago == esperado["estado"]
    assert en_base.origen_tarifa == "oficial"
    assert en_base.en_spac == esperado.get("en_spac", False)


@pytest.mark.unit
@pytest.mark.req("RF-IPU-03 · Liquidación estimada")
def test_ejemplo_de_la_seccion_4_4() -> None:
    u03 = next(p for u, _, p in PREDIOS if u == "U03")["ipu_2026"]
    assert u03["valor"] - u03["descuento"] == u03["valor_con_descuento"] == 1_921_500


@pytest.mark.unit
@pytest.mark.req("RF-ICA-02 · Estimación por actividad")
@pytest.mark.parametrize("caso", [c for c in PREDIOS if "ica_2026" in c[2]], ids=_id)
def test_ica_2026_escrito_a_mano_igual_a_la_funcion_y_a_la_base(caso, datos_sinteticos) -> None:
    _, contribuyente, predio = caso
    esperado = predio["ica_2026"]
    periodo = (
        PeriodoICA(2026, "bimestral", 4)
        if esperado["regimen"] == "comun_bimestral"
        else PeriodoICA(2026)
    )
    tarifa = buscar_tarifa_ica(esperado["ciiu"], periodo)
    assert tarifa.tarifa_por_mil == Decimal(esperado["tarifa_por_mil"])
    if esperado["regimen"] == "comun_bimestral":
        assert buscar_tarifa_ica(
            esperado["ciiu"], PeriodoICA(2026, "bimestral", 6)
        ).tarifa_por_mil == Decimal(predio["ica_bimestre_6_por_mil"])
    en_base = next(
        o
        for o in datos_sinteticos.obligaciones
        if o.matricula_catastral == predio["matricula"]
        and o.tipo_tributo == "ICA"
        and o.vigencia_fiscal == 2026
    )
    assert en_base.base_gravable == esperado["base"]
    assert en_base.tarifa_por_mil == Decimal(esperado["tarifa_por_mil"])
    assert en_base.valor_liquidado == esperado["valor"]
    assert en_base.estado_pago == esperado["estado"]
    assert en_base.fecha_limite_pago.isoformat() == esperado["fecha_limite"]
    contribuyente_base = next(
        c for c in datos_sinteticos.contribuyentes if c.id_contribuyente == contribuyente
    )
    assert contribuyente_base.regimen_ica == esperado["regimen"]
    assert contribuyente_base.codigo_ciiu == esperado["ciiu"]


@pytest.mark.unit
@pytest.mark.req("RF-IPU-02 · Estado de cuenta e historial")
@pytest.mark.parametrize("caso", PREDIOS, ids=_id)
def test_estado_de_cuenta_esperado_en_las_dos_implementaciones(caso, adaptador) -> None:
    _, contribuyente, predio = caso
    cuenta = adaptador.get_estado_cuenta(predio["matricula"], contribuyente)
    assert cuenta.obligaciones_pendientes == predio["estado_cuenta"]["pendientes"]
    assert cuenta.saldo_total_pendiente == predio["estado_cuenta"]["saldo"]
    assert all(
        o.estado_pago in ESTADOS_VIGENTES
        for o in adaptador.get_obligaciones_vigentes(predio["matricula"], contribuyente, "IPU")
    )
    avaluo = adaptador.get_avaluo_catastral(predio["matricula"], contribuyente)
    assert avaluo.avaluo_catastral == predio["avaluo_2026"]


@pytest.mark.unit
@pytest.mark.req("RF-IPU-03 · Liquidación estimada")
def test_pagos_esperados_de_2026(datos_sinteticos) -> None:
    for _, _, predio in PREDIOS:
        esperado = predio["ipu_2026"]
        if "valor_pagado" not in esperado:
            continue
        obl = next(
            o
            for o in datos_sinteticos.obligaciones
            if o.matricula_catastral == predio["matricula"]
            and o.tipo_tributo == "IPU"
            and o.vigencia_fiscal == 2026
        )
        pagado = sum(
            p.valor_pagado for p in datos_sinteticos.pagos if p.id_obligacion == obl.id_obligacion
        )
        assert pagado == esperado["valor_pagado"], predio["matricula"]


@pytest.mark.unit
@pytest.mark.req("RF-IPU-03 · Liquidación estimada")
def test_2027_de_los_preferenciales_no_se_estima_sin_el_smmlv() -> None:
    for u, _, p in PREDIOS:
        if u in ("U09", "U10", "U11"):
            with pytest.raises(DatoNoPublicadoError):
                buscar_tarifa_ipu(2027, p["destino"], p["estrato"], p["avaluo_2026"])


@pytest.mark.unit
@pytest.mark.req("RF-IPU-02 · Estado de cuenta e historial")
@pytest.mark.parametrize("caso", CON_COPIA, ids=_id)
def test_obligaciones_y_pagos_copiados_coinciden_con_el_adaptador(caso, adaptador) -> None:
    _, contribuyente, predio = caso
    cuenta = adaptador.get_estado_cuenta(predio["matricula"], contribuyente)
    vigencias = {o.vigencia_fiscal: o for o in cuenta.obligaciones if o.tipo_tributo == "IPU"}
    if "obligaciones" in predio:
        assert sorted(vigencias) == [o["vigencia"] for o in predio["obligaciones"]]
    for esperada in predio.get("obligaciones", []):
        obtenida = vigencias[esperada["vigencia"]]
        assert obtenida.valor_liquidado == esperada["valor"], esperada
        assert obtenida.estado_pago == esperada["estado"], esperada
        if "fecha_limite" in esperada:
            assert obtenida.fecha_limite_pago.isoformat() == esperada["fecha_limite"]
    pagos = adaptador.get_historial_pagos(predio["matricula"], contribuyente)
    if "pagos" in predio:
        obtenidos = sorted((p.fecha_pago.isoformat(), p.valor_pagado, p.medio_pago) for p in pagos)
        esperados = sorted((p["fecha"], p["valor"], p["medio"]) for p in predio["pagos"])
        assert obtenidos == esperados
