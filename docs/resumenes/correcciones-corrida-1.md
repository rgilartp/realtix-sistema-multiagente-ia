# Correcciones de la corrida 1

Correcciones de `reports/corrida-1/fallas.md` (sección 8.15), en el orden de ese archivo, con los
ajustes de la revisión externa que aprobó Rodolfo. Cada grupo tuvo:

- su rama y su PR, con el protocolo completo;
- casos de regresión con datos inventados (A8);
- la verificación de sus escenarios contra la API local;
- una revisión independiente, cuyos hallazgos se corrigieron antes de fusionar.

La corrida 1 queda reportada tal como se midió: **48,3 %** (29 de 60).

## Qué se hizo

| PR | Falla | Qué cambió | Escenarios verificados |
|---|---|---|---|
| [#38](https://github.com/rgilartp/realtix-sistema-multiagente-ia/pull/38) `fix/instrumento` | F1, F3, F10 (instrumento, ADR-25) | El juez y RAGAS ven los datos de las herramientas, las notas, el recibo y el aviso de IA, anonimizados; normalización de «Distrital»; el detector de fuga descuenta los textos públicos | 11 de 11 de F1 (OCR-07, en el 2.º intento). F3 y F10, sin costo, sobre las respuestas de la corrida 1: 4 escenarios pasan el código y ninguna verificación aprobada cambia |
| [#39](https://github.com/rgilartp/realtix-sistema-multiagente-ia/pull/39) `fix/categoria-clasificada` | F2 | La API reporta la primera clasificación del turno; el caso escalado antes del agente lleva su categoría | 6 de 6 |
| [#40](https://github.com/rgilartp/realtix-sistema-multiagente-ia/pull/40) `fix/juez-afirmaciones` | Revisión externa del PR #38 | Juez v3: lista las afirmaciones sin fuente y la justificación antes del veredicto; A4 con el criterio de la meta y 3 repeticiones | A4: 9 de 9 criterios en las 3 repeticiones; recalificación de 17 ensayos: ninguno cambia |
| [#41](https://github.com/rgilartp/realtix-sistema-multiagente-ia/pull/41) `fix/ica` | F4, F8 | Periodicidad registrada por una regla del servicio, con avisos; `estimar_ica` en la primera ronda; `ica.v2` | 7 de 7 (ICA-02, después de la revisión; ACC-04 pasó a F7) |
| [#42](https://github.com/rgilartp/realtix-sistema-multiagente-ia/pull/42) `fix/anclaje-y-citas` | F5 | `comun.v3` (anclaje de toda afirmación; Ley 1995 condicional); verificador de citas sin modelo con una reescritura | IPU-01 sí; IPU-04, en 1 de 2 intentos; **GEN-02 no** |
| [#43](https://github.com/rgilartp/realtix-sistema-multiagente-ia/pull/43) `fix/aclaraciones` | F6 | Tres reglas de aclaración en `comun.v3`; `ipu.v2` alineado | AMB-01 e ICA-03 sí; **IPU-14 no** |
| [#44](https://github.com/rgilartp/realtix-sistema-multiagente-ia/pull/44) `fix/tarifas-por-ano` | F7 | `tarifas_predial` y `tarifa_ica`, sin sesión, con las cifras de `datos/` y su fuente | 2 de 2 (ACC-04, en el 2.º intento) |
| [#45](https://github.com/rgilartp/realtix-sistema-multiagente-ia/pull/45) `fix/acceso-previo` | F9 | Rechazo previo, sin modelo, de una matrícula ajena del mensaje (IPU, ICA y OCR) | 2 de 2 |
| [#46](https://github.com/rgilartp/realtix-sistema-multiagente-ia/pull/46) `fix/notas-y-formato` | F11, F12 | Se quitan las copias casi literales de una nota, sin tocar las cifras; coma decimal en el resumen del caso | 2 de 2. La nota repetida se resolvió sin API sobre las respuestas guardadas |

F13 queda para la calibración del umbral de B15. La mejora de la búsqueda se decide con la corrida 2,
como propone fallas.md.

## Requerimientos

- RNF-16 · Tasa de respuestas correctas (instrumento)
- RF-OBS-05 · Ejecución repetible de pruebas
- RNF-03 · Protección de datos personales
- RF-ORQ-01 · Clasificación de la consulta
- RF-OBS-02 · Matriz de confusión de enrutamiento
- RF-ORQ-03 · Consultas multiagente
- RF-ESC-03 · Resumen del caso
- RF-ICA-02 · Estimación por actividad
- RF-ICA-03 · Fechas de declaración
- RNF-08 · Tiempos de espera y degradación
- RF-IPU-05 · Citación de la norma
- RF-GEN-03 · Respuesta sustentada en fuentes
- RF-UI-02 · Contexto de la sesión
- RF-IPU-02 · Estado de cuenta e historial
- RF-IPU-03 · Liquidación estimada
- RF-AUT-02 · Restricción a predios propios
- RNF-09 · Lenguaje accesible

## Cómo se verificó

### Escenarios afectados

| Grupo | Superados | Pendientes |
|---|---|---|
| F1 (instrumento) | 11 de 11 | — |
| F3 y F10 (instrumento) | 4 de 4, sin costo | — |
| F2 | 6 de 6 | — |
| F4 y F8 | 7 de 7 | — |
| F5 | 2 de 3 | GEN-02 |
| F6 | 2 de 3 | IPU-14 |
| F7 | 2 de 2 | — |
| F9 | 2 de 2 | — |
| F11 | 2 de 2 | La nota repetida, en parte |

### Regresión de los 29 superados en la corrida 1

Se corrió con el juez v3 contra la API local (`reports/regresion-correcciones-corrida-1/`). ACC-01 no
se volvió a correr: se verificó en el PR #45.

- **26 de 29 se mantienen** (25 de 28 corridos, más ACC-01).
- **IPU-09:** el orquestador la trató como una consulta personal y pidió sesión.
- **IPU-13:** omitió el plazo de expedición de las facturas.
- **MULTI-01:** el juez v3 listó una afirmación que de verdad no tiene fuente: «Si pagas después del 9
  de octubre, se generarán intereses de mora». Según la instrucción de Rodolfo, no es una regresión de
  las correcciones; se anota y no se corrige en esta ronda.

**IPU-09 e IPU-13 no son regresiones de las correcciones.** Se repitieron, sin el juez, con el código
de hoy y con el de la corrida 1 (`805f2ef`):

- el clasificador pidió sesión en IPU-09 en 3 de 3 intentos con los dos códigos;
- el agente omitió el plazo en IPU-13 en 3 de 3 con los dos códigos.

Las dos pasaron en la corrida 1 por la variación del modelo. La evidencia está en
`variacion_sin_juez.json` y `variacion_sin_juez_antes_de_las_correcciones.json` de esa carpeta.

### Despliegue

- **Comando, en el servidor:** `./deploy/desplegar.sh --version main`.
- **Resultado:** «Desplegado: v0.9.0-55-g7695209 (modo de evaluación: false)», es decir, el `main` con las ocho correcciones.
- **Ingesta:** corpus `408d90bdb6af2d40`, sin cambios ni costo.
- **Salud:** `curl https://tg2-multiagente.duckdns.org/health` respondió HTTP 200 con `{"estado":"ok", …, "postgres":"ok","chroma":"ok","realsit":"ok"}`. Antes del despliegue respondía 502.

### Pruebas

La suite completa pasa en la CI en cada PR (en local, 680 passed y 8 skipped en el PR #45). En cada
grupo hubo:

- casos de regresión;
- `test_evaluacion_sobreajuste.py` en verde (A8);
- ruff y pre-commit.

### Gasto

| Concepto | US$ |
|---|---|
| Verificaciones de los escenarios afectados (14 ejecuciones) | 2,32 |
| Regresión de los 29 | 0,93 |
| Validación A4: juez v2 (2 ejecuciones) y juez v3 | 0,53 (0,08 de OpenAI) |
| Recalificación con el juez v3 (17 ensayos) | 0,57 |
| Consultas directas sin juez (humo, GEN-02, reescritura forzada, variación) | 0,07 |
| **Total** | **4,42 de 4,5** (4,35 en Anthropic y 0,08 en OpenAI) |

Gasto acumulado del proyecto: unos **US$9,57 de 25 en Anthropic** y **US$0,78 de 10 en OpenAI**.

## Decisiones tomadas y pendientes

- **Pendientes de recuperar, con su evidencia, para el análisis de la corrida 2:**
  - **GEN-02 (F5):**
    - escala por confianza (0,686 y 0,651 en local; 0,724 en la corrida 1), que es asunto de F13 y
      del umbral;
    - el agente general sigue diciendo dónde se paga o se presenta, sin fuente (es la candidata de la
      segunda ronda).
  - **IPU-14 (F6):** recuperación. El art. 7 del Acuerdo 1084, del alivio de intereses, no estuvo entre
    los 5 fragmentos. Desde `ipu.v2`, también la suficiencia.
  - **F11:** solo se quitan las copias casi literales; las paráfrasis libres siguen.
- **Variación del modelo** en IPU-09 (clasificación personal) e IPU-13 (plazo omitido): la mide la
  corrida 2.
- **Afirmación sin fuente en MULTI-01**, que detectó el juez v3: se anota.
- **Prompts:** cada archivo subió una sola versión en las correcciones (`comun.v3`, `ica.v2`,
  `ipu.v2`). Las verificaciones de los primeros PR usaron versiones intermedias de esos archivos; la
  corrida 2 mide el conjunto final.
- **ADR-23:** se propone agregar `categoria_clasificada` (y `duracion_escalamiento_ms`, que ya faltaba)
  a la lista de claves de `marcas`; la decisión no cambia.
- **Revisiones independientes:** encontraron hallazgos de severidad alta en los PR #41 (un diagnóstico
  falso de ICA-02), #42 (encabezados de citas que no se reconocían), #44 (un código CIIU que no está en
  la tabla de 2027) y #46 (oraciones con cifras que la regla podía quitar). Todos se corrigieron antes
  de fusionar.

## Cambios frente al documento de grado

Las filas nuevas de `docs/cambios_para_documento.md`:

- la nota de transparencia de la corrida 1 y del juez (ADR-25);
- el contrato de `meta` (`herramientas`, `notas` y `reescrituras`, solo en el modo de evaluación);
- la salida del juez v3 (sección 6.4);
- el verificador de citas (sección 3.3);
- las herramientas de tarifas sin sesión (sección 3.2);
- una fila de este resumen.

## Resumen para el documento

Después de la corrida 1 se corrigieron sus fallas en nueve cambios.

- **Instrumento.** Tres fallas eran del instrumento de evaluación: el juez y RAGAS no veían los datos
  de las herramientas ni las notas del sistema, la verificación de texto no reconocía «Decreto
  Distrital», y el detector de fuga marcaba textos públicos. Se corrigieron de forma general. El juez
  pasó a listar las afirmaciones sin fuente antes de su veredicto, y la validación con casos conocidos
  se repitió tres veces, con resultados estables.
- **Sistema.** Las ocho fallas restantes eran del sistema: la categoría que reportaba la API, la
  periodicidad del ICA, las afirmaciones y citas sin fuente, las aclaraciones, las tarifas por año sin
  sesión, el rechazo de un predio ajeno, las notas repetidas y el formato del resumen. Se corrigieron
  con reglas generales, en los prompts o sin modelo, cada una con su caso de regresión.

En la verificación local, la mayoría de los escenarios afectados se superaron. Dos no se recuperaron:
uno por una confianza cercana al umbral y otro por la recuperación. De los 29 escenarios que se habían
superado en la corrida 1, 26 se mantuvieron. De los otros tres, dos fallaron igual con el código
anterior a las correcciones, por la variación del modelo, y en el tercero el juez nuevo detectó una
afirmación sin fuente.
