# Fallas de la verif-fix-busqueda

Esqueleto generado por `scripts/evaluar.py`: una fila por ensayo no superado. La causa técnica (enrutamiento, recuperación, prompt, datos, umbral o infraestructura) y la familia de MAST (diseño del sistema, desalineación entre agentes o verificación de la tarea) se llenan en el análisis (sección 6.6).

| Conjunto | Escenario | Ensayo | Fallaron | Juez | Causa | MAST |
|---|---|---|---|---|---|---|
| principal | GEN-02 | 1 | «declaraciones»; responder (estado: escalada; datos por confirmar: False) | incorrecta: La respuesta no contesta la pregunta: en lugar de explicar que el asistente no presenta declaraciones ni hace pagos, y qué sí puede hacer, transfiere a un funcionario sin que se pidiera, omitiendo lo esencial de la referencia aunque los fragmentos recuperados lo contenían. |  |  |
| principal | IPU-14 | 1 | «60 %»; «21 de diciembre de 2026»; responder (estado: aclaracion; datos por confirmar: False) | incorrecta: No inventa datos: lo que dice del art. 7, su parágrafo 6 y el art. 138 sale de los fragmentos. Pero omite lo esencial del alivio: el descuento del 60 % de intereses y sanciones, el pago del 100 % del capital y del 40 % restante en un solo pago hasta el 21 de diciembre de 2026, y que la deuda debía estar pendiente al 9 de octubre de 2026, omisión que la lista prohíbe. Tampoco da el saldo del predio. |  |  |
