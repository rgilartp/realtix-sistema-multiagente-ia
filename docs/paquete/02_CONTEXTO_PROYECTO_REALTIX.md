# Contexto del proyecto — Sistema Multiagente de IA para Realtix (v3)

> **Cómo usar este documento:** súbelo al inicio de una conversación nueva con Claude,
> junto con los otros archivos del paquete. Contiene todo lo decidido y construido
> hasta ahora, para continuar sin repetir trabajo ni contradecir decisiones tomadas.
>
> **Estado (v3, octubre de 2026):** OE1 y OE2 completados, con la versión 2 de
> ambos documentos ya aplicada (20 páginas cada uno). OE3: solo existe 6.3.1 (base
> sintética y adaptador), con correcciones pendientes, y el plan de desarrollo está
> definido. El documento final del trabajo de grado está en redacción en el chat de
> documentos. **Lo que sigue es el Paso 1 del plan: el esqueleto del repositorio.**

---

## Cambios de esta versión del contexto

**v3 (octubre de 2026).** Reúne lo decidido después de la revisión técnica de septiembre de 2026:

- El paquete se reorganizó (sección 0) y los documentos FINAL ya contienen la versión 2.
- D4 incluye el volumen del conjunto sintético: 500 predios con 4 vigencias de IPU (2023 a
  2026), es decir, 2.000 obligaciones de IPU (sección 4).
- `nodo_escalamiento` no invoca un modelo: el resumen del caso se arma a partir del estado,
  como establece el plan (Paso 4) para cumplir los 5 segundos de RF-ESC-04, y como refleja la
  sección 8.3 de arquitectura, que no le asigna modelo. La v2 de este contexto decía, por
  error, Haiku 4.5 (sección 5.1).
- Se agregan las metas de los agentes, tal como quedaron en el documento final (sección 5.9).
- El capítulo de desarrollo del documento final se escribe con los resúmenes que entregue el
  chat de desarrollo al cerrar cada paso (sección 10).
- El código de 6.3.1 se volvió a verificar en octubre de 2026 y tiene observaciones nuevas
  (sección 11 y `codigo_6.3.1/realtix-mvp/ESTADO_DEL_CODIGO.md`).
- La condición de la transición confianza → orquestador ahora copia la de la Tabla 2 de
  arquitectura: la v2 de este contexto omitía que la respuesta parcial debe alcanzar el umbral.
  Se listan cuatro casos de enrutamiento que el Paso 3 debe precisar (sección 5.2).
- Se señala que dos normas del documento de requerimientos no tienen colección asignada
  (sección 5.6) y se registran las fechas de retiro tentativas de los modelos (sección 11).

**v2 (septiembre de 2026).** Incorporó la revisión técnica (detalle y evidencia en
`04_REVISION_Y_HALLAZGOS.md`): el contrato del adaptador (7 métodos), el grafo (8 transiciones,
con ciclo), el estado compartido (14 campos), las reglas del nivel de confianza, el tratamiento
de las consultas fuera de alcance, la normativa de las colecciones y la estructura del
repositorio. Las decisiones D1 a D4 se registran en la sección 4.

No cambian: 48 RF, 16 RNF, 18 HU, 8 nodos, 4 colecciones y 4 contenedores.

---

## 0. Qué hay en este paquete

| Archivo | Para qué sirve |
|---|---|
| `00_LEEME_PRIMERO.md` | Índice del paquete, orden de lectura y qué cambió |
| `01_PROMPT_INICIAL.md` | Mensaje con el que se abre el chat de desarrollo |
| `02_CONTEXTO_PROYECTO_REALTIX.md` | Este documento |
| `03_PLAN_DESARROLLO_OE3.md` | Plan de desarrollo del OE3 en 11 pasos (versión 2) |
| `04_REVISION_Y_HALLAZGOS.md` | Revisión técnica de septiembre de 2026: verificaciones, hallazgos y evidencia |
| `05_COMPARACION_Y_MEJORAS.md` | Comparación con una tesis de referencia del mismo director |
| `documentos/Requerimientos_OE1_Realtix_FINAL.docx` y `.md` | 20 páginas. Los 48 RF, 16 RNF y 18 HU (versión 2) |
| `documentos/Arquitectura_OE2_Realtix_FINAL.docx` y `.md` | 20 páginas. Grafo, capas, datos, RAG, seguridad, contenedores (versión 2) |
| `figuras/` | Las 3 figuras del documento de arquitectura (versión 2) |
| `codigo_6.3.1/realtix-mvp/` | El código que existe hoy (actividad 6.3.1) y su `ESTADO_DEL_CODIGO.md` |

