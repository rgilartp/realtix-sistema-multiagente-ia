# Auditoría de seguridad

Revisión de seguridad del sistema multiagente de IA antes de la corrida final, y lo que se hizo con
lo que encontró. El informe completo queda fuera del repositorio, con los autores.

## Alcance

- **Pasada rápida y estática** (perfil `quick`): 12 invocaciones de agentes (4 de reconocimiento,
  3 cazadores, 1 crítico final y 4 verificadores independientes), sobre el commit `f5954f6` de
  `main`.
- **Qué se revisó:** `src/`, `web/`, `deploy/`, `scripts/`, `docker-compose.yml`, la CI y las
  dependencias. Quedaron fuera, por decisión de los autores, `docs/`, `knowledge_base/`, `datos/`,
  `reports/` y `tests/` (las pruebas solo se leyeron para entender el código).
- **Sin ejecutar ataques:** no se ejecutó código del proyecto, no se usó la red ni el sistema
  desplegado, no se gastó API de modelos y no se leyó ningún `.env`. Por eso ninguna pista tiene una
  reproducción observada.
- Es una pasada parcial, no una garantía de ausencia de fallas.

## Resultado

- **0 hallazgos confirmados.**
- **4 pistas** que necesitaban validación (un hecho del despliegue o una medición local).
- **23 notas de refuerzo**, sin un afectado demostrable.
- **Patrones positivos:** una sola regla de propiedad de predios (`verificar_predio_propio`) en todas
  las rutas revisadas; el contribuyente sale siempre de la sesión y nunca de los argumentos del
  modelo; la firma HMAC se verifica antes de leer la carga; el modo de evaluación queda apagado por
  configuración; Caddy solo publica `/api/*` y `/health`; el front no tiene sumideros de HTML; SQL
  parametrizado y RealSit en solo lectura; `uv.lock` con hashes y CI con permisos de solo lectura.

## Qué se hizo con cada pista

Las validó una revisión externa contra el código; se corrigieron en el PR `fix/seguridad-auditoria`.

1. **Imágenes enormes** (`POST /api/v1/chat/documento` → `src/agents/vision.py`). Un PNG de pocos KB
   puede declarar miles de millones de píxeles y ocupar cientos de MB al abrirse.
   - **Corregida:** `abrir_documento` lee el tamaño del encabezado, sin decodificar, y rechaza las
     imágenes de más de 25 millones de píxeles (unos 5.000 × 5.000, muy por encima de un recibo
     escaneado); `Image.MAX_IMAGE_PIXELS` queda con el mismo límite. El nodo OCR convierte ese error
     en el rechazo de documento ilegible, sin llamar al modelo y sin error técnico.
   - **Pruebas:** con el límite bajado en la prueba, la imagen se rechaza sin decodificarse y una
     justo en el límite se abre; por la API, el rechazo es «no se pueden leer los datos del recibo»,
     con estado 200 y sin llamadas al modelo.
   - `mem_limit` en Compose queda como refuerzo futuro.
2. **Botón de escalamiento sin límite por IP** (`POST /api/v1/escalamiento`). Registra un caso por
   conversación: sin límite, cualquiera podía llenar la bandeja con ids distintos.
   - **Corregida:** el botón lleva el mismo límite por IP que el chat y el documento (10 por minuto y
     200 por día); el docstring de `src/api/limite.py` lo dice.
   - **Pruebas:** la tercera petición con un límite de 2 recibe 429 con el mensaje y `Retry-After`; con
     el modo de evaluación y `X-Escenario-Id`, no cuenta.
   - **Riesgo aceptado:** el botón comparte la cuenta diaria (200) con el chat, así que quien la agote
     no puede pedir un funcionario por el botón hasta el día siguiente, aunque el aviso de IA dice «en
     cualquier momento». El widget muestra el mensaje del 429.
3. **`X-Escenario-Id` en el modo de evaluación** quita el límite por IP.
   - **Riesgo aceptado**, ya documentado en `src/api/limite.py`: el modo de evaluación solo se
     enciende durante una corrida (A9), y al terminar se despliega sin él y se comprueba desde afuera.
     Mientras está encendido, cualquiera podría usar esa cabecera, igual que ya puede usar
     `X-Reloj-Simulado` o `X-Falla-Inyectada`. Un secreto para el modo de evaluación queda como
     refuerzo futuro.
