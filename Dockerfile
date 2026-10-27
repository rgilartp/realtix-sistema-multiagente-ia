# Imagen del backend del sistema multiagente de IA (RNF-12 · Imágenes de contenedor; sección 3.7).
#
# Tres etapas (la de uv, la de construcción y la de ejecución). La de construcción instala las
# dependencias exactas de uv.lock (sin los grupos de desarrollo, curaduría ni evaluación) y descarga
# la codificación cl100k_base de tiktoken, que la segmentación necesita y que de otro modo se bajaría
# al primer uso; la de ejecución solo copia lo necesario y corre con un usuario sin privilegios. El .env nunca entra en la imagen (.dockerignore): los secretos
# llegan como variables de entorno desde Compose.

FROM ghcr.io/astral-sh/uv:0.13.5 AS uv

FROM python:3.12-slim AS construccion
COPY --from=uv /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/app/.venv \
    TIKTOKEN_CACHE_DIR=/app/.tiktoken
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
RUN /app/.venv/bin/python -c "import tiktoken; tiktoken.get_encoding('cl100k_base')"

FROM python:3.12-slim
ENV PATH=/app/.venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TIKTOKEN_CACHE_DIR=/app/.tiktoken
RUN useradd --create-home --uid 1000 --shell /usr/sbin/nologin realtix
WORKDIR /app
COPY --from=construccion /app/.venv /app/.venv
COPY --from=construccion /app/.tiktoken /app/.tiktoken
COPY pyproject.toml ./
COPY src/ src/
COPY scripts/ scripts/
COPY datos/ datos/
COPY knowledge_base/ knowledge_base/
# Punto de montaje del volumen de RealSit: un volumen nuevo hereda este dueño, así que el generador
# corre también sin privilegios.
RUN install -d -o realtix -g realtix /realsit
USER realtix
EXPOSE 8001
HEALTHCHECK --interval=15s --timeout=5s --start-period=60s --retries=3 \
    CMD ["python", "-c", "import sys, urllib.request; sys.exit(urllib.request.urlopen('http://127.0.0.1:8001/health', timeout=4).status != 200)"]
CMD ["uvicorn", "--factory", "src.api.app:crear_app", "--host", "0.0.0.0", "--port", "8001"]