---

## 1. Qué es el proyecto

Trabajo de grado de Ingeniería de Sistemas y Computación, Universidad Católica de
Colombia, 2026.

**Autores:** Rodolfo Angel Gilart Pulido y Dayanna Liceth Varón Puerto
**Director:** MsC. Juan Carlos Barrero Calixto

**Título (TG2):** Sistema multiagente de inteligencia artificial para soporte en procesos
de facturación de Realtix (13 palabras, dentro del límite de la plantilla).

Realtix (marca de Realidad 5.0) vende **RealSit**, una plataforma de administración
tributaria territorial que liquida, notifica y recauda impuestos municipales. Tiene
un entorno privado para funcionarios y uno público, la **Oficina Virtual Tributaria
(OVT)**, para el contribuyente.

El problema: el chatbot actual de la OVT responde con plantillas fijas y deriva casi
todo a atención humana, lo que satura el servicio en los picos de facturación predial.

**Objetivo general:** implementar un sistema multiagente de IA para el soporte del
proceso de facturación de Realtix, a partir de un framework de orquestación, una base
de conocimiento en un RAG y la integración de un LLM.

---

## 2. Estado y siguiente paso

| Objetivo | Descripción | Estado |
|---|---|---|
| **OE1** | Definir los requerimientos | **Completado** |
| **OE2** | Diseñar la arquitectura | **Completado** |
| **OE3** | Desarrollar el sistema | **En curso** — 6.3.1 hecha; plan en `03_PLAN_DESARROLLO_OE3.md` |
| **OE4** | Evaluar el desempeño | Pendiente |

**Fecha límite registrada:** sistema multiagente de IA funcional en octubre de 2026. El calendario
del plan (semanas 9 a 12) lo reemplaza el orden de bloques de la especificación técnica.

### Actividades de la Fase 3

| # | Actividad | Estado |
|---|---|---|
| 6.3.1 | Base de datos sintética | **Hecha** (correcciones en el Paso 2 del plan) |
| 6.3.2 | Curaduría de la base de conocimiento documental | Pendiente |
| 6.3.3 | Ingesta y vectorización | Pendiente |
| 6.3.4 | Agente orquestador | Pendiente |
| 6.3.5 | Agentes especializados con RAG | Pendiente |
| 6.3.6 | Agente OCR | Pendiente |
| 6.3.7 | Mecanismo de escalamiento | Pendiente |
| 6.3.8 | Interfaz conversacional embebible | Pendiente |
| 6.3.9 | Observabilidad | Pendiente |
| 6.3.10 | Despliegue | Pendiente |

Equivalencia con el cronograma: 6.3.1 a 6.3.10 corresponden a las actividades 14 a 23
(semanas 7 a 12).

**Siguiente paso recomendado:** Paso 1 del plan (esqueleto del repositorio), luego la
migración de 6.3.1 con correcciones (Paso 2) y el grafo con nodos simulados (Paso 3).

---

## 3. Restricciones que explican las decisiones

1. **No hay acceso a RealSit** — ni al ambiente ni a su documentación privada. Por eso
   todo se construye contra un adaptador con datos sintéticos.
2. **Hay acuerdo de confidencialidad** — no se procesan datos reales de contribuyentes
   (RNF-04).
3. **El equipo decide por su cuenta** — no se espera validación de Realtix para
   avanzar.
4. **El sistema multiagente de IA es de solo lectura** — no paga, no escribe en sistemas
   de Realtix, no tramita nada (RF-SYS-02).

---

## 4. Decisiones ya tomadas (no reabrir sin motivo)

