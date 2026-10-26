# Sistema multiagente de IA para Realtix

Trabajo de grado de Rodolfo Angel Gilart Pulido y Dayanna Liceth Varón Puerto.
Universidad Católica de Colombia, 2026. Director: MsC. Juan Carlos Barrero Calixto.

Sistema multiagente de IA para el soporte del proceso de facturación de Realtix: atiende consultas
del impuesto predial unificado (IPU) y de industria y comercio (ICA) de Bogotá D.C., con un
orquestador sobre LangGraph, agentes especializados con recuperación aumentada (RAG) y escalamiento
a un funcionario. Funciona solo con datos sintéticos.

La especificación técnica está en `docs/ESPECIFICACION_TECNICA.md`; las decisiones de arquitectura,
en `docs/decisiones/`.

## Instalar

Requisitos: WSL 2 con Ubuntu 24.04 (o Linux), [uv](https://docs.astral.sh/uv/), Docker Engine con
Compose y Git con firma de commits.

```bash
uv sync --all-groups                 # Python 3.12 y todas las dependencias
uv run pre-commit install            # ganchos pre-commit y commit-msg
cp .env.example .env                 # luego llene las claves (ver .env.example)
```

Los secretos propios (`OVT_HMAC_SECRET`, `TOKEN_FUNCIONARIO`, `TOKEN_ADMIN`) se generan con
`openssl rand -hex 32`. El archivo `.env` nunca se versiona.

## Ejecutar

```bash
docker compose up -d postgres chromadb
docker compose exec postgres pg_isready          # PostgreSQL listo
curl -s localhost:8000/api/v2/heartbeat          # Chroma listo
```

API (B9), en el puerto 8001 para no chocar con Chroma:

```bash
uv run uvicorn --factory src.api.app:crear_app --port 8001
curl -s localhost:8001/health
curl -s localhost:8001/api/v1/chat/mensaje -H 'Content-Type: application/json' \
  -d '{"id_conversacion": "prueba-1", "mensaje": "¿Qué es el predial?"}'
```

Recibos sintéticos para el agente OCR (B10), en `datos/recibos/`:

```bash
uv run python -m src.data.generar.recibos
```

Fuera del horario de atención (lunes a viernes no festivos, de 8:00 a. m. a 5:00 p. m.) la API
responde el aviso de horario. Los puntos de acceso están en `/docs`.

Web (B11: OVT simulada, widget y consola), con la API anterior corriendo en el puerto 8001:

```bash
cd web
npm ci
npm run dev                 # http://localhost:5173/ovt/ y /consola/
npm run build && npx playwright test   # pruebas con la API simulada en el navegador
npm run capturas            # capturas en 390 y 1280 px en docs/capturas/
```

La OVT simulada necesita `OVT_SIMULADA_ACTIVA=true` en la API.

## Probar

```bash
uv run pytest -q                                  # pruebas unitarias y de contrato
uv run pytest -q -m integration                   # integración (servicios de Compose)
uv run ruff check . && uv run ruff format --check .
uv run pre-commit run --all-files                 # ganchos, incluido gitleaks
uv run python scripts/trazabilidad.py             # matriz en reports/trazabilidad.md
```

La CI (GitHub Actions) ejecuta en cada PR los ganchos, gitleaks sobre todo el historial y pytest con
cobertura.

## Desplegar

El despliegue en AWS (EC2 con Docker Compose y Caddy con HTTPS automático) se documenta en
`deploy/README.md` en el bloque B13.

## Control de acceso

El sistema multiagente de IA solo entrega datos de un predio al contribuyente autenticado que es su
dueño, y el rechazo es el mismo para un predio ajeno y para uno inexistente. Tiene doble fundamento:

- la reserva de la información tributaria (Decreto Distrital 807 de 1993, art. 18);
- la Circular Externa 002 de 2024 de la SIC: un dato accesible al público (como la matrícula
  catastral) no es, por eso, un dato público.

## Antes de producción

El MVP usa solo datos sintéticos (RNF-04 · Uso exclusivo de datos sintéticos), así que nada de lo
siguiente aplica todavía. Antes de procesar datos reales hace falta:

1. **Estudio de impacto de privacidad** (Circular Externa 002 de 2024 de la SIC, instrucción II):
   descripción del tratamiento, evaluación de riesgos y medidas para mitigarlos.
2. **Contrato de transmisión** con los proveedores de modelos y de observabilidad (Anthropic,
   OpenAI y LangSmith), por ser encargados en el exterior (Decreto 1074 de 2015, arts.
   2.2.2.25.5.1 y 2.2.2.25.5.2). A OpenAI también llega el texto de la pregunta, porque la búsqueda
   vectorial la convierte en embedding.
3. **Revisión del Registro Nacional de Bases de Datos** (Decreto 1074 de 2015, cap. 26): evaluar si
   las bases de conversaciones y casos escalados deben inscribirse.
