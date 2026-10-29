# Corrida 2d: análisis (ensayo general con el código congelado)

Un ensayo de los 60 escenarios, más R3 y R4, sin R1 ni RAGAS, contra el despliegue `d3dab00` (con
los PR #72 y #73) en modo de evaluación, con el juez v3 de la calibración (`afecd5c1…`,
`--exigir-huella`) y la revisión de trazas en el servidor.

## Regla fijada antes de ver el resultado

52 o más de 60; ninguna falla de un tipo que no haya salido en las corridas 2, 2b o 2c; ninguna
respuesta con una expresión relativa al día de la consulta o un error de fecha; latencias dentro de
las metas de RNF-01; y, sin llamar modelos, las comprobaciones de las sondas sobre todas las
respuestas (`revisar_fechas.py`). **Resultado: se cumple.**

## Cifras

| Medida | Valor |
|---|---|
| Principal, tasa de la meta | **91,7 %** (55 de 60; Wilson de 81,9 % a 96,4 %) |
| Principal, tasa estricta | 75,0 % (45 de 60) |
| Respuestas con alucinación | 2 de 60 en el principal; 0 en R3 y R4 |
| R3 y R4 | 3 de 3 y 2 de 2 |
| Errores técnicos | 0 |
| Latencia del servidor, sin fragmentos (18 turnos) | p50 de 2.547 ms y p95 de 4.424 ms; 18 de 18 bajo 8 s |
| Latencia del servidor, con RAG (40 turnos) | p50 de 6.192 ms y p95 de 11.852 ms; 40 de 40 bajo 15 s |
| Trazas (RNF-05) | 1.285 ejecuciones revisadas, 0 con identificadores |
| Revisión de fechas sin modelos | 73 respuestas; ninguna expresión relativa ni referencia interna; 2 señaladas por la verificación con estados correctos (abajo) |
| Costo | US$2,59 |

## Cada no superado

| Escenario | 2 | 2b | 2c | Causa | ¿Tipo nuevo? |
|---|---|---|---|---|---|
| GEN-02 | falló | falló | falló | Transfiere a un funcionario en vez de responder que el asistente no presenta declaraciones ni hace pagos | No |
| ICA-02 | falló | pasó | falló | No dice «bimestre» (verificación de código); el juez la da como parcialmente correcta | No |
| IPU-06 | pasó | pasó | pasó | Atribuye los límites preferenciales en pesos a la Resolución SDH-000194 de 2025, art. 1, que solo trae la tabla general. La 2c hizo la misma atribución («los rangos en pesos de 2026 vienen de la Resolución SDH-000194…») y el juez no la marcó: variación del juez sobre una afirmación anterior a los cambios de esta ronda | No (cita que no sustenta lo dicho, como CAD-02 en la 2c) |
| IPU-14 | falló | falló | falló | Omite el alivio de intereses del Acuerdo 1084 de 2026 y no da el saldo | No |
| MULTI-03 | pasó | falló | falló | Afirma sin fuente quién paga el predial y que es anual | No |

Frente a la 2c pasaron a superarse AIA-01, IPU-04, IPU-07, IPU-08, IPU-13 y MULTI-02, y CAD-02 en R3.

## Revisión de fechas (sin modelos)

`revision_fechas.md` señala 2 respuestas, y las dos tienen los estados correctos:

- CAD-01, turno 3: «el 5 de junio de 2026 y el 14 de agosto de 2026 (ya pasaron), el 2 de octubre
  de 2026 (aún no vence) y el 4 de diciembre de 2026 (aún no vence)», con el reloj del 1 de octubre:
  la verificación no separa varias fechas en una oración.
- CAD-02, turno 2: «con fecha límite de pago el 9 de octubre de 2026, y ninguna obligación está
  vencida»: la verificación no toma «ninguna» como negación.
