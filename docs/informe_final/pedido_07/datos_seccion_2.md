# Datos para la sección 2 (pedido 07)

Solo datos leídos del repositorio o medidos en él, cada uno con su archivo de origen. El código del
sistema es el evaluado en la corrida 3 (`d3dab00`; `main` no lo cambió después, ADR-27). Sin
dominio, IP ni secretos.

## 1. Versiones exactas

| Componente | Versión | Origen |
|---|---|---|
| Python | 3.12 (`requires-python = "==3.12.*"`); CPython 3.12.15 en el equipo de desarrollo; imagen `python:3.12-slim` en el servidor | `pyproject.toml`, `.python-version`, `uv run python -V`, `Dockerfile` |
| LangGraph | 1.2.16 | `uv.lock` |
| LangChain | `langchain-core` 1.6.12 (el que usa el sistema); `langchain` 1.4.6 solo como dependencia de RAGAS | `uv.lock` |
| langchain-anthropic | 1.7.6 (con `anthropic` 1.15.0) | `uv.lock` |
| langchain-openai / langchain-chroma | 1.7.2 / 1.1.0 | `uv.lock` |
| FastAPI | 0.143.3 (con `uvicorn` 0.54.0) | `uv.lock` |
| Chroma, servidor | imagen `chromadb/chroma:1.5.9` | `docker-compose.yml` |
| Chroma, cliente | `chromadb` 1.5.9 | `uv.lock` |
| psycopg | 3.3.6 (`psycopg[binary]`) | `uv.lock` |
| SQLAlchemy | 2.1.5 | `uv.lock` |
| RAGAS | 0.4.3 | `uv.lock` |
| PostgreSQL | imagen `postgres:16` | `docker-compose.yml` |
| React | 19.3.1 | `web/package-lock.json` |
| Vite | 8.3.4 | `web/package-lock.json` |
| Tailwind CSS | 4.3.3 (`tailwindcss` y `@tailwindcss/vite`) | `web/package-lock.json` |
| Playwright | 1.64.1 (`@playwright/test`) | `web/package-lock.json` |
| Caddy | imagen `caddy:2.11` (la web se compila con `node:24-slim`) | `deploy/Dockerfile.proxy` |

## 2. Modelos y precios

| Función | Modelo | Entrada / salida (US$ por millón de tokens) | Origen |
|---|---|---|---|
| Orquestador | `claude-sonnet-5-5` | 2 / 10 | `src/config.py`, `src/integrations/costos.py` |
| Agentes IPU, ICA y general | `claude-haiku-5-5` | 0,10 / 0,50 (prompts de hasta 100.000 tokens; 0,50 / 2,50 por encima; los del sistema no pasan de unos 25.000) | ídem |
| OCR (lectura del recibo) | `claude-haiku-5-5` | ídem | ídem |
| Embeddings (corpus, consultas y relevancia de RAGAS) | `text-embedding-3-large` | 0,13 / no aplica | ídem y `src/evaluacion/ragas_eval.py` |
| Juez | `claude-opus-5-5` (juez v3, huella `afecd5c1…`) | 4 / 20 | `src/config.py`, `src/integrations/costos.py`, `reports/corrida-3/metricas.json` |
| Evaluador de RAGAS | `gpt-4.1-mini` | 0,40 / 1,60 | `src/evaluacion/ragas_eval.py`, `src/integrations/costos.py` |

Páginas oficiales de precios, consultadas en octubre de 2026 (`src/integrations/costos.py`):

- Anthropic: https://platform.claude.com/docs/en/about-claude/pricing
- OpenAI: https://developers.openai.com/api/docs/pricing

Parámetros de los modelos (`src/integrations/modelos.py`): sin `temperature`, `top_p` ni `top_k`;
el orquestador razona entre herramientas con esfuerzo bajo; los agentes y el OCR, sin razonamiento
extendido y con esfuerzo medio; el juez, con esfuerzo medio.

## 3. Base sintética (RealSit simulado)

Consultada en solo lectura (`sqlite3`, `mode=ro`) sobre `datos/realsit_sintetico.db` del equipo de
desarrollo. Su huella SHA-256 (`4479d036…`) es la registrada en `src/data/huella_realsit.sha256` y
la del servidor antes y después de la corrida 3 (`reports/no_funcionales/huella_realsit.txt`), así
que los conteos son los del sistema evaluado.

| Dato | Valor |
|---|---|
| Semilla | 42; 500 predios; fecha de referencia: primer día hábil de octubre de 2026 (`src/data/generar/generate_synthetic_data.py`) |
| Contribuyentes | 420 (272 personas naturales y 148 jurídicas) |
| Contribuyentes con ICA | 201, con su CIIU: 94 del régimen común anual, 79 del común bimestral y 28 del preferencial |
| Predios | 500, todos en Bogotá D.C. |
| Vigencias | 2023, 2024, 2025 y 2026 (avalúo de cada predio en las cuatro: 2.000 filas) |
| Obligaciones | 2.804: 2.000 de IPU (500 predios × 4 vigencias) y 804 de ICA (201 × 4) |
| Pagos | 2.676 (PSE 893, ventanilla 907 y corresponsal bancario 876) |
| Tarifas del ICA | 486 actividades |

