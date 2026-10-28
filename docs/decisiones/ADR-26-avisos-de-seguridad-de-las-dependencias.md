# ADR-26 · Avisos de seguridad de las dependencias

**Estado:** aceptada, octubre de 2026 (Rodolfo pidió revisar los avisos antes de la corrida 3, porque después el sistema queda congelado). **Fuente:** `pip-audit` sobre `uv.lock` (todos los grupos) y `npm audit` de `web/`. Complementa ADR-04, que no cambia: Chroma sigue en 1.5.9.

## Contexto

`npm audit` de `web/` no reporta nada. `pip-audit` reporta 7 avisos en 4 paquetes:

| Paquete | Aviso | Qué permite | Corregido en | ¿En la imagen del backend? |
|---|---|---|---|---|
| certifi 2026.7.22 | PYSEC-2026-4320 (GHSA-6q48-6c7w-9gw2) | El almacén de CA trae una raíz cuyas intermedias tienen llaves comprometidas: quien tenga una y esté en el camino puede suplantar un sitio por HTTPS | 2026.10.19 | Sí (lo usa httpx) |
| chromadb 1.5.9 | PYSEC-2026-311 (CVE-2026-45829) | Sin autenticación, ejecutar código en el servidor con un repositorio de modelo y `trust_remote_code` en el punto de acceso de las colecciones | Sin versión | Sí: el cliente; el servidor es la imagen `chromadb/chroma:1.5.9` |
| chromadb 1.5.9 | PYSEC-2026-3814 (CVE-2026-45833) | Lo mismo, para un usuario autenticado con permiso de actualizar colecciones | Sin versión | Igual |
| chromadb 1.5.9 | PYSEC-2026-3815 (CVE-2026-45831) | La autorización por roles no revisa a qué inquilino se aplica un permiso | Sin versión | Igual |
| chromadb 1.5.9 | PYSEC-2026-3813 (CVE-2026-45830) | Un usuario autenticado lee o cambia colecciones de otro inquilino | Sin versión | Igual |
| diskcache 5.6.3 | PYSEC-2026-2447 (CVE-2025-69872) | Quien pueda escribir en el directorio de la caché ejecuta código (usa `pickle`) | Sin versión | No |
| ragas 0.4.3 | PYSEC-2026-3046 (CVE-2026-6587) | Falsificación de peticiones desde el servidor en la utilidad de la métrica de fidelidad multimodal | Sin versión | No |

Comprobado en el servidor, en solo lectura y antes de este cambio:

- Desde afuera, el anfitrión escucha solo en los puertos 22, 80 y 443. Chroma publica `127.0.0.1:8000` y PostgreSQL `127.0.0.1:5432`, como pide la sección 3.11 («no se exponen fuera del host»).
- Caddy no enruta nada a Chroma: `/api/*` y `/health` van al backend, y lo demás, a los archivos de la web.
- La imagen del backend no trae ragas ni diskcache, porque `uv sync --frozen --no-dev` no instala el grupo `eval`. Sí trae chromadb 1.5.9 y certifi 2026.7.22.

## Decisión

1. **certifi sube a 2026.10.19**, la más reciente con al menos 7 días en PyPI (`exclude-newer` de `pyproject.toml`). No cambia ningún otro paquete.
2. **En el servidor, Chroma no publica su puerto** ni en el `127.0.0.1` del anfitrión. `deploy/compose.servidor.yml` lo quita (`ports: !reset []`) y `deploy/desplegar.sh` lo agrega con `-f`. Queda solo en la red de Compose, donde lo usa el backend. En el equipo se conserva, porque lo usan las pruebas y la ingesta locales.
3. **Riesgos aceptados, con su mitigación:**
   - **chromadb (4 avisos).** No hay versión corregida, y cambiar de base vectorial antes de la corrida 3 cambiaría ADR-04 y el sistema que se mide. Mitigación:
     - solo el anfitrión y los contenedores de Compose llegan a la API de Chroma: en el servidor no publica puerto y el proxy no la enruta;
     - el sistema no usa funciones de embeddings de Chroma ni modelos de Hugging Face: los vectores los calcula el backend con `text-embedding-3-large` de OpenAI, a través de LangChain;
     - hay un solo inquilino, el predeterminado, sin usuarios ni roles, así que los avisos de autorización no tienen a quién aplicarse.
   - **ragas y diskcache.** Solo están en el grupo `eval`, en el equipo de Rodolfo, para las corridas; no van en la imagen ni en el servidor. Mitigación:
     - de ragas se usan solo `Faithfulness`, `AnswerRelevancy`, `ContextPrecision` y `ContextRecall`; la función vulnerable es de la métrica multimodal, que no se usa;
     - los contextos que recibe ragas son del propio sistema, con datos sintéticos;
     - diskcache llega como dependencia de ragas, y el proyecto no activa la caché de ragas, así que no se usa.

## Consecuencias

- El despliegue con estos cambios va junto con la restauración del horario, antes de la corrida 2b, y nunca durante la usabilidad. Recrea el contenedor de Chroma; sus datos siguen en el volumen `chroma-data`.
- La corrida 2b confirma que la subida de certifi no cambia los resultados: solo cambia el almacén de CA.
- Los comandos de operación en el servidor llevan los dos `-f` (`deploy/README.md`).
- Después de la corrida 3 el sistema queda congelado. Los riesgos aceptados pasan al informe.