| Tema | Decisión |
|---|---|
| Municipio piloto | Bogotá D.C. |
| Tributos del MVP | IPU e ICA. Fuera: retenciones de ICA y otros tributos locales |
| Framework | LangGraph (se descartó CrewAI por menor control sobre transiciones y checkpoints) |
| Modelo del orquestador y del nodo de confianza | Claude Sonnet 4.6 |
| Modelo de agentes de ejecución y OCR | Claude Haiku 4.5 |
| Base vectorial | ChromaDB |
| Embeddings | text-embedding-3-large |
| Memoria de sesión | PostgreSQL como checkpointer de LangGraph |
| Observabilidad | LangSmith |
| Backend | FastAPI |
| Interfaz | Widget JavaScript embebible en la OVT |
| Autenticación | Delegada en la sesión existente de la OVT |
| Horario de atención | 8:00 a. m. – 5:00 p. m., días hábiles |
| Empaquetado | Contenedores OCI con Docker Compose |
| Nube del MVP | AWS (donde opera RealSit), sin quedar atado al proveedor |
| Evaluación | LLM-as-judge + revisión de los autores |
| Contrato del adaptador (D1) | 7 métodos: se agrega `get_predios_contribuyente` |
| Topología del grafo (D2) | 8 nodos y 8 transiciones: retorno al orquestador y escalamiento directo desde él |
| Consultas fuera de alcance (D3) | No tributarias: se informan sin escalar. Tributarias excluidas del MVP: se escalan |
| Consulta de un predio ajeno (D3) | Rechazo explícito, sin revelar datos y sin escalar |
| Datos sintéticos (D4) | IDs reproducibles, un ICA por contribuyente y vigencia, casos pendientes y en mora, IPU mínimo 5 por mil; 500 predios y 4 vigencias de IPU (2023 a 2026) = 2.000 facturas de IPU |
| Python de desarrollo | 3.12, igual que el contenedor |

---

## 5. Arquitectura

### 5.1 Los 8 nodos del grafo

Patrón **Supervisor-Worker** sobre un grafo de estados de LangGraph.

| Nodo | Tipo | Responsabilidad | Modelo |
|---|---|---|---|
| `nodo_orquestador` | Supervisor | Clasifica, planifica consultas multiagente y enruta; retoma el control tras cada respuesta parcial | Sonnet 4.6 |
| `nodo_ipu` | Worker | Predial: consultas, estado de cuenta, liquidación | Haiku 4.5 |
| `nodo_ica` | Worker | Industria y comercio: consultas y estimación | Haiku 4.5 |
| `nodo_general` | Worker | Normativa transversal y uso de la plataforma; informa lo no tributario fuera de alcance | Haiku 4.5 |
| `nodo_ocr` | Worker | Extrae campos del recibo predial | Haiku 4.5 |
| `nodo_confianza` | Evaluador | Calcula el nivel de confianza | Sonnet 4.6 |
| `nodo_escalamiento` | Worker | Genera el resumen del caso a partir del estado y lo registra | — (sin modelo; RF-ESC-04) |
| `nodo_respuesta` | Consolidador | Formato final y entrega a la interfaz | — (si consolidar una respuesta multiagente requiere un modelo, Sonnet 4.6, según RF-ORQ-05) |

### 5.2 Transiciones

| Transición | Tipo | Condición |
|---|---|---|
| orquestador → ipu \| ica \| general \| ocr | Condicional | Categoría clasificada; lo no tributario va a `general`, que informa que no está cubierto |
| orquestador → escalamiento | Condicional | Solicitud explícita, tributario fuera de alcance, tope de reclasificaciones o fallo del orquestador |
| workers → confianza | Fija | Toda respuesta pasa por evaluación |
| confianza → orquestador | Condicional | La respuesta parcial alcanza el umbral y quedan categorías pendientes de una consulta multiagente, o el worker declaró que la consulta no corresponde a su dominio y no se ha alcanzado el máximo de reclasificaciones |
| confianza → respuesta | Condicional | Confianza ≥ umbral y sin categorías pendientes |
| confianza → escalamiento | Condicional | Confianza < umbral, fallo reportado por el worker o tributario fuera de alcance detectado por el worker |
| escalamiento → END | Fija | El resumen se entrega al funcionario |
| respuesta → END | Fija | Respuesta consolidada a la interfaz |

Las condiciones son las de la Tabla 2 de arquitectura v2, que rige. Cuatro casos quedan por
precisar en el Paso 3, sin agregar transiciones (D2), con una propuesta que el equipo aprueba:

- **Aviso de sesión requerida (RF-AUT-04):** la sección 6.1 dice que el orquestador informa que
  hay que iniciar sesión, pero no existe una transición orquestador → respuesta.
- **Predio ajeno (D3):** el rechazo no se escala, pero la sección 3.4 solo exceptúa del
  escalamiento las aclaraciones y lo no tributario.
- **"No corresponde" con el tope de reclasificaciones alcanzado:** la Tabla 2 solo cubre el caso
  en que el tope no se ha alcanzado.
- **Consulta multiagente escalada:** la regla 3 de la sección 3.4 pide entregar las partes ya
  resueltas junto con el aviso de transferencia, y escalamiento → END no pasa por
  `nodo_respuesta`.

