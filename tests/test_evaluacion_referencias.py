"""Verificador de referencias (ADR-24, A7): sin red, con el adaptador sintético en memoria."""

import copy

import pytest

from src.evaluacion.escenarios import cargar_conjunto
from src.evaluacion.referencias import cifras_de, siguiente_dia_habil, verificar_escenario

OBS05 = "RF-OBS-05 · Ejecución repetible de pruebas"


@pytest.mark.unit
@pytest.mark.req(OBS05)
def test_extrae_cifras_con_su_tipo_y_sin_normas_ni_divisor() -> None:
    texto = (
        "Ley 44 de 1990, art. 4: $350.000.000 × 6,1 / 1.000 = $2.135.000, con el 10 % hasta el "
        "17 de abril de 2026; tope de 600 UVT."
    )
    tipos = {(c.tipo, c.texto) for c in cifras_de(texto)}
    assert ("pesos", "$350.000.000") in tipos and ("pesos", "$2.135.000") in tipos
    assert ("porcentaje", "10 %") in tipos and ("fecha", "17 de abril de 2026") in tipos
    assert ("unidades", "600 UVT") in tipos
    assert not any(t[1] in ("1.000", "44", "1990") for t in tipos)


@pytest.mark.unit
@pytest.mark.req(OBS05)
def test_siguiente_dia_habil_salta_fines_de_semana_y_festivos() -> None:
    from datetime import date

    assert siguiente_dia_habil(date(2026, 10, 3)) == date(2026, 10, 5)  # sábado -> lunes
    assert siguiente_dia_habil(date(2026, 10, 12)) == date(2026, 10, 13)  # festivo -> martes


@pytest.mark.unit
@pytest.mark.req(OBS05, "RNF-16 · Tasa de respuestas correctas")
def test_todas_las_referencias_tienen_fuente_y_cifras_verificadas() -> None:
    """Criterio de entrada a la corrida 1: si falla, es una parada (Rodolfo decide)."""
    pendientes = {
        r.escenario: (r.fuentes_faltantes, r.sin_resolver)
        for r in (verificar_escenario(e) for e in cargar_conjunto(["principal", "R3", "R4"]))
        if not r.pasa
    }
    assert not pendientes


@pytest.mark.unit
@pytest.mark.req(OBS05)
@pytest.mark.parametrize(
    ("id_", "bien", "mal"),
    [
        ("IPU-10", "2.135.000", "2.136.000"),
        ("IPU-08", "10 de julio de 2026", "11 de julio de 2026"),
        ("IPU-07", "10 %", "15 %"),
        ("ICA-05", "3.450.000", "3.460.000"),
    ],
)
def test_una_cifra_alterada_queda_sin_resolver(id_, bien, mal) -> None:
    esc = copy.deepcopy(next(e for e in cargar_conjunto(["principal"]) if e["id"] == id_))
    esc["respuesta_referencia"] = str(esc["respuesta_referencia"]).replace(bien, mal, 1)
    assert verificar_escenario(esc).sin_resolver


@pytest.mark.unit
@pytest.mark.req(OBS05)
def test_una_fuente_que_no_esta_en_la_base_se_reporta() -> None:
    esc = copy.deepcopy(next(e for e in cargar_conjunto(["principal"]) if e["id"] == "IPU-08"))
    esc["fuentes_esperadas"] = ["Acuerdo 999 de 2031, art. 1", "datos/calendario/2099.yaml"]
    assert verificar_escenario(esc).fuentes_faltantes == esc["fuentes_esperadas"]
