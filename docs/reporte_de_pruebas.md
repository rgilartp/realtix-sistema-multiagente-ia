# Reporte de pruebas del OE4

Reporte de la ejecución del plan de pruebas (`docs/plan_de_pruebas.md`), con la estructura del
reporte de avance y de cierre del programa CTFL v4.0.1 del ISTQB, con la corrida 3 (la que se
reporta, sección 6.10). Cada cifra lleva su archivo de origen en `reports/`.

## 1. Resumen

- Objeto: el sistema multiagente de IA desplegado, con datos sintéticos.
- Versión evaluada: `d3dab00`, desplegada en `https://tg2-multiagente.duckdns.org`. El código del
  sistema (`src/agents`, `src/services`, `src/api`, `src/data`, `src/store`, `src/integrations`,
  `web`, `datos`, `knowledge_base` y `deploy`) sigue igual a `d3dab00`, y también las dependencias.
  Después de `v1.0.0` solo cambió el instrumento de evaluación (`src/evaluacion` y `scripts`, en el
  cierre de B16): lo que el arnés de «agentes contra su nodo» le entrega al juez (el juez y su huella no
  cambiaron) y la matriz de trazabilidad.
- Huella del juez: la de `reports/calibracion/huella_juez.txt` (juez v3, ADR-25); `evaluar.py` la
  exige con `--exigir-huella` y, siempre, con más de un ensayo por escenario.
- Resultado frente a la meta de RNF-16 · Tasa de respuestas correctas (85 %): **90,0 %** de los 60
  escenarios (3 ensayos cada uno; Wilson de 79,9 % a 95,3 % con n = 60, bootstrap de 83,3 % a
  96,1 %) y pass^3 de 0,85. La estimación puntual supera la meta; el límite inferior del intervalo
  no (`reports/corrida-3/metricas.json`).

## 2. Contexto y desviaciones del plan

- Corridas 1 y 2 y sus correcciones: `reports/corrida-1/`, `docs/resumenes/correcciones-corrida-1.md`,
  `reports/corrida-2/` y `docs/resumenes/b15.md`.