### 5.3 Estado compartido (`AgentState`)

| Campo | Tipo | Descripción |
|---|---|---|
| `messages` | `list[Message]` | Historial de la sesión; persiste vía checkpointer |
| `categoria` | `str` | `ipu` \| `ica` \| `general` \| `ocr` \| `fuera_de_alcance` |
| `datos_extraidos` | `dict` | Campos identificados por el worker o el OCR |
| `nivel_confianza` | `float` | Puntaje de 0.0 a 1.0 |
| `requiere_escalamiento` | `bool` | Activa la transición al escalamiento |
| `resumen_caso` | `str` | Resumen estructurado para el funcionario |
| `id_conversacion` | `str` | Clave del checkpointer |
| `contribuyente_id` | `Optional[str]` | Contribuyente autenticado; vacío sin sesión |
| `predios_autorizados` | `list[str]` | Contexto autorizado (sección 6.1 de arquitectura) |
| `categorias_pendientes` | `list[dict]` | Partes pendientes de una consulta multiagente |
| `intentos_clasificacion` | `int` | Reclasificaciones de la conversación (tope configurable) |
| `respuestas_parciales` | `list[dict]` | Respuesta, fuentes, similitud y suficiencia de cada worker |
| `motivo_escalamiento` | `Optional[str]` | Causa del escalamiento |
| `documento_adjunto` | `Optional[dict]` | Referencia al archivo para OCR, nunca su contenido |

Ciclo de vida: se conservan entre turnos `messages`, `id_conversacion`, `datos_extraidos`,
`resumen_caso` e `intentos_clasificacion`; la capa de acceso fija `contribuyente_id` y
`predios_autorizados` en cada solicitud; el resto se reinicia en cada turno.

### 5.4 Separación de capas (importante antes de escribir código)

Cada capa tiene una responsabilidad **y una restricción explícita**:

| Capa | Responsabilidad | Restricción |
|---|---|---|
| **Nodos** | Orquestan el flujo: leen y escriben el estado e invocan servicios | No contienen lógica de dominio tributario |
| **Servicios** | Lógica de dominio: liquidación estimada, cálculo de confianza, armado del resumen | No conocen LangGraph ni el estado del grafo |
| **Adaptador de datos** | Único punto de acceso a la fuente de datos del contribuyente | No contiene reglas tributarias |
| **Integraciones** | Clientes de modelos, base vectorial y observabilidad | No contienen lógica de dominio |
| **Contenedor de dependencias** | Construye los servicios una vez y los inyecta en los nodos | Es el único que conoce las implementaciones concretas |

**Por qué importa:** si la liquidación del IPU o el cálculo de confianza se escriben
dentro de los nodos, no se pueden probar sin levantar el grafo entero. Esta regla es
lo que permite que el adaptador sea sustituible (RF-SYS-05) y que el modelo se cambie
por configuración (RF-SYS-04).

### 5.5 Cálculo del nivel de confianza

Puntaje compuesto de 0.0 a 1.0, contra un umbral configurable que se calibra en la
Fase 4:

- **Similitud de recuperación** — promedio de similitud de los fragmentos de ChromaDB
- **Suficiencia declarada** — el agente reporta si respondió completo, parcial o no pudo,
  o si necesita aclaración o la consulta no le corresponde
- **Cobertura de alcance** — verifica que sea IPU o ICA en Bogotá D.C. (la evalúa Sonnet 4.6)

Reglas (sección 3.4 de arquitectura v2): sin fragmentos recuperados (respuestas solo con datos
del adaptador) el factor de similitud no aplica y se renormaliza; una pregunta de aclaración es
respuesta válida y no escala; "no corresponde" devuelve la consulta al orquestador; en una
consulta multiagente basta una parte bajo el umbral para escalar; lo no tributario no se escala.
Pesos y umbral son configurables y se calibran en la Fase 4.

### 5.6 Pipeline RAG — recuperación híbrida

**Ingesta** (una vez por documento): carga → segmentación en 400–800 tokens con
solape de 50–100 → embeddings con text-embedding-3-large → ChromaDB con índice HNSW.

**Recuperación** (en cada consulta): búsqueda **vectorial** + búsqueda **léxica**,
ambas filtradas por colección, fusionadas, y se seleccionan los mejores fragmentos.

> La búsqueda léxica no es opcional en este dominio: la semántica puede no recuperar
> el fragmento que dice literalmente "Ley 44 de 1990" o "artículo 354", que es
> justamente lo que el agente necesita para citar la norma.

