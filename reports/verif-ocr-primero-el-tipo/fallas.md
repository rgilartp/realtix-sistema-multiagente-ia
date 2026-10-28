# Fallas de la verif-ocr-primero-el-tipo

Esqueleto generado por `scripts/evaluar.py`: una fila por ensayo no superado. La causa técnica (enrutamiento, recuperación, prompt, datos, umbral o infraestructura) y la familia de MAST (diseño del sistema, desalineación entre agentes o verificación de la tarea) se llenan en el análisis (sección 6.6).

| Conjunto | Escenario | Ensayo | Fallaron | Juez | Causa | MAST |
|---|---|---|---|---|---|---|
| R3 | CAD-03 | 1 | — | parcialmente correcta, alucinación: Lo esencial coincide con la referencia: los datos del recibo se contrastan después de la confirmación, el descuento del 10 % vencía el 17 de abril de 2026 (art. 6) y ya no está disponible. Sin embargo, la respuesta dice literalmente que el plazo sin descuento no pasó, lo que contradice la herramienta (plazo_sin_descuento_ya_paso: true) y su propia conclusión de mora. Además omite el caso del SPAC, que es secundario. |  |  |