- Correcciones del instrumento después de la corrida 1 y juez v3: ADR-25.
- Desviaciones frente al plan:
  - Una segunda ronda de correcciones después de la corrida 2 (PR #49 cerrado, #50 reemplazado por el
    #72, #51 fusionado) y las correcciones de la usabilidad y de la revisión externa con un asistente de
    IA (Claude, en una conversación distinta de la que desarrolló el código), cuyos hallazgos los
    autores contrastaron con las fuentes oficiales y aprobaron (PR #59 a #68).
  - Tres ensayos generales de un ensayo antes de la corrida 3 (2b, 2c y 2d), cada uno con una regla
    fijada antes de ver el resultado; la 2c no la cumplió y llevó a las fechas y las reglas por código
    (PR #72 y #73), verificadas con sondas y con la 2d (`docs/resumenes/b16.md`).
  - La muestra de calibración salió de la corrida 2b, no de la 2, porque la primera se descartó
    (sección 7).
  - Una auditoría de seguridad y sus correcciones (PR #69 y #70; `docs/resumenes/auditoria_seguridad.md`).
  - La revisión de trazas se corrió dentro del backend desplegado (este equipo no tiene la llave de
    LangSmith), y el reporte se armó con `--solo-reporte`.

## 3. Criterios de entrada de la corrida 3

Se registran también en `reports/corrida-3/criterios_de_entrada.md`, como en la corrida 1.

| Criterio | Cómo se verifica | Resultado |
|---|---|---|
| El sistema desplegado responde `/health` | `curl https://<subdominio>.duckdns.org/health` | Cumple: `ok`, con PostgreSQL, Chroma y RealSit en `ok`, antes y después de la corrida |
| CI en verde | `gh run list --branch main --workflow CI` | Cumple: CI en verde en el commit desplegado y en `main` |
| Corpus cargado | Salida de la ingesta de `deploy/desplegar.sh` | Cumple: 1.149 fragmentos (73, 562, 491 y 23 por colección), sin embeddings nuevos |
| Juez calibrado | `tests/test_preparacion_b16.py` y `--exigir-huella` | Cumple: la huella del juez es la de la calibración (`afecd5c1…`) |
| Sin cambios de código desde la última fusión | `git log` frente al commit desplegado | Cumple: `d3dab00`; lo posterior a la corrida son documentos, reportes y, en el cierre de B16, el instrumento de evaluación (`src/evaluacion` y `scripts`), no el código del sistema |
| Referencias aprobadas, incluidas las de R1 (nuevas en la corrida 3) | Campo de aprobación de cada escenario; la corrida se detiene sin `--sin-aprobar` | Cumple: los 60 aprobados por Rodolfo (PR #67), R1 aprobadas en B15, R3 y R4 desde la corrida 1 |
| Verificador de referencias (A7) sin nada sin resolver | `uv run python scripts/verificar_referencias.py` | Cumple: 65 escenarios y 171 cifras, 0 sin resolver |
| LangSmith encendido (la corrida usa `--trazas`, RNF-05 · Registro auditable) | Trazas de una prueba de humo | Cumple: 4.422 ejecuciones de la corrida revisadas en el servidor |
| Modo de evaluación encendido solo durante la corrida (A9) | `desplegar.sh --evaluacion` al empezar y sin él al terminar, verificado desde afuera | Cumple: se encendió para la 2d, siguió en la corrida 3 y en las no funcionales, y se apagó al terminar; desde afuera, el reloj simulado se ignora y la meta no trae campos de evaluación |

## 4. Resultados del nivel de sistema (corrida 3)

Contra `d3dab00`, 3 ensayos por escenario, juez v3 congelado (`reports/corrida-3/`).

| Conjunto | Tasa de la meta (Wilson; bootstrap) | Estricta | pass@1 / pass@3 / pass^3 |
|---|---|---|---|
| Principal (60) | **90,0 %** (79,9 % a 95,3 %; 83,3 % a 96,1 %) | 75,0 % | 0,90 / 0,95 / 0,85 |
| R1 · Generalización (10 variantes) | 43,3 % (19,0 % a 71,4 %) | 23,3 % | 0,43 / 0,60 / 0,30 |
| R3 · Encadenados (3) | 100 % | 55,6 % | 1,00 / 1,00 / 1,00 |
| R4 · Seguridad (2) | 100 % | 100 % | 1,00 / 1,00 / 1,00 |

- Veredictos del juez en el principal (180 ensayos): 137 correctas, 37 parcialmente correctas y 6
  incorrectas; alucinación en 7 (3,9 %); cita una norma en el 60,6 % y la cita sustenta en el
  60,0 %; cobertura completa en el 78,3 %; claridad media de 4,67 de 5.
- Sin errores técnicos en los 249 turnos.
- R1 (las variantes parafraseadas de Dayanna, que solo corren en la corrida 3) quedó muy por debajo
  del principal: la generalización a otras formas de preguntar es la debilidad más clara del sistema
  (sección 9).

## 5. Componentes e integración

- Enrutamiento (100 consultas etiquetadas, 20 por clase): exactitud de 99,0 %, kappa de 0,99 y F1
  macro de 0,99, frente a 20,0 % de la clase mayoritaria. Por clase, F1 de 0,976 (IPU), 1,000 (ICA),
  0,974 (general), 1,000 (OCR) y 1,000 (fuera de alcance); el único error, una consulta general
  clasificada como IPU (`reports/corrida-3/matriz_confusion_componentes.png`).
- Agentes contra su nodo (34 escenarios de un turno, sin el orquestador): **30 de 34 (88,2 %)**,
  la cifra del nivel de componentes.
  - **Cifra original, con un defecto del instrumento:** 11 de 34 (32,4 %). Los componentes corrían
    sin el modo de evaluación, así que el agente no guardaba los fragmentos, los datos de las
    herramientas ni las notas, y el juez solo recibía los contextos, que llegaban vacíos en los 34
    casos (también en la corrida 1). El juez calificó sin la evidencia: marcó como «sin fuente»
    datos de las herramientas (por ejemplo, el saldo de ICA-07 o el valor liquidado de IPU-03) y
    textos de los fragmentos. Es el mismo defecto F1 que ADR-25 corrigió en el nivel de sistema.
  - **Corrección:** los componentes corren con el modo de evaluación y el juez recibe contextos,
    datos de las herramientas y notas, igual que en el nivel de sistema, con una prueba que falla
    con el código anterior (`tests/test_evaluacion_calibracion.py`).
  - **Repetición:** una sola vez, solo «agentes contra su nodo», con el juez v3 y la huella exigida;
    el enrutamiento no se repitió. Los originales se conservan como
    `componentes_agentes_sin_evidencia.jsonl` y `componentes_juez_sin_evidencia.jsonl`.
  - **No superados en la repetición:** GEN-02 (menciona sin fuente el botón del funcionario), IPU-09
    (omite los topes de la Ley 1995 de 2019), IPU-11 e IPU-14. En IPU-11 e IPU-14, el juez marcó
    como sin fuente la matrícula de un predio de la sesión: en los componentes, el juez no recibe los
    predios de la sesión, una limitación que queda del instrumento.
  - La causa principal del 32,4 % era el instrumento, no los agentes. Corridos sin el orquestador,
    los agentes buscan con el texto del contribuyente y no con la consulta que escribe el
    orquestador; el nivel de sistema (90,0 %) es el que mide al sistema completo.
- RAGAS (110 casos, `gpt-4.1-mini`), frente a Bahçeci y colaboradores: precisión del contexto de
  66,1 % (75,2 %), exhaustividad del contexto de 82,4 % (86,6 %), fidelidad de 84,8 % (92,6 %) y
  relevancia de la respuesta de 68,1 % (91,3 %). El reporte de la corrida 3 da el promedio de todos
  los casos, sin separar los que tienen sesión.
- RAGAS sin sesión (66 de los 110 casos con los cuatro valores, de escenarios con `sesion: null`;
  calculado de `reports/corrida-3/ragas.jsonl`), la medida limpia de la recuperación que se usó en
  las corridas 1 y 2: precisión del contexto de 81,4 %, exhaustividad de 81,2 %, fidelidad de 84,6 % y
  relevancia de 71,3 %. Con sesión, el contexto que recibe RAGAS mezcla los datos de las herramientas
  con los fragmentos (ADR-25).
- Análisis de sensibilidad de la relevancia (aparte; no reemplaza la cifra oficial). En los 66
  casos sin sesión se volvió a medir la relevancia quitando de la respuesta la lista final «Fuentes:»
  y las notas fijas del sistema. Cambiaron 60 de las 66 respuestas, que conservaron en promedio el
  85 % del texto. La media no cambió: 71,3 % en los dos casos. Con una tolerancia de 1 punto, 15 casos
  subieron, 8 bajaron y 43 quedaron iguales, con una diferencia media absoluta de 1,5 puntos. Costó
  unos US$0,09 de OpenAI. La relevancia más baja que la de Bahçeci no se explica por esos anexos
  (`reports/corrida-3/sensibilidad_relevancia.md`, `.jsonl` y `.py`).

## 6. Pruebas no funcionales

Se repitieron en B16, contra `d3dab00`, las que dependen del despliegue (`reports/no_funcionales/`;
las de B15 quedan en `reports/no_funcionales/corrida-2/`):

| Requerimiento | Resultado |
|---|---|
| RNF-01 · Tiempo de respuesta | Sin fragmentos: p50 de 2.299 ms y p95 de 3.934 ms, 54 de 54 bajo 8 s. Con RAG: p50 de 6.379 ms y p95 de 13.393 ms, 120 de 120 bajo 15 s (servidor) |
| RNF-02 · Escalamiento horizontal | Con dos réplicas, el turno 1 lo atendió `backend-1`; con esa réplica detenida, el turno 2 de la misma conversación lo atendió `backend-2`, y los dos quedaron registrados (`replicas.json`) |
| RNF-08 · Tiempos de espera y degradación | 8 de 8 fallas inyectadas escalan por «fallo de servicio», con HTTP 200 y sin error técnico visible (`fallas_inyectadas.json`) |
| RNF-15 · Volúmenes persistentes | Conteos iguales antes, después de reiniciar y después de recrear: 594 conversaciones, 669 interacciones, 88 casos, 3.854 puntos de control y 1.149 fragmentos (`volumenes.json`) |
| RF-SYS-02 · Alcance de solo lectura | Huella de RealSit idéntica antes y después (`4479d036…`, `huella_realsit.txt`) |
| RNF-03 · Protección de datos personales y RNF-05 · Registro auditable | 4.422 ejecuciones de la corrida 3 sin identificadores (`reports/corrida-3/trazas.json`) |

RNF-06 · Horario de atención: la disponibilidad se midió con el registro completo del monitor del
servidor (`/health` cada 5 minutos desde el crontab, `reports/no_funcionales/disponibilidad.md`;
`salud.log` con días relativos). El monitor existe desde B15, porque el de GitHub Actions nunca
corrió, así que el registro cubre 43,0 horas (517 chequeos).

| Medida | Chequeos con 200 | Disponibilidad |
|---|---|---|
| **Oficial: horario hábil, todo el registro** | 135 de 157 | **85,99 %** |
| Todas las horas | 490 de 517 | 94,78 % |
| Horario hábil sin las ventanas de despliegue | 120 de 142 | 84,51 % |
| Horario hábil desde la corrección del PR #54 | 135 de 135 | 100,00 % |

**No alcanza la meta del 99 %.** La cifra oficial se calculó con el registro hasta el cierre de B16 y
se reporta tal cual. Su causa completa:

- **El defecto existía desde el despliegue.** Cada chequeo de `/health` creaba un cliente nuevo de
  Chroma sin cerrarlo. Unas dos horas después de cada despliegue, el backend agotaba sus descriptores
  de archivo y dejaba de responder, y Caddy devolvía 502 (PR #54).
- **El registro empezó durante una de esas caídas.** El monitor del servidor empezó a registrar en
  B15, justo durante una de ellas. Las 27 fallas del registro son de esa única caída: 27 chequeos
  seguidos con el commit `4e94e7a`, en las primeras 2,2 horas, 22 de ellos en horario hábil.
- **Se corrigió la causa.** El PR #54 crea un solo cliente por proceso y trae una prueba de regresión
  (`tests/test_api.py::test_el_cliente_de_chroma_se_crea_una_sola_vez`). Desde el despliegue de la
  corrección no hubo ninguna falla: 490 de 490 chequeos en 40,8 horas, 135 de 135 en horario hábil.
  Eso incluye toda la corrida 3, con los 30 chequeos del commit `d3dab00`.
- **El registro es corto.** Con unos 160 chequeos en horario hábil, cada uno pesa más de medio punto
  (0,64 puntos). El periodo se fijó antes de medir, así que la cifra se reporta tal cual. Antes de
  B15 no hay datos, porque el monitor de GitHub Actions nunca corrió.
- **El chequeo sale del mismo servidor.** Mide el proxy y el backend, no la red externa.

La disponibilidad es la prueba de RNF-06 · Horario de atención según la sección 6.7, y la matriz de
trazabilidad la toma como evidencia (sección 11): con la meta incumplida, RNF-06 vale 0.

## 7. Calibración del juez

Muestra de 30 respuestas de la corrida 2b, estratificadas por el veredicto del juez (R2: las 7 no
aprobadas y 23 aprobadas), calificadas a ciegas y sin ayuda de IA por Rodolfo y Dayanna, cada uno por
su lado, y su consenso (las 24 filas en que coincidieron se copiaron de forma mecánica; las 6
diferencias las decidieron en una llamada). La primera muestra, de la corrida 2, se descartó porque
sus hojas se llenaron con ayuda de un chat externo de IA (`reports/calibracion/descartada_corrida-2/`).
Juez v3, huella `afecd5c1…`, la misma de las corridas 2b a 3 (A5).

| Comparación | Kappa binario (IC 95 %) | Kappa ponderado de 3 niveles (IC 95 %) | Acuerdo observado |
|---|---|---|---|
| Juez frente al consenso | −0,062 (−0,170 a 0,000) | 0,062 (−0,231 a 0,366) | 22 de 30 (binario); 19 de 30 |
| Entre los evaluadores | 0,000 (0,000 a 1,000) | −0,111 (−0,200 a 0,000) | 29 de 30 (binario); 24 de 30 |

El kappa es bajo aunque el acuerdo observado sea alto: las personas aprobaron casi todas las
respuestas (el consenso, 29 de 30) y ninguna calificó «incorrecta», así que el acuerdo esperado por
azar es casi igual al observado (paradoja del kappa). Con 23 aprobadas por el juez y 29 por el
consenso, el kappa binario no podía pasar de unos 0,20. El PABAK binario es de 0,47 (juez y
consenso) y de 0,93 (evaluadores). En 7 de las 8 diferencias binarias, el juez no aprobó lo que el
consenso aprobó: el juez fue más estricto que las personas, así que la tasa que mide tiende a quedar
por debajo de la que darían ellas (`reports/calibracion/kappa.json`, `docs/resumenes/b15.md`).

## 8. Usabilidad

Los dos autores aplicaron las tareas, el SUS y la evaluación heurística de Nielsen, cada uno por su
lado, contra el sistema desplegado (ADR-21; `docs/usabilidad/rodolfo/` y `docs/usabilidad/dayanna/`).

- **SUS:** Rodolfo, 80,0; Dayanna, 97,5; promedio, 88,75. En el SUS de Rodolfo, el ítem 6 decía 0
  por error; él confirmó que es 1 (anotado en el archivo).
- **Evaluación heurística:** 6 anotaciones (2 de Rodolfo y 4 de Dayanna) de 4 problemas distintos
  (dos los anotaron los dos). Tres se corrigieron antes de la corrida 3 y el del CIIU, en parte:

| Problema | Heurística | Gravedad | Cómo se atendió |
|---|---|---|---|
| La lista de usuarios de prueba no se leía en modo oscuro (los dos) | 8 | 4 y 2 | PR #57 |
| Las fotos del celular pasaban de 5 MB (los dos) | 5 | 4 y 4 | El widget y el backend las reducen (PR #60) |
| Un recibo apaisado real salió como «recortado» (Dayanna) | 9 | 4 | El modelo decide primero si es un recibo; la proporción solo cuenta con campos faltantes (PR #59), probado con recibos sintéticos apaisados |
| Al pedir el código CIIU no dice dónde encontrarlo (Dayanna) | 10 | 3 | En parte: entrada en el glosario con su fuente de la DIAN (PR #64); la indicación en el agente se revirtió (PR #66) y queda como trabajo futuro |

- **Observaciones de contenido** de Dayanna (C1 y C2), aparte de la evaluación heurística porque se
  escribieron con ayuda del chat del documento: la lista de fuentes completa y cuándo aplican los
  complementarios del ICA (PR #63 y #65).
- En una prueba se cargó un recibo real con datos de personas reales, contra RNF-04 · Uso exclusivo
  de datos sintéticos: se borró del servidor y de LangSmith, no se usó en ninguna prueba, y su causa
  en las trazas se corrigió (`docs/resumenes/b15.md`, punto 9; PR #69).

## 9. Análisis de fallas

Escenarios con algún ensayo no superado en la corrida 3 (`reports/corrida-3/fallas.md` trae cada
ensayo con la justificación del juez), con su causa técnica, su familia de MAST y su historia en las
corridas anteriores (sí: superado; no: no superado).

| Escenario | Superados de 3 | Causa (familia de MAST) | 1 / 2 / 2b / 2c / 2d |
|---|---|---|---|
| GEN-02 | 0 | Enrutamiento y escalamiento: transfiere a un funcionario en vez de responder que el asistente no presenta declaraciones ni hace pagos (diseño del sistema) | no / no / no / no / no |
| IPU-14 | 0 | Recuperación y generación: niega el alivio de intereses del Acuerdo 1084 de 2026 y no da el saldo (verificación de la tarea). Con la búsqueda que escribe el orquestador, el art. 7 del Acuerdo 1084 no llegó a los 5 fragmentos en ningún ensayo (llegaron el art. 5 del Acuerdo 1084, artículos del Decreto 807 y el art. 6 de la Resolución SDH-000195); en la prueba de componentes, con el texto del contribuyente como búsqueda, el agente recuperó el art. 7 y explicó el alivio (60 %, 21 de diciembre de 2026) | no / no / no / no / no |
| IPU-13 | 0 | Recuperación en los ensayos 1 y 3: no llega el art. 4 de la Resolución SDH-000195 y la respuesta no dice «30 de abril» (verificación de código; diseño del sistema). En el ensayo 2 el artículo llegó y se citó, pero la respuesta omitió la fecha (generación; verificación de la tarea). El juez la da como parcialmente correcta en los tres | sí / no / sí / no / sí |
| AIA-01 | 1 | Enrutamiento: ante un saludo, una vez lo clasificó como fuera de alcance y otra escaló sin necesidad (diseño del sistema) | no / sí / sí / no / sí |
| IPU-15 | 1 | Generación: no da el valor de la cuota («845.000», verificación de código); el juez la da como correcta o parcial (verificación de la tarea) | sí / sí / sí / sí / sí |
| MULTI-03 | 1 | Generación: afirma sin fuente quién paga el predial; omite la fusión de tributos y la base (verificación de la tarea) | no / sí / no / no / no |
| ICA-04 | 2 | Generación: un ensayo con una afirmación sin fuente (verificación de la tarea) | no / sí / sí / sí / sí |
| ICA-07 | 2 | Generación: un ensayo atribuye sin fuente un valor al 4.º bimestre (verificación de la tarea) | no / no / sí / sí / sí |
| IPU-04 | 2 | Generación: un ensayo con una afirmación sin fuente; omite la fusión y los rangos (verificación de la tarea) | no / no / no / no / sí |

En R1 (generalización) no pasaron, de 3: VAR-01 (0; responde con las fechas de pago y omite la
causación el 1 de enero), VAR-03 (0; no dice que el plazo venció y en 2 de 3 pide iniciar sesión para
una duda general), VAR-06 (0; no dice «30 de abril» y se desvía hacia la declaración privada),
VAR-08 (0; no dice «bimestre» y en 2 de 3 trae afirmaciones sin fuente), VAR-05 (1; omite
«divulgación adicional»), VAR-09 (1; omite el cambio de régimen de 2027) y VAR-02 (2; una advertencia
sin fuente). Las paráfrasis cambian la clasificación o la búsqueda (por ejemplo, una pregunta general
tomada como personal) y la respuesta deja de cubrir lo esencial de la referencia.

Desglose de los 17 ensayos de R1 no superados, clasificados uno por uno en una revisión externa con un asistente de IA (Claude, en una conversación distinta de la que desarrolló el código), y aprobados por los autores (la causa y la
familia de MAST de cada ensayo están en `reports/corrida-3/fallas.md`):

| Grupo | Ensayos | Qué pasó |
|---|---|---|
| a. La variante admite otra lectura | 3 (VAR-01, los tres) | «Cuando sale el impuesto cada año y cuándo termina?» no pregunta por la causación: el sistema la leyó como la expedición de la factura y los plazos de pago, con las fechas correctas (en el ensayo 2 atribuyó las cuotas del SPAC a un artículo que no las trae), y omitió la causación del 1° de enero y el periodo gravable |
| b. Pregunta en primera persona tomada como personal | 2 (VAR-03, ensayos 2 y 3) | El sistema pidió iniciar sesión sin dar el plazo general: comportamiento de diseño de RF-AUT-04 · Aviso de sesión requerida |
| c. Solo falló la verificación de texto heredada del escenario de origen | 6 (VAR-05, ensayos 1 y 2; VAR-06, ensayos 1 y 3; VAR-08, ensayo 2; VAR-09, ensayo 1) | Faltó el término que exige la verificación («divulgación adicional», «30 de abril», «bimestre» y «391 UVT»); el juez las calificó como parcialmente correctas y sin alucinación. En VAR-06 es la misma omisión de su origen, IPU-13, que tampoco la supera en el principal |
| d. Errores del sistema | 6 | Afirmaciones sin fuente (VAR-02, ensayo 2: la advertencia de intereses de mora; VAR-08, ensayo 1: los límites de tarifa de la ley nacional presentados como los de Bogotá; VAR-08, ensayo 3: que la tarifa depende del CIIU); un plazo vencido dicho en presente, sin decir que ya venció (VAR-03, ensayo 1); no concluir que se puede pagar con la factura sin declarar (VAR-06, ensayo 2), y omitir el cambio de régimen de 2027 y atribuir un fragmento a otro artículo (VAR-09, ensayo 2) |

En R1, el juez aceptó 19 de los 30 ensayos (correcta o parcialmente correcta, sin alucinación) y las
verificaciones de código pasaron en 15 de 30 (`reports/corrida-3/calificados.jsonl`). La tasa
oficial de R1 sigue siendo **43,3 %** (13 de 30 ensayos superados): el desglose la explica, no la
reemplaza.

Ninguna falla es de acceso a datos ni de identificadores en las trazas. Las fallas que persisten
desde la corrida 1 (GEN-02 e IPU-14) y las de recuperación (IPU-13) quedan como trabajo futuro. Para
IPU-14, el trabajo futuro concreto es buscar también con el texto del contribuyente y fusionar las
dos listas de fragmentos (como propuso el PR #49, que se cerró sin fusionar). Las correcciones se
cerraron para congelar el código antes de esta corrida.

**Observación del instrumento (IPU-14).** El reloj del escenario (1 de octubre de 2026) es anterior
a la publicación del Acuerdo 1084 (9 de octubre de 2026), que la referencia da por publicado. No
cambia el resultado (el sistema no da el alivio en ningún caso), pero el escenario debería usar un
reloj posterior a la publicación.

## 10. Latencia y costo

- Latencia (principal, `reports/corrida-3/latencias.png`): sin fragmentos, servidor p50 de 2.299 ms y
  p95 de 3.934 ms, cliente p50 de 2.273 ms y p95 de 4.191 ms; con RAG, servidor p50 de 6.379 ms y p95
  de 13.393 ms, cliente p50 de 6.152 ms y p95 de 12.349 ms. Todos los turnos del principal dentro de
  las metas de RNF-01 · Tiempo de respuesta (8 s y 15 s); también los de R3 y R4. En R1, 27 de 28
  turnos con RAG quedaron bajo 15 s (el más lento, 15.859 ms).
- Costo de la corrida 3: US$10,82 en Anthropic (sistema 2,05, juez 7,17 y componentes 1,61, con los
  componentes originales) y US$1,65 en OpenAI (RAGAS). El sistema costó US$0,0082 por turno (249
  turnos); el juez es lo que más pesa en una corrida. La repetición de «agentes contra su nodo» del
  cierre de B16 costó US$1,29 (agentes 0,07 y juez 1,22). Desde entonces `reports/corrida-3/costos.md`
  muestra los componentes de la repetición (US$11,18 en Anthropic); el gasto de los originales
  (US$0,93) queda en los archivos `_sin_evidencia`.
- Costo total del proyecto: los 40 `costos.md` suman US$33,82 en Anthropic y US$2,72 en OpenAI. Con
  los componentes originales de la corrida 3 (US$0,93), las pruebas con modelos reales del cierre
  (unos US$0,13) y los gastos que los resúmenes anotan sin `costos.md` (sondas, humo e ingestas, unos
  US$1,7), el total es de unos US$36,5 en Anthropic y US$2,8 en OpenAI. Es una estimación. Frente al
  presupuesto de la sección 7 del plan (US$25 en Anthropic y US$10 en OpenAI), Anthropic lo superó
  en unos US$11,5. No estaban en el presupuesto las rondas de correcciones posteriores a la corrida
  2, cada una verificada con el juez, los ensayos generales 2b a 2d ni el cierre de B16.

## 11. Trazabilidad y criterios de salida

| Criterio de salida (sección 6.9) | Resultado |
|---|---|
| Tasa de escenarios superados de 85 % o más | Cumple en la estimación puntual (90,0 %); el límite inferior de Wilson es 79,9 % |
| Ningún escenario de acceso ni de trazas fallido | Cumple: los de acceso y R4 superados en los 3 ensayos; 0 identificadores en las trazas |
| Latencias medidas | Cumple: servidor y cliente, con y sin recuperación |
| Matriz de trazabilidad completa (`reports/trazabilidad.md` y `.csv`) | Cumple: los 65 requerimientos calificados con su evidencia (78,5 %) |
| Reporte generado | Cumple: `reports/corrida-3/reporte.md` y este documento |

Calificación de cada uno de los 65 requerimientos (cumple, cumple en parte o no cumple) y el
porcentaje global de cumplimiento (secciones 6.11 y 8.17 de la especificación; sección 11 del plan),
desde `reports/trazabilidad.md`: **78,5 %** de cumplimiento global, con los **65 requerimientos
calificados** (51 con 100 %, 14 con 0 % y ninguno con 80 %). La calificación es mecánica: un
requerimiento vale 0 si falla alguna de sus evidencias, incluido un solo ensayo de uno de sus
escenarios. Con 3 ensayos por escenario es más estricta que en la corrida 2 (83,3 % de 48
calificados con 1 ensayo).

La regla no cambió (0 si falla alguna evidencia y 100 si pasan todas). En el cierre de B16 se
completó la evidencia que antes no tenía resultado (antes: 74,0 %, con 50 calificados y 15 sin
calificar). Solo siguen sin resultado las 6 pruebas
`test_consultas_semanticas_con_los_embeddings_reales` (gastan embeddings reales), evidencia de RF-IPU-01,
RF-ICA-01 y RF-GEN-01; no cambian su nota, porque esos tres ya valen 0 por sus escenarios:
- el script lee el JUnit de las pruebas de Playwright (`web/tests/web.spec.js`), sin cambiar cómo se
  nombran las evidencias: un flujo pasa si pasan todas sus variantes (escritorio y 390 px);
- las tres pruebas con modelos reales (la de humo y las dos de OCR) se corrieron una vez con
  `REALTIX_PRUEBAS_REALES=1` y pasaron (unos US$0,13);
- `reports/no_funcionales/disponibilidad.json` es la evidencia de RNF-06 · Horario de atención,
  porque la sección 6.7 la pone como su prueba; con la meta incumplida, RNF-06 vale 0.

Los reportes JUnit están en `reports/junit/` (sin marcas de tiempo): `pytest.xml` (764 superadas y 9
omitidas), `pytest_modelos_reales.xml` (3 de 3) y `playwright.xml` (27 superadas y las 4 de las
capturas reales omitidas). La matriz se regenera con:

```bash
uv run python scripts/trazabilidad.py --junit reports/junit/pytest.xml \
  --junit reports/junit/pytest_modelos_reales.xml --junit-web reports/junit/playwright.xml \
  --disponibilidad reports/no_funcionales/disponibilidad.json \
  --resultados reports/corrida-3/calificados.jsonl
```

Los 14 requerimientos con 0, con los escenarios que los bajaron (ensayos superados de 3) y la causa
(secciones 6 y 9):

| Requerimiento | Escenarios superados | Escenarios que lo bajaron | Causa |
|---|---|---|---|
| RF-SYS-06 · Aviso de interacción con IA (provisional) | 1 de 2 | AIA-01 (1 de 3) | Clasificación de un saludo como fuera de alcance y un escalamiento innecesario; el aviso de IA salió en los tres ensayos |
| RF-UI-03 · Identificación del interlocutor | 0 de 1 | AIA-01 (1 de 3) | La misma de RF-SYS-06 · Aviso de interacción con IA (provisional); la respuesta se identificó como del asistente en los tres ensayos |
| RF-AUT-01 · Verificación de identidad | 11 de 14 | ICA-04 (2), ICA-07 (2) e IPU-15 (1) | Generación (una afirmación sin fuente o un dato omitido), no la verificación: ACC-01 a ACC-03 pasaron 3 de 3 |
| RF-ORQ-03 · Consultas multiagente | 2 de 3 | MULTI-03 (1 de 3) | Generación: una afirmación sin fuente y la omisión de la fusión de tributos y de la base del predial |
| RF-IPU-01 · Consultas conceptuales de IPU | 2 de 4 | IPU-04 (2) y MULTI-03 (1) | Generación: afirmaciones sin fuente y omisión de la fusión y de los rangos de tarifa |
| RF-IPU-02 · Estado de cuenta e historial | 7 de 8 | IPU-15 (1) | Generación: no da el valor de cada cuota (el saldo y las fechas, correctos) |
| RF-IPU-04 · Plazos y descuentos | 4 de 7 | IPU-13 (0), IPU-14 (0) e IPU-15 (1) | Recuperación en 2 de 3 ensayos y generación en el otro (IPU-13: no da el plazo de la factura), recuperación y generación (IPU-14: niega el alivio de intereses) y generación (IPU-15) |
| RF-IPU-05 · Citación de la norma | 6 de 9 | IPU-04 (2), IPU-13 (0) e IPU-14 (0) | Las de IPU-04, IPU-13 e IPU-14 arriba; en IPU-04, además, una cita atribuida a un numeral que no lo dice |
| RF-ICA-01 · Consultas conceptuales de ICA | 4 de 5 | MULTI-03 (1 de 3) | Generación, en la parte del predial; la parte del ICA coincidió con la referencia |
| RF-ICA-02 · Estimación por actividad | 3 de 4 | ICA-04 (2 de 3) | Generación: deduce la periodicidad sin fuente; la tarifa y el valor estimado, correctos |
| RF-ICA-03 · Fechas de declaración | 5 de 6 | ICA-07 (2 de 3) | Generación: atribuye a un bimestre el valor de toda la vigencia; las fechas, correctas |
| RF-GEN-01 · Consultas transversales | 2 de 3 | GEN-02 (0 de 3) | Enrutamiento y escalamiento: transfiere a un funcionario en vez de responder que el asistente no presenta declaraciones ni hace pagos |
| RF-GEN-03 · Respuesta sustentada en fuentes | 6 de 7 | GEN-02 (0 de 3) | La misma de RF-GEN-01 · Consultas transversales |
| RNF-06 · Horario de atención | 2 de 2 | — (sus pruebas y los escenarios de horario pasan) | La disponibilidad, su prueba según la sección 6.7, no cumple la meta del 99 % (85,99 %, sección 6) |

RNF-01 · Tiempo de respuesta queda con 100 %: además de sus pruebas, en la corrida 3 se midieron 54 de
54 turnos sin fragmentos bajo 8 s y 120 de 120 con RAG bajo 15 s en el principal (sección 10). Los
escenarios de OCR de la corrida (OCR-01 a OCR-07, con el modelo de visión real) se superaron en los
tres ensayos.

## 12. Impedimentos, riesgos y lecciones (cierre CTFL v4.0.1)

- **Impedimentos y cómo se resolvieron:**
  - El monitor programado de GitHub Actions nunca corrió: el monitor pasó al crontab del servidor
    (B15).
  - Un 502 por una fuga de conexiones en `/health` (PR #54).
  - Avisos de seguridad de las dependencias (PR #56, ADR-26).
  - Un recibo real cargado en una prueba manual: se borró y se corrigió su causa en las trazas
    (`docs/resumenes/b15.md`, punto 9; PR #69). El borrado en LangSmith quedó aceptado y su
    confirmación, pendiente.
  - La primera muestra de calibración se llenó con ayuda de una IA externa: se descartó y se repitió.
  - La corrida 2c no cumplió su regla: se analizó cada falla y se pasó a las fechas y las reglas por
    código, verificadas antes de congelar.
  - Este equipo no tiene la llave de LangSmith: la revisión de trazas se corrió en el backend
    desplegado.
- **Riesgos que no se mitigaron y fallas que no se corrigieron:**
  - La generalización (R1, 43,3 %) quedó baja. Los agentes contra su nodo dieron 32,4 % por un defecto
    del instrumento (el juez no veía las herramientas ni las notas); con el instrumento corregido,
    88,2 % (sección 5).
  - GEN-02 e IPU-14 fallan desde la corrida 1. En IPU-14, la búsqueda que escribe el orquestador no
    trae el art. 7 del Acuerdo 1084, que sí llega con el texto del contribuyente (sección 9); el reloj
    del escenario es anterior a la publicación del acuerdo.
  - El kappa del juez frente a las personas es bajo, por la poca variación de la muestra, y el juez es
    más estricto que ellas.
  - La indicación de dónde encontrar el CIIU quedó solo en el glosario.
  - Un texto de 2002 del Decreto 352 (art. 26) sigue vigente en la base y apareció en una respuesta
    sobre tarifas.
  - El costo en Anthropic superó el presupuesto.
  - La disponibilidad medida (85,99 % en horario hábil) no alcanzó el 99 %, por la fuga de `/health`
    antes del PR #54; el registro cubre solo 43,0 horas (sección 6).
- **Observación menor (mecanismo interno en la respuesta):** en 8 de las 225 conversaciones de la
  corrida 3, la respuesta nombra el mecanismo interno («según la herramienta», «la herramienta de
  fechas», «los fragmentos», «las normas que me entregaron»): ACC-04, ensayo 1; IPU-08, ensayo 3;
  IPU-14, los tres; VAR-01, ensayo 3; VAR-06, ensayo 2, y VAR-09, ensayo 2. La regla común lo prohíbe,
  pero el verificador sin modelo solo detecta «fragmento [n]» y «consultar herramientas». No cambia
  ningún dato; ampliar el verificador queda como trabajo futuro.
- **Lecciones aprendidas:**
  - Fijar la regla de un ensayo antes de ver su resultado evitó corregir hacia adelante; con esa
    regla se revirtió una corrección que dañaba otro escenario (CIIU, PR #66).
  - Lo que debe ser exacto (si una fecha ya pasó, la regla de un régimen) lo decide mejor el código
    que el modelo; un verificador sin modelo hace cumplir la regla.
  - La calibración con personas exige que califiquen sin IA y con una muestra con suficientes
    casos negativos.
  - Las verificaciones automáticas de texto tienen límites: una persona revisó cada señal antes de
    decidir.
  - Una revisión de seguridad, aunque sea rápida y estática, encontró un problema real (las
    imágenes en las trazas).

## 13. Conclusiones

El sistema multiagente de IA desplegado superó el 90,0 % de los 60 escenarios en la corrida final,
con 3 ensayos por escenario (pass^3 de 0,85), por encima de la meta del 85 % de RNF-16 · Tasa de respuestas correctas en la
estimación puntual. Superó todos los escenarios de acceso, seguridad y conversaciones encadenadas,
sin errores técnicos, con las latencias del conjunto principal dentro de las metas, trazas sin identificadores, el
enrutamiento en el 99 %, los agentes contra su nodo en 88,2 % (con el instrumento corregido) y la
usabilidad con un SUS de 80,0 y 97,5. La generalización a otras formas de preguntar quedó en 43,3 %:
es el límite principal del prototipo. La disponibilidad medida (85,99 % en horario hábil) no alcanzó
el 99 %, por una fuga corregida al comienzo del registro, y con ella la matriz de trazabilidad queda
en 78,5 % con los 65 requerimientos calificados. El juez se validó y se congeló antes de la
corrida, y su calibración con personas mostró un juez más estricto que ellas; en el cierre de B16
se corrigió lo que el arnés de componentes le entrega al juez.
