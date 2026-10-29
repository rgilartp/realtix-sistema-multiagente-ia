"""Verificador sin modelo de las expresiones que relacionan una fecha con hoy."""

import pytest

from src.services.calendario_tributario import ya_paso
from src.services.expresiones_relativas import expresiones_relativas

REQ = ("RF-IPU-04 · Plazos y descuentos", "RF-ICA-03 · Fechas de declaración")


@pytest.mark.unit
@pytest.mark.req(*REQ)
@pytest.mark.parametrize(
    ("texto", "esperadas"),
    [
        ("Vence mañana, el 9 de marzo.", ["mañana"]),
        ("Mañana vence la cuota.", ["mañana"]),
        ("Vence pasado mañana.", ["pasado mañana"]),
        ("Venció ayer y la anterior anteayer.", ["ayer", "anteayer"]),
        ("Venció hace 83 días.", ["hace 83 días"]),
        ("Venció hace dos semanas; la otra, hace 1 mes.", ["hace dos semanas", "hace 1 mes"]),
        ("Faltan 8 días para el plazo.", ["faltan 8 días"]),
        ("Solo falta un día.", ["falta un día"]),
        ("Te quedan 3 días.", ["quedan 3 días"]),
    ],
)
def test_encuentra_las_expresiones_relativas_a_hoy(texto: str, esperadas: list[str]) -> None:
    assert expresiones_relativas(texto) == esperadas


@pytest.mark.unit
@pytest.mark.req(*REQ)
@pytest.mark.parametrize(
    "texto",
    [
        "La fecha límite es el 10 de marzo de 2091; ya venció.",
        "Atiendo de lunes a viernes, de 8:00 a. m. a 5:00 p. m.",
        "Puedes llamar a las 8 de la mañana o por la mañana.",
        "Se responde dentro de los 10 días hábiles.",
        "Tiene que corregirse en 15 días hábiles.",
        "Los rendimientos financieros hacen parte de la base; falta el código CIIU.",
        "Quedan exentos los predios de la lista.",
    ],
)
def test_no_marca_plazos_legales_ni_la_hora_ni_otras_palabras(texto: str) -> None:
    assert expresiones_relativas(texto) == []


@pytest.mark.unit
@pytest.mark.req(*REQ)
def test_una_fecha_igual_a_hoy_no_ha_pasado() -> None:
    from datetime import date

    hoy = date(2091, 3, 10)  # fechas inventadas
    assert not ya_paso("2091-03-11", hoy) and not ya_paso("2091-03-10", hoy)
    assert ya_paso("2091-03-09", hoy) and ya_paso(date(2091, 3, 9), hoy)
