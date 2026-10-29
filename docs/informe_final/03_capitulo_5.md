# Capítulo 5 · Pruebas y resultados (borrador)

Cada cifra lleva su archivo de origen en el repositorio.

## 5.1 Plan de pruebas

El plan siguió la estructura del programa CTFL v4.0.1 del ISTQB, con contexto y alcance, supuestos,
interesados, riesgos de producto y de proyecto, niveles, tipos y técnicas de prueba, evaluadores,
métricas, criterios de entrada y de salida, presupuesto, orden de ejecución y la tabla de compromisos del
documento con el lugar donde se miden (`docs/plan_de_pruebas.md`; ADR-24, A1). Los ajustes al plan
(ADR-24: A1 a A9 y las mejoras R1 a R4) salieron de una revisión externa con un asistente de IA (Claude, en una conversación distinta de la que desarrolló el código), cuyos hallazgos los autores contrastaron con las fuentes oficiales y aprobaron.

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
- **Juez v3.** Una revisión externa con un asistente de IA (Claude, en una conversación distinta de la que desarrolló el código), cuyos hallazgos los autores contrastaron con las fuentes oficiales y aprobaron, encontró que la bandera de alucinación del juez v2 cambiaba entre
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
| Agentes (componentes) | 19 de 34 escenarios superados, con un defecto del instrumento que se halló después de la corrida 3 (sección 5.8) | `reports/corrida-1/metricas.json` |
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

