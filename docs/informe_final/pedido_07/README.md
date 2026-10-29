# Paquete de datos para el pedido 07

Datos del sistema multiagente de IA para el chat de documentos, leídos de los archivos versionados
del repositorio, sin gasto de API y sin cambiar el código del sistema (el evaluado, `d3dab00`).
Los CSV están en UTF-8, separados por comas y con punto decimal; «sí» y «no» en las columnas
de verdadero o falso.

Los seis CSV salen de `docs/informe_final/generar_pedido_07.py` (con `uv run python`), que
al final compara sus totales con las cifras publicadas y falla si alguno no coincide: la tasa del
conjunto principal y el costo de cada conjunto (`reports/corrida-3/metricas.json`), los casos y los
promedios de RAGAS, las aprobadas por el juez en la calibración (`reports/calibracion/kappa.json`),
el SUS y los fragmentos por colección.

| N.º | Archivo | Contenido | Origen |
|---|---|---|---|
| 1 | `escenarios.csv` | Corrida 3: 225 ensayos (60 escenarios principales, 10 variantes de R1, 3 de R3 y 2 de R4, tres ensayos cada uno) | `reports/corrida-3/calificados.jsonl`, `resultados.jsonl.gz`, `tests/escenarios/` y `tests/escenarios_adicionales/` |
| 2 | `ragas.csv` | 110 casos de RAGAS | `reports/corrida-3/ragas.jsonl` |
| 3 | `calibracion.csv` | Los 30 ítems de la calibración del juez | `reports/calibracion/muestra.csv`, `clave.json` y `reports/corrida-2b/juez.jsonl` |
| 4 | `heuristica.csv` | Las 6 anotaciones de la evaluación heurística | `docs/usabilidad/*/heuristica.md` y `docs/reporte_de_pruebas.md`, sección 8 |
| 5 | `usuarios.csv` | Las respuestas del SUS y su puntaje | `docs/usabilidad/*/sus.md` |
| 6 | `base_conocimiento.csv` | Un documento de la base de conocimiento por fila, con sus fragmentos | `knowledge_base/*/fuentes.yaml` y la segmentación de `src/integrations/segmentacion.py` |
| 7 | `pytest.txt` | Resumen de `uv run pytest -q` sin pruebas reales, la cobertura y los JUnit de Playwright y de modelos reales | Esta corrida, la CI de `main` y `reports/junit/` |
| 8 | `grafo_compilado.mmd` y `.png` | El grafo compilado | `get_graph().draw_mermaid()` de `scripts/exportar_grafo.py` |
| 9 | `capturas.md` | Las capturas que existen y las que faltan | `docs/capturas/` |
| 10 | `datos_seccion_2.md` | Versiones, modelos y precios, base sintética, parámetros, D5 y D6, escalamiento, aviso de IA, despliegue y repositorio | Cada dato con su archivo |

## Notas por archivo

**`escenarios.csv`**

- Una fila por escenario y ensayo. `estado_obtenido` es el del primer turno y, si el último es
  otro, «primero → último» (pasa en CAD-03 y OCR-07).
- Las latencias son las del primer turno, en ms.
- Los tokens son los del sistema, sumados por modelo. `costo_usd` se calcula con los precios de
  `src/integrations/costos.py`.
- `escalo` dice si algún turno quedó escalado; coincide con los turnos que registraron un caso.
- `superado` es la regla de la meta: pasan las verificaciones de código y el juez da «correcta» o
  «parcialmente correcta» sin alucinación (`src/evaluacion/juez.py`).
- Dos columnas más, al final: `superado_estricto`, que además exige «correcta» (la tasa estricta
  del reporte, A3), y `costo_juez_usd`, el costo de calificar el ensayo, que no es del sistema.
- Con estas filas, el conjunto principal da 162 de 180 ensayos superados (90,0 %), y el costo por
  conjunto coincide con `metricas.json`.

**`ragas.csv`**

- Una fila por caso vigente, como en `scripts/evaluar.py`: `ragas.jsonl` tiene 114 filas porque 4
  casos (ICA-04, ensayo 2; ICA-05, 1; ICA-06, 1; MULTI-02, 2) quedaron sin `context_recall` la
  primera vez y se volvieron a evaluar; cuenta la segunda fila.
- RAGAS solo corrió en los ensayos de un turno con fragmentos de los 60 escenarios principales.
- `con_sesion` sale del campo `sesion` del escenario: 44 casos con sesión y 66 sin ella (los del
  análisis de sensibilidad).

**`calibracion.csv`**

- La muestra es de la corrida 2b, calificada por el juez v3 (huella `afecd5c1…`).
- El juez aprueba una respuesta si la califica «correcta» o «parcialmente correcta» sin
  alucinación: 23 de 30, como en `kappa.json`.
- `evaluador_A` y `evaluador_B` son los dos autores, sin nombres; A y B son las mismas personas en
  `calibracion.csv`, `heuristica.csv` y `usuarios.csv`.

**`heuristica.csv`**

- `que_pasa` copia el texto de cada evaluador tal cual. `correccion` dice cómo se atendió, según
  `docs/reporte_de_pruebas.md` (sección 8).
- No incluye las dos observaciones de contenido (C1 y C2), porque se escribieron con ayuda del chat
  del documento y no son parte de la evaluación heurística.

**`usuarios.csv`**

- Es la evaluación interna de los dos autores del trabajo (ADR-21), no una prueba con usuarios
  externos: no hubo usuarios externos.
- Las respuestas van de 1 a 5. El puntaje sigue la fórmula del SUS: en las preguntas impares,
  respuesta − 1; en las pares, 5 − respuesta; la suma por 2,5.
- En el cuestionario del evaluador A, la pregunta 6 decía 0, un valor fuera de la escala, por
  error. El evaluador confirmó que su respuesta es 1, y así quedó anotado en su archivo.

**`base_conocimiento.csv`**

- Los fragmentos se cuentan con la misma segmentación de la ingesta, sobre `knowledge_base/`, que
  es la misma de `d3dab00`. Suman 1.149: 73 en `normativa_datos`, 562 en `normativa_ica`, 491 en
  `normativa_ipu` y 23 en `plataforma_general`, los de `reports/no_funcionales/volumenes.json`.
- Si una norma tiene varias URL, van separadas por « ; ».
- El manual de la OVT simulada no tiene URL, porque es un documento del proyecto.
