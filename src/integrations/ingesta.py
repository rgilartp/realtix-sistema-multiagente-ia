"""Ingesta y reingesta idempotente de `knowledge_base/` en Chroma (sección 5.5 y RF-OBS-04).

Una colección de Chroma por dominio, con `langchain-chroma` y el índice HNSW por defecto. La
ingesta compara el id y el hash de cada fragmento con lo que ya hay: solo calcula los embeddings de
lo nuevo o cambiado y borra lo que ya no está, así que correrla dos veces no gasta nada la segunda.
Agregar o cambiar una norma es editar `knowledge_base/` y volver a correrla, sin tocar el código.
Guarda la versión del corpus en los metadatos de cada colección; con ella cada réplica sabe cuándo
reconstruir su índice BM25.
"""

from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings

from src.integrations.costos import costo_usd
from src.integrations.recuperador import RAIZ_BASE
from src.integrations.segmentacion import (
    FragmentoBase,
    contar_tokens,
    segmentar_base,
    version_del_corpus,
)

LOTE = 100  # fragmentos por pedido de embeddings (unos 80.000 tokens como máximo)
CLAVE_VERSION = "version_corpus"


@dataclass(frozen=True)
class ReporteColeccion:
    coleccion: str
    fragmentos: int
    embebidos: int  # nuevos o cambiados
    borrados: int
    tokens: int
    costo_usd: Decimal


def _lotes(elementos: Sequence[FragmentoBase], tamano: int) -> Iterator[Sequence[FragmentoBase]]:
    for i in range(0, len(elementos), tamano):
        yield elementos[i : i + tamano]


def ingestar(
    cliente: Any,
    embeddings: Embeddings,
    raiz: Path = RAIZ_BASE,
    *,
    prefijo: str = "",
    simular: bool = False,
    modelo: str = "text-embedding-3-large",
) -> list[ReporteColeccion]:
    """Sincroniza Chroma con la base; con `simular`, solo cuenta tokens y costo."""
    version = version_del_corpus(raiz)
    reportes = []
    for coleccion, fragmentos in segmentar_base(raiz).items():
        nombre = f"{prefijo}{coleccion}"
        tienda = Chroma(collection_name=nombre, embedding_function=embeddings, client=cliente)
        existentes = tienda.get(include=["metadatas"])
        hashes = {
            id_: (meta or {}).get("hash")
            for id_, meta in zip(existentes["ids"], existentes["metadatas"], strict=True)
        }
        actuales = {f.id for f in fragmentos}
        pendientes = [f for f in fragmentos if hashes.get(f.id) != f.metadatos["hash"]]
        sobrantes = [id_ for id_ in hashes if id_ not in actuales]
        tokens = sum(contar_tokens(f.texto) for f in pendientes)
        if not simular:
            if sobrantes:
                tienda.delete(ids=sobrantes)
            for lote in _lotes(pendientes, LOTE):
                tienda.add_texts(
                    [f.texto for f in lote],
                    metadatas=[f.metadatos for f in lote],
                    ids=[f.id for f in lote],
                )
            coleccion_chroma = cliente.get_collection(nombre)
            coleccion_chroma.modify(metadata={CLAVE_VERSION: version})
        reportes.append(
            ReporteColeccion(
                coleccion=coleccion,
                fragmentos=len(fragmentos),
                embebidos=len(pendientes),
                borrados=len(sobrantes),
                tokens=tokens,
                costo_usd=costo_usd(modelo, tokens),
            )
        )
    return reportes
