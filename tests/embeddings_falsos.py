"""Embeddings falsos y deterministas, para probar la ingesta y la recuperación sin red.

Cada palabra (en minúsculas, sin tildes, de 3 letras o más) suma 1 en una de 512 dimensiones elegida
por su hash; el vector se normaliza. Dos textos con palabras en común tienen un coseno alto. Cuenta
cuántos textos embebe, para verificar que la reingesta no recalcula nada.
"""

import hashlib
import math
import re
import unicodedata

from langchain_core.embeddings import Embeddings

DIMENSIONES = 512
PALABRA = re.compile(r"[a-z0-9]{3,}")


def _palabras(texto: str) -> list[str]:
    sin_tildes = unicodedata.normalize("NFD", texto.lower())
    return PALABRA.findall("".join(c for c in sin_tildes if unicodedata.category(c) != "Mn"))


class EmbeddingsFalsos(Embeddings):
    def __init__(self) -> None:
        self.textos_embebidos = 0
        self.consultas = 0

    def _vector(self, texto: str) -> list[float]:
        vector = [0.0] * DIMENSIONES
        for palabra in _palabras(texto):
            vector[int(hashlib.md5(palabra.encode()).hexdigest(), 16) % DIMENSIONES] += 1.0
        norma = math.sqrt(sum(x * x for x in vector)) or 1.0
        return [x / norma for x in vector]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        self.textos_embebidos += len(texts)
        return [self._vector(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        self.consultas += 1
        return self._vector(text)
