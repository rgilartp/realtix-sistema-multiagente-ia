# Sensibilidad de la relevancia de RAGAS (corrida 3)

Análisis aparte, después de la corrida; no reemplaza la cifra oficial de `ragas.jsonl`. Generado con
`sensibilidad_relevancia.py`; resultados por caso en `sensibilidad_relevancia.jsonl`.

- Casos: los 66 sin sesión con los cuatro valores de RAGAS (escenarios con `sesion: null`).
- Cambio: la respuesta sin la lista final «Fuentes:» ni las notas fijas que agrega el sistema
  (`meta.notas`). Cambiaron 60 de las 66 respuestas, que conservaron en promedio el 85 % del texto.
- Solo se volvió a medir la relevancia de la respuesta (`answer_relevancy`, `gpt-4.1-mini`), con las
  respuestas anonimizadas, como en la corrida.

| Medida | Valor |
|---|---|
| Relevancia oficial (los mismos 66 casos) | 71,3 % |
| Relevancia sin anexos | 71,3 % |
| Diferencia media | +0,08 puntos |
| Diferencia media absoluta | 1,5 puntos |
| Con una tolerancia de 1 punto | 15 subieron, 8 bajaron y 43 quedaron iguales |
| Sin tolerancia | 30 subieron, 19 bajaron y 17 quedaron iguales |
| Costo (OpenAI) | US$0,0864 |

La relevancia más baja que la de Bahçeci y colaboradores no se explica por la lista de fuentes ni
por las notas fijas.