Obligaciones por estado de pago:

| Estado | IPU | ICA |
|---|---|---|
| Al día | 1.729 | 575 |
| Pendiente | 75 | 186 |
| Vencido | 192 | 43 |
| No obligado | 4 | 0 |
| **Total** | **2.000** | **804** |

Además, 75 obligaciones de IPU están en el SPAC (pago por cuotas), y las de ICA son 488 anuales y
316 bimestrales.

## 4. Parámetros finales

| Parámetro | Valor | Origen |
|---|---|---|
| Fragmentos | Uno por artículo; los de más de 800 tokens se parten con 75 de solape (codificación `cl100k_base`); las tablas repiten su encabezado | `src/integrations/segmentacion.py` |
| Corpus de la corrida 3 | 1.149 fragmentos: 73, 562, 491 y 23 por colección (datos, ICA, IPU y plataforma general) | `reports/no_funcionales/volumenes.json`; detalle por documento en `base_conocimiento.csv` |
| k por canal | 8 (vectorial y BM25) | `src/integrations/recuperacion_hibrida.py` (`K_CANAL`) |
| k del RRF | 60 | ídem (`K_RRF`) |
| Fragmentos al prompt | 5 | ídem y `src/agents/agente.py` |
| BM25 | `bm25s` 0.3.13, con las palabras vacías del español de `bm25s` y el lematizador Snowball del español de `PyStemmer` 3.1.0 | `src/integrations/recuperacion_hibrida.py`, `uv.lock` |
| Pesos de la confianza | 0,4 similitud, 0,4 suficiencia y 0,2 cobertura (suficiencia: completa 1, parcial 0,5 y no pudo 0) | `src/config.py`, `deploy/servidor.env`, `src/services/confianza.py` |
| Escala de la similitud | Coseno 0,40 vale 0 y coseno 0,68 vale 1 | `src/integrations/recuperador.py` (`ESCALA_SIMILITUD`) |
| Umbral de la confianza | 0,7 | `src/config.py`, `deploy/servidor.env` |
| Tope de reclasificaciones | 2 | `src/config.py` (`max_reclasificaciones`) |
| Tiempos máximos | Modelos, 20 s; embeddings y Chroma, 5 s; adaptador de RealSit, 5 s; juez, 120 s | `src/config.py`, `src/evaluacion/juez.py` |
| Reintentos | Uno ante una falla transitoria (`con_tiempo_y_reintento`); los clientes de Anthropic y de OpenAI, además, con `max_retries=1` | `src/integrations/robustez.py`, `src/integrations/modelos.py`, `src/integrations/embeddings.py` |
| Tamaño máximo del archivo | 5 MB en la API; Caddy corta el cuerpo a 6 MB en `/api/v1/chat/documento` y a 64 KB en el resto de `/api`; el widget reduce las fotos a un lado largo de 2.000 px en JPEG antes de subirlas | `src/config.py`, `src/api/chat.py`, `docs/resumenes/b13.md`, `web/src/widget/fotos.js` |
| Límite de píxeles | 25.000.000 por imagen (`Image.MAX_IMAGE_PIXELS`); al modelo va a 1.000 × 2.000 px como máximo y a 3,5 MB en PNG; el PDF, a 150 ppp y 2.500 px por lado como máximo; lado corto mínimo de 800 px para no marcarla como de baja resolución | `src/agents/vision.py`, `src/services/documentos.py` |
| Mensaje | 2.000 caracteres como máximo | `src/api/esquemas.py` |
| Límite de peticiones | 10 por minuto y 200 por día por IP (chat, documento y escalamiento) | `src/config.py`, `src/api/chat.py`, `src/api/escalamiento.py` |
| Horario | Lunes a viernes no festivos, de 8:00 (incluida) a 17:00 (excluida), hora de Bogotá (`America/Bogota`) | `src/config.py`, `src/services/horario.py` |
| Festivos | Los de Colombia de la biblioteca `holidays` 0.106, con los trasladados por la Ley Emiliani | `src/services/horario.py`, `pyproject.toml` |

## 5. Decisiones D5 y D6