Cuatro colecciones separadas:

| Colección | Contenido | Agente |
|---|---|---|
| `normativa_ipu` | Ley 44 de 1990 (con el art. 23 de la Ley 1450 de 2011), Ley 1995 de 2019, Decretos 352 de 2002 y 807 de 1993, acuerdos del Concejo | `nodo_ipu` |
| `normativa_ica` | Ley 14 de 1983, Decretos 352 de 2002 y 807 de 1993, acuerdos del Concejo | `nodo_ica` |
| `normativa_datos` | Ley 1581 de 2012 y decretos reglamentarios | `nodo_general` |
| `plataforma_general` | Manuales de la OVT y glosario | `nodo_general` |

La Ley 1819 de 2016 (artículo 354, sistema de facturación) y el Decreto Ley 1421 de 1993
(Estatuto Orgánico de Bogotá) figuran en la normativa del documento de requerimientos (sección
7), pero la Tabla 6 de arquitectura no los asigna a ninguna colección. Se decide en la curaduría
(6.3.2), antes del Paso 6.

### 5.7 Contenedores

| Contenedor | Responsabilidad | Imagen base | Volumen |
|---|---|---|---|
| `proxy` | Terminación TLS y enrutamiento | Nginx | — |
| `backend` | API REST, control de acceso y grafo | Python 3.12 · FastAPI · LangGraph | `datos-sinteticos` |
| `chromadb` | Base de conocimiento vectorial | `chromadb/chroma` | `chroma-data` |
| `postgres` | Memoria de sesión | `postgres:16` | `postgres-data` |

Configuración por variables de entorno, sin valores fijos en el código. Solo `proxy`
queda expuesto al exterior.

### 5.8 Endpoints del backend

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/api/v1/chat/mensaje` | Recibe un mensaje e invoca el grafo |
| POST | `/api/v1/chat/documento` | Recibe imagen o PDF para el `nodo_ocr` |
| GET | `/api/v1/predios/{predio_id}/estado-cuenta` | Estado de cuenta |
| GET | `/api/v1/predios/{predio_id}/pagos` | Historial de pagos |
| POST | `/api/v1/escalamiento` | Registra un caso escalado |
| GET | `/api/v1/admin/metricas` | Métricas de enrutamiento y tiempo |
| GET | `/health` | Estado del servicio e inicialización de agentes |

### 5.9 Metas de los agentes

Los requerimientos se derivaron de la meta de cada agente (capítulo 2 del documento final).
Sirven de guía para redactar los prompts de sistema y para decidir qué hace cada nodo:

| Agente | Meta | Grupo de RF |
|---|---|---|
| Agente orquestador | Dirigir cada consulta al agente especializado capaz de resolverla | RF-ORQ |
| Agente especializado en IPU | Dar al contribuyente la información necesaria sobre su impuesto predial: cuánto debe, por qué y hasta cuándo | RF-IPU |
| Agente especializado en ICA | Orientar al contribuyente sobre sus obligaciones de industria y comercio y estimar su valor | RF-ICA |
| Agente de información general | Resolver las dudas transversales e informar con claridad lo que el sistema no cubre | RF-GEN |
| Agente de extracción OCR | Extraer con exactitud los datos del recibo predial que carga el contribuyente | RF-OCR |
| Mecanismo de escalamiento | Garantizar que ninguna consulta quede sin una respuesta confiable, transfiriendo a un funcionario lo que el sistema no resuelve | RF-ESC |

---

## 6. Estructura del repositorio (a seguir al desarrollar)

```
src/
  config.py         Configuración leída de variables de entorno (RNF-14)
  container.py      Contenedor de dependencias: construye e inyecta servicios
  agents/
    nodes/          Un archivo por nodo del grafo, con su prompt asociado
    graph.py        Definición del grafo: nodos, aristas y transiciones
    state.py        AgentState, el estado compartido
  services/         Lógica de dominio, independiente de LangGraph (incluye tarifas.py)
  data/
    adapter.py      RealSitAdapter y su implementación sintética
    models.py       Entidades y tipos de retorno del adaptador
    database.py     Esquema SQLite del conjunto sintético
    generate_synthetic_data.py   Generador (python -m src.data.generate_synthetic_data)
  integrations/     Clientes de modelos, base vectorial y observabilidad
  api/              Aplicación FastAPI, endpoints y control de acceso
