"""Cliente de embeddings de OpenAI: `text-embedding-3-large`, 3.072 dimensiones (sección 3.2)."""

from langchain_openai import OpenAIEmbeddings

from src.config import Settings

DIMENSIONES = 3072


def crear_embeddings(settings: Settings) -> OpenAIEmbeddings:
    """Cliente con la clave, el modelo y el tiempo máximo de la configuración y un reintento."""
    return OpenAIEmbeddings(
        model=settings.modelo_embeddings,
        dimensions=DIMENSIONES,
        api_key=settings.openai_api_key,
        timeout=settings.timeout_chroma_s,
        max_retries=1,
    )
