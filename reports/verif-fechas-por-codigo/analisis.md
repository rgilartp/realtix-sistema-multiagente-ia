# Sondas de fechas por código: análisis de la ronda 2 (PARADA)

Ronda 2, con la regla nueva de Rodolfo (no relacionar fechas con el día de la consulta), el
verificador que suma «hoy» y las referencias internas, y la verificación de las sondas corregida
(`sondas.yaml` y `sondas.py`, fijados antes de correr). La ronda 1 está en `ronda1/`.

Antes de correr, sin llamar modelos, la verificación corregida marcó en las respuestas guardadas de
la ronda 1 la 4.2 («que es hoy, 9 de julio de 2026») y la 11.1 («consultar herramientas»,
«fragmento [1]» y «hoy»), como pidió Rodolfo.

**Resultado: 32 de 34** (`resumen.md`). La regla pedía todas: PARADA. Costo: US$0,33.

Ninguna de las 34 respuestas trae «hoy» ni otra expresión relativa al día de la consulta, ni una
referencia interna; ninguna da por vencida una fecha que no ha llegado.

| Respuesta | Qué pasó | ¿Error del sistema? |
|---|---|---|
| 11.2 (facturas, 4 de mayo) | No llamó la herramienta de fechas (respondió con un fragmento) y dijo «La fecha de expedición ya llegó», en la oración siguiente a la fecha y con palabras que no son «ya venció» | Sí: no siguió la regla de llamar la herramienta y decidió por su cuenta que la fecha pasó (acertó) |
| 15.2 (ICA bimestral, 13 de octubre) | Lista las seis fechas en una sola oración, cada una con «(ya venció)» o «(aún no vence)», todas correctas según `ya_paso`. La verificación juzga por oración y no puede atribuir cada marca a su fecha | No: limitación de la verificación (la respuesta es correcta) |

Además:

- 4 de 34 respuestas no llamaron la herramienta de fechas, todas de la pregunta de las facturas
  (10.1, 10.2, 11.1 y 11.2): respondieron con el fragmento de la Resolución SDH-000195 de 2025,
  art. 4. Las otras tres pasaron.
- 23 de 34 respuestas tuvieron la reescritura del verificador (por citas o por expresiones
  relativas, el registro no distingue): el modelo todavía escribe «hoy» o similares en el primer
  intento, y el verificador lo corrige. Cada reescritura suma una llamada al modelo (más latencia y
  costo).