4. **Trazas de LangSmith con la imagen del recibo y los nombres declarados** (`src/integrations/trazas.py`).
   - **Era la causa** de que las trazas del incidente de datos reales de la usabilidad
     (`docs/resumenes/b15.md`, punto 9) guardaran la imagen: el anonimizador de las trazas no
     enmascaraba imágenes ni los nombres que el usuario escribe («me llamo…»). La prueba sin red de
     abajo lo muestra con el anonimizador anterior.
   - **Corregida:** `AnonimizadorDeTrazas`, solo para LangSmith, cambia por «[IMAGEN]» las cadenas que
     son imágenes (las que empiezan por `data:image/` y las cadenas en base64 de 1.000 caracteres o
     más, también con espacios delante) y enmascara los nombres declarados, después de los documentos
     (así «soy CC-…» no deja la cifra a la vista). Una imagen en base64 de menos de 1.000 caracteres
     (unos 750 bytes) o metida dentro de un texto más largo no se reconoce; el recibo pesa decenas de
     KB y va en su propio bloque. Es una subclase: `Anonimizador`, que usan el juez, el
     clasificador y los agentes (`para_modelos=True`), no cambia, y la huella del juez sigue siendo
     la misma (`afecd5c1…`), porque incluye el código de esa clase.
   - **Pruebas sin red** (`tests/test_trazas_langsmith.py`), con las peticiones HTTP del cliente de
     `langsmith` instalado interceptadas:
     - la carga real (multipart: entradas, salidas, eventos y extras; no hay adjuntos aparte) lleva
       «[IMAGEN]» y «[NOMBRE]», y no lleva la imagen en base64 ni el nombre; con el anonimizador
       anterior sí los llevaba;
     - con `LANGSMITH_TRACING` encendido en el entorno (como lo pasa Compose al contenedor), un grafo
       que recibe el trazador del sistema no suma el trazador por defecto de LangChain, tampoco en el
       hilo de `con_tiempo_y_reintento`: LangChain solo hace copias del trazador del sistema, con el
       mismo cliente anonimizado. Sin el trazador del sistema, sí crearía uno sin anonimizador (se
       comprobó a mano): la protección depende de que toda llamada a un modelo pase por el grafo.

## Áreas que la auditoría no revisó

El perfil rápido dejó cuatro áreas sin revisar. Una revisión externa las cubrió así:

- **Las marcas del clasificador** (`solicitud_explicita`, `consulta_personal` y las demás) cambian la
  ruta del turno, pero no dan acceso a datos: el código exige la sesión y la propiedad del predio
  (`verificar_predio_propio`), y un adjunto sin sesión siempre pide iniciarla.
- **`/health`** es síncrono y queda acotado por el pool de hilos del servidor. Cada sonda con tiempo
  máximo (`con_tiempo_y_reintento`) puede dejar un hilo atrasado vivo (`shutdown(wait=False)`); queda
  como refuerzo futuro, con las notas de disponibilidad.
- **La curaduría** (`scripts/curaduria/convertir.py` y los demás) **y el evaluador**
  (`src/evaluacion/`, `scripts/evaluar.py`) son herramientas locales de los autores, fuera del
  sistema publicado.

## Notas de refuerzo (23)

### Aplicadas (4)

En el PR `chore/refuerzos-auditoria`. Motivo: no tocan el sistema desplegado ni el instrumento de
medición.

| # | Nota | Qué se hizo |
|---|---|---|
| 1 | Las acciones de la CI van por etiqueta | Fijadas por SHA de commit, con la versión en un comentario |
| 2 | El binario de gitleaks se verifica con el `checksums.txt` del mismo release | Se verifica contra un SHA-256 fijado en el repositorio |
| 4 | `deploy/preparar_servidor.sh` da de alta la clave GPG de Docker sin verificar su huella | Verifica la huella publicada antes de darla de alta (no se ejecutó: el servidor ya está preparado) |
| 5 | URL `http://` de secretariasenado.gov.co en `scripts/curaduria/fuentes.yaml` | Pasan a `https://` las que responden por https (comprobado con HEAD); sin descargar ni convertir nada |