Pruebas no funcionales (`reports/no_funcionales/corrida-2/README.md`):

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
- **Segunda ronda de correcciones** (PR #49 a #51, `docs/resumenes/b15.md`):
  - la fusión de la búsqueda y el texto en la recuperación (G2 y G3; de 40 a 42 de 69 fuentes
    esperadas sin modelos) se **cerró sin fusionar**, como trabajo futuro: la ganancia era pequeña,
    duplicaba la latencia del agente general y cambiaba la similitud que alimenta la confianza
    (PR #49);
  - la regla del agente general que no inventa el canal de un trámite (G1, la parte de generación)
    superó 8 de 8 escenarios generales y del aviso de IA y **se fusionó** (PR #51);
  - los días que faltan calculados por código (G4) se cerraron, se fusionaron después como excepción
    y se **reemplazaron** por las fechas por código (PR #50 y #72, sección 5.7);
  - el umbral (G1) se mantuvo en 0,70, aprobado por los autores, y el orquestador (G6) quedó sin
    cambios.

## 5.7 Correcciones posteriores, ensayos generales y sondas de fechas

Después de la corrida 2 se corrigió lo que encontraron la usabilidad y una revisión externa con un asistente de IA (Claude, en una conversación distinta de la que desarrolló el código), cuyos hallazgos los autores contrastaron con las fuentes oficiales y aprobaron (PR #59 a #68), se
hizo una auditoría de seguridad (PR #69 y #70) y se pasó a decidir por código lo que debe ser exacto
(PR #72 y #73). Cada ronda se verificó con un ensayo general de un ensayo por escenario, más R3 y R4,
contra el despliegue y con el juez calibrado, y con una regla fijada antes de ver el resultado.

| Corrida | Qué verificó | Superados de 60 (Wilson del 95 %) | Estricta | R3 y R4 | Origen |
|---|---|---|---|---|---|
| 2b | Correcciones de la usabilidad y de la revisión externa con un asistente de IA | 52 (86,7 %; 75,8 % a 93,1 %) | 75,0 % | 3 de 3 y 2 de 2 | `reports/corrida-2b/` |
| 2c | Verificación tributaria, fechas relativas (#50) y auditoría | 50 (83,3 %; 72,0 % a 90,7 %) | 75,0 % | 2 de 3 y 2 de 2 | `reports/corrida-2c/analisis.md` |
| 2d | Código congelado, con las fechas y las reglas por código | 55 (91,7 %; 81,9 % a 96,4 %) | 75,0 % | 3 de 3 y 2 de 2 | `reports/corrida-2d/analisis.md` |

- En la 2b, una sola regresión se debió a un cambio del día (la regla del CIIU en el agente del
  ICA, que el juez marcó sin fuente) y se revirtió (PR #66).
- La 2c no cumplió su regla (52 o más): se analizó cada falla sin corregir nada por cuenta propia.
  Una fue probablemente del PR #50: el modelo usó «hace 83 días» y concluyó sin fuente que «no se
  puede pagar» (MULTI-02).
- **Fechas por código.** Por decisión de los autores, el sistema no relaciona fechas con el día de
  la consulta: da la fecha exacta y, cuando importa, «ya venció» o «aún no vence» según lo que
  calcula el código; un verificador sin modelo pide reescribir toda respuesta que diga «hoy»,
  «mañana», «hace N días» o frases parecidas, traiga una referencia con número («el fragmento [1]»)
  o diga «consultar las herramientas» (PR #72). Se verificó con 34
  sondas sin juez (17 combinaciones de pregunta y día, casi todas el día antes, el mismo día y después
  de un plazo, dos veces cada una). En la repetición final, ninguna respuesta relacionó una fecha con
  el día de la consulta, trajo una referencia interna o dio un estado de fecha equivocado; 2 de 34 no
  llamaron la herramienta de fechas, sin error, y las reescrituras bajaron de 23 a 9 de 34
  (`reports/verif-fechas-por-codigo/`).
- **Reglas por código.** Las herramientas del ICA entregan la regla de la periodicidad tal como está
  en los datos (el modelo había invertido la de los 391 UVT), y la tarifa del predial se describe con
  la herramienta de tarifas (PR #73): 6 de 6 escenarios superados con el juez y ninguna inversión ni
  tarifa sin fuente en 6 preguntas nuevas (`reports/verif-reglas-por-codigo/`).
- La 2d cumplió su regla: 55 de 60, sin errores técnicos, latencias dentro de las metas, trazas sin
  identificadores y ninguna respuesta que relacionara una fecha con el día de la consulta. Sus 5
  fallas fueron de tipos ya vistos.

## 5.8 Corrida 3 (final)

Corrió contra el despliegue (commit `d3dab00`, código congelado) con 3 ensayos por escenario, R1,
R3, R4, los componentes, RAGAS y la revisión de trazas, con el juez v3 de la calibración
(`reports/corrida-3/reporte.md`; `docs/reporte_de_pruebas.md`).

| Medida | Valor | Origen |
|---|---|---|
| Tasa de la meta | **90,0 %** (60 escenarios, 3 ensayos; Wilson de 79,9 % a 95,3 %; bootstrap de 83,3 % a 96,1 %) | `reports/corrida-3/metricas.json` |
| Tasa estricta | 75,0 % (Wilson de 62,8 % a 84,2 %) | ídem |
| pass@1, pass@3 y pass^3 | 0,90, 0,95 y 0,85 | ídem |
| R1 · Generalización (10 variantes) | 43,3 % (Wilson de 19,0 % a 71,4 %); pass^3 de 0,30 | ídem |
| R3 y R4 | 9 de 9 y 6 de 6 ensayos | ídem |
| Veredictos del juez | correcta, 137; parcialmente correcta, 37; incorrecta, 6; con alucinación, 7 de 180 (3,9 %) | ídem |
| Orquestador (componentes) | exactitud de 99,0 %, kappa de 0,99, F1 macro de 0,99 (clase mayoritaria: 20,0 %) | `reports/corrida-3/reporte.md` |
| Agentes (componentes) | **30 de 34 (88,2 %)** con el instrumento corregido; 11 de 34 con el defecto | `reports/corrida-3/metricas.json` y `componentes_*_sin_evidencia.jsonl` |
| RAGAS (110 casos) | precisión del contexto de 66,1 %, exhaustividad de 82,4 %, fidelidad de 84,8 % y relevancia de 68,1 % | ídem |
| RAGAS sin sesión (66 casos) | precisión de 81,4 %, exhaustividad de 81,2 %, fidelidad de 84,6 % y relevancia de 71,3 % | `reports/corrida-3/ragas.jsonl`; `docs/reporte_de_pruebas.md`, sección 5 |
| Latencia del servidor (principal) | sin fragmentos, p50 de 2.299 ms y p95 de 3.934 ms (54 de 54 bajo 8 s); con RAG, p50 de 6.379 ms y p95 de 13.393 ms (120 de 120 bajo 15 s). En R1, 27 de 28 turnos con RAG bajo 15 s (el más lento, 15.859 ms) | `reports/corrida-3/reporte.md`; `docs/reporte_de_pruebas.md`, sección 10 |
| Trazas | 4.422 ejecuciones, ninguna con identificadores | `reports/corrida-3/trazas.json` |
| Errores técnicos | 0 en 249 turnos | `reports/corrida-3/calificados.jsonl` |

- **Frente a la meta de RNF-16 · Tasa de respuestas correctas (85 %):** la estimación puntual (90,0 %)
  la supera; el límite inferior de Wilson (79,9 %), no.
- **No superados** (con algún ensayo fallido; la causa y la familia de MAST de cada ensayo, en
  `reports/corrida-3/fallas.md`, y el análisis, en `docs/reporte_de_pruebas.md`, sección 9):
  - 0 de 3: GEN-02 (transfiere a un funcionario en vez de responder) e IPU-14 (niega un alivio de
    intereses), que fallan desde la corrida 1, e IPU-13 (no da el plazo de la factura: en 2 de 3
    ensayos la recuperación no trae el artículo y, en el otro, llega y la respuesta lo omite);
  - 1 de 3: AIA-01 (enrutamiento de un saludo), IPU-15 (omite el valor de la cuota) y MULTI-03 (una
    afirmación sin fuente);
  - 2 de 3: ICA-04, ICA-07 e IPU-04 (una afirmación sin fuente en un ensayo).
  - Por la familia de MAST, predominan la verificación de la tarea (generación sin fuente o
    incompleta) y el diseño del sistema (enrutamiento y recuperación). Ninguna falla es de acceso a
    datos.
- **R1 · Generalización.** Siete de las diez variantes tuvieron algún ensayo fallido. Los 17 ensayos
  no superados se clasificaron uno por uno en una revisión externa con un asistente de IA (Claude, en una conversación distinta de la que desarrolló el código), y los aprobaron los autores:
  - 3 (VAR-01): la variante admite otra lectura; el sistema respondió la expedición de la factura y
    los plazos de pago, con las fechas correctas, y omitió la causación y el periodo gravable;
  - 2 (VAR-03): la pregunta en primera persona se tomó como personal y el sistema pidió iniciar
    sesión sin dar el plazo general, como dispone RF-AUT-04 · Aviso de sesión requerida;
  - 6: solo falló la verificación de texto heredada del escenario de origen; el juez las calificó
    como parcialmente correctas y sin alucinación (en VAR-06, la misma omisión de su origen, IPU-13);
  - 6: errores del sistema (afirmaciones sin fuente, un plazo vencido dicho en presente, una
    conclusión omitida y un fragmento atribuido a otro artículo).

  El juez aceptó 19 de los 30 ensayos y las verificaciones de código pasaron en 15. La tasa oficial
  sigue siendo 43,3 %: el desglose la explica, no la reemplaza (`reports/corrida-3/calificados.jsonl`
  y `fallas.md`; análisis en `docs/reporte_de_pruebas.md`, sección 9).
- **Mecanismo interno en la respuesta.** En 8 de las 225 conversaciones, la respuesta nombra el
  mecanismo interno («según la herramienta», «los fragmentos», «las normas que me entregaron»), algo
  que la regla común prohíbe. El verificador sin modelo solo detecta «fragmento [n]» y «consultar herramientas». No cambia
  ningún dato; ampliar el verificador queda como trabajo futuro (`reports/corrida-3/resultados.jsonl.gz`;
  `docs/reporte_de_pruebas.md`, sección 12).
- **Pruebas no funcionales** (`reports/no_funcionales/README.md`): 8 de 8 fallas inyectadas escalaron
  sin errores técnicos (RNF-08 · Tiempos de espera y degradación); con dos réplicas, una conversación
  continuó en la otra (RNF-02 · Escalamiento horizontal); los volúmenes persistieron al reiniciar y al
  recrear (RNF-15 · Volúmenes persistentes); la huella de RealSit fue idéntica (RF-SYS-02 · Alcance de
  solo lectura).
- **Disponibilidad** (RNF-06 · Horario de atención): **85,99 %** en horario hábil (135 de 157
  chequeos; el registro completo, hasta el cierre de B16, cubre 43,0 horas y 517 chequeos), **por
  debajo de la meta del 99 %**; la cifra se reporta tal cual, porque el periodo se fijó antes de medir.
  - **Causa.** Desde el despliegue, cada chequeo de `/health` creaba un cliente nuevo de Chroma sin
    cerrarlo, y unas dos horas después de cada despliegue el backend agotaba sus descriptores y
    dejaba de responder.
  - **El registro empezó durante una caída.** El monitor del servidor empezó a registrar en B15,
    justo durante una de esas caídas: los 27 fallos (502; 22 en horario hábil) son de esa única
    caída, en las primeras 2,2 horas.
  - **Corrección.** Se corrigió la causa, con una prueba de regresión (PR #54). Desde su despliegue,
    ninguna falla: 490 de 490 chequeos en 40,8 horas y 135 de 135 en horario hábil, incluida toda la
    corrida 3.
  - **Alcance del registro.** Con unos 160 chequeos en horario hábil, cada uno pesa más de medio
    punto. Antes de B15 no hay datos, porque el monitor de GitHub Actions nunca corrió. El chequeo
    sale del mismo servidor.
  - En la matriz, la disponibilidad es la evidencia de RNF-06, que vale 0
    (`reports/no_funcionales/disponibilidad.md`; `docs/reporte_de_pruebas.md`, sección 6).
- **Agentes contra su nodo.** Los componentes corrían sin el modo de evaluación, así que el juez solo
  recibía los contextos, que llegaban vacíos, y no veía los datos de las herramientas ni las notas.
  Por eso marcó como «sin fuente» datos que sí tenían fuente (por ejemplo, el saldo de ICA-07). Es el
  mismo defecto F1 que ADR-25 corrigió en el nivel de sistema, y afectó también a la corrida 1. Se
  corrigió con una prueba de regresión y se repitió una sola vez, solo esa parte (con el juez v3 y la
  huella exigida; el enrutamiento no se repitió): de 11 de 34 (32,4 %) a **30 de 34 (88,2 %)**, la
  cifra del nivel de componentes. Queda una limitación del instrumento: en los componentes el juez
  no recibe los predios de la sesión (IPU-11 e IPU-14). La causa principal del 32,4 % era el
  instrumento, no los agentes (`docs/reporte_de_pruebas.md`, sección 5).
- **IPU-14.** Con la búsqueda que escribe el orquestador, el art. 7 del Acuerdo 1084 de 2026 no llegó
  a los 5 fragmentos en ningún ensayo; en la prueba de componentes, con el texto del contribuyente
  como búsqueda, el agente lo recuperó y explicó el alivio (60 %, 21 de diciembre de 2026). El reloj
  del escenario (1 de octubre de 2026) es anterior a la publicación del acuerdo (9 de octubre de
  2026), que la referencia da por publicado; no cambia el resultado (`docs/reporte_de_pruebas.md`,
  sección 9).
- **Código evaluado.** El código del sistema sigue igual a `d3dab00`; después de la corrida solo
  cambió el instrumento de evaluación (`src/evaluacion` y `scripts`).

## 5.9 Calibración del juez

Dos evaluadores calificaron a ciegas y sin ayuda de IA 30 respuestas de la corrida 2b, estratificadas
por el veredicto del juez (las 7 no aprobadas y 23 aprobadas), y su consenso. Una primera muestra, de
la corrida 2, se descartó porque sus hojas se llenaron con ayuda de un chat externo de IA
(`reports/calibracion/descartada_corrida-2/`).

| Comparación | Kappa binario (IC 95 %) | Kappa ponderado de 3 niveles (IC 95 %) | Acuerdo observado |
|---|---|---|---|
| Juez frente al consenso | −0,062 (−0,170 a 0,000) | 0,062 (−0,231 a 0,366) | 22 de 30 (binario); 19 de 30 |
| Entre los evaluadores | 0,000 (0,000 a 1,000) | −0,111 (−0,200 a 0,000) | 29 de 30 (binario); 24 de 30 |

El valor bajo se debe a que las personas aprobaron casi todas las respuestas (paradoja del kappa;
PABAK binario de 0,47 y 0,93): en 7 de las 8 diferencias binarias, el juez fue más estricto que el
consenso, así que la tasa que mide tiende a quedar por debajo de la que darían las personas
(`reports/calibracion/kappa.json`; el acuerdo observado y el PABAK, en `docs/resumenes/b15.md` y `docs/reporte_de_pruebas.md`, sección 7).

## 5.10 Usabilidad

Evaluación interna preliminar de los dos autores, que además desarrollaron el sistema multiagente de
IA (ADR-21; `docs/usabilidad/rodolfo/` y `docs/usabilidad/dayanna/`):

- **SUS:** 80,0 y 97,5, uno por autor; promedio de 88,75 (`docs/reporte_de_pruebas.md`, sección 8).
- **Evaluación heurística:** 6 anotaciones de 4 problemas distintos (dos los anotaron los dos
  autores), de gravedad 2 a 4: la lista de usuarios en modo oscuro, las fotos de más de 5 MB, el
  recibo de formato realista tomado como recortado y dónde encontrar el CIIU. Tres se corrigieron
  antes de la corrida 3 (PR #57, #60 y #59) y el del CIIU, en parte (glosario, PR #64).

## 5.11 Matriz de trazabilidad

Con la corrida 3, la suite, las pruebas de la interfaz, las pruebas con modelos reales y la
disponibilidad, el cumplimiento global fue de **78,5 %**, con los **65 requerimientos calificados**
(51 con 100 % y 14 con 0 %) (`reports/trazabilidad.md` y `.csv`; los resultados de las pruebas, en
`reports/junit/`). La calificación es mecánica: un requerimiento vale 0 si falla alguna de sus
evidencias, incluido un solo ensayo de uno de sus escenarios, más estricta con 3 ensayos que con 1
(83,3 % de 48 en la corrida 2). La regla no cambió.

En el cierre de B16 se completó la evidencia que no tenía resultado (antes, 74,0 % con 50 calificados
y 15 sin calificar):
- el script toma el resultado de las pruebas de Playwright;
- las tres pruebas con modelos reales se corrieron una vez (3 de 3);
- la disponibilidad entró como la evidencia de RNF-06 · Horario de atención (sección 6.7 de la
  especificación).

El análisis está en `docs/reporte_de_pruebas.md`, sección 11.

- **Los 14 con 0.** A trece los bajaron nueve escenarios del principal, casi siempre por la
  generación y no por la función que nombra el requerimiento:
  - RF-AUT-01 · Verificación de identidad bajó por ICA-04, ICA-07 e IPU-15, que fallaron por la
    generación: los de acceso (ACC-01 a ACC-03) pasaron 3 de 3;
  - RF-SYS-06 · Aviso de interacción con IA (provisional) y RF-UI-03 · Identificación del
    interlocutor bajaron por AIA-01, que falló por la clasificación y por un escalamiento
    innecesario, aunque el aviso de IA salió en los tres ensayos;
  - RF-GEN-01 · Consultas transversales y RF-GEN-03 · Respuesta sustentada en fuentes, por GEN-02;
  - los de IPU, por IPU-04, IPU-13, IPU-14 e IPU-15;
  - los de ICA, por ICA-04, ICA-07 y MULTI-03;
  - RF-ORQ-03 · Consultas multiagente, por MULTI-03.

  El otro es RNF-06 · Horario de atención, por la disponibilidad.
- RNF-01 · Tiempo de respuesta quedó con 100 %: en la corrida, 54 de 54 turnos sin fragmentos y 120
  de 120 con RAG dentro de la meta. Los escenarios de OCR, con el modelo de visión real, se
  superaron en los tres ensayos.

## 5.12 Comparación con Bahçeci y colaboradores

Bahçeci y colaboradores reportaron 92,63 % de fidelidad, 91,31 % de relevancia, 75,20 % de precisión
del contexto, 86,60 % de exhaustividad del contexto y una latencia cercana a 4.000 ms (sección 6.5 de
la especificación técnica). En las consultas sin sesión, la medida limpia de la recuperación:

| Métrica | Bahçeci | Corrida 1 | Corrida 2 | Corrida 3 |
|---|---|---|---|---|
| Precisión del contexto | 75,20 % | 87,1 % | 82,7 % | 81,4 % |
| Exhaustividad del contexto | 86,60 % | 82,2 % | 82,5 % | 81,2 % |
| Fidelidad | 92,63 % | 84,4 % | 87,8 % | 84,6 % |
| Relevancia de la respuesta | 91,31 % | — | — | 71,3 % |
| Casos sin sesión | — | 22 | 21 | 66 |

Fuentes: `reports/corrida-1/fallas.md`, `reports/corrida-2/fallas.md` y `reports/corrida-3/ragas.jsonl`.
La latencia de la corrida 3 con recuperación tuvo una mediana de 6.379 ms en el servidor, por encima de
los 4.000 ms de Bahçeci; el sistema hace dos o tres llamadas a modelos por turno.

## 5.13 Costo

| Concepto | Anthropic (US$) | OpenAI (US$) | Origen |
|---|---|---|---|
| Corrida 1 | 3,80 | 0,49 | `docs/resumenes/b14.md` |
| Correcciones de la corrida 1 | 4,34 | 0,08 | `docs/resumenes/correcciones-corrida-1.md` |
| Corrida 2 y pruebas no funcionales | ~2,61 | 0,54 | `docs/resumenes/b15.md` |
| Corrida 3 (con los componentes originales) | 10,82 | 1,65 | `docs/resumenes/b16.md`; `reports/corrida-3/` |
| Cierre de B16: repetición de los agentes contra su nodo y pruebas con modelos reales | ~1,42 | — | `docs/resumenes/b16.md` |
| Lo demás (correcciones posteriores a la corrida 2, ensayos 2b a 2d, sondas, verificaciones, humo e ingestas), por diferencia con el total | ~13,5 | < 0,1 | `reports/*/costos.md` y los resúmenes |
| Total del proyecto (estimación) | ~36,5 | ~2,8 | `docs/resumenes/b16.md`; `docs/reporte_de_pruebas.md`, sección 10 |

Los 40 `costos.md` suman US$33,82 en Anthropic y US$2,72 en OpenAI; el de la corrida 3 muestra los
componentes de la repetición. El total agrega:
- los componentes originales de la corrida 3 (US$0,93);
- las pruebas con modelos reales del cierre;
- los gastos que los resúmenes anotan sin `costos.md`.

Por eso es una estimación.

El sistema costó US$0,0082 por turno en la corrida 3 (249 turnos; `reports/corrida-3/costos.md`),
con dos o tres llamadas a modelos por turno; el juez es lo que más pesa en una corrida. Frente al
presupuesto de la sección 7 del plan (US$25 en Anthropic y US$10 en OpenAI), Anthropic lo superó en
unos US$11,5. No estaban en el presupuesto:
- las rondas de correcciones posteriores a la corrida 2, cada una verificada con el juez;
- los ensayos generales 2b a 2d;
- el cierre de B16.

## 5.14 Limitaciones identificadas y trabajo futuro

| Limitación | Causa | Efecto | Por qué no compromete el resultado o cómo se mitigó | Trabajo futuro | Origen |
|---|---|---|---|---|---|
| Generalización (R1): 43,3 % | Las paráfrasis cambian la clasificación o la búsqueda. De los 17 ensayos no superados: 3 admiten otra lectura (VAR-01), 2 son preguntas en primera persona tomadas como personales (diseño de RF-AUT-04 · Aviso de sesión requerida), 6 solo fallan la verificación de texto heredada y 6 son errores del sistema | R1 queda lejos de la meta | Se reporta aparte de la tasa principal. El juez aceptó 19 de 30 ensayos y solo 6 de los 17 no superados son errores del sistema | Más variantes por escenario, verificaciones propias de cada variante y una regla para las preguntas generales en primera persona | `docs/reporte_de_pruebas.md`, sección 9; `reports/corrida-3/fallas.md` |
| IPU-14, GEN-02 y MULTI-03 (fuente esperada fuera de los 5 fragmentos) | La búsqueda que escribe el orquestador no trae la fuente esperada | IPU-14 y GEN-02, 0 de 3; MULTI-03, 1 de 3 | Medida sin modelos, la fusión de la búsqueda del orquestador con el texto del contribuyente trae la fuente esperada de los tres (el art. 7 del Acuerdo 1084 de 2026, el manual de la OVT simulada y la Ley 44 de 1990, arts. 1 y 3), pero pierde la del manual en ACC-02 y ACC-03 (de 40 a 42 de 69 fuentes esperadas). Se cerró sin fusionar para no cambiar la similitud que alimenta la confianza antes de congelar | Buscar también con el texto del contribuyente y fusionar las dos listas, recalibrando la confianza | `reports/recuperacion_fusion.json` en la rama del PR #49 (`fix/busqueda`); `docs/reporte_de_pruebas.md`, sección 9 |
| Disponibilidad de 85,99 %, bajo la meta del 99 % | Una fuga de conexiones en `/health`, presente desde el despliegue; el registro empezó durante una de sus caídas | RNF-06 · Horario de atención vale 0 en la matriz | Se corrigió la causa con una prueba de regresión (PR #54): desde entonces, 490 de 490 chequeos (135 de 135 en horario hábil), incluida toda la corrida 3. El registro es corto (cada chequeo hábil pesa más de medio punto) | Un monitoreo más largo y desde fuera del servidor | `reports/no_funcionales/disponibilidad.md`; `docs/reporte_de_pruebas.md`, sección 6 |
| Instrumento de componentes | Los agentes contra su nodo corrían sin el modo de evaluación; el juez no veía las herramientas ni las notas (F1) | 11 de 34 en la corrida 3 y 19 de 34 en la corrida 1, subestimados | Corregido con una prueba de regresión y repetido: 30 de 34. Los originales se conservan | Pasar al juez los predios de la sesión también en los componentes (IPU-11 e IPU-14) | `reports/corrida-3/metricas.json` y `componentes_*_sin_evidencia.jsonl`; `docs/reporte_de_pruebas.md`, sección 5 |
| 8 respuestas nombran el mecanismo interno | El verificador sin modelo solo detecta «fragmento [n]» y «consultar herramientas» | 8 de 225 conversaciones dicen «según la herramienta», «los fragmentos» o parecido | No cambia ningún dato de la respuesta | Ampliar el verificador a esas formas | `reports/corrida-3/resultados.jsonl.gz`; `docs/reporte_de_pruebas.md`, sección 12 |
| Art. 26 del Decreto 352 de 2002 en la base | `knowledge_base/vigencias.yaml` no tiene una regla para él (sí para el art. 25) | Una respuesta sobre tarifas citó ese texto de 2002 (sistema preferencial en salarios mínimos) | Apareció en una pregunta de verificación, no en un escenario; la cita tenía fuente | Confirmar su vigencia con la fuente oficial y agregar la regla | `reports/verif-reglas-por-codigo/analisis.md` |
| El juez es más estricto que las personas; la muestra es de 30 | Las personas aprobaron casi todo (29 de 30): paradoja del kappa | Kappa binario de −0,062 (PABAK de 0,47) | En 7 de las 8 diferencias, el juez fue más estricto: la tasa medida tiende a quedar por debajo de la que darían las personas | Una muestra más grande, con más respuestas negativas y evaluadores externos | `reports/calibracion/kappa.json`; `docs/reporte_de_pruebas.md`, sección 7 |
| Usabilidad interna de los autores | ADR-21: sin usuarios externos | SUS de 80,0 y 97,5, no generalizable | Se presenta como preliminar; la evaluación heurística halló 4 problemas, 3 corregidos y 1 en parte | Pruebas con contribuyentes y funcionarios reales | `docs/usabilidad/`; `docs/reporte_de_pruebas.md`, sección 8 |
| Datos sintéticos y reloj simulado | RNF-04 · Uso exclusivo de datos sintéticos; reloj inyectable (ADR-16) | No se mide la distribución de los datos reales. El reloj de IPU-14 (1 de octubre de 2026) es anterior a la publicación del Acuerdo 1084 (9 de octubre de 2026), que la referencia da por publicado | La base sintética cumple el contrato de RealSit (adaptador) y la observación de IPU-14 no cambia su resultado | Un piloto con datos reales anonimizados bajo un acuerdo con Realtix; un reloj posterior en IPU-14 | `docs/reporte_de_pruebas.md`, sección 9 |
| Matriz mecánica | 0 si falla alguna evidencia, con 3 ensayos | 78,5 %, con 14 requerimientos en 0 aunque su función se cumpla (por ejemplo, RF-AUT-01) | La tabla de la sección 11 del reporte explica cada 0 con su escenario y su causa | Calificar con 80 % los que pasan con una limitación documentada | `reports/trazabilidad.md`; `docs/reporte_de_pruebas.md`, sección 11 |
| Auditoría de seguridad rápida y estática | La hizo un asistente de IA (Claude Code, con 12 subagentes de revisión), sin ejecutar ataques | No confirmó hallazgos; dejó 4 pistas | Tres se corrigieron y una quedó como riesgo aceptado; de 23 notas de refuerzo, 3 se aplicaron y 4 se verificaron | Una prueba de penetración dinámica y las 16 notas restantes | `docs/resumenes/auditoria_seguridad.md` |
| Costo sobre el presupuesto | Rondas de correcciones verificadas con el juez, ensayos generales y el cierre de B16 | Unos US$11,5 más en Anthropic | El sistema cuesta US$0,0082 por turno; el exceso es del juez y de las verificaciones | Muestras más chicas para las verificaciones intermedias | `docs/reporte_de_pruebas.md`, sección 10 |
| Límite inferior de Wilson bajo el 85 % | Con 60 escenarios, el intervalo es ancho (ADR-24: n = escenarios) | 90,0 % de estimación puntual, pero un límite inferior de 79,9 % | Se reportan juntos el bootstrap (83,3 % a 96,1 %) y el pass^3 (0,85) | Más escenarios para estrechar el intervalo | `reports/corrida-3/metricas.json` |
