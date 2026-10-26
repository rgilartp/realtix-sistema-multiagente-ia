"""Recuperación híbrida: Chroma (vectorial) más BM25 en español, fusionados con RRF (ADR-04).

Por consulta:

- el embedding de la consulta se calcula una sola vez;
- 8 fragmentos por canal (vectorial y BM25), filtrados por colección y, si se da el año gravable,
  por vigencia;
- fusión por rango recíproco (RRF, k = 60) y los 5 mejores al prompt;
- la similitud de cada fragmento es el coseno entre la consulta y el fragmento, calculado
  directamente con sus embeddings, también para los que solo trajo BM25 (sección 3.3). La
  distancia de Chroma no se usa: con el HNSW por defecto es la L2 al cuadrado.

El índice BM25 de cada réplica se construye con los documentos guardados en Chroma y se reconstruye
cuando cambia la versión del corpus (sección 5.5), que se consulta como mucho cada 30 segundos.
"""

import time
from dataclasses import dataclass
from typing import Any

import bm25s
import numpy as np
import Stemmer
from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings

from src.integrations.ingesta import CLAVE_VERSION
from src.integrations.recuperador import Fragmento
from src.integrations.segmentacion import SIN_FIN, SIN_INICIO

K_CANAL = 8
K_RRF = 60
TTL_VERSION_S = 30.0
COLECCIONES = ("normativa_ipu", "normativa_ica", "normativa_datos", "plataforma_general")


def filtro_de_vigencia(anio: int | None) -> dict[str, Any]:
    """Fragmentos que rigen en algún momento del año gravable; sin año, todos los que rigen alguna
    vez (un texto anterior sin vigencia conocida queda fuera siempre)."""
    if anio is None:
        return {"vigencia_hasta": {"$gt": SIN_INICIO}}
    return {
        "$and": [
            {"vigencia_desde": {"$lte": anio * 10000 + 1231}},
            {"vigencia_hasta": {"$gte": anio * 10000 + 101}},
        ]
    }


def rige_en(metadatos: dict[str, Any], anio: int | None) -> bool:
    desde = int(metadatos.get("vigencia_desde", SIN_INICIO))
    hasta = int(metadatos.get("vigencia_hasta", SIN_FIN))
    if anio is None:
        return hasta > SIN_INICIO
    return desde <= anio * 10000 + 1231 and hasta >= anio * 10000 + 101


def fusion_rrf(canales: list[list[str]], k: int = K_RRF) -> list[tuple[str, float]]:
    """Fusión por rango recíproco: cada id suma 1 / (k + rango) en cada canal (rango desde 1)."""
    puntajes: dict[str, float] = {}
    for canal in canales:
        for rango, id_ in enumerate(canal, 1):
            puntajes[id_] = puntajes.get(id_, 0.0) + 1.0 / (k + rango)
    return sorted(puntajes.items(), key=lambda par: (-par[1], par[0]))


def coseno(a: Any, b: Any) -> float:
    va, vb = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    return float(va @ vb / (np.linalg.norm(va) * np.linalg.norm(vb)))


def _tokenizar(textos: list[str], stemmer: Any) -> Any:
    return bm25s.tokenize(textos, stopwords="es", stemmer=stemmer, show_progress=False)


@dataclass
class _IndiceBM25:
    version: str | None
    ids: list[str]
    metadatos: list[dict[str, Any]]
    modelo: Any