- **D5 (ADR-11, registro de las decisiones de enrutamiento):** un registro propio en PostgreSQL, la
  tabla `interaccion`, con una fila por turno y sin el texto de los mensajes ni datos personales:
  categoría, nivel de confianza, si escaló, estado, motivo, agentes invocados, tiempos por nodo,
  tokens por modelo, modelo por nodo y duración. `/api/v1/admin/metricas` se calcula de ese
  registro, y LangSmith guarda las trazas (el plan gratuito, 14 días). Si el registro falla, el
  turno sigue (`src/store/tablas.py`, `src/api/turno.py`, `docs/decisiones/ADR-11-registro-de-interacciones.md`).
- **D6 (ADR-12, mensajes nuevos en una conversación escalada):** los agentes ya no responden. Cada
  mensaje nuevo se guarda en el caso, a cualquier hora. Dentro del horario, la API contesta con
  `interlocutor: "sistema"` y el aviso «Tu caso ya está registrado para un funcionario. Guardé tu
  mensaje en el caso para que lo vea.»; fuera de él, con el aviso de fuera de horario
  (`src/api/turno.py`, `docs/decisiones/ADR-12-modo-humano.md`).

## 6. Escalamiento y aviso de IA

Flujo del escalamiento:

1. Escala el grafo, por uno de seis motivos: confianza insuficiente, sin cobertura, solicitud
   explícita, fuera de alcance, fallo de servicio o tope de reclasificaciones
   (`src/agents/state.py`). El botón «Hablar con un funcionario» llama a
   `POST /api/v1/escalamiento`, que marca la solicitud explícita y ejecuta el grafo, sin registrar
   el caso por su cuenta (ADR-18).
2. `nodo_escalamiento`, sin modelo, es el único que registra casos: arma el resumen en texto y en
   JSON (`src/services/resumen.py`) y lo guarda en la tabla `caso_escalado` del almacén, que deja
   la conversación como escalada (`src/store/almacen.py`). Si la parte que escala no tiene
   confianza calculada, guarda 0,0 con su motivo (ADR-13).
3. El contribuyente recibe el aviso de transferencia con el número del caso
   (`AVISO_TRANSFERENCIA`, `src/agents/nodes/escalamiento.py`). Si una falla inesperada interrumpe
   el turno, se intenta registrar el caso con «fallo de servicio» y nunca se muestra un error
   técnico (`src/api/turno.py`).
4. La consola muestra la bandeja de solo lectura con el token de funcionario
   (`GET /api/v1/escalamiento/casos` y `/casos/{id_caso}`): lista con filtros y el detalle con el
   resumen, el resumen estructurado y la conversación.
5. Los mensajes nuevos del contribuyente quedan en la tabla `mensaje_funcionario` (D6). El widget
   consulta los mensajes cada 5 s (`GET /api/v1/chat/{id}/mensajes`, `web/src/widget/Widget.jsx`).
   La respuesta del funcionario desde la consola no está construida (sección 3.6 de la
   especificación, opcional).

Aviso de IA (RF-SYS-06 · Aviso de interacción con IA):

- La API manda el aviso en el campo `aviso_ia` de la primera respuesta de cada conversación, también
  si esa respuesta es el aviso de fuera de horario o el rechazo de un recibo: «Te atiende un
  asistente de inteligencia artificial. Sus respuestas son orientativas y puedes pedir que te
  atienda un funcionario en cualquier momento» (`src/api/esquemas.py`, `src/api/turno.py`). El
  texto de la respuesta no tiene que repetirlo (`docs/cambios_para_documento.md`, fila 1.5.2.8.3).
- El widget lo muestra al abrir, antes de cualquier respuesta, en el recuadro «Antes de empezar», y
  debajo el aviso de datos personales (Ley 1581 de 2012). La cabecera dice quién atiende: «Te
  atiende un asistente de IA», «Tu caso está con un funcionario» o «Te atiende un funcionario»
  (`web/src/widget/Widget.jsx`).

## 7. Despliegue

| Dato | Valor | Origen |
|---|---|---|
| Servicio | Amazon EC2, en una cuenta nueva de AWS con el plan Free | ADR-10, `deploy/README.md` |
| Instancia | m7i-flex.large (2 vCPU y 8 GiB), Ubuntu 24.04 | ídem |
| Región | us-east-1 | ídem |
| Nombre y TLS | Subdominio gratuito de DuckDNS; Caddy con HTTPS automático de Let's Encrypt, HTTP redirige con 308, HSTS sin `preload` y CSP sin scripts en línea | ADR-09, `deploy/Caddyfile`, `docs/resumenes/b13.md` |
| Contenedores | `proxy` (Caddy con la web), `backend` (FastAPI con el grafo), `postgres` y `chromadb`; `generar-realsit` solo para crear la base sintética | `docker-compose.yml` |
| Imágenes | Backend multietapa (`uv` 0.13.5 y `python:3.12-slim`, usuario sin privilegios, sin `.env`, 1,09 GB); proxy (`node:24-slim` para compilar la web y `caddy:2.11`, 94 MB); `postgres:16`; `chromadb/chroma:1.5.9` | `Dockerfile`, `deploy/Dockerfile.proxy`, `docs/resumenes/b13.md` |
| Red | Compose publica 80 y 443 (el proxy); PostgreSQL queda ligado a `127.0.0.1` y Chroma, sin puerto publicado en el servidor; desde fuera, 5432 y 8000 cerrados | `docker-compose.yml`, `deploy/compose.servidor.yml`, ADR-26, `docs/resumenes/b13.md` |
| Volúmenes | `postgres-data`, `chroma-data`, `caddy-data`, `caddy-config` y `datos-sinteticos` (en solo lectura en el backend) | `docker-compose.yml` |