knowledge_base/     Corpus normativo para las colecciones vectoriales
tests/              Pruebas por dominio, organizadas como el código
```

El código de 6.3.1 se migra en el Paso 2 del plan: `models.py`, `database.py`, `adapter.py`
y `generate_synthetic_data.py` pasan a `src/data/`; la tabla de tarifas pasa a
`src/services/tarifas.py`, fuente única para el generador y la liquidación estimada; las
verificaciones de `demo.py` se convierten en `tests/data/test_adapter.py`. Imports absolutos
desde la raíz (`from src.data.adapter import ...`).

---

## 7. El código que ya existe

Solo la actividad 6.3.1. **No hay ningún agente ni grafo todavía.** Está en
`codigo_6.3.1/realtix-mvp/`; su estado detallado, la verificación de octubre de 2026 y las
fallas pendientes están en `ESTADO_DEL_CODIGO.md`, en la misma carpeta.

```
realtix-mvp/
  models.py                     6 entidades + tipos de retorno del adaptador
  database.py                   Esquema SQLite con claves foráneas
  generate_synthetic_data.py    Genera datos con Faker (es_CO)
  adapter.py                    RealSitAdapter + MockRealSitAdapter (6 de los 7 métodos)
  demo.py                       Verificación del contrato de punta a punta
  requirements.txt              Solo Faker
  README.md                     Guía de instalación en VS Code
  ESTADO_DEL_CODIGO.md          Estado, verificación y fallas pendientes
  data/realtix_sintetico.db     Base generada (no viene en el paquete: se regenera)
```

### Cómo correrlo

```bash
python -m venv venv
venv\Scripts\activate            # Windows;  source venv/bin/activate en Mac/Linux
pip install -r requirements.txt
python generate_synthetic_data.py --contribuyentes 150 --seed 42
python demo.py
```

Con la semilla 42 genera: **150 contribuyentes, 170 predios, 434 obligaciones,
317 pagos.**
Son las cifras de la versión actual, verificadas de nuevo en octubre de 2026 con
Python 3.12 y Faker 40.38.0. Con D4, el Paso 2 genera 500 predios con 4 vigencias de IPU
(2023 a 2026), es decir, 2.000 obligaciones (facturas) de IPU; el número de contribuyentes,
las vigencias y obligaciones de ICA y los pagos se reportan al terminar ese paso.

### El contrato del adaptador — lo que consumirán los agentes

```python
from adapter import MockRealSitAdapter
adapter = MockRealSitAdapter()

