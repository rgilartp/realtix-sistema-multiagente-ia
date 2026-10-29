# Regla de la repetición única (ronda 3 de las sondas y ronda 2 de la verificación de las reglas)

Fijada por Rodolfo antes de correr, con el código congelado de los PR #72 y #73. Se corren una vez
las 34 sondas de fechas (`sondas.yaml`) y la verificación de las reglas por código
(`../verif-reglas-por-codigo/`: ICA-03, ICA-07, ICA-08, MULTI-02, IPU-04 y MULTI-03 con el juez, y
las 6 preguntas nuevas). En cada respuesta se registran la latencia del servidor y si hubo
reescritura.

**PARADA solo por un error real del sistema en una respuesta final:**

a. una expresión que relacione una fecha con el día de la consulta;
b. una referencia interna;
c. un estado de fecha equivocado (una fecha futura dada por vencida o una pasada dada por
   pendiente), comprobado leyendo la respuesta;
d. la regla de los 391 UVT invertida;
e. una descripción de tarifas sin fuente en las preguntas sobre tarifas;
f. una falla nueva: un escenario de los 6 que pasó en la verificación anterior y ahora falla.
   MULTI-03 ya fallaba: se anota, no detiene.

**No detienen, pero se anotan:** las limitaciones de la verificación automática cuando la respuesta
es correcta, y las respuestas que no llamaron la herramienta y acertaron (cuántas).

Las verificaciones automáticas (`sondas.py` y `preguntas.py`) señalan candidatas; cada respuesta
señalada se lee para decidir si es un error real del sistema (PARADA) o una limitación de la
verificación (se anota).