Prueba de humo del despliegue de B13 (`docs/resumenes/b13.md`, «Cómo se verificó»):

- en el servidor: huella de RealSit igual a la registrada, ingesta de 1.148 fragmentos (404.639
  tokens) y `/health` en verde por HTTPS;
- desde fuera: certificado de Let's Encrypt, cabeceras de seguridad y CSP de cada página, puertos
  5432 y 8000 cerrados, y el modo de evaluación apagado (la API ignoró el reloj simulado);
- en el navegador (Playwright contra el servidor): la OVT simulada y la consola cargaron sin errores
  de CSP ni de JavaScript, y el widget apareció dentro de la OVT simulada;
- en local: los cuatro contenedores sanos, la imagen sin `.env` ni bases `.db`, y los límites de
  tamaño (413) con su mensaje.

## 8. Repositorio

Estructura (archivos versionados por carpeta, `git ls-files`):

| Carpeta | Archivos | Contenido |
|---|---|---|
| `src/` | 117 | Agentes y grafo, servicios, datos, almacén, integraciones, API y evaluación |
| `tests/` | 120 | Pruebas, 60 escenarios del sistema, conjuntos adicionales (R1, R3 y R4) y componentes |
| `knowledge_base/` | 38 | 32 documentos en cuatro colecciones, sus `fuentes.yaml` y `vigencias.yaml` |
| `datos/` | 9 | Tarifas, calendario y regímenes por año gravable |
| `scripts/` | 35 | Curaduría, ingesta, evaluación, trazabilidad y utilidades |
| `web/` | 29 | OVT simulada, widget y consola |
| `deploy/` | 8 | Caddyfile, guía y scripts de despliegue |
| `docs/` | 180 | Especificación, adenda, ADR, resúmenes, informe (con este paquete) y capturas |
| `reports/` | 476 | Resultados de las corridas y de las verificaciones |

Pruebas por tipo (`pytest.txt`):

| Tipo | Número |
|---|---|
| Pytest, unitarias (`unit`) | 758 |
| Pytest, de integración (`integration`) | 14 |
| Pytest, sin marca | 1 |
| Pytest en total | 773 (763 superadas y 10 omitidas: 3 con modelos reales, 6 con embeddings reales y 1 con un PDF que no se versiona) |
| Playwright | 31 (27 superadas y 4 omitidas, las de las capturas reales) |
| Escenarios del nivel de sistema | 60, más 10 variantes (R1), 3 cadenas (R3) y 2 de seguridad (R4) |
| Componentes | 100 consultas de enrutamiento y 34 casos de agentes contra su nodo |

Cobertura de sentencias (medida en la integración continua de `main`, con `--cov=src --cov=scripts`):
81 % en total; 92,4 % en `src/` y 41,3 % en `scripts/` (`pytest.txt`).

Integración continua (`.github/workflows/`):

- `ci.yml`, en cada PR y en cada push a `main`:
  - **Ganchos, secretos y pruebas:** los ganchos de pre-commit en todos los archivos (ruff y su
    formato, YAML, TOML, espacios y fin de línea, archivos grandes y gitleaks), gitleaks sobre todo
    el historial y pytest con cobertura, con PostgreSQL 16 y Chroma 1.5.9 como servicios;
  - **Web (compilación y Playwright):** contraste WCAG de los dos modos, compilación con Vite y
    las pruebas de Playwright en Chromium contra la API simulada.
- `monitor.yml`: `/health` por HTTPS cada 15 minutos en el horario hábil. GitHub registra 7
  ejecuciones (`gh run list --workflow monitor.yml`): 1 manual, antes de B15, y 6 programadas, 1 de
  ellas fallida, todas después de empezar B15. GitHub no lanzó las demás ejecuciones programadas.
  Por eso la disponibilidad se calculó con el monitor del servidor
  (`reports/no_funcionales/disponibilidad.md`). El reporte (secciones 6 y 12) y los capítulos 4 y 5
  dicen que el monitor de GitHub Actions «nunca corrió»: antes de B15 es cierto, pero después
  corrió esas 6 veces; ese texto no se cambió en este paquete.

El repositorio es **privado** en GitHub (`gh repo view`).
