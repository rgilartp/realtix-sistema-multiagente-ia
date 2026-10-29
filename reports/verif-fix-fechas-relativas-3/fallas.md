# Fallas de la verif-fix-fechas-relativas-3

Esqueleto generado por `scripts/evaluar.py`: una fila por ensayo no superado. La causa técnica (enrutamiento, recuperación, prompt, datos, umbral o infraestructura) y la familia de MAST (diseño del sistema, desalineación entre agentes o verificación de la tarea) se llenan en el análisis (sección 6.6).

| Conjunto | Escenario | Ensayo | Fallaron | Juez | Causa | MAST |
|---|---|---|---|---|---|---|
| R3 | CAD-01 | 1 | — | parcialmente correcta, alucinación: Las cifras, estados, fechas, intereses de mora y la nota de estimación no vinculante coinciden con las herramientas y con la referencia. Sin embargo, hay dos citas mal atribuidas: la Ley 44 art. 2 no regula las modalidades de pago, y el descuento del 10 % está en la Resolución SDH-000195 art. 6, no en la SDH-000194 art. 1. |  |  |
| principal | MULTI-02 | 1 | — | parcialmente correcta, alucinación: El predial ($2.583.000, al día) y la fecha del ICA (26 de febrero de 2027) coinciden con la referencia. Pero la razón de la periodicidad anual contradice la Resolución SDH-000195 art. 1 y el Decreto 639 art. 205: declara anual quien no excede 391 UVT de impuesto a cargo, no quien supera ese umbral en ingresos. Por eso la cita al art. 205 no sustenta lo dicho. |  |  |
