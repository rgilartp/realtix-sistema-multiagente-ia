"""Servicio de confianza (ADR-17): casos límite, origen del nivel, cobertura y escala."""

import pytest

from src.services.confianza import (
    EscalaSimilitud,
    combinar_niveles,
    evaluar_parte,
    factor_cobertura,
    normalizar_similitud,
)

UMBRAL = 0.7


@pytest.mark.unit
@pytest.mark.req("RF-ESC-01 · Cálculo del nivel de confianza")
def test_umbral_exacto_se_aprueba_y_un_poco_menos_escala() -> None:
    # 0,4 × 0,75 + 0,4 × 0,5 + 0,2 × 1 = 0,70 exacto
    exacto = evaluar_parte(0.75, "parcial", 1.0, umbral=UMBRAL)
    assert exacto.nivel == pytest.approx(0.7) and exacto.aprobada and exacto.motivo is None
    debajo = evaluar_parte(0.74, "parcial", 1.0, umbral=UMBRAL)
    assert not debajo.aprobada and debajo.motivo == "confianza insuficiente"


@pytest.mark.unit
@pytest.mark.req("RF-ESC-01 · Cálculo del nivel de confianza")
def test_sin_fragmentos_se_renormaliza_sobre_suficiencia_y_cobertura() -> None:
    completa = evaluar_parte(None, "completa", 1.0, umbral=UMBRAL)
    assert completa.nivel == pytest.approx(1.0) and completa.aprobada
    parcial = evaluar_parte(None, "parcial", 1.0, umbral=UMBRAL)
    assert parcial.nivel == pytest.approx((0.4 * 0.5 + 0.2) / 0.6)  # 0,667 < 0,7
    assert not parcial.aprobada


@pytest.mark.unit
@pytest.mark.req("RF-ESC-01 · Cálculo del nivel de confianza")
def test_aclaracion_y_rechazo_por_acceso_valen_1_con_su_origen() -> None:
    aclaracion = evaluar_parte(None, "aclaracion", 0.0, umbral=UMBRAL)
    rechazo = evaluar_parte(None, "completa", 1.0, rechazo_acceso=True, umbral=UMBRAL)
    calculada = evaluar_parte(0.9, "completa", 1.0, umbral=UMBRAL)
    assert (aclaracion.nivel, aclaracion.origen, aclaracion.aprobada) == (1.0, "aclaracion", True)
    assert (rechazo.nivel, rechazo.origen, rechazo.aprobada) == (1.0, "rechazo_acceso", True)
    # B15 calibra solo con los niveles que salen de la fórmula.
    assert calculada.origen == "formula" and calculada.nivel < 1.0


@pytest.mark.unit
@pytest.mark.req("RF-ESC-01 · Cálculo del nivel de confianza")
def test_sin_cobertura_nunca_se_aprueba_aunque_el_puntaje_alcance() -> None:
    r = evaluar_parte(1.0, "completa", 0.0, umbral=0.1)
    assert r.nivel >= 0.1 and not r.aprobada and r.motivo == "sin cobertura"


@pytest.mark.unit
@pytest.mark.req("RF-ESC-01 · Cálculo del nivel de confianza")
def test_en_una_consulta_multiagente_cuenta_el_menor_nivel() -> None:
    assert combinar_niveles(None, 0.9) == 0.9
    assert combinar_niveles(0.94, 0.48) == 0.48 and combinar_niveles(0.48, 0.94) == 0.48


@pytest.mark.unit
@pytest.mark.req("RF-ESC-01 · Cálculo del nivel de confianza")
def test_la_escala_de_la_similitud_es_un_parametro() -> None:
    assert normalizar_similitud(0.5) == 0.5  # identidad por defecto hasta B8
    escala = EscalaSimilitud(minimo=0.2, maximo=0.8)
    assert normalizar_similitud(0.2, escala) == 0.0
    assert normalizar_similitud(0.5, escala) == pytest.approx(0.5)
    assert normalizar_similitud(0.95, escala) == 1.0 and normalizar_similitud(0.0, escala) == 0.0
    with pytest.raises(ValueError):
        normalizar_similitud(0.5, EscalaSimilitud(0.5, 0.5))
    ajustada = evaluar_parte(0.2, "completa", 1.0, umbral=UMBRAL, escala=escala)
    assert ajustada.nivel == pytest.approx(0.6)  # similitud normalizada 0


@pytest.mark.unit
@pytest.mark.req("RF-SYS-03 · Tributos y municipio cubiertos")
@pytest.mark.parametrize(
    ("tributo", "municipio", "declarada", "esperada"),
    [
        ("ipu", None, 1.0, 1.0),
        ("ica", "Bogotá", 1.0, 1.0),
        ("ipu", "Medellín", 1.0, 0.0),  # otro municipio: fuera del alcance
        ("renta", None, 1.0, 0.0),  # otro tributo
        (None, "Medellín", 1.0, 1.0),  # general u OCR: no es un tributo
        ("ipu", None, 0.5, 0.5),  # lo que declara el agente solo puede bajarla
        ("ipu", None, 7.0, 1.0),
    ],
)
def test_factor_de_cobertura_combina_alcance_y_lo_declarado(
    tributo, municipio, declarada, esperada
) -> None:
    assert factor_cobertura(tributo, municipio, declarada) == esperada
