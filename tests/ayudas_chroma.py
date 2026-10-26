"""Ayudas de las pruebas que usan el Chroma de Compose: el cliente y qué hacer si no responde."""

import os

import pytest


def cliente_chroma_compose():
    """Cliente HTTP del Chroma de Compose (`CHROMA_HOST`/`CHROMA_PORT` o localhost:8000)."""
    import chromadb

    host = os.environ.get("CHROMA_HOST", "localhost")
    puerto = int(os.environ.get("CHROMA_PORT", "8000"))
    try:
        cliente = chromadb.HttpClient(host=host, port=puerto)
        cliente.heartbeat()
    except Exception as error:  # sin Chroma: se salta en local y falla en la CI
        mensaje = f"Chroma no responde ({type(error).__name__}): `docker compose up -d chromadb`."
        if os.environ.get("CHROMA_OBLIGATORIO") == "1":
            pytest.fail(mensaje, pytrace=False)
        pytest.skip(mensaje)
    return cliente
