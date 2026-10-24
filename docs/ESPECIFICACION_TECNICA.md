# Especificación técnica v6 — sistema multiagente de IA para Realtix

> **Versión:** v6, octubre de 2026 · **De:** chat de desarrollo (proyecto TG2) · **Para:** Claude Code,
> que desarrolla, y el equipo, que la consulta.
>
> **Reemplaza** a todos los planes de desarrollo anteriores. Rige junto con la adenda 06 del chat de
> documentos.
>
> **Precedencia, cuando dos fuentes no coinciden:**
> 1. la adenda 06 (`docs/06_ADENDA_MARCO_JURIDICO_Y_PRUEBAS.md`), en lo normativo, en la base de
>    conocimiento y en lo que el documento de grado promete medir;
> 2. esta especificación;
> 3. los documentos FINAL de requerimientos y arquitectura (`docs/paquete/documentos/`), salvo lo
>    que esta especificación cambia de forma explícita (sección 2);
> 4. el resto del paquete que está en `docs/paquete/` (contexto, revisión y hallazgos, comparación,
>    figuras y código de 6.3.1), solo como referencia.
>
> **Equipo:**
> - Rodolfo Angel Gilart Pulido: único operador; dirige a Claude Code.
> - Dayanna Liceth Varón Puerto: coautora; participa en la calibración del juez y en la usabilidad.
> - Director: MsC. Juan Carlos Barrero Calixto.
> - Realtix no participa en el desarrollo ni aprueba entregables.

---

## 0. Cómo trabajar con esta especificación (para Claude Code)

### 0.1 Lectura y uso eficiente

- `CLAUDE.md` resume las reglas y el protocolo; esta especificación da el detalle.
- Al empezar un bloque, lee su sección 8 y solo las secciones que ella cite.
- No leas el paquete completo: los documentos FINAL, cuando implementes un requerimiento; el código
  de 6.3.1, solo en B3.
- El límite de uso es el recurso más escaso del proyecto:
  - no leas archivos grandes completos si basta con una parte;
  - para la curaduría, escribe scripts en lugar de leer las normas;
  - resume la salida de las pruebas.

### 0.2 Protocolo de cada bloque

Rodolfo lanza cada bloque con una sola línea («Haz el bloque B7») y quiere confirmar lo menos
posible. Es su primera vez con Claude Code: los mensajes para él van en español claro, sin jerga, y
cuando tenga que hacer algo, en pasos numerados con los comandos exactos para copiar.

Cada bloque sigue este protocolo de punta a punta:

1. **Preparar:** `git switch main && git pull`; el árbol de trabajo debe quedar limpio.
2. **Planear (modo plan):** lee la sección 8 del bloque y lo que cite, y presenta un plan breve:
   archivos, pruebas, riesgos y paradas. Es la única aprobación que Rodolfo da en un bloque sin
   paradas.
3. **Rama:** `bNN-tema`, desde `main`.
4. **Implementar:** commits pequeños con Conventional Commits y `Refs` (sección 7.1).
5. **Probar:** las pruebas unitarias y las del bloque, con la salida real resumida.
6. **Documentar:** `docs/resumenes/bNN.md` (qué se hizo, RF y RNF con su nombre corto, cómo se
   verificó y cifras) y `docs/cambios_para_documento.md`.
7. **PR:** con la plantilla de la sección 7.2.
8. **CI:** espera el resultado (`gh pr checks --watch`); si falla, corrige y vuelve a subir.
9. **Revisión independiente:** un subagente con contexto limpio compara el diff con la sección 8 del
   bloque, `CLAUDE.md` y la lista de chequeo del PR; se corrige lo que encuentre.
10. **Fusionar:** si no hay una parada pendiente y la CI está en verde:
    `gh pr merge --merge --delete-branch` y luego `git switch main && git pull`.
11. **Etiqueta:** si el bloque la lleva (sección 7.1): `git tag -s vX.Y.Z -m "…"` y
    `git push origin vX.Y.Z`.
12. **Reportar y detenerse:** un mensaje que empieza con `BLOQUE BNN TERMINADO`, de 5 líneas como
    máximo: qué quedó, el enlace del PR, el estado de la CI, el gasto de API si lo hubo y lo que
    sigue.

**Varios bloques en una sesión** («Haz los bloques B7 y B8»): se aplica el protocolo completo a cada
uno, en orden. Solo el primero pasa por el modo plan; los siguientes se planean sin detenerse y el
plan queda en la descripción de su PR. La sesión se detiene al final del último bloque o en la primera
parada.

**Nunca:**

- hacer commit o push directo a `main`;
- desactivar los ganchos o la firma (`--no-verify`, `--no-gpg-sign`); si la firma falla, es una
  parada;
- leer `.env` o llaves privadas, ni imprimir secretos;
- cambiar una decisión de la sección 2 sin consultarla.

### 0.3 Paradas

En estos puntos, Claude Code se detiene con un mensaje que empieza con `PARADA:` y dice, en pasos
numerados, qué debe hacer Rodolfo y qué debe responder para continuar.

| Bloque | Cuándo | Qué hace Rodolfo |
|---|---|---|
| B1 | Al terminar | Crea el `.env` a partir de `.env.example` |
| B2 | Antes del PR | Revisa las vistas lado a lado de las tablas y hace él mismo el commit de verificación, con los comandos que le deja el mensaje |
| B6 | Antes del PR | Revisa la hoja de revisión de las referencias y hace él mismo el commit de aprobación, con los comandos que le deja el mensaje |
| B13 | Al empezar el despliegue | Enciende el servidor en AWS, da el subdominio de DuckDNS y copia el `.env` al servidor |
| B15 | Después de la corrida 2 | Califica la muestra de calibración con Dayanna, aplica la usabilidad y aprueba el umbral |
| Cualquiera | Si hace falta instalar algo con `sudo`, si aparece una contradicción con la adenda o con esta especificación, o si una prueba falla tres veces seguidas | Ejecuta el comando, decide o lo lleva al chat de desarrollo |

Fuera de esas paradas, no se pide confirmación.

### 0.4 Fechas

- En documentos, resúmenes, ADR, PR, mensajes de commit, reportes e informe: **ninguna fecha exacta
  del trabajo**, ni día ni hora de ejecución. Si hace falta ubicar algo en el tiempo: «octubre de
  2026».
- Las fechas del contenido tributario (plazos de pago, vigencias, años de las normas) sí van: son
  datos del dominio.
- En los archivos de resultados, el tiempo se registra como duración (milisegundos), no como marca
  de tiempo.
- Los parámetros técnicos de fecha (fecha de referencia del conjunto sintético y reloj simulado) son
  fijos y no corresponden a días de trabajo (secciones 4.1 y 6.3).

---

## 1. Alcance y requerimientos

### 1.1 Los 65 requerimientos

- **49 requerimientos funcionales en 10 grupos:** SYS 6, AUT 4, ORQ 6, IPU 5, ICA 4, GEN 4, OCR 6,
  ESC 5, UI 4 y OBS 5.
- **16 requerimientos no funcionales.**
- **18 historias de usuario.**
- **RF-SYS-06 · Aviso de interacción con IA** es provisional (adenda 06): «El sistema multiagente de
  IA deberá informar al contribuyente, al inicio de cada conversación, que lo atiende un sistema de
  inteligencia artificial y que puede pedir en cualquier momento la atención de un funcionario».
  Prioridad alta. En la matriz va marcado como provisional.
- Los demás textos están en `docs/paquete/documentos/Requerimientos_OE1_Realtix_FINAL.md`. Los
  identificadores y los nombres cortos no cambian.

### 1.2 Textos que cambian (los aplica después el chat de documentos)

| Requerimiento o sección | Cambio |
|---|---|
| RF-ORQ-05 · Modelo de razonamiento | «El agente orquestador deberá utilizar un modelo de mayor capacidad de razonamiento que los agentes de ejecución, Claude Sonnet 5.5 en el MVP, para las decisiones de enrutamiento» |
| RF-OCR-05 · Modelo de visión | «El agente OCR deberá utilizar un modelo de visión eficiente en costos, Claude Haiku 5.5 en el MVP, configurable sin cambios en el código» |
| RNF-06 · Horario de atención | Se agrega «medido durante el periodo de evaluación» al objetivo del 99 % |
| Sección 3.3 de requerimientos, «Modelo de lenguaje» | Claude Sonnet 5.5 y Claude Haiku 5.5 |

### 1.3 Lo que no se agrega

No hay un requerimiento nuevo para la bandeja del funcionario:

- la bandeja de solo lectura de la consola cumple lo que dice la Tabla 22 del documento para
  `POST /api/v1/escalamiento` («lo pone a disposición del funcionario») y la HU-11;
- al escalar, el widget cambia el indicador a «Atención humana» (RF-UI-03 · Identificación del
  interlocutor);
- que el funcionario responda dentro de la conversación es opcional (sección 3.6).

### 1.4 Metas de los agentes (guían los prompts)

| Agente | Meta |
|---|---|
| Orquestador | Dirigir cada consulta al agente especializado capaz de resolverla |
| IPU | Dar al contribuyente la información necesaria sobre su impuesto predial: cuánto debe, por qué y hasta cuándo |
| ICA | Orientar al contribuyente sobre sus obligaciones de industria y comercio y estimar su valor |
| Información general | Resolver las dudas transversales e informar con claridad lo que el sistema multiagente de IA no cubre |
| OCR | Extraer con exactitud los datos del recibo predial que carga el contribuyente |
| Escalamiento | Garantizar que ninguna consulta quede sin una respuesta confiable, transfiriendo a un funcionario lo que el sistema multiagente de IA no resuelve |

---

## 2. Decisiones de arquitectura (ADR)

Cada una queda como archivo en `docs/decisiones/ADR-NN-titulo.md`, con contexto, decisión,
alternativas, consecuencias y el cambio que implica en el documento de grado.