### Verificadas (3)

Se comprobó que no hay un afectado en el sistema tal como está.

| # | Nota | Verificación |
|---|---|---|
| 14 | La IP del límite es la última de `X-Forwarded-For` | Correcto con Caddy directo, que es el despliegue (`tests/test_despliegue.py` exige que Caddy no confíe en proxies; `tests/test_limite.py` prueba la IP). Un balanceador delante o IPv6 no aplican hoy |
| 21 | Compose pasa `LANGSMITH_*` al contenedor | Prueba local sin red: con el trazador del sistema, LangChain no agrega el suyo sin anonimizador, tampoco en los hilos (pista 4) |
| 23 | `rechazo_previo` es un prefiltro por regex | La garantía es `verificar_predio_propio` en el adaptador, con pruebas de regresión de predio ajeno e inexistente en las herramientas, el OCR y la API |

### Trabajo futuro (16)

| Grupo | # | Nota | Motivo |
|---|---|---|---|
| CI y cadena de suministro | 3 | `deploy/desplegar.sh` no verifica la firma de la etiqueta | Cambia el despliegue justo antes de la corrida final |
| CI y cadena de suministro | 6 | Imágenes de Docker por etiqueta, sin digest | Cambia las imágenes del despliegue justo antes de la corrida final |
| Contenedores | 7 | Sin `cap_drop`, `no-new-privileges` ni `read_only` | Cambia el despliegue justo antes de la corrida final; va con `mem_limit` (pista 1) |
| Contenedores | 19 | El servicio `generar-realsit` recibe todos los secretos | Cambia Compose; es una herramienta de los autores, no del sistema publicado |
| Tokens y secretos | 13 | Sin longitud mínima ni tope de intentos para los tokens de rol | Exige cambiar secretos del servidor |
| Tokens y secretos | 20 | Sin validar que `OVT_HMAC_SECRET` y los dos tokens sean largos y distintos | Exige cambiar secretos del servidor |
| Tokens y secretos | 22 | `POSTGRES_PASSWORD` con valor por defecto en Compose | Exige cambiar secretos del servidor (Postgres solo escucha en el host y en la red de Compose) |
| Tokens y secretos | — | Un secreto para el modo de evaluación (pista 3) | Exige un secreto nuevo en el servidor y en el evaluador |
| Diseño de la OVT simulada | 16 | Tokens de sesión sin credencial, sin revocación, `aud` ni `jti` | Es el diseño de la OVT simulada, con usuarios sintéticos |
| Disponibilidad de `/health` | 8 | `/health` publica la versión y el estado de cada dependencia | Cambia el código medido justo antes de la corrida final (el monitor solo necesita el estado) |
| Disponibilidad del documento | 11 | La conversión de un PDF no tiene tiempo máximo | Cambia el código medido justo antes de la corrida final |
| Código medido | 9 | Primera petición de una conversación sin atomicidad (comprobar y luego crear) | Cambia el código medido justo antes de la corrida final; la ventana es mínima con ids aleatorios |
| Código medido | 10 | `GET /mensajes` distingue 404 de 403 | Cambia el código medido justo antes de la corrida final; inocuo con ids aleatorios |
| Código medido | 12 | Una herramienta devuelve el texto del error al modelo | Cambia el código medido justo antes de la corrida final; el texto solo trae los argumentos del turno |
| Código medido | 17 | El anonimizador para modelos deja pasar una cifra de 9 o 10 dígitos después de «valor» o «base» | Cambia `Anonimizador` y con él la huella del juez (habría que repetir la calibración) |
| Datos y retención | 15, 18 | Listas sin paginar; texto del usuario en el checkpoint y en los mensajes del caso, sin purga | Solo aplican a un paso a producción con datos reales |

Además, como en la pista 1, queda como refuerzo futuro `mem_limit` para el backend.