adapter.get_estado_cuenta(predio_id, contribuyente_id)      -> EstadoCuenta
adapter.get_historial_pagos(predio_id, contribuyente_id)    -> list[Pago]
adapter.get_avaluo_catastral(predio_id, contribuyente_id)   -> Avaluo
adapter.get_tarifa_ica(actividad_economica)                 -> Tarifa
adapter.get_obligaciones_vigentes(predio_id, contribuyente_id, tributo) -> list[ObligacionTributaria]
adapter.registrar_caso_escalado(resumen)                    -> Ack
adapter.get_predios_contribuyente(contribuyente_id)         -> list[Predio]  # D1: se agrega en el Paso 2
```

**Reglas:**
- Ningún agente toca SQL directamente. Todo pasa por el adaptador.
- Cada método que expone datos de un predio recibe el `contribuyente_id` autenticado
  y lanza `PredioNoAutorizadoError` si el predio no le pertenece (RF-AUT-02). Esto
  evita que alguien consulte la deuda de un tercero conociendo solo su matrícula
  catastral, que en Colombia es información pública. El rechazo se comunica con un
  mensaje explícito, sin revelar datos del predio y sin escalar (D3).
- Se consideran obligaciones vigentes las pendientes de pago (pendiente o vencido) de
  cualquier vigencia (sección 8.1 de arquitectura v2).
- El día que Realtix dé acceso real, se escribe otra clase que implemente la misma
  interfaz `RealSitAdapter` y los agentes no cambian (RF-SYS-05).

### Modelo de datos

Seis entidades: `Contribuyente`, `Predio`, `ObligacionTributaria`, `Pago`,
`Conversacion`, `CasoEscalado`. Las cuatro primeras replican lo que expondría
RealSit; las dos últimas son propias del sistema multiagente de IA.

---

## 8. Convenciones del proyecto

- **Siempre "sistema multiagente de IA"**, nunca "el sistema" o "la aplicación".
- **Identificadores:** `RF-<COMPONENTE>-<NN>` y `RNF-<NN>`. Componentes: `SYS`, `AUT`,
  `ORQ`, `IPU`, `ICA`, `GEN`, `OCR`, `ESC`, `UI`, `OBS`.
- **Cada requerimiento tiene un nombre corto** además de su descripción. Ejemplo:
  "RF-IPU-02 · Estado de cuenta e historial". Úsalo al referirte a ellos.
- **Redacción:** ISO/IEC/IEEE 29148:2018. Atómicos, verificables, con "deberá".
- **Toda tabla y figura lleva una línea "Fuente:" debajo.** Es requisito del formato
  de este director.
- **Estilo de documentos:** sobrio, sin colores ni líneas decorativas, tablas en
  blanco y negro. Tabla de contenido, lista de tablas y lista de figuras con páginas
  reales.
- **Numeración de tablas y figuras como texto fijo** ("Tabla 7. …"), no campos
  automáticos de Word.
- **Referencias cruzadas explícitas:** "Tabla 5" o "Sección 6.1", nunca un número
  suelto.
- **Al insertar una tabla, renumerar todas las referencias posteriores.** El documento de
  arquitectura v1 quedó con 14 números de tabla desfasados por no hacerlo.
- **Las figuras también llevan línea "Fuente:"**; las 3 de arquitectura v1 no la tenían.
- **Nunca un título inmediatamente debajo de otro**; los documentos v1 tenían 7 casos.

---

## 8b. KPI aprobados (redacción confirmada por el equipo)

| Objetivo | KPI | Meta |
|---|---|---|
| OE1 | Porcentaje del documento de requerimientos aprobado por Realtix | 100 % |
| OE2 | Porcentaje de documento del diseño de arquitectura | 100 % |
| OE3 | Porcentaje del sistema multiagente funcional | 100 % |
| OE4 | Porcentaje de escenarios de prueba superados | ≥ 85 % |

> El equipo confirmó la redacción del borrador del TG2 para el OE2 y el OE3 (difiere del
> TG.pdf). El resultado de los KPI del OE1 y el OE2 se reporta como «validado con el
> director», marcado en el documento para confirmar después con él.

**Decisiones sobre las observaciones de la revisión v2:**
- O-01: no se cambian los títulos ni el actor "Administrador del sistema".
- O-03: el KPI del OE2 se queda en 100 %, según el TG1.
- O-05: la referencia de RNF-16 se ajusta al integrar el documento principal.

**Cifra de adopción de IA:** 7,5 % de las empresas colombianas (MinTIC, nota de prensa de
agosto de 2024). El TG.pdf decía 18,5 % en el Resumen y en la sección 2.2; esa cifra
no aparece en la fuente citada y no debe usarse.

## 9. Cifras de los documentos (no contradecirlas)

- **48** requerimientos funcionales en 10 grupos:
  SYS 5 · AUT 4 · ORQ 6 · IPU 5 · ICA 4 · GEN 4 · OCR 6 · ESC 5 · UI 4 · OBS 5
- **16** requerimientos no funcionales
- **18** historias de usuario
- **8** nodos en el grafo
- **8** transiciones en el grafo (antes 6; D2)
- **14** campos en AgentState (antes 7; D2)
- **7** métodos en el contrato del adaptador (antes 6; D1)
- **4** colecciones en la base de conocimiento
- **4** contenedores
- Documento de requerimientos: **20 páginas, 24 tablas, 24 líneas "Fuente"** (versión 2)
- Documento de arquitectura: **20 páginas, 11 tablas, 3 figuras, 14 líneas "Fuente"** (versión 2)

---

## 10. Lo que falta y no es código

Lo que sigue no es código, pero condiciona lo que entrega el chat de desarrollo. Más detalle en
`05_COMPARACION_Y_MEJORAS.md`.

**El documento principal del trabajo de grado.** Está en redacción en el chat de documentos,
con capítulos que corresponden uno a uno con los objetivos: el 2 (requerimientos) y el 3
(arquitectura) ya están integrados; el 4 (desarrollo) y el 5 (evaluación) esperan resultados.
El capítulo 4 tiene una sección por actividad de la Fase 3: 4.1 base sintética y adaptador, 4.2
base de conocimiento e ingesta, 4.3 orquestador y grafo, 4.4 agentes especializados con RAG, 4.5
agente OCR, 4.6 escalamiento, 4.7 interfaz embebible, 4.8 observabilidad, 4.9 despliegue y 4.10
resultado frente al KPI del OE3. Se completa con los resúmenes que el chat de desarrollo entregue
al cerrar cada paso: qué se construyó, qué RF y RNF cubre y la evidencia de las pruebas. El
capítulo 5 reportará la matriz de confusión, la precisión, la exhaustividad y el F1 por
categoría, la tasa de alucinación y los tiempos de respuesta, así que el sistema multiagente de IA debe dejar esas
mediciones disponibles (Paso 10).

**El plan de pruebas del OE4.** Hoy solo está definido "LLM-as-judge y métricas de
enrutamiento", que es la mitad de lo que el director espera. Falta: manual de pruebas
con casos atados a IDs de requerimiento, manual de usuario, y rúbrica de usabilidad
tipo Likert aplicada a usuarios reales (el semillero Mailab es población disponible y
con precedente). Esquema de calificación sugerido: 100 % aprobado, 80 % aprobado con
observaciones, 0 % no aprobado. El presupuesto aprobado prevé 60 escenarios de prueba.

**Pruebas automatizadas.** Hoy no hay ninguna. Como mínimo, cubrir el enrutamiento
del orquestador, el cálculo de confianza y el control de acceso del adaptador. El plan
las cubre en los Pasos 2, 3 y 4.

Con D3, la categoría "fuera de dominio" del plan de pruebas del OE4 ya tiene resultado
esperado.

---

## 11. Notas técnicas

- **`demo.py` es idempotente** desde la última corrección: antes fallaba en la segunda
  corrida por usar IDs fijos. Ahora genera un sufijo único por ejecución.
- **El contrato del adaptador es la Tabla 7 del documento de arquitectura.** Las versiones
  anteriores del código y de este contexto la llamaban Tabla 5 por un desfase de
  numeración; en este paquete ya se corrigió en los comentarios y el README del código.
  La v1 no mostraba el `contribuyente_id`; la v2 lo incluye.
- **Correcciones pendientes del código de 6.3.1 (Paso 2):** H-01 a H-06, M-01, M-02, M-03
  y M-07 (detalle en `04_REVISION_Y_HALLAZGOS.md`), más las observaciones OC-01 a OC-08 de
  `ESTADO_DEL_CODIGO.md` (la mayoría van en el Paso 2; OC-05 en los Pasos 4 y 7, y OC-06 en
  los Pasos 5 y 8). Las que romperían la integración: una conexión por operación (hoy el
  adaptador falla si se usa desde otro hilo), registro de la conversación al escalar (hoy
  falla por la llave foránea), IDs derivados de la semilla (hoy `uuid4` los vuelve
  irrepetibles) y el registro de casos que escalan antes de calcular la confianza (OC-08).
- **Identificadores de los modelos:** según la página de deprecaciones de Anthropic,
  consultada en octubre de 2026, `claude-sonnet-4-6` está activo con retiro tentativo
  no antes de febrero de 2027, y `claude-haiku-4-5-20251001` está activo con retiro
  tentativo no antes de octubre de 2026. Anthropic avisa al menos 60 días antes de
  retirar un modelo. Hay que revisar esa página al iniciar y antes de la evaluación; si un
  modelo decidido entra en deprecación, se consulta al equipo antes de cambiarlo (el cambio
  es de configuración, RF-SYS-04):
  https://platform.claude.com/docs/en/about-claude/model-deprecations
- **Límites de la portabilidad:** la contenerización cubre cómputo y datos, pero las
  APIs de los modelos y LangSmith siguen siendo servicios externos, y el certificado
  TLS y el DNS hay que resolverlos con el equivalente de la nube destino o con el
  propio contenedor `proxy`. En AWS, para instalar un certificado de ACM en Nginx
  dentro de EC2 hay que emitirlo como certificado público exportable, que tiene costo y,
  según la documentación de AWS consultada en octubre de 2026, una vigencia de 198
  días.
- **El contrato de datos es una suposición.** Los 7 métodos son la mejor hipótesis del
  equipo sobre lo que RealSit podría exponer, no algo confirmado. Cuando haya acceso
  real hay que validar que calce; si no, el ajuste va solo en la clase nueva del
  adaptador.

---

## 12. Qué necesitaría Realtix para integrarlo

(Por si surge en la sustentación.)

1. Exponer los datos: API REST de solo lectura, o acceso a una réplica de su base
2. Un puente de autenticación para validar la sesión del contribuyente en la OVT
3. Insertar el `<script>` del widget en las páginas de la OVT
4. Un canal para recibir los casos escalados que hoy solo se registran localmente

Del lado del proyecto, lo único que cambia es la implementación del adaptador.
