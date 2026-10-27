"""Verificación de las citas de una respuesta, sin modelo (F5 de la corrida 1).

Reconoce las citas «norma, art. N» de un texto (por ejemplo, «Decreto 807 de 1993, art. 66»,
«Ley 1819 de 2016 (arts. 342 y 345)» o «Decreto 1074 de 2015, caps. 25 y 26, art. 2.2.2.25.1.1»)
y dice cuáles no están en las fuentes que tuvo el agente: el encabezado de cada fragmento (su norma
y su artículo) y sus líneas de fuente o de vigencia, las fuentes de las herramientas y las notas del
sistema. Solo se revisan las citas con artículo; el capítulo, el parágrafo o el literal no cuentan.
La comparación usa la misma normalización que la evaluación (F3): sin tildes, sin mayúsculas y sin
«Distrital»; «Decreto Ley» y «Decreto» son el mismo tipo.
"""

import re
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass

# «Decreto Distrital 352» es «Decreto 352»: el adjetivo entre el tipo de la norma y su número no
# cambia la norma. Se aplica sobre texto ya normalizado (minúsculas y sin tildes).
DISTRITAL = re.compile(r"\b(decreto|acuerdo)\s+distrital\s+(?=(?:no\.?\s*)?\d)")
_NUMERO_DE_ARTICULO = r"\d+(?:[.-]\d+)*"
_NORMA = (
    r"\b(?P<tipo>decreto[\s-]+ley|decreto|acuerdo|ley|resolucion)\s+(?:no\.?\s*)?"
    r"(?P<numero>[a-z]{0,5}-?\d[\d.]*\d|[a-z]{0,5}-?\d)(?:\s+de\s+(?P<anio>\d{4}))?"
)
_CITA = re.compile(
    _NORMA + r"(?:\s*\([^)]*\))?"  # «(rangos del predial de 2026)»
    r"(?:\s*,\s*(?:caps?\.?|capitulos?|titulo)\s*[ivxlcdm\d]+(?:\s*y\s*[ivxlcdm\d]+)?)*"
    r"\s*[,(]?\s*(?:arts?\.|articulos?)\s*"
    rf"(?P<articulos>{_NUMERO_DE_ARTICULO}"
    rf"(?:\s*(?:y|a)\s*{_NUMERO_DE_ARTICULO}|\s*,\s*(?!\d{{4}}\b){_NUMERO_DE_ARTICULO})*)"
)
_SOLO_NORMA = re.compile(_NORMA)
_ARTICULO_DE_SECCION = re.compile(rf"^art[ií]culo\s+({_NUMERO_DE_ARTICULO})", re.IGNORECASE)
_LINEA_DE_FUENTE = re.compile(r"^\W*\*\*(?:fuente|vigencia)[^*]*\*\*.*$", re.IGNORECASE | re.M)


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


def _tipo(texto: str) -> str:
    return "decreto" if texto.startswith("decreto") else texto


def _articulos(lista: str) -> list[str]:
    """«13 a 15» son 13, 14 y 15; «2 y 9» o «2, 9» son 2 y 9."""
    salida: list[str] = []
    partes = re.split(r"\s*(y|a|,)\s*", lista)
    for i in range(0, len(partes), 2):
        actual = partes[i]
        anterior = salida[-1] if salida else None
        if i and partes[i - 1] == "a" and anterior and anterior.isdigit() and actual.isdigit():
            salida += [str(n) for n in range(int(anterior) + 1, int(actual) + 1)][:200]
        else:
            salida.append(actual)
    return salida


def extraer_citas(texto: str) -> list[Cita]:
    """Las citas con artículo de un texto, una por artículo."""
    citas = []
    for m in _CITA.finditer(normalizar(texto)):
        numero = m["numero"].replace(".", "")
        for articulo in _articulos(m["articulos"]):
            citas.append(Cita(_tipo(m["tipo"]), numero, m["anio"], articulo))
    return citas


def fuentes_de_fragmento(norma: str, seccion: str, texto: str) -> list[str]:
    """Lo que un fragmento sustenta como cita: su norma (la primera que nombra) con el artículo de
    su sección, las citas de la propia norma («Acuerdo 780 de 2020, arts. 6 y 7») y sus líneas de
    fuente o de vigencia (el glosario pone la fuente de cada término en el texto)."""
    fuentes = [norma, *_LINEA_DE_FUENTE.findall(texto)]
    articulo = _ARTICULO_DE_SECCION.match(seccion.strip())
    primera = _SOLO_NORMA.search(normalizar(norma))
    if articulo and primera:
        fuentes.append(f"{primera.group(0)}, art. {articulo.group(1)}")
    return fuentes


def citas_sin_fuente(texto: str, fuentes: Iterable[str]) -> list[str]:
    """Las citas del texto, una por artículo y sin repetir, que no están en ninguna fuente."""
    validas = [c for f in fuentes for c in extraer_citas(f)]
    sin_fuente = [c.texto for c in extraer_citas(texto) if not any(c.coincide(v) for v in validas)]
    return list(dict.fromkeys(sin_fuente))
