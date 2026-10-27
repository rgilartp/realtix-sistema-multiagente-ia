# Fallas de la verif-fix-ica-3

Esqueleto generado por `scripts/evaluar.py`: una fila por ensayo no superado. La causa técnica (enrutamiento, recuperación, prompt, datos, umbral o infraestructura) y la familia de MAST (diseño del sistema, desalineación entre agentes o verificación de la tarea) se llenan en el análisis (sección 6.6).

| Conjunto | Escenario | Ensayo | Fallaron | Juez | Causa | MAST |
|---|---|---|---|---|---|---|
| principal | ACC-04 | 1 | «9,66»; responder (estado: aclaracion; datos por confirmar: False) | incorrecta, alucinación: La respuesta da 10 por mil como tarifa vigente en 2026 para la actividad 6201. Según la referencia, la tarifa de 2026 es 9,66 por mil, y 10 por mil es la tarifa que aplica desde 2027 (o desde el bimestre 6 de 2026), justo lo que no debía hacer. Además se contradice al decir que el Acuerdo 1084 «cambia» la tarifa sin dar un valor distinto. |  |  |
