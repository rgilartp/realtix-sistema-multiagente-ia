"""Expresiones que relacionan una fecha con el día de la consulta, sin modelo (fechas por código).

El sistema no relaciona fechas con el día de la consulta: da la fecha exacta y, cuando importa, si
el plazo ya venció o aún no vence, según lo que calcula el código (`ya_paso`, `vencida_a_hoy` y
similares). Este verificador encuentra en una respuesta lo que no debe aparecer:

- las expresiones relativas al día de la consulta: «hoy» (también «a la fecha de hoy» y «hoy en
  día»), «mañana», «pasado mañana», «ayer», «anteayer», «hace N días, semanas o meses» y
  «falta(n)» o «queda(n) N días»;
- las referencias internas: «fragmento [n]», «fragmentos [n]» y «consultar herramientas».

No marca la mañana como parte del día («de la mañana», «cada mañana», «mañana y tarde», «8:00
a. m.»), los plazos legales («dentro de los 10 días hábiles», «se hace 3 días después») ni otras
palabras parecidas («hace parte», «falta el dato», «quedan exentos»).
"""

import re

_NUMERO = (
    r"(?:(?:más|mas|menos)\s+de\s+)?"
    r"(?:\d+|un|una|uno|unos|unas|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|once|doce|"
    r"trece|catorce|quince|dieci\w+|veinte|veinti\w+|treinta|pocos|pocas|varios|varias|algunos|"
    r"algunas)"
)
_CANDIDATAS = re.compile(
    r"\bpasado\s+mañana\b|\bmañana\b|\banteayer\b|\bantier\b|\bayer\b|\bhoy\b"
    rf"|\bhace\s+{_NUMERO}\s+(?:días?|semanas?|mes(?:es)?)\b(?!\s+(?:después|antes)\b)"
    rf"|\b(?:faltan?|quedan?)\s+(?:solo\s+|apenas\s+)?{_NUMERO}\s+días?\b"
    r"|\bfragmentos?\s*\[\s*\d+(?:\s*[,y]\s*\d+)*\s*\]|\bconsultar\s+(?:las\s+|la\s+)?herramientas?\b",
    re.IGNORECASE,
)
# «mañana» como parte del día, no como el día siguiente.
_MAÑANA_DEL_DIA_ANTES = re.compile(r"\b(?:la|cada|toda|una|las)\s*$", re.IGNORECASE)
_MAÑANA_DEL_DIA_DESPUES = re.compile(r"^\s*(?:y|o)\s+(?:la\s+)?tarde\b", re.IGNORECASE)


def expresiones_relativas(texto: str) -> list[str]:
    """Las expresiones relativas al día de la consulta y las referencias internas del texto, sin
    repetir y en el orden en que aparecen."""
    encontradas = []
    for m in _CANDIDATAS.finditer(texto):
        if m.group(0).lower() == "mañana" and (
            _MAÑANA_DEL_DIA_ANTES.search(texto[: m.start()])
            or _MAÑANA_DEL_DIA_DESPUES.match(texto[m.end() :])
        ):
            continue
        encontradas.append(" ".join(m.group(0).lower().split()))
    return list(dict.fromkeys(encontradas))
