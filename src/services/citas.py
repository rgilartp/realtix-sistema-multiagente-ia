"""Verificación de las citas de una respuesta, sin modelo (F5 de la corrida 1).

Reconoce las citas «norma, art. N» de un texto (por ejemplo, «Decreto 807 de 1993, art. 66» o
«Ley 1819 de 2016 (arts. 342 y 345)») y dice cuáles no están en las fuentes que tuvo el agente: los
encabezados de los fragmentos, las fuentes de las herramientas y las notas del sistema. Solo se
revisan las citas con artículo; el capítulo, el parágrafo o el literal no cuentan. La comparación
usa la misma normalización que la evaluación (F3): sin tildes, sin mayúsculas y sin «Distrital».
"""

import re
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass

# «Decreto Distrital 352» es «Decreto 352»: el adjetivo entre el tipo de la norma y su número no
# cambia la norma. Se aplica sobre texto ya normalizado (minúsculas y sin tildes).
DISTRITAL = re.compile(r"\b(decreto|acuerdo)\s+distrital\s+(?=(?:no\.?\s*)?\d)")
_CITA = re.compile(
    r"\b(?P<tipo>decreto[\s-]+ley|decreto|acuerdo|ley|resolucion)\s+(?:no\.?\s*)?"
    r"(?P<numero>[a-z]{0,5}-?\d[\d.]*)(?:\s+de\s+(?P<anio>\d{4}))?"
    r"(?:\s*,\s*(?:cap(?:itulo)?\.?\s*[ivxlcdm\d]+|t[ií]tulo\s+[ivxlcdm\d]+))*"
    r"\s*[,(]?\s*(?:arts?\.|articulos?)\s*"
    r"(?P<articulos>\d+(?:-\d+)?(?:\s*(?:,|y)\s*\d+(?:-\d+)?)*)"
)
_ARTICULO = re.compile(r"\d+(?:-\d+)?")


def normalizar(texto: str) -> str:
    """Minúsculas, sin tildes, sin «Distrital» entre el tipo y el número, y espacios simples."""
    sin_tildes = "".join(
        c for c in unicodedata.normalize("NFD", texto.lower()) if unicodedata.category(c) != "Mn"
    )
    return " ".join(DISTRITAL.sub(r"\1 ", sin_tildes).split())


@dataclass(frozen=True)
class Cita:
    tipo: str
    numero: str
    anio: str | None
    articulo: str

    @property
    def texto(self) -> str:
        """La cita de un artículo, para la observación al modelo: «ley 44 de 1990, art. 13»."""
        anio = f" de {self.anio}" if self.anio else ""
        return f"{self.tipo} {self.numero}{anio}, art. {self.articulo}"

    def coincide(self, otra: "Cita") -> bool:
        """Misma norma y artículo; el año cuenta solo si las dos lo dicen."""
        return (self.tipo, self.numero, self.articulo) == (
            otra.tipo,
            otra.numero,
            otra.articulo,
        ) and (self.anio is None or otra.anio is None or self.anio == otra.anio)


def extraer_citas(texto: str) -> list[Cita]:
    """Las citas con artículo de un texto, una por artículo."""
    citas = []
    for m in _CITA.finditer(normalizar(texto)):
        tipo = re.sub(r"[\s-]+", " ", m["tipo"])
        numero = m["numero"].replace(".", "")
        for articulo in _ARTICULO.findall(m["articulos"]):
            citas.append(Cita(tipo, numero, m["anio"], articulo))
    return citas


def citas_sin_fuente(texto: str, fuentes: Iterable[str]) -> list[str]:
    """Las citas del texto, una por artículo y sin repetir, que no están en ninguna fuente."""
    validas = [c for f in fuentes for c in extraer_citas(f)]
    sin_fuente = [c.texto for c in extraer_citas(texto) if not any(c.coincide(v) for v in validas)]
    return list(dict.fromkeys(sin_fuente))