class RecuperadorHibrido:
    """Implementa `Recuperador` sobre Chroma (con `langchain-chroma`) y BM25 por réplica."""

    def __init__(
        self,
        cliente: Any,  # cliente de Chroma, o una función sin argumentos que lo crea al primer uso
        embeddings: Embeddings,
        *,
        prefijo: str = "",
        ttl_version_s: float = TTL_VERSION_S,
    ) -> None:
        self._cliente_o_fabrica = cliente
        self._cliente_creado: Any = None
        self._embeddings = embeddings
        self._prefijo = prefijo
        self._ttl = ttl_version_s
        self._stemmer = Stemmer.Stemmer("spanish")
        self._tiendas: dict[str, Chroma] = {}
        self._bm25: dict[str, _IndiceBM25] = {}
        self._version: tuple[float, str | None] = (0.0, None)
        self.reconstrucciones = 0  # cuántas veces se construyó un índice BM25 (pruebas)

    # -- Versión del corpus y BM25 ---------------------------------------------------------------

    @property
    def _cliente(self) -> Any:
        if self._cliente_creado is None:
            fabrica = self._cliente_o_fabrica
            perezoso = callable(fabrica) and not hasattr(fabrica, "get_collection")
            self._cliente_creado = fabrica() if perezoso else fabrica
        return self._cliente_creado

    def _tienda(self, coleccion: str) -> Chroma:
        if coleccion not in self._tiendas:
            self._tiendas[coleccion] = Chroma(
                collection_name=f"{self._prefijo}{coleccion}",
                embedding_function=self._embeddings,
                client=self._cliente,
                create_collection_if_not_exists=False,
            )
        return self._tiendas[coleccion]

    @property
    def version_corpus(self) -> str | None:
        """Versión del corpus guardada en Chroma por la ingesta (con caché corta). Se lee de la
        primera colección que exista; todas guardan la misma."""
        leida, version = self._version
        if time.monotonic() - leida > self._ttl:
            version = None
            for nombre in COLECCIONES:
                try:
                    coleccion = self._cliente.get_collection(f"{self._prefijo}{nombre}")
                except Exception:  # noqa: S112 - esa colección no existe; se prueba la siguiente
                    continue
                version = (coleccion.metadata or {}).get(CLAVE_VERSION)
                break
            self._version = (time.monotonic(), version)
        return version

    def _indice(self, coleccion: str) -> _IndiceBM25:
        version = self.version_corpus
        indice = self._bm25.get(coleccion)
        if indice is None or indice.version != version:
            datos = self._tienda(coleccion).get(include=["documents", "metadatas"])
            modelo = bm25s.BM25()
            if datos["ids"]:
                modelo.index(_tokenizar(datos["documents"], self._stemmer), show_progress=False)
            indice = _IndiceBM25(version, datos["ids"], datos["metadatas"], modelo)
            self._bm25[coleccion] = indice
            self.reconstrucciones += 1
        return indice

    # -- Canales ---------------------------------------------------------------------------------

    def _canal_bm25(self, coleccion: str, consulta: str, anio: int | None) -> list[str]:
        indice = self._indice(coleccion)
        if not indice.ids:
            return []
        consulta_tokens = _tokenizar([consulta], self._stemmer)
        if not consulta_tokens.vocab:
            return []
        posiciones, puntajes = indice.modelo.retrieve(
            consulta_tokens, k=len(indice.ids), show_progress=False
        )
        elegidos = []
        for posicion, puntaje in zip(posiciones[0], puntajes[0], strict=True):
            if puntaje <= 0:
                break
            if rige_en(indice.metadatos[posicion], anio):
                elegidos.append(indice.ids[posicion])
                if len(elegidos) == K_CANAL:
                    break
        return elegidos

    def _canal_vectorial(self, coleccion: str, vector: list[float], anio: int | None) -> list[str]:
        resultados = self._tienda(coleccion).similarity_search_by_vector_with_relevance_scores(
            vector, k=K_CANAL, filter=filtro_de_vigencia(anio)
        )
        return [documento.id for documento, _ in resultados if documento.id]

    # -- Consulta --------------------------------------------------------------------------------

    def recuperar(
        self,
        consulta: str,
        *,
        coleccion: str | None = None,
        k: int = 5,
        anio: int | None = None,
    ) -> list[Fragmento]:
        """Los `k` fragmentos de la fusión, con el coseno de cada uno como similitud."""
        vector = self._embeddings.embed_query(consulta)
        fragmentos: list[Fragmento] = []
        for nombre in [coleccion] if coleccion else list(COLECCIONES):
            fusion = fusion_rrf(
                [
                    self._canal_vectorial(nombre, vector, anio),
                    self._canal_bm25(nombre, consulta, anio),
                ]
            )[:k]
            if not fusion:
                continue
            ids = [id_ for id_, _ in fusion]
            datos = self._tienda(nombre).get(
                ids=ids, include=["documents", "metadatas", "embeddings"]
            )
            por_id = {
                id_: (documento, metadatos, embedding)
                for id_, documento, metadatos, embedding in zip(
                    datos["ids"],
                    datos["documents"],
                    datos["metadatas"],
                    datos["embeddings"],
                    strict=True,
                )
            }
            for id_ in ids:
                documento, metadatos, embedding = por_id[id_]
                fragmentos.append(
                    Fragmento(
                        texto=documento,
                        fuente=str(metadatos.get("archivo", "")),
                        seccion=str(metadatos.get("articulo", "")),
                        similitud=coseno(vector, embedding),
                        norma=str(metadatos.get("norma", "")),
                        url=str(metadatos.get("url", "")),
                        id=id_,
                        vigencia_desde=int(metadatos.get("vigencia_desde", SIN_INICIO)),
                        vigencia_hasta=int(metadatos.get("vigencia_hasta", SIN_FIN)),
                    )
                )
        if not coleccion:  # varias colecciones: los de mayor similitud
            fragmentos.sort(key=lambda f: f.similitud, reverse=True)
        return fragmentos[:k]
