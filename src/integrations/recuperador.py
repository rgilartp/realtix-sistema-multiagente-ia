"""Interfaz del recuperador y una implementación provisional en memoria.

B7 usa esta interfaz; B8 la reemplaza con la recuperación híbrida (Chroma + BM25 + RRF, ADR-04).
`RecuperadorEnMemoria` lee `knowledge_base/` y puntúa por solapamiento de palabras: sirve para
probar el flujo, no para medir la calidad de la recuperación.
"""

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import yaml

RAIZ_BASE = Path(__file__).resolve().parent.parent.parent / "knowledge_base"
PALABRA = re.compile(r"[a-z0-9]{3,}")


@dataclass(frozen=True)
class Fragmento:
    texto: str
    fuente: str  # archivo de la norma, con su colección
    seccion: str  # encabezado del fragmento (artículo)
    similitud: float  # coseno del canal vectorial (en memoria: solapamiento de palabras)
    norma: str = ""  # nombre de la norma, de `fuentes.yaml`
    url: str = ""

    @property
    def cita(self) -> str:
        """Norma y artículo, para citar: «Ley 44 de 1990, art. 4»."""
        norma = self.norma or self.fuente
        articulo = re.sub(r"^Art[ií]culo\s+", "art. ", self.seccion)
        if not articulo or articulo in norma:
            return norma
        return f"{norma}, {articulo}"


class Recuperador(Protocol):
    def recuperar(
        self,
        consulta: str,
        *,
        coleccion: str | None = None,
        k: int = 5,
        anio: int | None = None,
    ) -> list[Fragmento]:
        """Los `k` fragmentos más cercanos, de una colección o de todas, vigentes en `anio`."""
        ...


def normas_por_archivo(raiz: Path = RAIZ_BASE) -> dict[str, tuple[str, str]]:
    """`coleccion/archivo.md` -> (norma, url principal), leídos de cada `fuentes.yaml`."""
    normas: dict[str, tuple[str, str]] = {}
    for indice in sorted(raiz.glob("*/fuentes.yaml")):
        for fuente in yaml.safe_load(indice.read_text(encoding="utf-8"))["fuentes"]:
            url = fuente.get("url") or ""
            normas[f"{indice.parent.name}/{fuente['archivo']}"] = (
                str(fuente["norma"]),
                str(url[0] if isinstance(url, list) else url),
            )
    return normas


def _palabras(texto: str) -> set[str]:
    sin_tildes = "".join(
        c for c in unicodedata.normalize("NFD", texto.lower()) if unicodedata.category(c) != "Mn"
    )
    return set(PALABRA.findall(sin_tildes))


class RecuperadorEnMemoria:
    """Fragmentos por encabezado `##` de cada norma en Markdown de `knowledge_base/`."""

    def __init__(self, raiz: Path = RAIZ_BASE) -> None:
        self._fragmentos: list[tuple[str, Fragmento, set[str]]] = []
        normas = normas_por_archivo(raiz)
        for archivo in sorted(raiz.glob("*/*.md")):
            coleccion = archivo.parent.name
            norma, url = normas.get(f"{coleccion}/{archivo.name}", ("", ""))
            partes = re.split(r"^## ", archivo.read_text(encoding="utf-8"), flags=re.MULTILINE)
            for parte in partes[1:]:
                encabezado, _, cuerpo = parte.partition("\n")
                texto = cuerpo.strip()
                if texto:
                    fragmento = Fragmento(
                        texto, f"{coleccion}/{archivo.name}", encabezado.strip(), 0.0, norma, url
                    )
                    self._fragmentos.append((coleccion, fragmento, _palabras(texto)))

    def recuperar(
        self,
        consulta: str,
        *,
        coleccion: str | None = None,
        k: int = 5,
        anio: int | None = None,  # el recuperador en memoria no filtra por vigencia
    ) -> list[Fragmento]:
        buscadas = _palabras(consulta)
        if not buscadas:
            return []
        puntuados: list[Fragmento] = []
        for col, fragmento, palabras in self._fragmentos:
            if coleccion is not None and col != coleccion:
                continue
            similitud = len(buscadas & palabras) / len(buscadas)
            if similitud > 0:
                puntuados.append(
                    Fragmento(
                        fragmento.texto,
                        fragmento.fuente,
                        fragmento.seccion,
                        similitud,
                        fragmento.norma,
                        fragmento.url,
                    )
                )
        puntuados.sort(key=lambda f: f.similitud, reverse=True)
        return puntuados[:k]