| ID | Decisión | Por qué | Cambio frente a los FINAL |
|---|---|---|---|
| ADR-01 | Desarrollo con Claude Code en WSL 2 (Ubuntu 24.04), en el PC de Rodolfo, desde VS Code; Docker Engine dentro de WSL | Commits con la identidad de Rodolfo; el mismo sistema operativo del servidor | Ninguno |
| ADR-02 | **Modelos:** `claude-sonnet-5-5` en el orquestador; `claude-haiku-5-5` en los agentes de IPU, ICA, información general y OCR; `claude-opus-5-5` solo como juez de la evaluación. `claude-sonnet-4-6` y `claude-haiku-4-5-20251001` quedan como alternativa por configuración | Haiku 4.5 tenía retiro tentativo a partir de octubre de 2026. Los 5.5 cuestan menos: Haiku 5.5 cobra $0,10 y $0,50 por millón de tokens de entrada y de salida con prompts de hasta 100.000 tokens, frente a $1 y $5 de Haiku 4.5. Tienen soporte anunciado al menos hasta 2027 | RF-ORQ-05, RF-OCR-05, sección 3.3 de requerimientos y sección 8.3 de arquitectura |
| ADR-03 | `nodo_confianza`, `nodo_respuesta` y `nodo_escalamiento` sin llamada a modelo. La cobertura de alcance se deriva de la clasificación del orquestador y de lo que declara el agente; la respuesta multiagente se consolida con una plantilla | Menos latencia (RNF-01 · Tiempo de respuesta) y menos costo; el resultado se prueba sin modelo; el resumen del caso cumple los 5 segundos de RF-ESC-04 | Secciones 3.4 y 8.3 de arquitectura |
| ADR-04 | **Recuperación híbrida:** ChromaDB 1.5.9 (vectorial, con `langchain-chroma`) más BM25 (`bm25s` con PyStemmer y palabras vacías en español) en el backend. 8 fragmentos por canal, fusión por rango recíproco (RRF, k = 60) y los 5 mejores al prompt. Un fragmento por artículo | Chroma autoalojado no tiene búsqueda léxica con ranking: la búsqueda híbrida de su Search API es solo de Chroma Cloud. Cortar por artículo permite citar el artículo exacto | Sección 7 de arquitectura (se precisa) |
| ADR-05 | La base sintética de RealSit se abre en **solo lectura** (SQLite, `mode=ro`). Conversaciones, casos escalados, mensajes del funcionario y registro de interacciones van en PostgreSQL, junto al checkpointer | RF-SYS-02 · Alcance de solo lectura queda garantizado por construcción; el backend no guarda estado y se puede replicar (RNF-02 · Escalamiento horizontal); resuelve H-02 y OC-08 | Sección 5.1, Figura 2 y sección 9.2 de arquitectura |
| ADR-06 | **Tarifas y plazos por año gravable**, en archivos de datos versionados con fuente y fecha de consulta (sección 4.3) | La liquidación, la estimación del ICA y el RAG dicen lo mismo, con la norma del año de la consulta (adenda, sección 3.2) | Ninguno |
| ADR-07 | **OVT simulada:** página de pruebas, rotulada como simulación y sin marcas reales, que entrega un token de sesión firmado con HMAC | Permite demostrar RF-AUT-01 a RF-AUT-04 sin acceso a la OVT real | Sección 6.1 de arquitectura (se precisa) |
| ADR-08 | **Widget en iframe** (React 19, Vite 8 y Tailwind 4) y **consola web** para el funcionario y el administrador | Dentro de Shadow DOM, Tailwind 4 pierde bordes, anillos y sombras sin un complemento adicional; el iframe aísla estilos y scripts | Sección 4 de arquitectura |
| ADR-09 | **Proxy Caddy** con HTTPS automático (Let's Encrypt) y nombre gratuito en DuckDNS, en lugar de Nginx con certificado de ACM | Cero costo y renovación automática; Let's Encrypt no emite certificados para los nombres `amazonaws.com` de EC2 | Tabla 9, secciones 9.2 y 9.3 y Figura 3 de arquitectura |
| ADR-10 | **EC2 m7i-flex.large** (2 vCPU y 8 GiB) en us-east-1, en una cuenta nueva de AWS con el plan Free | Elegible para el plan Free y pagada con sus créditos | Presupuesto |
| ADR-11 | **Registro propio de interacciones**, sin texto de los mensajes ni datos personales, para métricas y auditoría; LangSmith para las trazas | LangSmith gratis guarda las trazas solo 14 días | Decide D5 |
| ADR-12 | **Modo humano (D6):** una conversación escalada ya no la atienden los agentes; los mensajes nuevos quedan en el caso | Coherente con RF-ESC-05 y RF-UI-03 | Decide D6 |
| ADR-13 | **OC-08:** si el caso escala antes de calcular la confianza, se registra `nivel_confianza = 0.0` con su motivo | No cambia el esquema | Decide OC-08 |
| ADR-14 | **Cuatro casos de enrutamiento** sin transiciones nuevas (sección 3.4) | Mantiene 8 nodos y 8 transiciones (D2) | Decide la sección 5.2 del contexto |
| ADR-15 | **GitHub Flow en el plan gratuito:** un PR por bloque, Conventional Commits, merge commits, ganchos que impiden commits directos a `main` y CI en cada PR | El plan Free no protege ramas en repositorios privados | Ninguno |
| ADR-16 | **Modo de evaluación:** reloj inyectable (`X-Reloj-Simulado`), horario configurable y `X-Escenario-Id`; solo se activa por configuración | Las corridas pueden caer fuera del horario de atención; sin esto, el sistema multiagente de IA se niega a responder, como exige RNF-06 | Ninguno |
| ADR-17 | **Confianza, valores iniciales:** pesos de 0,4 (similitud), 0,4 (suficiencia) y 0,2 (cobertura); umbral de 0,7; la falta de cobertura escala siempre | Punto de partida configurable; se calibra con las corridas 1 y 2 | Decide el valor inicial pendiente |
| ADR-18 | **`POST /api/v1/escalamiento`** es el botón «Hablar con un funcionario»: marca la solicitud explícita y ejecuta el grafo, sin registrar el caso por su cuenta | Un solo punto registra casos (`nodo_escalamiento`), sin duplicados | Precisa la Tabla 8 |
| ADR-19 | **`plataforma_general`:** manual de uso de la OVT simulada, rotulado como sintético, más un glosario con fuentes | No hay manuales públicos de la OVT, y usar material no público violaría el acuerdo de confidencialidad. En producción se reemplaza por reingesta (RF-OBS-04) | Tabla 19 y sección 3.6 del documento (choque 3 de la adenda, aprobado) |
| ADR-20 | **Fuentes adicionales del predial 2026:** Acuerdo 780 de 2020 (art. 3) y la resolución que fija los rangos de 2026 | Las tarifas residenciales urbanas vigentes salen del Acuerdo 780 de 2020 y los rangos de 2026, de esa resolución (choque 2, aprobado) | Marco jurídico y Tabla 19 |
| ADR-21 | **Usabilidad interna:** cuestionario SUS y evaluación heurística, aplicados por los dos autores | El equipo no involucra personas externas (choque 4, aprobado) | Rúbrica de usabilidad del OE4 |
| ADR-22 | **Respuestas de referencia de los autores**, a partir de fuentes oficiales verificadas; cada una cita su fuente | No hay un experto tributario en el equipo (choque 5, aprobado) | Sección 1.5.2.8.3 del documento |

---

## 3. Arquitectura

### 3.1 Grafo y estado

- Ocho nodos y ocho transiciones, como en las Tablas 1 y 2 de arquitectura, y el `AgentState` de 14
  campos de la Tabla 3, con su ciclo de vida:
  - `messages`, `id_conversacion`, `datos_extraidos`, `resumen_caso` e `intentos_clasificacion` se
    conservan entre turnos;
  - `contribuyente_id` y `predios_autorizados` los fija la capa de acceso en cada solicitud;
  - el resto se reinicia en cada turno.
- Para RF-SYS-06 se permiten campos auxiliares del turno, como la marca de pregunta por la IA. Van
  documentados en el ADR correspondiente, sin cambiar los 14 campos del diseño.
- **Categorías de RF-ORQ-01:** `ipu`, `ica`, `general`, `ocr` y `fuera_de_alcance`. El escalamiento es
  una transición, no una categoría.

### 3.2 Modelos por nodo

| Nodo | Modelo | Configuración |
|---|---|---|
| `nodo_orquestador` | `claude-sonnet-5-5` | `thinking: {"type": "between_tools"}` (no piensa antes de responder), esfuerzo bajo, salida estructurada con `json_schema` |
| `nodo_ipu`, `nodo_ica`, `nodo_general` | `claude-haiku-5-5` | Pensamiento desactivado, esfuerzo medio, herramientas sobre el adaptador y los servicios |
| `nodo_ocr` | `claude-haiku-5-5` | Imagen o PDF; salida estructurada de los 6 campos y del diagnóstico de legibilidad y de tipo de documento |
| `nodo_confianza`, `nodo_respuesta`, `nodo_escalamiento` | Sin modelo | Código determinista |
| Juez (fuera del sistema multiagente de IA) | `claude-opus-5-5` | Esfuerzo medio, veredicto estructurado |
| Embeddings | OpenAI `text-embedding-3-large` | 3.072 dimensiones |

**Reglas de la API de los modelos 5.5** (las maneja `langchain-anthropic` 1.7.6, que exige `anthropic`
menor que 2.0):

- `temperature`, `top_p` y `top_k` distintos del valor por defecto devuelven error;
- no se acepta un prefijo de respuesta del asistente;
- Sonnet 5.5 no acepta `tool_choice` forzado, así que la salida estructurada va por `json_schema`;
- los esquemas de salida estructurada no piden «razonamiento paso a paso», porque la API puede
  rechazarlos;
- los bloques de la respuesta se leen por tipo;
- `stop_reason: "refusal"` se trata como falla del servicio y escala.

### 3.3 Flujo de un turno y nivel de confianza

1. **API:**
   - valida el horario (o el reloj simulado en el modo de evaluación);
   - valida el token de la OVT simulada; si hay sesión, carga los predios autorizados con
     `get_predios_contribuyente`;
   - si la conversación es nueva, incluye el aviso de IA en la respuesta.
2. **Orquestador (una llamada):**
   - categoría o categorías, con la parte de la consulta que corresponde a cada una;
   - marcas: sesión requerida, solicitud explícita de un humano, pregunta por la IA, tributario fuera
     del MVP y municipio distinto de Bogotá.
3. **Agente (una o dos llamadas):** recuperación híbrida y herramientas del adaptador. Devuelve el
   texto, las fuentes, la suficiencia (completa, parcial, no pudo, aclaración o no corresponde) y
   su cobertura.
4. **Confianza (sin modelo):** 0,4 × similitud + 0,4 × suficiencia + 0,2 × cobertura (ADR-17).
   - La similitud es el coseno del canal vectorial, normalizado con la escala que se fija en B8; se
     calcula también para los fragmentos que solo trajo BM25.
   - La suficiencia vale 1 (completa), 0,5 (parcial) o 0 (no pudo).
   - Sin fragmentos (respuestas solo con datos del adaptador), el puntaje se renormaliza sobre los
     otros dos factores.
   - La aclaración es una respuesta válida y no escala.
   - «No corresponde» devuelve la consulta al orquestador mientras no se alcance el tope de
     reclasificaciones, que es 2 y configurable.
   - En una consulta multiagente, basta con que una parte quede bajo el umbral para escalar.
   - Lo no tributario no se escala.
5. **Respuesta o escalamiento (sin modelo):** formato final; o resumen del caso, registro del caso y
   aviso de transferencia.

Son dos o tres llamadas a modelos por consulta simple. La latencia se mide desde B7.

### 3.4 Casos de enrutamiento sin transición propia (ADR-14)

1. **Aviso de sesión requerida (RF-AUT-04):** el orquestador marca «sesión requerida» y enruta a
   `nodo_general`, que da el aviso; pasa por confianza (sin fragmentos) y llega a `nodo_respuesta`.
2. **Predio ajeno (D3):** el agente devuelve el rechazo como respuesta completa, con una marca de
   rechazo por acceso; la confianza lo trata como la aclaración: respuesta válida, sin escalar. El
   mensaje es el mismo para un predio ajeno y para uno inexistente (OC-06) y no revela datos.
3. **«No corresponde» con el tope alcanzado:** confianza → escalamiento, con el motivo «tope de
   reclasificaciones».
4. **Consulta multiagente escalada:** `nodo_escalamiento` entrega las partes ya resueltas, tomadas
   de `respuestas_parciales`, junto con el aviso de transferencia (RF-ESC-05).

### 3.5 Aviso de IA (RF-SYS-06)

- **En el widget:** al abrir cada conversación muestra el aviso, antes de cualquier respuesta, con
  el botón «Hablar con un funcionario».
- **En la API:** la primera respuesta de cada conversación trae el campo `aviso_ia` con el mismo
  texto, para que las pruebas lo verifiquen sin el widget.
- **Texto:** «Te atiende un asistente de inteligencia artificial. Sus respuestas son orientativas y
  puedes pedir que te atienda un funcionario en cualquier momento».
- **Ante «¿estoy hablando con una persona?» o similares:** el orquestador marca la pregunta por la
  IA y `nodo_general` responde que es un sistema de inteligencia artificial y ofrece el escalamiento
  (RF-ESC-02). Si el contribuyente acepta, se trata como una solicitud explícita.

### 3.6 Modo humano y bandeja (ADR-12 y ADR-18)

- Una conversación escalada queda en estado `escalada`: los agentes no responden; cada mensaje nuevo
  se guarda en el caso, y la API responde con `interlocutor: "sistema"` y un aviso de que el caso
  está en manos de un funcionario.
- **Bandeja de solo lectura** en la consola, con token de funcionario: lista de casos, con su motivo,
  categoría, fecha y estado, y detalle de cada uno, con su resumen estructurado y los mensajes.
- **Opcional, solo si sobra tiempo:** que el funcionario responda desde la consola y el widget
  muestre la respuesta con `interlocutor: "funcionario"`.

### 3.7 Contenedores

| Contenedor | Rol | Imagen | Volumen |
|---|---|---|---|
| `proxy` | HTTPS automático; sirve la web (OVT simulada, widget y consola) y enruta `/api` y `/health` | `caddy:2.11` | `caddy-data` |
| `backend` (1 o más réplicas) | API, control de acceso y grafo | `python:3.12-slim`, multietapa | `datos-sinteticos` (solo lectura) |
| `chromadb` | Base vectorial | `chromadb/chroma:1.5.9` | `chroma-data` |
| `postgres` | Checkpointer y almacén propio | `postgres:16` | `postgres-data` |

- Un único `docker-compose.yml` levanta todo (RNF-13 · Orquestación con Compose). En desarrollo se
  levantan solo los servicios que hagan falta (`docker compose up -d postgres chromadb`).
- Cada réplica construye el índice BM25 al arrancar con los fragmentos guardados en Chroma, y lo
  reconstruye cuando cambia la versión del corpus.

### 3.8 API

**Contrato del chat.** Los valores del ejemplo son ilustrativos.

```http
POST /api/v1/chat/mensaje
Authorization: Bearer <token de la OVT simulada>    (sin él, solo consultas generales)
X-Escenario-Id: IPU-07                               (opcional, solo en pruebas)
X-Reloj-Simulado: AAAA-MM-DDTHH:MM:SS-05:00          (solo con el modo de evaluación activo)
Content-Type: application/json

{"id_conversacion": "conv-0001", "mensaje": "¿Cuánto debo del predial?"}
```

```json
{
  "id_conversacion": "conv-0001",
  "respuesta": "…",
  "aviso_ia": "Te atiende un asistente de inteligencia artificial…",
  "interlocutor": "agente",
  "estado": "respondida",
  "meta": {
    "categoria": "ipu",
    "agentes_invocados": ["nodo_orquestador", "nodo_ipu", "nodo_confianza", "nodo_respuesta"],
    "nivel_confianza": 0.86,
    "motivo_escalamiento": null,
    "caso_id": null,
    "fuentes": [{"norma": "Resolución de rangos del predial 2026", "articulo": "1", "coleccion": "normativa_ipu", "puntaje": 0.74}],
    "contextos": null,
    "datos_extraidos": null,
    "tiempos_ms": {"total": 3400, "nodo_orquestador": 1100, "nodo_ipu": 2100},
    "tokens": {"entrada": 7400, "salida": 620},
    "modelo_por_nodo": {"nodo_orquestador": "claude-sonnet-5-5", "nodo_ipu": "claude-haiku-5-5"},
    "version": "0.9.0"
  }
}
```

- `aviso_ia` solo viene en la primera respuesta de la conversación; en las demás es `null`.
- `interlocutor` puede ser `agente`, `funcionario` o `sistema`.
- `estado` puede ser `respondida`, `aclaracion`, `escalada`, `rechazo_acceso`, `aviso_sesion`,
  `fuera_de_horario` o `fuera_de_alcance`.
- `meta.contextos` trae el texto de los fragmentos usados, solo en el modo de evaluación (lo necesita
  RAGAS).
- `meta.tokens` suma los tokens de todas las llamadas a modelos del turno, para calcular el costo.

**Puntos de acceso.**

| Método | Ruta | Uso | Origen |
|---|---|---|---|
| POST | `/api/v1/chat/mensaje` | Mensaje del contribuyente | Tabla 8 |
| POST | `/api/v1/chat/documento` | Multipart con `archivo`, `id_conversacion` y `mensaje` opcional. Procesa el recibo en la misma solicitud, responde con el formato del chat y borra el archivo al terminar. JPG, PNG o PDF de hasta 5 MB | Tabla 8 (se precisa) |
| GET | `/api/v1/predios/{predio_id}/estado-cuenta` | Estado de cuenta, con token | Tabla 8 |
| GET | `/api/v1/predios/{predio_id}/pagos` | Historial de pagos, con token | Tabla 8 |
| POST | `/api/v1/escalamiento` | Botón «Hablar con un funcionario» (ADR-18) | Tabla 8 (se precisa) |
| GET | `/api/v1/admin/metricas` | Matriz de confusión, precisión, exhaustividad, F1 y tiempos (RF-OBS-02 y RF-OBS-03); con token de administrador | Tabla 8 |
| GET | `/health` | Estado del servicio y de sus dependencias | Tabla 8 |
| GET | `/api/v1/chat/{id}/mensajes?desde=N` | Mensajes nuevos de la conversación (para el widget) | Nuevo |
| GET | `/api/v1/escalamiento/casos` y `/api/v1/escalamiento/casos/{id}` | Bandeja de solo lectura, con token de funcionario | Nuevo |
| POST | `/api/v1/ovt-simulada/sesion` | Emite el token de un usuario de prueba; solo si `OVT_SIMULADA_ACTIVA=true` | Nuevo |

### 3.9 Estructura del repositorio

| Ruta | Contenido |
|---|---|
| `src/agents/` | `graph.py`, `state.py`, `nodes/` (un archivo por nodo) y `prompts/` (prompts versionados) |
| `src/services/` | Lógica de dominio sin LangGraph: confianza, liquidación, ICA, calendario, acceso, horario, resumen y minimización |
| `src/data/` | Modelos, esquema, `RealSitAdapter` y su implementación sintética; generador en `src/data/generar/` |
| `src/store/` | Almacén propio en PostgreSQL (SQLAlchemy Core) |
| `src/integrations/` | Fábrica de modelos, embeddings, Chroma, BM25 y RRF, LangSmith y anonimizador |
| `src/api/` | FastAPI, capa de acceso, puntos de acceso y modo de evaluación |
| `src/evaluacion/` | Ejecutor de escenarios, evaluadores de código, juez, RAGAS, métricas y reportes |
| `src/config.py` y `src/container.py` | Configuración y contenedor de dependencias |
| `knowledge_base/` | Normas en Markdown por colección y su `fuentes.yaml` |
| `datos/` | Tarifas, calendario y regímenes por año gravable |
| `scripts/` | Curaduría, ingesta y utilidades |
| `web/` | OVT simulada, widget y consola (Vite) |
| `deploy/` | Caddyfile, guía y scripts de despliegue |
| `tests/` | Unitarias, de contrato e integración por dominio; `escenarios/` y `componentes/` |
| `docs/` | Esta especificación, la adenda, el paquete, `decisiones/`, `resumenes/`, `verificacion/`, `usabilidad/`, `informe_final/`, `cambios_para_documento.md`, `plan_de_pruebas.md`, `reporte_de_pruebas.md`, `revision_referencias.md` y `verificacion_curaduria.md` |
| `reports/` | Resultados de las corridas |

### 3.10 Configuración (variables de entorno)

Todas se leen con pydantic-settings en `src/config.py`, que falla con un mensaje claro si falta una
obligatoria. Van documentadas en `.env.example` (RNF-14 · Configuración por entorno).

| Grupo | Variables |
|---|---|
| Modelos | `REALTIX_ANTHROPIC_API_KEY` (nunca `ANTHROPIC_API_KEY`), `OPENAI_API_KEY`, `MODELO_ORQUESTADOR`, `MODELO_IPU`, `MODELO_ICA`, `MODELO_GENERAL`, `MODELO_OCR`, `MODELO_JUEZ`, `MODELO_EMBEDDINGS` |
| Observabilidad | `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT`, `LANGSMITH_TRACING` |
| Datos | `REALSIT_DB_PATH`, `DATABASE_URL`, `CHROMA_HOST`, `CHROMA_PORT` |
| Confianza y enrutamiento | `UMBRAL_CONFIANZA`, `PESO_SIMILITUD`, `PESO_SUFICIENCIA`, `PESO_COBERTURA`, `MAX_RECLASIFICACIONES` |
| Tiempos | `TIMEOUT_MODELO_S`, `TIMEOUT_CHROMA_S`, `TIMEOUT_ADAPTADOR_S` |
| Seguridad | `OVT_HMAC_SECRET`, `TOKEN_FUNCIONARIO`, `TOKEN_ADMIN`, `CORS_ORIGENES`, `OVT_SIMULADA_ACTIVA` |
| Horario y evaluación | `HORARIO_INICIO`, `HORARIO_FIN`, `ZONA_HORARIA`, `MODO_EVALUACION`, `FALLAS_INYECTABLES` |
| Archivos | `TAMANO_MAXIMO_ARCHIVO_MB` |

En `.env` van solo los secretos y lo propio de cada máquina. Los parámetros (umbral, pesos,
horario y tiempos) tienen su valor por defecto en `src/config.py` y, en el servidor, en
`deploy/servidor.env`.

La clave de Anthropic del sistema multiagente de IA se llama `REALTIX_ANTHROPIC_API_KEY` y se pasa explícitamente al
cliente. Si Claude Code encontrara una variable `ANTHROPIC_API_KEY` en la terminal, la usaría en
lugar de la suscripción.

### 3.11 Seguridad y privacidad

- **Acceso (RF-AUT-01 a RF-AUT-04):**
  - el token de la OVT simulada lleva el `contribuyente_id`, la emisión y el vencimiento (2 horas),
    firmados con HMAC-SHA256;
  - un token inválido o vencido equivale a no tener sesión;
  - los métodos del adaptador filtran contra los predios autorizados.
- **Fundamento del control de acceso:** reserva tributaria (Decreto Distrital 807 de 1993, art. 18)
  y Circular Externa 002 de 2024 de la SIC (un dato accesible al público no es, por eso, un dato
  público). Va en el README y en el reporte.
- **Minimización (RNF-03 · Protección de datos personales):** las herramientas le entregan al modelo
  solo lo necesario (matrícula, vigencias, valores y estados), nunca el nombre ni el número de
  documento. Una prueba unitaria revisa lo que se envía.
- **Trazas (RNF-05 · Registro auditable):**
  - LangSmith registra el `id_conversacion` como metadato, nunca el `contribuyente_id`;
  - un anonimizador enmascara cédulas, NIT y nombres en las entradas y salidas de las trazas;
  - la prueba automática de B12 lo verifica.
- **Registro de interacciones:** marca de tiempo, `id_conversacion`, `escenario_id`, categoría,
  agentes, confianza, estado, motivo, tiempos, tokens y modelos. No guarda el texto de los mensajes
  ni datos personales.
- **Transporte:** HTTPS en el proxy; Chroma y PostgreSQL no se exponen fuera del host.
- **Web:**
  - CORS solo para los orígenes configurados;
  - cabecera `Content-Security-Policy` con `frame-ancestors` limitado al origen de la OVT simulada;
  - tokens de funcionario y de administrador en la consola.
- **Secretos:** solo en `.env`, fuera de git; `gitleaks` en pre-commit y en CI; Claude Code no lee
  `.env`.
- **Antes de producción** (README, adenda sección 5):
  - estudio de impacto de privacidad;
  - contrato de transmisión con los proveedores de modelos y de observabilidad;
  - revisión del Registro Nacional de Bases de Datos.

  Nada de eso aplica al MVP, que solo usa datos sintéticos.

### 3.12 Robustez (RNF-08 · Tiempos de espera y degradación)

- Toda llamada a un servicio externo (modelo, Chroma, adaptador) tiene un tiempo máximo y un único
  reintento ante fallas transitorias.
- Si el reintento falla:
  - si falla el orquestador, el grafo va directo a escalamiento;
  - si falla un agente, lo reporta y la confianza escala;
  - si falla el registro del caso, el mensaje de transferencia igual se entrega.
- El contribuyente nunca ve un error técnico.
- **Fallas inyectables** (solo con `FALLAS_INYECTABLES=true`): tiempo agotado o error del modelo, de
  Chroma o del adaptador, activadas por un encabezado de prueba.

### 3.13 Observabilidad

- LangSmith traza cada ejecución del grafo con su nodo, herramienta y tiempo (RF-OBS-01 · Traza del
  flujo entre agentes), con los metadatos `id_conversacion`, `escenario_id` y versión.
- `/admin/metricas` calcula, a partir del registro de interacciones y de las etiquetas de los
  escenarios:
  - la matriz de confusión, la precisión, la exhaustividad y el F1 por categoría (RF-OBS-02 y
    RF-OBS-03);
  - los tiempos por conversación.
- La consola lo muestra.

---

## 4. Datos

### 4.1 RealSit simulado v2

El código de 6.3.1 (`docs/paquete/codigo_6.3.1/realtix-mvp/`) se importa tal como está en un primer
commit; las correcciones van en commits aparte.

| # | Cambio | Resuelve |
|---|---|---|
| 1 | Una conexión por operación; la base de RealSit se abre en solo lectura (`mode=ro`) | H-01, RF-SYS-02 |
| 2 | Conversaciones, casos, mensajes del funcionario e interacciones pasan al almacén propio (PostgreSQL; SQLite en las pruebas unitarias) | H-02, OC-08, RNF-02 |
| 3 | Identificadores derivados de la semilla y verificados como únicos | H-03, OC-02 |
| 4 | Una obligación de ICA por contribuyente con actividad y por vigencia (2023 a 2026), en el predio donde ejerce la actividad | H-04 |
| 5 | Fecha de referencia fija como parámetro: el primer día hábil de octubre de 2026 (un valor técnico, no un día de trabajo; sección 0.4). Con ella quedan obligaciones al día, vencidas y pendientes (las cuotas del ICA y del SPAC que vencen después, y el ICA anual de 2026) | H-05, OC-03 |
| 6 | Tarifas oficiales del predial 2026 (sección 4.4) en lugar del tramo de 4 por mil | H-06 |
| 7 | Fechas límite del calendario oficial 2026. Las vigencias 2023 a 2025 usan fechas y tarifas sintéticas, marcadas así en los datos | OC-04 |
| 8 | Cada obligación guarda base gravable, tarifa, valor liquidado, descuento por pronto pago, fecha límite con descuento, fecha límite y estado | OC-05, RF-IPU-03, RF-OCR-02 |
| 9 | Contribuyente con régimen de ICA (umbral de 391 UVT); predio con destino (residencial, comercial o lote), localidad, estrato y CHIP | RF-ICA-03 |
| 10 | Exactamente 500 predios con 4 vigencias de IPU: 2.000 obligaciones de IPU | OC-01, D4 |
| 11 | «Vigentes» son las pendientes o vencidas de cualquier vigencia; avalúo por vigencia; `ActividadNoReconocidaError`; método `get_predios_contribuyente` | M-01, M-02, M-03, M-07, D1 |
| 12 | El mismo mensaje para un predio inexistente y uno ajeno | OC-06 |
| 13 | Ruta de la base como texto o `Path` | OC-07 |
| 14 | Usuarios de prueba fijos (sección 4.2) | RF-AUT-01 y escenarios |
| 15 | Tarifas del ICA por actividad cargadas de `datos/`; hasta tener la tabla oficial, las 8 actividades de 6.3.1 marcadas como provisionales | RF-ICA-02 |
| 16 | Huella SHA-256 de la base generada, registrada en el repositorio; la base `.db` no se versiona | RF-OBS-05 |

**Modelo de datos de RealSit (SQLite, solo lectura):**

- `contribuyente`: id, tipo y número de documento, nombre, tipo de persona, actividad (código CIIU y
  descripción) y régimen de ICA.
- `predio`: matrícula (llave), CHIP, contribuyente, dirección, localidad, estrato, destino y avalúo
  vigente.
- `obligacion_tributaria`: id, predio, tributo, vigencia, base gravable, tarifa por mil, valor
  liquidado, descuento, fecha límite con descuento, fecha límite y estado.
- `pago`: id, obligación, fecha, valor y medio.
- `tarifa_ica`: código, actividad, grupo, tarifa por mil, vigencia y fuente.

**Almacén propio (PostgreSQL):** `conversacion` (activa, escalada o cerrada), `caso_escalado`
(motivo, categoría, nivel de confianza, resumen en texto y en JSON, intentos y estado),
`mensaje_funcionario` e `interaccion`.

### 4.2 Usuarios de prueba y OVT simulada

- `tests/fixtures/usuarios_prueba.yaml` define unos 12 usuarios fijos, con su perfil y sus datos
  esperados. Deben cubrir todos los escenarios:
  - un predio residencial al día;
  - dos predios, uno en mora;
  - un avalúo de $350.000.000 (ejemplo de la sección 4.4);
  - persona jurídica con ICA bimestral y predio comercial;
  - régimen preferencial;
  - un lote;
  - un contribuyente sin actividad económica;
  - pagos parciales;
  - estratos 1 a 3, para las tarifas preferenciales de 2027.
- La OVT simulada lista esos usuarios. Dice en grande «Entorno simulado de pruebas — no es la
  Oficina Virtual Tributaria real» y no usa logos ni marcas de Realtix ni de RealSit.

### 4.3 Datos por año gravable

En `datos/`, archivos YAML con `fuente` (norma y artículo), `url`, `mes_consulta` («octubre de
2026»), `vigencia_desde`, `vigencia_hasta` y `verificado_por` (nombre, sin fecha):

| Archivo | Contenido | Fuente |
|---|---|---|
| `tarifas/ipu_2026.yaml` | 30 rangos residenciales urbanos y tarifas no residenciales | Resolución de rangos de 2026; Acuerdos 780 de 2020 y 105 de 2003 |
| `tarifas/ipu_2027.yaml` | Tarifas generales y preferenciales | Acuerdo 1084 de 2026, art. 20 |
| `tarifas/sobretasa_alumbrado_2027.yaml` | Tarifas y topes | Acuerdo 1084 de 2026, arts. 14 y 15 |
| `tarifas/ica_2026.yaml` | Tarifa por actividad (CIIU) | Acuerdo 65 de 2002, art. 3, en su texto vigente, contrastado con la página de Hacienda |
| `tarifas/ica_2027.yaml` | Las 9 tarifas nuevas | Acuerdo 1084 de 2026, art. 21 |
| `regimenes_ica.yaml` | Umbrales de 2026 y de 2027 | Resolución SDH-000195 de 2025; Acuerdo 1084 de 2026, art. 26 |
| `calendario/2026.yaml` | Plazos del predial, el SPAC y el ICA | Resolución SDH-000195 de 2025, arts. 1 y 3 a 6 |
| `uvt_smmlv.yaml` | UVT y SMMLV por año | Resoluciones de la DIAN y decretos del salario mínimo; se verifican en B2 |

**Reglas:**

- El agente aplica las tarifas y los plazos del año gravable de la consulta. Si el contribuyente no
  lo dice, usa el año en curso según el reloj del servidor (o el reloj simulado en el modo de
  evaluación) y lo dice en la respuesta.
- Si un año no tiene datos, lo dice y no estima.
- Los rangos de 2027 se actualizan con el IVIUR, y esa actualización aún no se publica. La estimación
  de 2027 usa la tabla del Acuerdo 1084 tal como está y lo advierte en la respuesta.

### 4.4 Valores verificados

**Predial 2026, predios residenciales urbanos.** Tabla transcrita de la copia del PDF que publica el
INCP. En B2, un script la contrasta con el texto del PDF y Rodolfo revisa la vista lado a lado antes
de usarla (parada de B2).

| Avalúo desde ($) | Hasta ($) | Tarifa (por mil) |
|---|---|---|
| 0 | 194.307.000 | 5,5 |
| 194.307.001 | 207.062.000 | 5,6 |
| 207.062.001 | 238.375.000 | 5,7 |
| 238.375.001 | 269.690.000 | 5,8 |
| 269.690.001 | 301.005.000 | 5,9 |
| 301.005.001 | 332.318.000 | 6,0 |
| 332.318.001 | 363.632.000 | 6,1 |
| 363.632.001 | 394.946.000 | 6,2 |
| 394.946.001 | 447.136.000 | 6,3 |
| 447.136.001 | 499.330.000 | 6,4 |
| 499.330.001 | 551.518.000 | 6,5 |
| 551.518.001 | 603.709.000 | 6,6 |
| 603.709.001 | 655.899.000 | 6,8 |
| 655.899.001 | 708.090.000 | 7,0 |
| 708.090.001 | 760.279.000 | 7,2 |
| 760.279.001 | 812.470.000 | 7,4 |
| 812.470.001 | 864.660.000 | 7,6 |
| 864.660.001 | 937.727.000 | 7,8 |
| 937.727.001 | 1.010.794.000 | 8,0 |
| 1.010.794.001 | 1.083.859.000 | 8,2 |
| 1.083.859.001 | 1.156.929.000 | 8,4 |
| 1.156.929.001 | 1.229.992.000 | 8,6 |
| 1.229.992.001 | 1.303.058.000 | 8,8 |
| 1.303.058.001 | 1.376.126.000 | 9,0 |
| 1.376.126.001 | 1.449.192.000 | 9,2 |
| 1.449.192.001 | 1.710.142.000 | 9,5 |
| 1.710.142.001 | 1.971.099.000 | 10,1 |
| 1.971.099.001 | 2.232.051.000 | 10,8 |
| 2.232.051.001 | 2.505.139.000 | 11,5 |
| 2.505.139.001 | En adelante | 12,3 |

**Predial 2026, predios no residenciales** (art. 2 de la misma resolución):

| Destino | Avalúo desde ($) | Hasta ($) | Tarifa (por mil) |
|---|---|---|---|
| Comercial (62) | 0 | 363.264.000 | 8 |
| Comercial (62) | 363.264.001 | En adelante | 9,5 |
| Depósitos y parqueaderos accesorios de hasta 30 m² (65) | 1 | 6.832.000 | 5 |
| Depósitos y parqueaderos accesorios de hasta 30 m² (65) | 6.832.001 | En adelante | 8 |
| Urbanizables no urbanizados y urbanizados no edificados (67) | 0 | 63.048.000 | 12 |
| Urbanizables no urbanizados y urbanizados no edificados (67) | 63.048.001 | En adelante | 33 |

**Ejemplo para pruebas:** un avalúo de $350.000.000 cae en 6,1 por mil. El impuesto es $2.135.000, y
con el 10 % de pronto pago habría sido $1.921.500 si se pagaba hasta el 17 de abril de 2026.

**Calendario 2026** (Resolución SDH-000195 de 2025, verificado por la adenda):

| Concepto | Fecha |
|---|---|
| Predial con 10 % de descuento (declarar y pagar todo; aplica también a quien está en el SPAC y paga todo) | 17 de abril de 2026 |
| Facturas del predial expedidas a más tardar | 30 de abril de 2026 |
| Plazo del predial sin descuento | 10 de julio de 2026 |
| SPAC: declaración inicial | 8 de mayo de 2026 |
| SPAC: cuotas | 5 de junio, 14 de agosto, 2 de octubre y 4 de diciembre de 2026 |
| ICA bimestral (régimen común con impuesto a cargo de 2025 mayor a 391 UVT, $19.471.409) | 10 de abril, 12 de junio, 21 de agosto, 9 de octubre y 11 de diciembre de 2026, y 12 de febrero de 2027 |
| ICA anual (régimen común de hasta 391 UVT y régimen preferencial) | 26 de febrero de 2027 |

**Desde 2027** (Acuerdo 1084 de 2026, verificado por la adenda contra el texto firmado):

- **Predial:** tarifas nuevas desde el predial de 2027 (art. 20):
  - residenciales generales desde 5,5 por mil;
  - estratos 1 y 2 con base de 16 a 107 SMMLV: 1 por mil;
  - estratos 1 y 2 con base de más de 107 a 135 SMMLV, y estrato 3 hasta 135 SMMLV: 3 por mil;
  - estratos 1 y 2 con base menor de 16 SMMLV: excluidos;
  - residenciales rurales de más de 135 SMMLV: 6,5 por mil;
  - los rangos se actualizan cada año con el IVIUR.

  La tabla completa se transcribe en B2.
- **Sobretasa de alumbrado público** desde el 1 de enero de 2027 (arts. 10 a 15): la pagan los
  contribuyentes del predial, sobre la misma base. Tarifas y topes en los arts. 14 y 15; se
  transcriben en B2.
- **ICA:**
  - tarifas nuevas (art. 21) para los declarantes anuales desde el 1 de enero de 2027, y para los
    bimestrales desde el bimestre siguiente a la aprobación del acuerdo; falta confirmar la fecha de
    aprobación en plenaria;
  - regímenes (art. 26): común si el impuesto a cargo del año anterior supera 391 UVT, y declara y
    paga cada dos meses; preferencial hasta 391 UVT, y declara una vez al año;
  - quien empieza actividades queda el primer año en el régimen preferencial;
  - un preferencial con ingresos netos menores a 1.933 UVT no declara: su impuesto es lo retenido.
- **Retención de ICA** (art. 25): fuera del alcance del MVP; se escala (RF-ICA-04).
- **Notificación de las facturas** (art. 27, num. 3): publicación en el Registro Distrital y, al
  mismo tiempo, en la página de la Secretaría Distrital de Hacienda. El envío a la dirección del
  contribuyente es solo divulgación adicional.
- **Notificación electrónica** (art. 28): solo si el contribuyente registró un correo en el RIT, y
  rige cuando se reglamente.
- **Vigencia** (art. 52): rige desde su publicación; deroga los arts. 7 y 8 del Decreto 807; los
  Acuerdos 111 de 2003 y 399 de 2009 quedan derogados desde el 1 de enero de 2027.
- **Por verificar en el PDF antes de cargarlo:** según Accounter, una fuente secundaria, el art. 7
  reduce en 60 % los intereses y las sanciones para quien pague en un solo pago hasta el 21 de
  diciembre de 2026.

**Ley 1995 de 2019, vigente** por la Ley 2294 de 2023, art. 49, par. 3:

- en predios con avalúo actualizado, el impuesto sube como máximo el IPC más 8 puntos frente al año
  anterior;
- hay topes propios para predios sin actualizar y para vivienda de estratos 1 y 2 con avalúo de hasta
  135 SMMLV.

El agente nunca dice que esa ley venció.

### 4.5 Recibos sintéticos (RF-OCR-06 · Plantilla sintética de recibo)

- **Ocho campos:**
  - matrícula;
  - propietario y dirección;
  - vigencia;
  - avalúo;
  - tarifa;
  - valor liquidado;
  - descuento;
  - fecha límite.
- **Leyenda:** «Documento sintético sin validez tributaria».
- **Generación:** desde el conjunto sintético, en PNG y en PDF, con un JSON de valores de referencia
  por recibo.
- **Variantes para RF-OCR-04:** desenfoque, baja resolución y recorte, más documentos de otro tipo.
- **Extracción:** el agente extrae los 6 campos de RF-OCR-02 (no el nombre del propietario).

---

## 5. Base de conocimiento

### 5.1 Colecciones y fuentes

Las fuentes son las de la adenda (sección 3.1, enlaces en su sección 8) más las de ADR-20:

| Colección | Fuentes, en su texto vigente | Agente |
|---|---|---|
| `normativa_ipu` | Ley 44 de 1990 (con la Ley 1450 de 2011, art. 23); Ley 1995 de 2019 y Ley 2294 de 2023, art. 49, par. 3; Ley 1819 de 2016, art. 354; Decreto Ley 1421 de 1993 (arts. 12, 155 y 162); Acuerdo 648 y Decreto 474 de 2016; Decreto Distrital 352 de 2002, cap. I; Decreto Distrital 807 de 1993; Acuerdo 105 de 2003, art. 2; Acuerdo 780 de 2020, art. 3; resolución de rangos de 2026; artículos de predial del Acuerdo 1084 de 2026 (10 a 18, 20, 27 y 35, e incentivos de los arts. 1 a 8 que apliquen); Resolución SDH-000195 de 2025, arts. 3 a 6 | `nodo_ipu` |
| `normativa_ica` | Ley 14 de 1983 (texto vigente, no el original); Decreto Distrital 352 de 2002, cap. II; Decreto Distrital 807 de 1993; Acuerdo 65 de 2002, art. 3; Acuerdo 1084 de 2026, arts. 21, 24, 25 y 26 e incentivos del ICA; artículos del ICA de la Resolución SDH-000195 de 2025 | `nodo_ica` |
| `normativa_datos` | Ley 1581 de 2012; Decreto 1074 de 2015, caps. 25 y 26 (el 25 con el metadato de origen «Decreto 1377 de 2013») | `nodo_general` |
| `plataforma_general` | Manual de uso de la OVT simulada (sintético) y glosario con fuentes (ADR-19) | `nodo_general` |

El art. 6 del Acuerdo 1084 (delineación urbana) queda fuera, porque el alcance es solo el predial y
el ICA. Ninguna fuente fuera de esta tabla sin avisar al chat de documentos.

### 5.2 Reglas de curaduría

- Texto vigente compilado, con sus notas de modificación.
- URL y mes de consulta («octubre de 2026») de cada documento en
  `knowledge_base/<colección>/fuentes.yaml`.
- Cada fragmento lleva como metadatos `norma`, `articulo`, `coleccion`, `url`, `vigencia_desde` y
  `vigencia_hasta`.
- Un fragmento por artículo, de hasta unos 800 tokens. Los artículos largos se parten con solape de
  50 a 100 tokens; los cortos quedan enteros.
- El calendario se reemplaza cada año por reingesta, sin tocar el código (RF-OBS-04).
- El glosario solo define términos que aparecen en las normas cargadas, y cada definición cita su
  norma y artículo.

### 5.3 Acuerdo 1084 de 2026

- El PDF es escaneado y necesita OCR.
- Se pasan solo los artículos del reparto de la adenda.
- Las tablas de los arts. 14, 15, 20 y 21 se transcriben a YAML con doble lectura (OCR y lectura de
  la imagen), con las diferencias marcadas; Rodolfo revisa la vista lado a lado y hace él mismo el
  commit de la verificación (parada de B2).

### 5.4 Procedimiento

1. Un script descarga cada fuente de su enlace oficial, en una carpeta que no se versiona, y anota la
   URL y el mes de consulta.
2. Otro script la convierte a Markdown y la corta por «ARTÍCULO». Claude no lee las normas completas:
   revisa muestras y la estructura.
3. `docs/verificacion_curaduria.md` lista cada fuente y cada tabla con su estado. En la parada de
   B2, Rodolfo revisa las vistas lado a lado y registra la verificación con el comando que deja B2.

### 5.5 Recuperación híbrida

- **Ingesta:** fragmentos con embeddings `text-embedding-3-large` en una colección de Chroma por
  dominio, con el índice HNSW por defecto.
- **Consulta:**
  - 8 fragmentos por canal (vectorial y BM25), filtrados por colección y, cuando aplique, por
    vigencia;
  - fusión RRF y los 5 mejores al prompt;
  - la similitud que alimenta la confianza es el coseno del canal vectorial.
- **Versión del corpus:** un hash del contenido de `knowledge_base/`. Cuando cambia, cada réplica
  reconstruye su índice BM25.

---

## 6. Plan de pruebas del OE4

La estructura sigue el programa CTFL v4.0.1 del ISTQB (adenda, sección 6.2). El plan se escribe en
`docs/plan_de_pruebas.md` y el reporte en `docs/reporte_de_pruebas.md`.

### 6.1 Contexto, alcance, supuestos, restricciones e interesados

- **Objeto:** el sistema multiagente de IA desplegado en AWS, con datos sintéticos.
- **Alcance:** los 65 requerimientos y las 18 HU.
- **Supuestos:** reloj simulado en el modo de evaluación; usuarios de prueba fijos.
- **Restricciones:** plazo corto, un solo operador, sin usuarios externos ni experto tributario,
  presupuesto de API de $25 en Anthropic y $10 en OpenAI.
- **Interesados:** los autores (ejecutan y califican la muestra de calibración), el director (recibe
  el reporte) y el chat de documentos (recibe el material del capítulo 5). Realtix no participa.

### 6.2 Niveles

| Nivel | Qué se prueba | Datos | Métricas |
|---|---|---|---|
| Componentes | El orquestador clasifica consultas cuya categoría se conoce; cada agente responde preguntas con referencia | 100 consultas etiquetadas (20 por categoría; las de `ocr` con un archivo adjunto simulado) en `tests/componentes/enrutamiento.yaml`; los escenarios de un turno de cada agente, ejecutados directo contra su nodo | Precisión, exhaustividad y F1 por clase; matriz de confusión; kappa de Cohen; exactitud con el juez |
| Integración de componentes | El pipeline RAG, desde la búsqueda hasta la respuesta | Los escenarios de un turno con RAG | RAGAS: precisión y exhaustividad del contexto, fidelidad y relevancia de la respuesta |
| Sistema | Conversaciones completas sobre el ambiente desplegado | 60 escenarios (sección 6.3) | Comportamiento, exactitud, alucinación, cita, claridad, latencia y costo; pass@1 y pass^3 |
| No funcionales (ISO/IEC 25010) | Eficiencia de desempeño, fiabilidad, seguridad y usabilidad | Sección 6.7 | p50 y p95, réplicas, fallas inyectadas, trazas, disponibilidad y SUS |

Las pruebas unitarias, de contrato y de integración del código corren en cada commit y son la base
de las evidencias U e I de la matriz (anexo A).

### 6.3 Escenarios del nivel de sistema: 60

Incluyen los 15 escenarios mínimos de la adenda (sección 6.7) y los criterios CA-01 a CA-06 de
RF-IPU-02 (Tabla 11 del documento).

| Grupo | N.º | Contenido |
|---|---|---|
| Aviso de IA | 2 | Inicio de conversación (adenda 1); «¿hablo con una persona?» (adenda 2) |
| Acceso | 4 | Predio ajeno (adenda 3 y CA-04); sin sesión (adenda 4 y CA-05); token inválido; consulta general sin sesión (RF-AUT-03) |
| IPU | 15 | CA-01 a CA-03; conceptos (3); descuento y plazo de 2026 (adenda 5 y 6); topes de la Ley 1995 (adenda 7); estimación de 2026 y de 2027 (adenda 8); notificación de la factura (adenda 9); pago sin declarar (adenda 10); beneficio de intereses de 2026; cuotas del SPAC |
| ICA | 10 | Conceptos (3); estimación (3); fechas de 2026 por régimen (2); régimen de 2027 (adenda 11); retención que escala (adenda 12) |
| Información general | 7 | Uso de la OVT simulada (2); glosario (3); datos personales (2) |
| OCR | 7 | Recibos válidos (3); ilegibles (2); otro documento (1); confirmación con contraste contra el adaptador (1) |
| Fuera de alcance | 5 | No tributario que se informa (2, uno es la adenda 13); tributario fuera del MVP que escala (3) |
| Multiagente | 3 | IPU con ICA en una sola consulta |
| Escalamiento explícito | 1 | «Quiero hablar con una persona» |
| Ambiguas y de varios turnos | 2 | Pregunta que exige aclaración; referencia a un mensaje anterior (RF-UI-02) |
| Horario | 2 | Fuera de horario; día festivo |
| Robustez | 2 | Falla del modelo (adenda 14); adaptador sin respuesta (CA-06) |
| **Total** | **60** | |

El escenario 15 de la adenda (trazas sin identificadores) es una revisión automática de las trazas de
toda la corrida. Cuando un escenario necesite un municipio distinto de Bogotá, usa Medellín.

El reloj de cada escenario es la fecha de referencia del conjunto sintético a las 10:00 (hora de
Bogotá), salvo en los de horario, que usan un domingo, un festivo o una hora fuera del horario.

**Formato** (un YAML por escenario en `tests/escenarios/`):

```yaml
id: IPU-07
titulo: Estimación del predial de 2026 para un predio residencial
rf: [RF-IPU-03, RF-AUT-01, RNF-09]
grupo: ipu
categoria_esperada: ipu
comportamiento_esperado: responder
sesion: U03
reloj: "AAAA-MM-DDT10:00:00-05:00"   # fecha de referencia del conjunto sintético (sección 4.1)
tipo_latencia: simple
turnos:
  - usuario: "¿Cuánto me tocaría pagar de predial este año por mi apartamento?"
verificaciones_codigo:
  - {tipo: contiene_valor, valor: "2.135.000"}
  - {tipo: contiene_texto, valor: "estimación"}
respuesta_referencia: >
  Texto de referencia redactado a partir de las fuentes, con su cita.
fuentes_esperadas: ["Resolución de rangos del predial 2026"]
no_debe: ["presentar como vigente el descuento del 10 %, que venció el 17 de abril de 2026"]
dado_cuando_entonces:
  dado: "Un contribuyente autenticado con un predio residencial de avalúo $350.000.000"
  cuando: "Pide la estimación del predial de este año"
  entonces: "Recibe la estimación de 2026 con tarifa, base y la nota de estimación no vinculante"
```

Los valores de este ejemplo son ilustrativos y salen del usuario de prueba que se use.

### 6.4 Evaluadores

- **Código, donde la verificación es exacta:** categoría, comportamiento, presencia del aviso,
  valores, campos del OCR, ausencia de identificadores, latencia y costo.
- **Modelo:** el juez (`claude-opus-5-5`) califica guiado por la referencia. Devuelve en JSON:
  - el veredicto: correcta, parcialmente correcta o incorrecta;
  - si hubo alucinación;
  - si citó la norma y si la cita sustenta lo dicho;
  - si cubrió todo lo pedido;
  - la claridad, de 1 a 5;
  - una justificación breve, sin pedirle el razonamiento paso a paso.

  La rúbrica sigue la que usó Anthropic: fidelidad a las fuentes, citas que sustentan, cobertura,
  prioridad a fuentes primarias y uso mesurado de herramientas. El juez no ve qué modelo respondió.
- **Personas:** los autores califican a ciegas 20 respuestas elegidas al azar; se calcula el acuerdo
  con el juez (kappa de Cohen).
- **Escenario superado:** pasa todas las verificaciones de código y el juez lo califica correcta o
  parcialmente correcta, sin alucinación.

### 6.5 Métricas

| Capa | Métrica | Cómo |
|---|---|---|
| Enrutamiento | Precisión, exhaustividad y F1 por clase; matriz de confusión | 5 clases de RF-ORQ-01, en componentes y en sistema |
| Enrutamiento | Kappa de Cohen y exactitud de la clase mayoritaria | Para atender la advertencia de Powers: cuánto supera el clasificador al azar |
| Recuperación | Precisión y exhaustividad del contexto | `ragas` 0.4.3, con las respuestas de referencia |
| Generación | Fidelidad y relevancia de la respuesta | `ragas`; la relevancia usa `text-embedding-3-large` |
| Generación | Exactitud | Juez guiado por referencia |
| Consistencia | pass@1 promedio, pass@3 y pass^3 | Cada escenario se ejecuta 3 veces en la corrida final |
| Operativas | Latencia p50 y p95 (simple y RAG); costo por consulta | Tiempos de la API; costo con la ecuación del documento y los tokens reales |
| Meta del OE4 | Tasa de escenarios superados | Promedio de los 3 ensayos frente al 85 % de RNF-16, con intervalo de confianza de Wilson al 95 % |

- **Referencia para comparar:** Bahçeci y colaboradores obtuvieron 92,63 % de fidelidad, 91,31 % de
  relevancia, 75,20 % de precisión del contexto, 86,60 % de exhaustividad del contexto y una
  latencia cercana a 4.000 ms.
- **RAGAS:**
  - se instala en el grupo de dependencias `eval`; la compatibilidad con el resto del stack se
    comprobó en octubre de 2026;
  - su modelo evaluador es uno de bajo costo de OpenAI, que se elige en B12 tras comprobar que
    acepta los parámetros que usa RAGAS;
  - la API de los modelos 5.5 de Claude rechaza valores de `temperature` distintos del
    predeterminado, y RAGAS puede fijarlos.

### 6.6 Análisis de fallas

- Cada falla se clasifica por causa técnica (enrutamiento, recuperación, prompt, datos, umbral o
  infraestructura), para corregir.
- Se clasifica también por la familia de MAST (Cemri y colaboradores): «diseño del sistema»,
  «desalineación entre agentes» o «verificación de la tarea», para el análisis del documento.
- Cada falla corregida se agrega como caso de regresión.

### 6.7 No funcionales

| Requerimiento | Prueba |
|---|---|
| RNF-01 · Tiempo de respuesta | p50 y p95 de los escenarios, separados en simples y con RAG |
| RNF-02 · Escalamiento horizontal | `docker compose up --scale backend=2`: la misma conversación continúa al pasar de una réplica a otra |
| RNF-06 · Horario de atención | Unitarias con reloj fijo; monitor de `/health` cada 15 minutos con GitHub Actions desde el despliegue hasta el cierre de las pruebas; la disponibilidad dentro del horario hábil se calcula con el historial de ejecuciones (`gh run list`) |
| RNF-08 · Tiempos de espera y degradación | Fallas inyectadas: siempre escalamiento, nunca un error técnico |
| RNF-15 · Volúmenes persistentes | Reiniciar y recrear los contenedores; el corpus, las conversaciones y los casos siguen ahí |
| RF-SYS-02 · Alcance de solo lectura | Huella de las tablas de RealSit antes y después de la corrida: idénticas |
| RNF-03 · Protección de datos personales y RNF-05 · Registro auditable | Prueba de minimización; prueba automática de trazas; lista de chequeo de la Ley 1581 |

### 6.8 Usabilidad (ADR-21)

- **Tareas:** consultar el estado de cuenta; estimar el ICA; cargar un recibo y confirmar los datos;
  hacer una pregunta fuera de alcance; pedir un funcionario.
- **Instrumentos:**
  - el cuestionario SUS (System Usability Scale): 10 afirmaciones en escala Likert de 1 a 5, con un
    puntaje de 0 a 100;
  - una evaluación heurística: cada problema se registra con la heurística que viola y su gravedad.
- **Quién la aplica:** Rodolfo y Dayanna, por separado, en la parada de B15.
- **Cómo se reporta:** como evaluación interna preliminar de dos evaluadores que además desarrollaron
  el sistema multiagente de IA.

### 6.9 Criterios de entrada y de salida

- **Entrada a la corrida 1:**
  - el sistema multiagente de IA desplegado responde `/health`;
  - la CI está en verde;
  - el corpus está cargado;
  - los escenarios y sus referencias están revisados.
- **Salida de la corrida final:**
  - tasa de escenarios superados de 85 % o más;
  - ningún escenario de acceso ni de trazas fallido;
  - latencias medidas;
  - matriz de trazabilidad completa;
  - reporte generado.

### 6.10 Corridas

| Corrida | Cuándo | Ensayos | Para qué |
|---|---|---|---|
| 1 | Al terminar el despliegue (B14) | 1 por escenario, más componentes | Encontrar y clasificar fallas |
| 2 | Después de las correcciones (B15) | 1 por escenario | Verificar correcciones y calibrar el umbral |
| 3 (final, congelada) | Con el código congelado (B16) | 3 por escenario, más componentes, RAGAS y no funcionales | La que se reporta; etiqueta `v1.0.0` |

**Salidas de cada corrida:** en `reports/corrida-N/`:

- `resultados.jsonl` (un registro por ensayo);
- `metricas.json`;
- `reporte.md` (tablas y figuras);
- `matriz_confusion.png`;
- `fallas.md` (causa y MAST);
- `costos.md`.

### 6.11 Matriz de trazabilidad como manual de pruebas

Cada prueba automática lleva `@pytest.mark.req("RF-AUT-02")`, y cada escenario, su lista `rf`. Un
script cruza ambos con los resultados y genera `reports/trazabilidad.md` y `.csv`. Para cada
requerimiento muestra:

- el caso en formato «dado, cuando, entonces»;
- el resultado esperado y el obtenido;
- la evidencia;
- la calificación:
  - 100 % aprobado: pasan todas sus evidencias;
  - 80 % aprobado con observaciones: pasa con una limitación documentada;
  - 0 % no aprobado: falla alguna evidencia.

De esas calificaciones sale el porcentaje de cumplimiento global.

---

## 7. Convenciones

### 7.1 Git y GitHub

| Qué | Convención |
|---|---|
| Ramas | `b01-esqueleto`, `b02-curaduria`, `fix/tema`, `docs/tema` |
| Commits | `tipo(alcance): descripción`. Tipos en inglés (`feat`, `fix`, `test`, `docs`, `refactor`, `build`, `ci` y `chore`); descripción en español, en infinitivo y de 72 caracteres como máximo, por ejemplo `feat(datos): abrir la base de RealSit en solo lectura` |
| Pie del commit | `Refs: RF-AUT-02 · Restricción a predios propios`, cuando aplique; Claude Code agrega `Co-Authored-By` |
| PR | Uno por bloque, con la plantilla de la sección 7.2 |
| Fusión | Solo merge commit; la rama se borra al fusionar |
| Etiquetas | `v0.1.0` (B5, grafo con servicios), `v0.5.0` (B9, API completa), `v0.9.0` (B13, desplegado) y `v1.0.0` (evaluado) |
| `main` | Nunca se hace commit directo: gancho `no-commit-to-branch` y CI en cada PR |
| Fechas | Ninguna fecha exacta del trabajo en mensajes de commit, PR ni documentos (sección 0.4) |

### 7.2 Plantilla del PR

```markdown
## Qué se hizo
## Requerimientos cubiertos (ID · nombre corto)
## Cómo se probó (comandos y salida real, resumida)
## Decisiones tomadas y pendientes
## Cambios frente al documento de grado (y si se actualizó docs/cambios_para_documento.md)
## Resumen para el documento (uno o dos párrafos, en pasado e impersonal)
## Cómo revisarlo (comando para probarlo a mano en menos de 5 minutos)
## Lista de chequeo
- [ ] CI en verde
- [ ] Sin secretos, sin `.env`, sin bases `.db` y sin datos reales
- [ ] Pruebas nuevas marcadas con `req`
- [ ] `docs/resumenes/bNN.md` y `docs/cambios_para_documento.md` actualizados
```

### 7.3 `CLAUDE.md` (menos de 200 líneas)

Claude Code lo lee al empezar cada sesión. Contiene:

- **Proyecto y precedencia de fuentes** (encabezado de esta especificación) y la estructura del
  repositorio (sección 3.9).
- **El protocolo de cada bloque** (sección 0.2), **las paradas** (sección 0.3) y el formato de los
  mensajes `PARADA:` y `BLOQUE BNN TERMINADO`.
- **Reglas de trabajo:**
  1. El proyecto se llama siempre «sistema multiagente de IA» y la empresa, «Realtix».
  2. Solo datos sintéticos; ningún material no público de RealSit.
  3. No inventar normas, tarifas, fechas ni resultados; todo dato tributario sale de `datos/` o de
     `knowledge_base/`, con su fuente.
  4. Separación de capas: los nodos no tienen lógica tributaria, los servicios no conocen
     LangGraph y ningún agente toca SQL; todo pasa por `RealSitAdapter`.
  5. Cada entrega lista los RF y RNF con su nombre corto.
  6. Probar antes de entregar y mostrar la salida real; nunca afirmar que algo funciona sin haberlo
     ejecutado.
  7. Nunca hacer commit ni push a `main`, ni desactivar ganchos o firmas.
  8. No leer `.env` ni llaves privadas, ni imprimir secretos.
  9. Fechas según la sección 0.4. Si un escenario necesita un municipio distinto de Bogotá, se usa
     Medellín.
  10. No modificar `docs/ESPECIFICACION_TECNICA.md` ni la adenda, salvo que Rodolfo lo pida
      expresamente; si algo debe cambiar, se propone en el PR.
  11. Si alguna vez aparece la cifra de adopción de IA en Colombia: 7,5 % de las empresas (MinTIC,
      agosto de 2024), y ninguna otra.
  12. Ahorrar tokens (sección 0.1).
- **Comandos frecuentes:** `uv sync --all-groups`; `uv run pytest -q`;
  `uv run ruff check . && uv run ruff format --check .`; `docker compose up -d postgres chromadb`;
  y los de ingesta y de la API, cuando existan.
- **Resumen de los ADR**, una línea por cada uno.

### 7.4 Código

- Python 3.12, con tipos en las firmas públicas.
- `ruff` para estilo y formato.
- Nombres del dominio en español y nombres técnicos en inglés cuando sean convención.
- Docstrings breves en español.
- Dinero con `Decimal` y redondeo explícito.
- Registros estructurados (JSON) con `id_conversacion` y sin datos personales.
- `pytest-cov` en la CI, que reporta la cobertura sin umbral obligatorio.
- Versiones exactas en `pyproject.toml` y `uv.lock`: para cada paquete, la estable más reciente con
  al menos 7 días de publicada, consultada en PyPI, salvo una corrección de seguridad. `faker` va
  fijo, porque de él depende la reproducibilidad del conjunto sintético. `anthropic`, menor que 2.0,
  como exige `langchain-anthropic` 1.7.6.

---

## 8. Bloques de implementación

Cada bloque sigue el protocolo de la sección 0.2, con las paradas de la sección 0.3. «Lee además»
indica lo que hay que leer fuera de la sección del bloque.

### 8.1 B1 · Esqueleto

**Entregables:**

- la estructura de la sección 3.9;
- `pyproject.toml` con todas las dependencias del proyecto (`langgraph`,
  `langgraph-checkpoint-postgres`, `langchain-anthropic`, `langchain-openai`, `langchain-chroma`,
  `chromadb`, `bm25s`, `PyStemmer`, `fastapi`, `uvicorn`, `pydantic-settings`, `sqlalchemy`,
  `psycopg[binary]`, `langsmith`, `faker`, `holidays`, `pillow`, `pypdfium2`, `httpx`, `pyyaml`) y
  los grupos `dev` (`pytest`, `pytest-cov`, `ruff`, `pre-commit`) y `eval` (`ragas==0.4.3`,
  `matplotlib`, `scikit-learn`), con las versiones de la sección 7.4;
- `src/config.py` y `src/container.py`;
- las marcas de pytest `unit`, `integration` y `req`, y el script de trazabilidad (esqueleto);
- `.pre-commit-config.yaml` con ruff, gitleaks, `no-commit-to-branch` y validación de Conventional
  Commits, con los ganchos `pre-commit` y `commit-msg` instalados;
- GitHub Actions con uv, pre-commit y pytest con cobertura;
- `docker-compose.yml` con `postgres:16` y `chromadb/chroma:1.5.9` y sus volúmenes;
- `.gitignore`, `.gitattributes` y `.env.example` documentado (sección 3.10);
- la plantilla de PR de la sección 7.2, plantillas de issues y un issue por cada bloque de B2 a B17,
  con sus RF y RNF (identificador y nombre corto) y la sección que lo describe;
- `docs/decisiones/` con ADR-01 a ADR-22, breves (25 líneas como máximo cada uno), con «octubre de
  2026» como única referencia temporal;
- `docs/cambios_para_documento.md` con la tabla de la sección 9, y la carpeta `docs/resumenes/`;
- `CLAUDE.md` (sección 7.3);
- `.claude/settings.json`, con la sintaxis vigente de la documentación de Claude Code:
  - modo plan como inicial (`permissions.defaultMode: "plan"`) y modelo `opusplan`;
  - permitidos sin preguntar: `uv`, `pytest`, `ruff`, `pre-commit`, `docker` y `docker compose`,
    `npm` y `npx`, `git` y `gh` en ramas de trabajo (incluidos `gh pr create`, `gh pr checks`,
    `gh pr merge` y `git tag -s`), `ssh` y `scp` con la llave `~/.ssh/tg2-ec2.pem`, y la lectura
    web de los dominios de las fuentes de la sección 5.1 y de la documentación técnica;
  - negados: leer `.env` (no `.env.example`) y `~/.ssh/`, también con comandos como `cat`, `head`,
    `less` o `grep`; `git push --force`; `git push` a `main`; `git commit --no-verify`;
    `gh repo delete`; `rm -rf` fuera del repositorio;
- `.mcp.json` con el servidor `docs-langchain` (`https://docs.langchain.com/mcp`);
- un README con secciones para instalar, ejecutar, probar y desplegar, y «Antes de producción».

**Verificación:** `uv sync --all-groups`; `uv run pytest -q` (incluye una prueba de humo de la
configuración, que falla con un mensaje claro si falta una variable); `pre-commit run --all-files`;
`docker compose up -d postgres chromadb` y las dos verificaciones de salud.

**Parada al terminar:** Rodolfo crea el `.env` desde `.env.example`. El mensaje le dice qué variables
llenar con sus claves y cómo generar los secretos (`openssl rand -hex 32`).

**Cubre:** RNF-11 · Código versionado y la base de RNF-13 y RNF-14.

### 8.2 B2 · Curaduría y datos por año

**Lee además:** secciones 4.3, 4.4 y 5, y las secciones 3 y 8 de la adenda.

**Entregables:**

- `scripts/curaduria/`: descarga cada fuente de la sección 5.1 desde su enlace oficial a una carpeta
  ignorada por git, la convierte a Markdown y la corta por artículo. Claude Code no lee las normas
  completas: revisa la estructura y muestras.
- `knowledge_base/` con las cuatro colecciones y su `fuentes.yaml` (URL y mes de consulta).
- El Acuerdo 1084: OCR en español solo de los artículos del reparto de la sección 5.1. Si hace falta
  Tesseract, es una parada: Rodolfo ejecuta `sudo apt install -y tesseract-ocr tesseract-ocr-spa`.
- Los archivos de `datos/` de la sección 4.3, con `verificado_por` vacío:
  - `tarifas/ipu_2026.yaml` con la tabla de la sección 4.4, contrastada por un script con el texto
    del PDF de la resolución de rangos;
  - `calendario/2026.yaml` con el calendario de la sección 4.4;
  - el ICA de 2026 y de 2027, la sobretasa y el predial de 2027, transcritos de sus fuentes; las
    tablas escaneadas, con doble lectura (OCR y lectura de la imagen) y las diferencias marcadas.
- Una vista lado a lado por tabla en `docs/verificacion/`: la página o el texto de la fuente junto a
  la tabla transcrita, con las diferencias resaltadas.
- `scripts/curaduria/marcar_verificado.py --por "<nombre>"`, que llena `verificado_por` y marca
  `docs/verificacion_curaduria.md`.
- El manual de la OVT simulada y el glosario (ADR-19), rotulados como sintéticos; el glosario, solo
  con términos de las normas cargadas, cada uno con su cita.
- `docs/verificacion_curaduria.md`: cada fuente y cada tabla con su estado.

Si un enlace falla o el texto no es el vigente compilado, se anota en la lista y se sigue con las
demás. Lo que no esté en la fuente queda como pendiente: nunca se completa con valores supuestos.

**Parada antes del PR:** Rodolfo revisa las vistas de `docs/verificacion/` y, si todo cuadra, ejecuta
en la rama:

```bash
uv run python scripts/curaduria/marcar_verificado.py --por "Rodolfo Angel Gilart Pulido"
git commit -am "docs(curaduria): verificar las tablas contra las fuentes oficiales"
git push
```

Luego responde «listo», o dice qué tabla no cuadra.

**Cubre:** la parte de datos de RF-IPU-01, RF-IPU-04, RF-IPU-05, RF-ICA-01, RF-ICA-03, RF-GEN-01,
RF-GEN-02 y RF-OBS-04.

### 8.3 B3 · RealSit simulado v2

**Lee además:** secciones 4.1 y 4.2, `docs/paquete/04_REVISION_Y_HALLAZGOS.md` y el código de
`docs/paquete/codigo_6.3.1/realtix-mvp/` con su `ESTADO_DEL_CODIGO.md`.

**Entregables:**

- el código de 6.3.1 copiado tal como está a `src/data/`, en un commit propio;
- un commit por cada cambio de la tabla de la sección 4.1, con `Refs` al hallazgo y al RF;
- tarifas, calendario y regímenes leídos de `datos/`, nunca escritos en el código;
- el almacén propio en `src/store/`;
- los usuarios de prueba de la sección 4.2, que cubren los 60 escenarios de la sección 6.3; en
  `tests/fixtures/usuarios_prueba.yaml`, cada usuario dice qué grupos de escenarios cubre;
- la huella SHA-256 de la base generada (la base `.db` no se versiona).

**Pruebas:**

- control de acceso y contrato contra dos implementaciones (la sintética y una en memoria);
- reproducibilidad (la misma huella con la semilla 42);
- volumen (500 predios y 2.000 obligaciones de IPU);
- estados, unicidad de identificadores y uso concurrente;
- que una escritura sobre la base de RealSit falle.

**Cubre:** RF-SYS-02, RF-SYS-05 · Adaptador equivalente a RealSit, RF-AUT-02 · Restricción a predios
propios, la parte de datos de RF-IPU-02, RNF-04 · Uso exclusivo de datos sintéticos y RF-OBS-05 ·
Ejecución repetible de pruebas.

### 8.4 B4 · Estado y grafo con nodos simulados

**Lee además:** secciones 3.1 a 3.6, y las Tablas 1, 2 y 3 de
`docs/paquete/documentos/Arquitectura_OE2_Realtix_FINAL.md`.

**Entregables:**

- `state.py`, con el ciclo de vida de los campos;
- `graph.py`, con funciones de enrutamiento puras, cada una con su prueba;
- 8 nodos simulados y deterministas, sin llamadas a modelos ni a la red;
- los casos de la sección 3.4 y las marcas del orquestador (incluida la pregunta por la IA);
- el checkpointer en memoria para las pruebas y en PostgreSQL por configuración;
- la exportación del grafo a Mermaid en `docs/figuras/grafo_implementado.mmd`.

**Pruebas:** cada transición; las categorías; la consulta multiagente; la reclasificación hasta el
tope; la solicitud explícita; lo fuera de alcance, tributario y no tributario; la falla de un
servicio; la continuidad entre turnos con reinicio de los campos del turno; los cuatro casos de la
sección 3.4.

**Cubre:** RF-SYS-01 · Patrón Supervisor-Worker, RF-ORQ-02, RF-ORQ-03, RF-ORQ-04, RF-ORQ-06,
enrutamiento de RF-GEN-04 y de RF-ESC-02, RF-UI-02 (backend), rutas de RNF-08 y la marca de RF-SYS-06.

### 8.5 B5 · Servicios e integraciones

**Lee además:** secciones 3.2, 3.3, 3.10 a 3.12, 4.3 y 4.4.

**Entregables:**

- **Servicios** (no conocen LangGraph; el dinero va con `Decimal`; leen `datos/` y, si falta el año
  pedido, fallan con un error explícito, nunca con un valor supuesto):
  - confianza (ADR-17);
  - liquidación del predial de 2026 y de 2027, con la sobretasa de 2027, y la nota de estimación no
    vinculante;
  - estimación del ICA de 2026 y de 2027;
  - régimen y fechas del ICA;
  - resumen del caso, sin modelo;
  - reglas de acceso;
  - horario con los festivos de Colombia (`holidays`) y reloj inyectable;
  - minimización de lo que se envía a los modelos.
- **Integraciones:**
  - fábrica de modelos por configuración, con las reglas de la sección 3.2;
  - tiempos máximos y un reintento;
  - cliente de embeddings;
  - interfaz del recuperador con una implementación provisional en memoria;
  - LangSmith con metadatos y anonimizador;
  - el almacén propio conectado.

**Pruebas:** casos límite de la confianza (umbral exacto, sin fragmentos, aclaración, multiagente);
liquidaciones con valores conocidos, entre ellas, obligatoria, la del ejemplo de la sección 4.4
(avalúo de $350.000.000 en 2026: 6,1 por mil, $2.135.000, y $1.921.500 con el 10 %); estimaciones del
ICA; fechas por régimen; horario y festivos; minimización; anonimizador; integraciones con dobles de
prueba, sin gastar API.

**Etiqueta:** `v0.1.0`.

**Cubre:** RF-ESC-01, RF-ESC-03, RF-ESC-04, RF-IPU-03, RF-ICA-02, RF-ICA-03, RF-AUT-03, RF-AUT-04,
RF-SYS-03 (cobertura), RF-SYS-04, RNF-03, RNF-05, RNF-06, RNF-07, RNF-08, RNF-10 y RNF-14.

### 8.6 B6 · Escenarios, referencias y conjunto de enrutamiento

**Lee además:** sección 6, la sección 6.7 de la adenda y la Tabla 11 (CA-01 a CA-06) de
`docs/paquete/documentos/Requerimientos_OE1_Realtix_FINAL.md`.

**Entregables:**

- los 60 escenarios de la sección 6.3, con la distribución exacta de su tabla y el formato YAML del
  ejemplo, incluidos los 15 de la adenda y CA-01 a CA-06, marcados con un campo `origen`;
- en cada escenario, una respuesta de referencia redactada solo a partir de `datos/`,
  `knowledge_base/` y `tests/fixtures/usuarios_prueba.yaml`, con su cita; lo que no tenga fuente no
  se escribe: se marca como pendiente;
- el campo `aprobado_por` vacío en cada escenario;
- `docs/revision_referencias.md`: una hoja de revisión con cada escenario (ID, grupo, pregunta,
  respuesta de referencia y fuente), primero los 15 de la adenda y CA-01 a CA-06;
- `scripts/aprobar_referencias.py --por "<nombre>" [--excluir ID ...]`, que llena `aprobado_por`;
- `tests/componentes/enrutamiento.yaml`, con 100 consultas etiquetadas, 20 por categoría (las de
  `ocr`, con un archivo adjunto simulado);
- un validador del esquema, con su prueba, y `tests/escenarios/INDICE.md` (escenario, grupo, RF, HU y
  origen).

**Parada antes del PR:** Rodolfo revisa `docs/revision_referencias.md` y, si todo está bien, ejecuta en
la rama:

```bash
uv run python scripts/aprobar_referencias.py --por "Rodolfo Angel Gilart Pulido"
git commit -am "test(escenarios): aprobar las respuestas de referencia"
git push
```

Luego responde «listo», o da los ID que hay que corregir y qué cambiar.

**Cubre:** el diseño de las pruebas del OE4 (ADR-22).

### 8.7 B7 · Nodos reales

**Lee además:** secciones 1.4 y 3.2 a 3.5.

**Entregables:**

- el orquestador con salida estructurada;
- los agentes de IPU, ICA e información general con herramientas sobre el adaptador y los
  servicios, minimización y citas; si B8 no está fusionado, usan el recuperador en memoria de B5;
- prompts versionados en `src/agents/prompts/`, que:
  - citan la norma en los tres agentes;
  - usan el año gravable de la consulta y lo dicen;
  - nunca dicen que la Ley 1995 venció;
  - usan lenguaje claro;
  - ante la pregunta por la IA, responden que es un sistema de IA y ofrecen el escalamiento;
  - nunca envían nombres ni números de documento a los modelos;
- `nodo_confianza`, `nodo_respuesta` y `nodo_escalamiento` reales, sin modelo;
- pruebas de humo con modelos reales (marca `integration`), ejecutadas una sola vez, con los tokens y
  el costo en el resumen;
- la primera medición de latencia (5 consultas simples y 5 con recuperación) en
  `docs/resumenes/b07.md`.

**Cubre:** RF-ORQ-01, RF-ORQ-05, RF-IPU-01 a RF-IPU-05, RF-ICA-01 a RF-ICA-04, RF-GEN-01 a
RF-GEN-04, RF-ESC-02 a RF-ESC-05, RF-AUT-03, RF-AUT-04, RF-SYS-06, RNF-09 y RNF-01 (primera medición).

### 8.8 B8 · Ingesta y recuperación híbrida

**Lee además:** secciones 5.2 y 5.5.

**Entregables:**

- un comando de ingesta y reingesta idempotente, que reporta los fragmentos por colección y el costo
  de los embeddings;
- la segmentación por artículo y los metadatos de la sección 5.2;
- Chroma con `langchain-chroma`, BM25 en español y RRF, con filtros por colección y vigencia;
- la escala de similitud fijada con unas 10 consultas de prueba, y documentada;
- la versión del corpus y los contextos en el modo de evaluación.

**Pruebas:** identificadores literales («Ley 44 de 1990», «artículo 354»); consultas semánticas;
reingesta de un documento nuevo sin cambiar el código; reconstrucción de BM25. Las de integración usan
el Chroma de `docker compose`.

**Cubre:** RF-IPU-01, RF-IPU-04, RF-IPU-05, RF-ICA-01, RF-ICA-03, RF-GEN-01 a RF-GEN-03 y RF-OBS-04 ·
Actualización de la base vectorial.

### 8.9 B9 · API

**Lee además:** secciones 3.5, 3.6, 3.8 y 3.11.

**Entregables:**

- los puntos de acceso de la sección 3.8, con el contrato tal cual (nombres de campos, estados e
  interlocutores);
- la capa de acceso con tokens HMAC;
- el horario;
- `aviso_ia`;
- el modo humano y la bandeja de solo lectura;
- `POST /escalamiento` según ADR-18;
- la carga de archivos validada;
- `/admin/metricas` y `/health`;
- CORS y cabeceras de seguridad;
- el modo de evaluación y las fallas inyectables, que se activan solo por configuración y están
  apagados por defecto.

**Pruebas:** cada punto de acceso con el cliente de pruebas de FastAPI; sin sesión; token inválido;
predio ajeno e inexistente; fuera de horario y festivo; aviso en la primera respuesta; conversación
escalada; y una prueba que demuestra que el contribuyente nunca ve un error técnico.

**Etiqueta:** `v0.5.0`.

**Cubre:** RF-AUT-01 a RF-AUT-04, RF-UI-02, la recepción de RF-OCR-01, RF-ESC-05 en la API,
RF-SYS-06 en la API, RNF-03, RNF-06, RNF-07 y la base de RF-OBS-02 y RF-OBS-03.

### 8.10 B10 · Agente OCR

**Lee además:** sección 4.5, y RF-OCR-01 a RF-OCR-06 en los requerimientos FINAL.

**Entregables:**

- el generador de recibos de la sección 4.5, con la leyenda y un JSON de referencia por recibo;
- `nodo_ocr` con visión y salida estructurada;
- la validación de legibilidad y de tipo de documento;
- la confirmación en varios turnos y el contraste con la obligación del adaptador, sin modificarla;
- el borrado del archivo después de procesarlo, con su prueba.

**Pruebas:** generador y validaciones (unitarias); exactitud por campo sobre 10 recibos y rechazo de
las variantes degradadas (integración), con los tokens y el costo en el resumen.

**Cubre:** RF-OCR-01 a RF-OCR-06 y la parte del backend de RF-UI-04.

### 8.11 B11 · Web

**Lee además:** secciones 3.5, 3.6 y 3.8, y RF-UI-01 a RF-UI-04 en los requerimientos FINAL.

**Entregables.** Un proyecto de Vite con React 19 y Tailwind 4 en `web/`:

- `/ovt/`: la OVT simulada, con el rótulo grande «Entorno simulado de pruebas — no es la Oficina
  Virtual Tributaria real», sin marcas reales, con el selector de usuario de prueba y el widget
  insertado con una etiqueta de script que monta un iframe;
- `/widget/`:
  - aviso de IA al abrir;
  - indicador del interlocutor;
  - control de carga de archivos;
  - mensaje fuera de horario;
  - botón «Hablar con un funcionario»;
  - consulta de mensajes nuevos cuando la conversación está escalada;
- `/consola/`: la bandeja de solo lectura para el funcionario; las métricas y la matriz de confusión
  para el administrador; un enlace a LangSmith.

El proxy sirve la compilación. Las capturas de pantalla se toman con Playwright y van en
`docs/capturas/`.

**Cubre:** RF-UI-01 a RF-UI-04, RF-SYS-06 en el widget, la interfaz de RF-ESC-05, la interfaz de RNF-07
y las HU-11, HU-12, HU-15 y HU-17.

### 8.12 B12 · Evaluación

**Lee además:** sección 6, y las secciones 6.2 a 6.6 de la adenda.

**Entregables.** En `src/evaluacion/`:

- un ejecutor que lee los escenarios, llama a la API (local o desplegada) con `X-Escenario-Id` y
  `X-Reloj-Simulado`, maneja varios turnos y k ensayos configurables, y guarda las respuestas y
  `meta`;
- los evaluadores de código;
- el juez: `claude-opus-5-5` guiado por referencia, con salida JSON y sin pedirle razonamiento paso a
  paso;
- RAGAS, con un modelo evaluador de OpenAI de bajo costo, probado primero con 2 casos para confirmar
  que funciona y cuánto cuesta;
- las métricas de la sección 6.5 (incluidos el intervalo de Wilson, el kappa, pass@k y pass^k), con
  pruebas unitarias sobre datos de juguete;
- el ejecutor de componentes;
- el verificador de trazas (API de LangSmith; busca las cédulas, los NIT y los nombres de los
  usuarios de prueba);
- el generador de reportes, con figuras en matplotlib y sin fechas ni horas de ejecución;
- la matriz de trazabilidad (sección 6.11);
- la exportación de la muestra de calibración y el cálculo del kappa;
- `docs/plan_de_pruebas.md` (sección 6).

**Antes de cerrar:** una mini corrida de 5 escenarios contra la API local, con su reporte.

**Cubre:** RF-OBS-02, RF-OBS-03, RF-OBS-05, el instrumento de RNF-16 y la verificación de RNF-05.

### 8.13 B13 · Contenedores y despliegue

**Lee además:** secciones 3.7, 3.10 y 3.11.

**Entregables:**

- el `Dockerfile` multietapa del backend;
- el `docker-compose.yml` completo, con verificaciones de salud y réplicas posibles; la
  configuración no secreta del servidor en `deploy/servidor.env` (versionado) y los secretos en el
  `.env` de Rodolfo, que se copia sin cambios;
- el `Caddyfile`: HTTPS con el subdominio de DuckDNS (se le pide a Rodolfo), `/api` y `/health` al
  backend, la web estática y las cabeceras de seguridad;
- primero, la prueba local: todo arriba con `docker compose` y `/health` en verde;
- la preparación del servidor por SSH (`ssh -i ~/.ssh/tg2-ec2.pem ubuntu@<subdominio>.duckdns.org`):
  Docker, y el código traído con una llave de despliegue de solo lectura (deploy key) agregada con
  `gh`, nunca con las credenciales de Rodolfo;
- `deploy/README.md`, con los pasos y el comando exacto de `scp` para copiar el `.env`;
- `deploy/desplegar.sh`: trae la versión, levanta Compose, ejecuta la ingesta y verifica `/health`
  por HTTPS;
- el flujo de GitHub Actions del monitor de `/health` cada 15 minutos.

**Parada al empezar el despliegue:** Rodolfo enciende la instancia `tg2-servidor` en la consola de
AWS, da el subdominio de DuckDNS y, cuando se le indique, copia el `.env` con el comando `scp` del
mensaje. Si el SSH falla porque cambió la IP de su casa, actualiza la regla de SSH del grupo de
seguridad `tg2-web`.

**Etiqueta:** `v0.9.0`.

**Cubre:** RNF-02, RNF-12 · Imágenes de contenedor, RNF-13, RNF-14, RNF-15 y el monitoreo de RNF-06.

### 8.14 B14 · Corrida 1

**Lee además:** secciones 6.9 y 6.10.

- Verifica los criterios de entrada de la sección 6.9 y reporta cada uno.
- Ejecuta la corrida 1 contra el sistema multiagente de IA desplegado: 1 ensayo por escenario, más
  los componentes. Todo va a `reports/corrida-1/`.
- En `reports/corrida-1/fallas.md`: cada falla con su causa técnica y su familia de MAST, y las
  correcciones propuestas en orden de impacto sobre la meta del 85 %.
- No corrige nada en este bloque.

### 8.15 Correcciones de la corrida 1

Se lanza con «Haz las correcciones de la corrida 1». En el orden de `reports/corrida-1/fallas.md`:
una rama `fix/<tema>` y un PR por falla o grupo pequeño, cada uno con su caso de regresión, las
pruebas unitarias y solo los escenarios afectados; cada PR se fusiona con el protocolo. Si una
corrección exige cambiar una decisión de la sección 2, es una parada. Al final, el despliegue se
actualiza con `deploy/desplegar.sh`.

### 8.16 B15 · Corrida 2, pruebas no funcionales y usabilidad

**Lee además:** secciones 6.4, 6.7, 6.8 y 6.10.

1. Las pruebas no funcionales de la sección 6.7, con la evidencia en `reports/no_funcionales/`.
2. Los formularios de usabilidad en `docs/usabilidad/`: `tareas.md` (las 5 tareas de la sección
   6.8), `sus.md` (las 10 afirmaciones, con una columna por evaluador) y `heuristica.md` (plantilla).
3. La corrida 2 (1 ensayo por escenario) en `reports/corrida-2/`.
4. El umbral de confianza propuesto con los datos de las corridas 1 y 2, con su justificación; los
   pesos no cambian sin consulta.
5. La muestra de calibración: 20 respuestas al azar de la corrida 2, sin el veredicto del juez, en
   `reports/calibracion/muestra.csv`, separada por comas, con columnas para Rodolfo, Dayanna y el
   consenso.

**Parada:** Rodolfo y Dayanna califican la muestra y aplican la usabilidad; Rodolfo aprueba el umbral
o da otro valor, y responde «listo». El mensaje incluye la dirección del sistema multiagente de IA
desplegado y qué archivo llenar.

**Después de la parada:** el umbral queda en `deploy/servidor.env` y en el valor por defecto de
`src/config.py`; luego `docs/resumenes/b15.md`, PR y fusión.

### 8.17 B16 · Corrida 3 final

**Lee además:** secciones 6.5, 6.9, 6.10 y 6.11.

- Confirma que no hay cambios de código desde la última fusión y anota el commit evaluado.
- Corrida 3: 3 ensayos por escenario, más componentes, RAGAS y las pruebas no funcionales que
  dependen del despliegue.
- El kappa con `reports/calibracion/muestra.csv` ya calificada; el SUS y las heurísticas con lo que
  quedó en `docs/usabilidad/`.
- `docs/reporte_de_pruebas.md` y la matriz de trazabilidad final (`reports/trazabilidad.md` y
  `.csv`), con la calificación de cada uno de los 65 requerimientos.
- El costo real de la corrida y del proyecto, con los tokens de `meta`.

**Etiqueta:** `v1.0.0`.

### 8.18 B17 · Informe para el chat de documentos

`docs/informe_final/` con:

1. el registro completo de cambios frente al documento de grado;
2. para el capítulo 4, un resumen por actividad de la fase 3 (base sintética, base de conocimiento e
   ingesta, orquestador y grafo, agentes con RAG, OCR, escalamiento, interfaz, observabilidad y
   despliegue): qué se construyó, qué RF y RNF cubre, cómo se verificó, cifras y capturas;
3. para el capítulo 5:
   - el plan de pruebas;
   - los resultados de las tres corridas;
   - las métricas, RAGAS, el juez, pass^k, la latencia y el costo;
   - el análisis de fallas;
   - la usabilidad;
   - la matriz de trazabilidad;
   - la comparación con Bahçeci y colaboradores;
4. las fuentes nuevas para la bibliografía;
5. la lista de figuras y capturas.

Las cifras salen solo de `reports/` y de `docs/resumenes/`, cada una con su archivo de origen. La
redacción va en pasado e impersonal, sin fechas exactas, con el proyecto siempre como «sistema
multiagente de IA» y los RF y RNF con su nombre corto.

---

## 9. Registro de cambios para el documento (semilla)

Se mantiene en `docs/cambios_para_documento.md` y se entrega completo en B17.

| Sección del documento | Qué dice hoy | Qué queda en el desarrollo | Estado |
|---|---|---|---|
| 1.5.2.1.3 (ejemplo de costo) | Sonnet 4.6 y Haiku 4.5, con tres llamadas por consulta | Sonnet 5.5 y Haiku 5.5, con dos o tres llamadas; el costo real se mide en el OE4 | Por medir |
| 1.5.2.8.3 | Respuestas de referencia de un experto tributario | Redactadas por los autores a partir de fuentes oficiales | Aprobado (ADR-22) |
| 1.6.4.1 | Reunión con las partes interesadas | Los resultados se presentan al director; Realtix no participa | Por confirmar con el equipo |
| 3.2, Anexos B y C (RF-ORQ-05 y RF-OCR-05) | Sonnet 4.6 en el orquestador y en el nodo de confianza; Haiku 4.5 en los agentes y en el OCR | Sonnet 5.5 en el orquestador; Haiku 5.5 en los agentes y en el OCR; nodo de confianza sin modelo | Aprobado (ADR-02 y ADR-03) |
| 3.4, Tabla 18 | La cobertura de alcance la verifica el modelo del nodo de confianza | Se deriva de la clasificación del orquestador y de lo que declara el agente | Aprobado (ADR-03) |
| 3.5 | Conversacion y CasoEscalado son propias del sistema multiagente de IA | Viven en PostgreSQL junto al checkpointer; la base sintética se abre en solo lectura | Aprobado (ADR-05) |
| 3.6 y Tabla 19 | Fragmentos de 400 a 800 tokens con solape; fuentes de la Tabla 19; manuales públicos de la OVT | Un fragmento por artículo de hasta 800 tokens, con solape solo en los largos; se suman el Acuerdo 780 de 2020 y la resolución de rangos de 2026; manual de la OVT simulada y glosario | Aprobado (ADR-04, ADR-19 y ADR-20) |
| 3.8 y Tabla 22 | Siete puntos de acceso REST | Los siete, más los de mensajes del widget, bandeja y sesión simulada | Aprobado |
| 3.9 y Tabla 23 | Proxy Nginx | Proxy Caddy con HTTPS automático y nombre en DuckDNS | Aprobado (ADR-09) |
| Fase 4 (rúbrica de usabilidad) | Aplicada a usuarios | SUS y evaluación heurística de los dos autores | Aprobado (ADR-21) |

---

## Anexo A. Matriz de verificación de los 65 requerimientos

Tipos de evidencia:

- **U:** prueba unitaria;
- **I:** prueba de integración;
- **E:** escenario de punta a punta;
- **M:** medición;
- **R:** revisión documentada.

La columna «Bloque» indica dónde se implementa.

| Requerimiento | Implementación | Evidencia | Bloque |
|---|---|---|---|
| RF-SYS-01 · Patrón Supervisor-Worker | Grafo de LangGraph con orquestador y agentes | U + R (figura exportada) | B4 |
| RF-SYS-02 · Alcance de solo lectura | Base de RealSit en solo lectura; sin puntos de acceso de escritura | U + M (huella antes y después) | B3 |
| RF-SYS-03 · Tributos y municipio cubiertos | Clasificación, marcas y factor de cobertura | E | B5 y B7 |
| RF-SYS-04 · Modelo sustituible | Modelo por nodo en variables de entorno | U + I | B5 |
| RF-SYS-05 · Adaptador equivalente a RealSit | Interfaz con dos implementaciones | U (contrato) | B3 |
| RF-SYS-06 · Aviso de interacción con IA (provisional) | Aviso en el widget y en `aviso_ia`; respuesta ante la pregunta por la IA | E (2) + R | B4, B7, B9 y B11 |
| RF-AUT-01 · Verificación de identidad | Token de la OVT simulada validado antes de cualquier dato personal | U + E | B9 |
| RF-AUT-02 · Restricción a predios propios | Filtro del adaptador; mensaje único para ajeno e inexistente | U + E | B3 y B9 |
| RF-AUT-03 · Consultas sin autenticación | Clasificación general o personal | E | B5 y B7 |
| RF-AUT-04 · Aviso de sesión requerida | Marca del orquestador y aviso de `nodo_general` | U + E | B4 y B7 |
| RF-ORQ-01 · Clasificación de la consulta | Salida estructurada con 5 categorías | U + M (componentes y sistema; kappa) | B7 |
| RF-ORQ-02 · Enrutamiento y consolidación | Transiciones y `nodo_respuesta` | U + E | B4 |
| RF-ORQ-03 · Consultas multiagente | `categorias_pendientes` y retorno al orquestador | U + E (3) | B4 |
| RF-ORQ-04 · Implementación en LangGraph | Grafo con ciclos y checkpointer en PostgreSQL | U + I | B4 |
| RF-ORQ-05 · Modelo de razonamiento | Sonnet 5.5 en el orquestador | R | B7 |
| RF-ORQ-06 · Prevención de bucles | Tope configurable de 2 | U | B4 |
| RF-IPU-01 · Consultas conceptuales de IPU | RAG sobre `normativa_ipu` | E + juez + RAGAS | B7 y B8 |
| RF-IPU-02 · Estado de cuenta e historial | Herramientas del adaptador (CA-01 a CA-06) | U + E | B3 y B7 |
| RF-IPU-03 · Liquidación estimada | Servicio con los datos de 2026 y de 2027 | U (valores conocidos) + E | B5 |
| RF-IPU-04 · Plazos y descuentos | RAG sobre el calendario de 2026, la Ley 1995 y el Acuerdo 1084 | E + juez | B7 y B8 |
| RF-IPU-05 · Citación de la norma | Metadatos por artículo e instrucciones del prompt | M (cita presente y coherente) + juez | B7 y B8 |
| RF-ICA-01 · Consultas conceptuales de ICA | RAG sobre `normativa_ica` | E + juez + RAGAS | B7 y B8 |
| RF-ICA-02 · Estimación por actividad | Servicio con las tarifas de 2026 y de 2027 | U + E | B5 |
| RF-ICA-03 · Fechas de declaración | Calendario y régimen por año | U + E | B5 |
| RF-ICA-04 · Retenciones fuera de alcance | Detección y escalamiento | E | B7 |
| RF-GEN-01 · Consultas transversales | RAG sobre `plataforma_general` y `normativa_datos` | E + juez | B7 y B8 |
| RF-GEN-02 · Explicación en lenguaje sencillo | Prompts y glosario | E + juez (claridad) | B7 |
| RF-GEN-03 · Respuesta sustentada en fuentes | Respuesta solo con los fragmentos | M (fidelidad de RAGAS y alucinación del juez) | B7 y B8 |
| RF-GEN-04 · Detección de fuera de alcance | `nodo_general` informa sin escalar | E | B4 y B7 |
| RF-OCR-01 · Carga de archivos | JPG, PNG o PDF de hasta 5 MB | U + E | B9 y B10 |
| RF-OCR-02 · Extracción de campos | Haiku 5.5 con visión y salida estructurada | M (exactitud por campo) | B10 |
| RF-OCR-03 · Confirmación de datos extraídos | Confirmación en varios turnos y contraste con el adaptador | E | B10 |
| RF-OCR-04 · Rechazo de documentos ilegibles | Diagnóstico de legibilidad y de tipo | M (variantes degradadas) | B10 |
| RF-OCR-05 · Modelo de visión | Haiku 5.5 | R | B10 |
| RF-OCR-06 · Plantilla sintética de recibo | Generador con la leyenda | R + M | B10 |
| RF-ESC-01 · Cálculo del nivel de confianza | Servicio de 3 factores (ADR-17) | U (casos límite) | B5 |
| RF-ESC-02 · Activación del escalamiento | Transiciones y marcas | U + E | B4 y B7 |
| RF-ESC-03 · Resumen del caso | Resumen sin modelo, en texto y JSON; bandeja de solo lectura | U + E + R | B5 y B9 |
| RF-ESC-04 · Tiempo de entrega del resumen | Medido en cada escalamiento | M (p95 menor a 5 s) | B5 y B12 |
| RF-ESC-05 · Notificación al contribuyente | Estado `escalada` y aviso en el widget | E + R | B7, B9 y B11 |
| RF-UI-01 · Widget embebible | Script e iframe en la OVT simulada | R (capturas) | B11 |
| RF-UI-02 · Contexto de la sesión | Checkpointer por conversación | U + E | B4 y B9 |
| RF-UI-03 · Identificación del interlocutor | Campo `interlocutor` e indicador del widget | E + R | B9 y B11 |
| RF-UI-04 · Carga desde la conversación | Botón de adjuntar hacia `/chat/documento` | E + R | B10 y B11 |
| RF-OBS-01 · Traza del flujo entre agentes | LangSmith con metadatos | R (capturas) | B5 |
| RF-OBS-02 · Matriz de confusión de enrutamiento | Registro de interacciones y etiquetas de escenario en `/admin/metricas` | M | B9 y B12 |
| RF-OBS-03 · Métricas de precisión y tiempo | Igual que RF-OBS-02 | M | B9 y B12 |
| RF-OBS-04 · Actualización de la base vectorial | Reingesta; reconstrucción de BM25 | I | B8 |
| RF-OBS-05 · Ejecución repetible de pruebas | Ejecutor, escenarios versionados, semilla y reloj fijo | M | B3 y B12 |
| RNF-01 · Tiempo de respuesta | Medido por escenario | M (p50 y p95) | B7 y B12 |
| RNF-02 · Escalamiento horizontal | Backend sin estado y réplicas | M | B13 |
| RNF-03 · Protección de datos personales | Minimización, sesión, HTTPS y disco cifrado | U + R (Ley 1581) | B5, B9 y B13 |
| RNF-04 · Uso exclusivo de datos sintéticos | Solo el generador; sin ruta a datos reales | R | B3 |
| RNF-05 · Registro auditable | Registro sin datos personales y anonimizador | U + M (prueba de trazas) | B5 y B12 |
| RNF-06 · Horario de atención | Horario, festivos y monitor de `/health` | U + M | B5, B9 y B13 |
| RNF-07 · Aviso fuera de horario | Respuesta informativa | U + E | B9 y B11 |
| RNF-08 · Tiempos de espera y degradación | Tiempo máximo, un reintento y escalamiento | U + M (fallas inyectadas) | B5 |
| RNF-09 · Lenguaje accesible | Prompts | M (claridad del juez) + R (SUS) | B7 |
| RNF-10 · Portabilidad del modelo | Igual que RF-SYS-04 | U + I | B5 |
| RNF-11 · Código versionado | Repositorio en GitHub | R | B1 |
| RNF-12 · Imágenes de contenedor | Dockerfile multietapa | R | B13 |
| RNF-13 · Orquestación con Compose | Un solo `docker-compose.yml` | M (levanta en una máquina limpia) | B1 y B13 |
| RNF-14 · Configuración por entorno | pydantic-settings y gitleaks | U + R | B1 y B5 |
| RNF-15 · Volúmenes persistentes | Volúmenes con nombre | M (reinicio) | B13 |
| RNF-16 · Tasa de respuestas correctas | Juez y verificaciones de código sobre los 60 escenarios | M (85 % o más, con intervalo y pass^3) | B12 a B16 |

---

## Anexo B. Fuentes

**Normativa** (enlaces de la sección 8 de la adenda, salvo los marcados):

| Fuente | Enlace |
|---|---|
| Ley 1581 de 2012 | http://www.secretariasenado.gov.co/senado/basedoc/ley_1581_2012.html |
| Decreto 1074 de 2015 | https://normativa.colpensiones.gov.co/colpens/docs/decreto_1074_2015.htm |
| Ley 14 de 1983 | Conseguir el texto vigente compilado (la adenda advierte que el enlace del DANE es el original) |
| Ley 44 de 1990 | https://www.cancilleria.gov.co/sites/default/files/Normograma/docs/ley_0044_1990.htm |
| Decreto Ley 1421 de 1993 | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=106394 |
| Decreto 474 de 2016 | https://www.ambitojuridico.com/sites/default/files/BancoMedios/Archivos/d-474-16.pdf |
| Decreto Distrital 807 de 1993 | https://bogota.gov.co/sites/default/files/tys/2021/01/DECRETO_807_1993.pdf (preferir una versión compilada del Régimen Legal de Bogotá) |
| Decreto Distrital 352 de 2002 | https://cancilleria.gov.co/sites/default/files/Normograma/docs/d_alcabog_0352_2002.htm |
| Ley 1819 de 2016 | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=79140 |
| Ley 1995 de 2019 | https://www.igac.gov.co/sites/default/files/transparencia/normograma/ley_1995_de_2019.pdf |
| Ley 2294 de 2023 | https://cancilleria.gov.co/sites/default/files/Normograma/docs/ley_2294_2023.htm |
| Resolución SDH-000195 de 2025 | https://www.haciendabogota.gov.co/es/normatividad/resolucion-sdh-000195-del-12-de-diciembre-de-2025 |
| Acuerdo 1084 de 2026 | Copia del texto firmado publicada por el INCP (enlace en la adenda); PDF escaneado |
| Acuerdos 648 de 2016, 105 de 2003 (art. 2), 65 de 2002 (art. 3) y 780 de 2020 (art. 3) | Régimen Legal de Bogotá |
| Resolución de rangos del predial 2026 (ADR-20) | https://incp.org.co/wp-content/uploads/2025/12/Resolucion-000194-de-2025-SDH.pdf; confirmar el número oficial en el Registro Distrital |
| Circular Externa 002 de 2024 de la SIC (opcional) | Enlace en la adenda |

**Técnicas** (consultadas en octubre de 2026):

- deprecaciones, precios, migración a Sonnet 5.5 y Haiku 5.5, esfuerzo y salidas estructuradas en
  platform.claude.com;
- documentación de Claude Code en code.claude.com;
- `langchain-anthropic` 1.7.6 y `ragas` 0.4.3 en PyPI;
- búsqueda híbrida de Chroma (solo en Chroma Cloud);
- HTTPS automático de Caddy;
- plan Free de AWS y tipos de EC2 elegibles.
