# Comparación con el trabajo de grado de Felipe y Laura

> **Nota (octubre de 2026).** Este documento se escribió para el lado de documentos. Para el
> desarrollo importan la Parte 2 (separación de capas, estructura del repositorio, RAG híbrido y
> `/health`) y las secciones 3.3 y 3.4 (pruebas automatizadas y archivos del repositorio). Lo de
> la Parte 2 ya está en la arquitectura v2. La sección 3.1 ya está en curso: el documento
> principal se redacta con capítulos por objetivo.

Referencia: *Implementación de un agente de IA académico para el apoyo a estudiantes
en la gestión del tiempo, la planificación de actividades y la recomendación de
métodos de estudio personalizados* (Jaramillo Rodríguez, J. F. y Gutiérrez Pulido,
L. M., 2026). Repositorio: `github.com/JuanFe2608/academic_agent`.

**Por qué esta referencia sirve tanto:** mismo director (Juan Carlos Barrero
Calixto), mismo programa, misma universidad, mismo año, y además usa LangGraph,
FastAPI, PostgreSQL como checkpointer, RAG y Docker. Es prácticamente el formato
exacto que se espera de nosotros.

---

## Parte 1 — Diferencias de formato (ya corregidas)

| Aspecto | Felipe | Nosotros antes | Acción |
|---|---|---|---|
| Línea de fuente | Toda tabla y figura lleva "Fuente:" debajo | Solo algunas figuras | **Corregido:** 33 líneas de fuente añadidas |
| Columna de nombre | `ID / Tipo / Requerimiento / Descripción` | `ID / Descripción / Prioridad` | **Corregido:** columna "Nombre" en los 64 requerimientos |
| Listas de tablas y figuras | Sí, con página | Sí, con página | Ya coincidía |
| Numeración de capítulos | Arábiga, jerárquica | Igual | Ya coincidía |

La columna de nombre no es cosmética: permite referirse a un requerimiento como
"RF-IPU-02 Estado de cuenta e historial" en vez de leer el párrafo completo, y es lo
que hace legibles los casos de prueba del OE4.

---

## Parte 2 — Diferencias de fondo (ya aplicadas a la arquitectura)

### 2.1 Separación de capas — el hallazgo más importante

El repositorio de Felipe separa explícitamente:

> **Nodos** — orquestan el flujo; llaman servicios y actualizan estado. Sin lógica de
> negocio. **Servicios** — contienen toda la lógica de negocio del dominio.
> **Repositorios** — capa de acceso a datos. **AppContainer** — inyección de
> dependencias. **Integraciones** — clientes externos.

Nuestra arquitectura tenía bien resuelto el acceso a datos (el `RealSitAdapter` es
exactamente su capa de repositorios, con la misma idea de interfaz sustituible), pero
**no decía dónde vive la lógica de dominio**. Sin esa regla, la liquidación del IPU y
el cálculo de confianza terminan escritos dentro de los nodos, y entonces no se
pueden probar sin levantar el grafo entero.

**Aplicado:** nueva sección 3.6 con la tabla de capas, donde cada una tiene una
responsabilidad y una restricción explícita de lo que *no* le corresponde.

### 2.2 Estructura del repositorio

Felipe tiene `src/agents/nodes/` (un archivo por nodo con su prompt), `flows/`,
`agent.py`, `state.py`, `services/`, `repositories/`, `integrations/`, `api/`,
`knowledge_base/`, `tests/`.

**Aplicado:** nueva sección 3.7 con la estructura que vamos a seguir, alineada con
nuestras capas. Esto define dónde va cada archivo antes de escribir el primero.

### 2.3 RAG híbrido en vez de solo vectorial

Felipe combina búsqueda vectorial y léxica (top-k=8 por canal), las fusiona y
selecciona los 5 mejores fragmentos.

Nuestro pipeline era solo vectorial. **En el dominio tributario esto es un problema
real:** la búsqueda semántica puede no recuperar el fragmento que dice literalmente
"Ley 44 de 1990" o "artículo 354", que es justo lo que el agente necesita citar.

**Aplicado:** la sección 7 ahora describe recuperación híbrida y explica por qué.

### 2.4 Endpoint de salud

Felipe valida el despliegue con `/health` devolviendo
`{"status":"ok","agent":"ready"}`, y eso queda como evidencia en su capítulo de
desarrollo.

**Aplicado:** `/health` añadido a la tabla de endpoints.

---

## Parte 3 — Lo que falta hacer (no aplicado todavía)

### 3.1 El documento principal del trabajo de grado

**Este es el cambio estructural más grande y aún está pendiente.**

