"""Verificador sin modelo de las expresiones que relacionan una fecha con hoy."""

import pytest

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
        ("Hoy vence; a la fecha de hoy y hoy en día.", ["hoy"]),
        ("Venció hace unos días; hace más de 10 días.", ["hace unos días", "hace más de 10 días"]),
        (
            "Faltan menos de 5 días; quedan dieciseis días.",
            ["faltan menos de 5 días", "quedan dieciseis días"],
        ),
        ("Hace veinticinco días.", ["hace veinticinco días"]),
        (
            "No necesito consultar herramientas: el fragmento [1] lo dice.",
            ["consultar herramientas", "fragmento [1]"],
        ),
        ("Según los fragmentos [1, 3].", ["fragmentos [1, 3]"]),
        ("Esta mañana venció. HACE UN MES.", ["mañana", "hace un mes"]),
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
        "Se hace 3 días después del cierre; se hace un mes antes.",
        "Abre cada mañana, en jornada mañana y tarde, desde las 8 de la  mañana.",
        "El fragmento de la norma lo dice; consulta la herramienta del simulador.",
    ],
)
def test_no_marca_plazos_legales_ni_la_hora_ni_otras_palabras(texto: str) -> None:
    assert expresiones_relativas(texto) == []
