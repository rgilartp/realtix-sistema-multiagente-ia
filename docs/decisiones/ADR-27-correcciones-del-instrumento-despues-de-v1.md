# ADR-27 · Correcciones del instrumento después de v1.0.0

**Estado:** aceptada, octubre de 2026 (Rodolfo aprobó las correcciones que pidió una revisión externa
con un asistente de IA después de la corrida 3; PR #76). **Fuente:** `docs/reporte_de_pruebas.md`
(secciones 5, 6, 10, 11 y 12), ADR-24 (A5) y ADR-25 (F1). No modifica la especificación ni la adenda.

## Contexto

La corrida 3 se hizo con el código congelado (`d3dab00`) y se etiquetó `v1.0.0`. Después, una
revisión externa con un asistente de IA (Claude, en una conversación distinta de la que desarrolló
el código), cuyos hallazgos los autores aprobaron, encontró dos problemas del instrumento de
evaluación, no del sistema:

- **Agentes contra su nodo (nivel de componentes).** `scripts/evaluar.py` armaba los componentes
  sin el modo de evaluación, así que el agente no guardaba los fragmentos, los datos de las
  herramientas ni las notas, y `como_ensayo` solo le pasaba al juez los contextos, que llegaban
  vacíos en los 34 casos (también en la corrida 1). El juez marcó como «sin fuente» datos de las
  herramientas (por ejemplo, el saldo de ICA-07 o el valor liquidado de IPU-03) y textos de los
  fragmentos. Es el mismo defecto F1 que ADR-25 corrigió en el nivel de sistema.
- **Matriz de trazabilidad incompleta.** 15 de los 65 requerimientos quedaban sin calificar, porque
  alguna de sus evidencias no tenía resultado en el JUnit de pytest: diez, una prueba de Playwright
  que corre en la integración continua; cinco, una prueba con modelos reales que la suite omite. Y
  la disponibilidad, que la sección 6.7 pone como la prueba de RNF-06 · Horario de atención, no
  entraba como evidencia.

## Decisión

1. **El juez de los agentes contra su nodo recibe toda la evidencia (F1).** Los componentes corren
   con el modo de evaluación (`settings_de_componentes`), y el juez recibe los contextos, los datos
   de las herramientas y las notas, igual que en el nivel de sistema. Una prueba de regresión
   (`tests/test_evaluacion_calibracion.py::test_el_juez_de_los_agentes_ve_herramientas_y_notas`)
   falla con el código anterior. El juez y su huella no cambian (`afecd5c1…`, la de la calibración).
2. **Repetición única.** Solo «agentes contra su nodo» (34 casos), una vez, con el juez v3 y
   `--exigir-huella`; el enrutamiento no se repite. Resultado: 30 de 34 (88,2 %), frente a 11 de 34
   (32,4 %) con el defecto. Costo: US$1,29.
3. **Matriz completa, con la misma regla** (0 si falla alguna evidencia, 100 si pasan todas):
   - `scripts/trazabilidad.py` lee el JUnit de Playwright: un flujo pasa si pasan todas sus
     variantes de tamaño, sin cambiar cómo se nombran las evidencias;
   - suma varios JUnit de pytest; las tres pruebas con modelos reales (la de humo y las dos de OCR)
     se corrieron una vez y pasaron;
   - toma `reports/no_funcionales/disponibilidad.json` como evidencia de RNF-06 · Horario de
     atención; con la meta incumplida, RNF-06 vale 0.

   Resultado: 78,5 %, con los 65 calificados (antes, 74,0 % con 50). Los JUnit están en
   `reports/junit/`.
4. **Análisis de sensibilidad de la relevancia de RAGAS, aparte.** La relevancia de los 66 casos sin
   sesión, sin la lista «Fuentes:» ni las notas fijas, dio 71,3 %, igual que la oficial; no la
   reemplaza (`reports/corrida-3/sensibilidad_relevancia.md`).
5. **El código del sistema no cambió.** `src/agents`, `src/services`, `src/api`, `src/data`,
   `src/store`, `src/integrations`, `web`, `datos`, `knowledge_base`, `deploy` y las dependencias
   siguen iguales a `d3dab00`; solo cambió el instrumento (`src/evaluacion` y `scripts`). La etiqueta
   `v1.0.0` no se movió.
6. **Se conservan las cifras originales.** Los resultados con el defecto quedan como
   `reports/corrida-3/componentes_agentes_sin_evidencia.jsonl` y
   `componentes_juez_sin_evidencia.jsonl`, y el reporte da las dos cifras: la original, con el defecto
   explicado, y la corregida, que es la del nivel de componentes.

## Alternativas

- **Dejar la cifra de componentes como se midió, solo con una nota:** se descartó, porque el 32,4 %
  medía la falta de evidencia del juez y no a los agentes; se reporta, pero no como la cifra vigente.
- **Repetir toda la corrida 3:** se descartó. El defecto solo afectaba a los componentes, y el nivel
  de sistema ya pasaba la evidencia completa al juez (ADR-25).
- **Calificar a mano los 15 requerimientos sin resultado:** se descartó; la matriz es mecánica, y la
  evidencia que faltaba se podía obtener corriendo las pruebas.

## Consecuencias

- Los agentes contra su nodo se califican con las mismas fuentes que tuvo el agente. Queda una
  limitación: en los componentes, el juez no recibe los predios de la sesión (IPU-11 e IPU-14).
- La cifra de componentes de la corrida 1 (19 de 34) tuvo el mismo defecto; no se repite.
- La matriz califica los 65 requerimientos. Solo siguen sin resultado 6 pruebas con embeddings
  reales, de requerimientos que ya valen 0 por sus escenarios.
- `reports/corrida-3/costos.md` muestra los componentes de la repetición; el gasto de los originales
  (US$0,93) queda en los archivos `_sin_evidencia`.

## Cambio en el documento de grado

En el capítulo de resultados, una nota de transparencia como la de ADR-25: los agentes contra su
nodo con las dos cifras, y la matriz completa con la disponibilidad como evidencia de RNF-06. Queda
en `docs/cambios_para_documento.md` (filas de la corrida 3 y de la matriz).
