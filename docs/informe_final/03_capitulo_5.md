# Capítulo 5 · Pruebas y resultados (borrador)

Cada cifra lleva su archivo de origen. Los archivos de la corrida 2, del umbral, de la calibración y
de las pruebas no funcionales están en la rama de B15 (PR #48), hasta que se fusione.

## 5.1 Plan de pruebas

El plan siguió la estructura del programa CTFL v4.0.1 del ISTQB, con contexto y alcance, supuestos,
interesados, riesgos de producto y de proyecto, niveles, tipos y técnicas de prueba, evaluadores,
métricas, criterios de entrada y de salida, presupuesto, cronograma y la tabla de compromisos del
documento con el lugar donde se miden (`docs/plan_de_pruebas.md`; ADR-24, A1).

- **Niveles.**
  - Componentes: 100 consultas etiquetadas para el orquestador, y los escenarios de un turno contra
    el nodo de cada agente.
  - Integración: RAGAS sobre el pipeline de recuperación.
  - Sistema: 60 escenarios con conversaciones completas sobre el despliegue.
  - No funcionales: ISO/IEC 25010.
- **Escenario superado:** pasa todas las verificaciones de código y el juez lo califica «correcta» o
  «parcialmente correcta», sin alucinación. Se reportó también una tasa estricta, solo «correcta»
  (A3).
- **Intervalo:** de Wilson con n = escenarios, porque los ensayos de un escenario no son
  independientes (A2), más un bootstrap por escenario.
- **Evaluadores:**
  - código, para lo exacto;
  - un juez (Claude Opus 5.5) guiado por la referencia, validado con casos conocidos (A4) y con su
    huella congelada (A5);
  - RAGAS con `gpt-4.1-mini`;
  - personas, para calibrar el juez: R2, 30 respuestas estratificadas.
- **Conjuntos aparte:** generalización (R1, solo en la corrida 3), encadenados (R3) y seguridad
  (R4).
- **Regla contra el sobreajuste (A8):** ningún texto, pregunta ni cifra de los escenarios en los
  prompts ni en el código, con una prueba automática que lo vigila.

## 5.2 Validación y correcciones del instrumento

- **Antes de la corrida 1:** el juez (v1) y RAGAS detectaron una afirmación inventada conocida en una
  respuesta real y aprobaron su versión fiel; un evaluador más económico de RAGAS no la detectó y se
  descartó (`docs/resumenes/b12.md`; ADR-24).
- **Después de la corrida 1:** 12 de los 31 escenarios no superados habían fallado por el instrumento
  y no por el sistema (`reports/corrida-1/fallas.md`, F1 y F3); otra falla del instrumento (F10)
  afectó a un escenario de seguridad de R4.
  - El juez y RAGAS no veían los datos de las herramientas, las notas del sistema, los datos del
    recibo ni el aviso de IA (F1).
  - La verificación de texto no reconocía «Decreto Distrital» (F3).
  - El detector de fuga marcaba textos públicos (F10, en R4).
  - Se corrigieron de forma general (ADR-25). La corrección de F1 produjo el juez v2, que ya veía
    esas fuentes.
- **Juez v3.** Una revisión externa encontró que la bandera de alucinación del juez v2 cambiaba entre
  ejecuciones, así que el juez pasó a v3: lista primero las afirmaciones sin fuente y la
  justificación, y al final da el veredicto (ADR-25).
- **Validación A4 repetida:** se hizo con el criterio de la tasa de la meta y tres repeticiones, y
  cumplió 9 de 9 criterios en las tres. El juez listó siempre la frase inventada, un requisito
  inventado y dos cifras alteradas de una herramienta, y aprobó siempre las respuestas fieles
  (`reports/validacion_evaluadores.json`).
- **Recalificación de 17 respuestas guardadas con el juez v3:** ninguna cambió de resultado
  (`reports/juez-v3-recalificacion/comparacion.md`).
- **Corrida 1:** quedó reportada tal como se midió, con el juez v1.

## 5.3 Corrida 1

Corrió contra el despliegue (commit `805f2ef`, etiqueta `v0.9.0`), con 1 ensayo por escenario más los
componentes y RAGAS (`reports/corrida-1/reporte.md`, `constancias.md`).

| Medida | Valor | Origen |
|---|---|---|
| Tasa de la meta | **48,3 %** (29 de 60; Wilson de 36,2 % a 60,7 %) | `reports/corrida-1/reporte.md` |
| Tasa estricta | 36,7 % (Wilson de 25,6 % a 49,3 %) | ídem |
| R3 y R4 | 0 de 3 y 0 de 2 | ídem |
| Veredictos del juez (v1) | correcta, 32; parcialmente correcta, 19; incorrecta, 9; con alucinación, 21,7 % | `reports/corrida-1/metricas.json` |
| Orquestador (componentes) | exactitud de 99,0 %, kappa de 0,99, F1 macro de 99,0 % (clase mayoritaria: 20,0 %) | `reports/corrida-1/reporte.md` |
| Agentes (componentes) | 19 de 34 escenarios superados | `reports/corrida-1/metricas.json` |
| RAGAS (38 casos) | precisión del contexto de 69,5 %, exhaustividad de 61,5 %, fidelidad de 65,5 % y relevancia de 64,1 % (los casos con sesión no veían los datos de las herramientas; ver la nota de 5.5) | ídem |
| RAGAS sin sesión (22 casos) | precisión de 87,1 %, exhaustividad de 82,2 % y fidelidad de 84,4 % | `reports/corrida-1/fallas.md` |
| Latencia del servidor | con RAG, p50 de 6.333 ms y p95 de 10.499 ms; sin fragmentos, p50 de 1.772 ms y p95 de 5.200 ms; todos bajo las metas | `reports/corrida-1/reporte.md` |
| Trazas | 1.279 ejecuciones de 63 conversaciones, ninguna con identificadores | `reports/corrida-1/constancias.md` |
| Costo | US$3,80 en Anthropic y US$0,49 en OpenAI | `docs/resumenes/b14.md` |
| RealSit | huella idéntica antes y después | `reports/corrida-1/constancias.md` |

## 5.4 Correcciones de la corrida 1

Se corrigieron en nueve PR las tres fallas del instrumento y las nueve del sistema. La del umbral (F13)
pasó a la calibración (`docs/resumenes/correcciones-corrida-1.md`).

- En la verificación local, la mayoría de los escenarios afectados se superaron.
- De los 29 escenarios superados en la corrida 1, 26 se mantuvieron con el juez v3: 25 de 28 en la
  regresión local (`reports/regresion-correcciones-corrida-1/`) más uno de acceso que se verificó
  aparte (`docs/resumenes/correcciones-corrida-1.md`).
  - Dos de los otros tres fallaron igual con el código anterior a las correcciones (debilidades
    previas).
  - En el tercero, el juez nuevo detectó una afirmación sin fuente.
- Costo: US$4,42 (`docs/resumenes/correcciones-corrida-1.md`).

## 5.5 Corrida 2

Corrió contra el despliegue (commit `4e94e7a`), con el juez v3, 1 ensayo por escenario, R3, R4 y
RAGAS (`reports/corrida-2/reporte.md`, PR de B15).

| Medida | Valor | Origen |
|---|---|---|
| Tasa de la meta | **88,3 %** (53 de 60; Wilson de 77,8 % a 94,2 %; bootstrap de 80,0 % a 95,0 %) | `reports/corrida-2/reporte.md` |
| Tasa estricta | 75,0 % (Wilson de 62,8 % a 84,2 %) | ídem |
| R3 y R4 | 3 de 3 y 2 de 2 | ídem |
| Recuperados frente a la corrida 1 | 26: 12 por el instrumento (F1 y F3) y 14 por el sistema | `reports/corrida-2/fallas.md` |
| Perdidos | 2, que fallan igual con el código anterior | ídem |
| RAGAS (37 casos) | precisión de 67,5 %, exhaustividad de 81,4 %, fidelidad de 84,7 % y relevancia de 63,6 % | `reports/corrida-2/metricas.json` |
| RAGAS sin sesión (21 casos) | precisión de 82,7 %, exhaustividad de 82,5 % y fidelidad de 87,8 % | `reports/corrida-2/fallas.md` |
| Latencia del servidor | con RAG, p50 de 6.373 ms y p95 de 12.372 ms (39 de 39 bajo 15 s); sin fragmentos, p50 de 2.162 ms y p95 de 8.782 ms (18 de 19 bajo 8 s) | `reports/corrida-2/reporte.md` |
| Trazas | 1.277 ejecuciones de 63 conversaciones, ninguna con identificadores | `reports/corrida-2/trazas.json` |
| Costo | US$2,55 en Anthropic y US$0,54 en OpenAI | `docs/resumenes/b15.md` |

Nota sobre RAGAS (ADR-25): desde la corrida 2, los contextos de RAGAS incluyen los datos de las
herramientas, las notas y los del recibo. Por eso los promedios generales de las corridas 1 y 2 no se
comparan directo: en los casos con sesión, la corrida 2 también mide las herramientas. La comparación
limpia de la recuperación es la de los casos sin sesión (las filas «RAGAS sin sesión»).

Pruebas no funcionales (`reports/no_funcionales/README.md`):

- **RNF-02 · Escalamiento horizontal:** la conversación continuó en otra réplica.
- **RNF-08 · Tiempos de espera y degradación:** 8 de 8 fallas inyectadas escalaron sin errores técnicos.
- **RNF-15 · Volúmenes persistentes:** los volúmenes persistieron.
- **RF-SYS-02 · Alcance de solo lectura:** la huella de RealSit fue idéntica.

## 5.6 Análisis de fallas

Cada falla se clasificó por su causa técnica y por la familia de MAST (Cemri y colaboradores): diseño
del sistema, desalineación entre agentes o verificación de la tarea.

- **Corrida 1** (`reports/corrida-1/fallas.md`): 13 fallas, F1 a F13.
  - Tres del instrumento: F1, F3 y F10.
  - En el sistema predominó el diseño del sistema: F2, F4, F7, F8, F9, F12 y F13 (umbral).
  - Luego, la desalineación entre agentes (F6 y F11) y la verificación de la tarea (F5).
  - Por el origen según RAGAS, predominó la generación con un contexto suficiente; la recuperación
    explicó un caso y, en parte, otro (`reports/corrida-1/fallas.md`).
- **Corrida 2** (`reports/corrida-2/fallas.md`): 7 fallas del sistema, G1 a G7, ninguna del
  instrumento.
  - Por su causa técnica: una de umbral (G1); dos de recuperación (G2 y G3; G3 también de
    generación); tres de generación (G4, G5 y G7), y una de enrutamiento (G6).
  - Por la familia de MAST: diseño del sistema (G1, G2, G4 y G6), verificación de la tarea (G3 y
    G5) y desalineación entre agentes (G7).
- **Segunda ronda de correcciones** (PR #49 a #51), con un tope de US$1,0 que se agotó: US$1,004, la
  suma de `reports/verif-fix-busqueda/costos.md`, `reports/verif-fix-fechas-relativas/costos.md`,
  `reports/verif-fix-fechas-relativas-2/costos.md` y `reports/verif-fix-general-canal/costos.md`
  (US$1,002), en las ramas de esos PR, más US$0,002 del agente general corrido directo (PR #51). Ninguna se fusionó ni se desplegó:
  - la fusión de la búsqueda y el texto en la recuperación (G2 y G3): de 40 a 42 de 69 fuentes
    esperadas sin modelos (`reports/recuperacion_fusion.json`, PR #49), y uno de los dos escenarios
    se superó en la verificación local. Esa verificación se hizo antes de las correcciones de la
    revisión y no se repitió. Quedó **pendiente de una decisión** sobre la técnica y sobre la
    similitud que alimenta la confianza;
  - los días que faltan calculados por código (G4): superó el escenario afectado, pero en una
    muestra otro escenario que se superaba nombró «hoy» una fecha de mañana
    (`reports/verif-fix-fechas-relativas-2/`, PR #50). Quedó **pendiente**;
  - una regla del agente general que no inventa el canal de un trámite (G1, la parte de
    generación): 0 de 3 respuestas directas lo nombraron
    (`reports/verif-fix-general-canal/agente_directo.json`, PR #51). Quedó **pendiente** de
    verificar dos escenarios generales y uno de aviso de IA.
  - El umbral (G1) y el orquestador (G6) quedaron propuestos, sin aplicar.

## 5.7 Corrida 3 (final)

**PENDIENTE (corrida 3):** 3 ensayos por escenario, R1, componentes, RAGAS, pass@1 promedio, pass@3
y pass^3, la tasa de la meta frente al 85 % de RNF-16 · Tasa de respuestas correctas con su intervalo
de Wilson, la latencia, el costo por consulta y las pruebas no funcionales que dependen del
despliegue.

## 5.8 Calibración del juez

**PENDIENTE (calibración):** el kappa entre el juez v3 y el consenso de los autores (binario y
ponderado de 3 niveles) y entre los dos evaluadores, con intervalos por bootstrap, sobre la muestra
de 30 respuestas de la corrida 2 (`reports/calibracion/`).

## 5.9 Usabilidad

**PENDIENTE (usabilidad):** el SUS de cada evaluador y los problemas de la evaluación heurística
(`docs/usabilidad/`), reportados como evaluación interna preliminar de dos evaluadores que además
desarrollaron el sistema multiagente de IA (ADR-21).

## 5.10 Matriz de trazabilidad

**PENDIENTE (corrida 3):** la calificación final de los 65 requerimientos (`reports/trazabilidad.md`
y `.csv`). La matriz al cierre de la corrida 1 está en `reports/trazabilidad.md`.

## 5.11 Comparación con Bahçeci y colaboradores

Bahçeci y colaboradores reportaron 92,63 % de fidelidad, 91,31 % de relevancia, 75,20 % de precisión
del contexto, 86,60 % de exhaustividad del contexto y una latencia cercana a 4.000 ms (sección 6.5 de
la especificación técnica). En las consultas sin sesión, la medida limpia de la recuperación:

| Métrica | Bahçeci | Corrida 1 | Corrida 2 |
|---|---|---|---|
| Precisión del contexto | 75,20 % | 87,1 % | 82,7 % |
| Exhaustividad del contexto | 86,60 % | 82,2 % | 82,5 % |
| Fidelidad | 92,63 % | 84,4 % | 87,8 % |

Fuentes: `reports/corrida-1/fallas.md` y `reports/corrida-2/fallas.md`.

**PENDIENTE (corrida 3):** la comparación final, con la relevancia y la latencia.

## 5.12 Costo

| Concepto | Anthropic (US$) | OpenAI (US$) | Origen |
|---|---|---|---|
| Corrida 1 | 3,80 | 0,49 | `docs/resumenes/b14.md` |
| Correcciones de la corrida 1 | 4,34 | 0,08 | `docs/resumenes/correcciones-corrida-1.md` |
| Corrida 2 y pruebas no funcionales | ~2,61 | 0,54 | `docs/resumenes/b15.md` |

**PENDIENTE (corrida 3):** el costo real de la corrida 3, el costo por consulta y el total del
proyecto.
