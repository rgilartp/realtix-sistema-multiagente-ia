# ADR-04 · Recuperación híbrida con Chroma y BM25

**Estado:** aprobada, octubre de 2026. **Fuente:** sección 2 de la especificación técnica v6.

## Contexto

La búsqueda léxica es necesaria para recuperar identificadores literales («Ley 44 de 1990», «artículo 354»). Chroma autoalojado no tiene búsqueda léxica con ranking: la búsqueda híbrida de su Search API es solo de Chroma Cloud.

## Decisión

ChromaDB 1.5.9 (vectorial, con `langchain-chroma`) más BM25 (`bm25s` con PyStemmer y palabras vacías en español) en el backend. 8 fragmentos por canal, fusión por rango recíproco (RRF, k = 60) y los 5 mejores al prompt. Un fragmento por artículo.

## Alternativas

Chroma Cloud; solo búsqueda vectorial; un motor de búsqueda aparte.

## Consecuencias

Cortar por artículo permite citar el artículo exacto (RF-IPU-05 · Citación de la norma). Cada réplica reconstruye su índice BM25 al arrancar.

## Cambio en el documento de grado

Sección 7 de arquitectura (se precisa).
