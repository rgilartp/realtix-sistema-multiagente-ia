"""Expresiones que relacionan una fecha con hoy, sin modelo (fechas por código).

La relación de una fecha con hoy la decide el código (`ya_paso`, `vencida_a_hoy` y similares);
el modelo da la fecha exacta y nunca hace la cuenta. Este verificador encuentra en una respuesta
las expresiones que delatan esa cuenta: «mañana», «pasado mañana», «ayer», «anteayer», «hace N
días, semanas o meses» y «falta(n)» o «queda(n) N días». No marca la mañana como parte del día
(«de la mañana», «8:00 a. m.») ni los plazos legales («dentro de los 10 días hábiles», «en 15 días
hábiles»).
"""

import re

_NUMERO = (
    r"(?:\d+|un|una|uno|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|once|doce|trece|"
    r"catorce|quince|dieciséis|diecisiete|dieciocho|diecinueve|veinte|treinta|pocos|pocas|"
    r"varios|varias|algunos|algunas)"
)
RELATIVAS = re.compile(
    r"\bpasado\s+mañana\b"
    r"|(?<!\bla\s)(?<!\bpasado\s)\bmañana\b"
    r"|\banteayer\b|\bantier\b|\bayer\b"
    rf"|\bhace\s+{_NUMERO}\s+(?:días?|semanas?|mes(?:es)?)\b"
    rf"|\b(?:faltan?|quedan?)\s+(?:solo\s+|apenas\s+)?{_NUMERO}\s+días?\b",
    re.IGNORECASE,
)


def expresiones_relativas(texto: str) -> list[str]:
    """Las expresiones relativas a hoy del texto, sin repetir y en el orden en que aparecen."""
    return list(dict.fromkeys(m.group(0).lower() for m in RELATIVAS.finditer(texto)))
