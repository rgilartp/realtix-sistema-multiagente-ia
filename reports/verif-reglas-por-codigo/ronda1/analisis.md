# Verificación de las reglas por código: análisis (PARADA)

Regla de Rodolfo: ninguna inversión de la regla de los 391 UVT, ninguna descripción de tarifas sin
fuente y ninguna falla nueva. Costo: US$0,33 (escenarios con el juez) + US$0,06 (preguntas).

## Escenarios con el juez (un ensayo)

| Escenario | 2 | 2b | 2c | Ahora |
|---|---|---|---|---|
| ICA-03 | pasó | falló | pasó | pasó (correcta) |
| ICA-07 | falló | pasó | pasó | pasó (correcta) |
| ICA-08 | pasó | falló | pasó | pasó (correcta) |
| MULTI-02 | pasó | pasó | falló | **pasó** (correcta) |
| IPU-04 | falló | falló | falló | **pasó** (parcialmente correcta, sin alucinación) |
| MULTI-03 | pasó | falló | falló | falló: «aplicando la tarifa que corresponda a su destino», sin fuente |

Ninguna falla nueva (MULTI-03 ya fallaba en la 2b y la 2c), pero MULTI-03 describe la tarifa sin
fuente: incumple la regla. La pregunta de MULTI-03 es conceptual (qué son el predial y el ICA) y
no pide la tarifa; el agente la mencionó de memoria y no llamó `tarifas_predial`.

## Preguntas nuevas (sin juez; `preguntas_resumen.md`: 2 de 6 por la verificación automática)

| Pregunta | Qué pasó | ¿Error del sistema? |
|---|---|---|
| 1 (U04, bimestral) | Copia la regla («el impuesto a cargo de 2025 fue mayor a 391 UVT») y agrega un contraste correcto («si fuera de hasta 391 UVT, tu régimen sería anual»); la verificación tomó el contraste como inversión | No: error de la verificación |
| 2 (U12, anual) | Copia la regla entre comillas y agrega el contraste correcto («con impuesto a cargo superior a 391 UVT… sería bimestral») | No: error de la verificación |
| 3 (U05, preferencial) | Da la regla con las palabras de la norma («no exceda de 391 UVT… única declaración anual») en lugar de copiar la de la herramienta; es correcta y no la invierte | En parte: no copió la regla de la herramienta |
| 4 y 5 (tarifa) | Llamaron `tarifas_predial` | — |
| 6 («¿Influye el estrato…?») | No llamó `tarifas_predial`: respondió con los fragmentos (Acuerdo 648 de 2016, art. 1, y Ley 44 de 1990, art. 4), con sus citas; el contenido es correcto | Sí: no siguió la regla de llamar la herramienta |

Ninguna respuesta invierte la regla de los 391 UVT.