La tesis de Felipe es **un solo documento** donde los capítulos de desarrollo
corresponden uno a uno con los objetivos:

| Capítulo de Felipe | Corresponde a |
|---|---|
| 7. Construcción de la base de conocimiento | Su OE1 |
| 8. Diseño de la arquitectura | Su OE2 |
| 9. Desarrollo del MVP del agente | Su OE3 |
| 10. Evaluación de la calidad | Su OE4 |
| 11. Resultados y análisis de resultados | — |
| 13. Conclusiones | — |

Nosotros tenemos documentos separados (Requerimientos y Arquitectura). Eso está bien
como entregables de fase, pero **el documento final del trabajo de grado tiene que
integrarlos** con esa estructura de capítulos.

**Recomendación concreta:** en el documento principal, el capítulo de requerimientos
debe llevar solo la **tabla resumen por componente** (los 10 grupos con su conteo), y
los 48 requerimientos completos van a un **anexo**. Felipe hace exactamente eso: su
Tabla 2 tiene 5 RF y 3 RNF, y remite al Anexo C para el catálogo completo. Meter 48
requerimientos en el cuerpo del documento lo vuelve ilegible.

### 3.2 El plan de pruebas del OE4

Nuestro OE4 dice "LLM-as-judge y métricas de enrutamiento". Eso es la mitad. Felipe
usa **tres instrumentos** y su director claramente los espera:

1. **Manual de pruebas** — casos funcionales atados a IDs de requerimiento
2. **Manual de usuario** — guía para quien va a probar el sistema
3. **Rúbrica de evaluación** — preguntas Likert 1 a 5 aplicadas a usuarios reales

Su esquema de calificación de casos funcionales es simple y defendible:
**100% aprobado · 80% aprobado con observaciones · 0% no aprobado**, y de ahí sale un
porcentaje de cumplimiento global.

**Dato aprovechable:** Felipe evaluó con estudiantes del **semillero Mailab** — el
mismo semillero en el que está nuestro proyecto. Es una población de evaluación
disponible y con precedente aceptado.

**Recomendación:** diseñar el plan de pruebas con casos atados a nuestros RF (por
ejemplo `RF-IPU-02 Estado de cuenta`, `RF-AUT-02 Restricción a predios propios`),
mantener el LLM-as-judge para la calidad de las respuestas, y agregar la rúbrica de
usabilidad. El LLM-as-judge es un diferencial nuestro que Felipe no tiene; no hay que
quitarlo, hay que sumarle lo otro.

### 3.3 Pruebas automatizadas

Felipe tiene **98 archivos de tests** organizados por dominio (agent/routing,
scheduling, planning, RAG, integraciones, onboarding). Nosotros tenemos **cero**.

No hace falta llegar a 98, pero sí tener pruebas de las piezas críticas: el
enrutamiento del orquestador, el cálculo de confianza y el control de acceso del
adaptador. La estructura `tests/` ya quedó prevista en la sección 3.7.

### 3.4 Otras cosas menores del repositorio de Felipe que vale la pena copiar

- **`.env.example`** con todas las variables documentadas y sin valores reales
- **Dockerfile multi-stage** para que la imagen final sea liviana
- **`langgraph.json`** para configuración del grafo
- **README con diagramas ASCII** del grafo y del pipeline RAG — muy útil para el jurado

---

## Parte 4 — Dónde estamos mejor

Para no perder de vista lo que ya es más sólido en nuestro proyecto:

- **Trazabilidad explícita:** tenemos dos matrices que amarran cada grupo de
  requerimientos a un componente de arquitectura. Felipe no tiene eso.
- **Requerimientos bajo norma:** ISO/IEC/IEEE 29148, atómicos y verificables, con
  prefijo por componente. Los de Felipe son más informales.
- **Control de acceso razonado:** RF-AUT-02 nace de un riesgo real y documentado (las
  matrículas catastrales son públicas). Está justificado, no solo enunciado.
- **Portabilidad:** contenedores sin atarse a un proveedor. Felipe quedó amarrado a
  Azure Container Apps.
- **Evaluación con LLM-as-judge:** más riguroso para medir calidad de respuestas que
  una rúbrica de percepción sola.

---

## Orden sugerido para lo que queda

1. Diseñar el plan de pruebas del OE4 con casos atados a RF (se puede hacer ya, no
   depende de que el código esté listo)
2. Montar el esqueleto del repositorio según la sección 3.7
3. Construir el grafo de LangGraph con los 8 nodos
4. Escribir las pruebas de las tres piezas críticas a medida que se desarrollan
5. Al final, integrar todo en el documento principal con la estructura de capítulos
   por objetivo
