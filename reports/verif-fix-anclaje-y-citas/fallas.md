# Fallas de la verif-fix-anclaje-y-citas

Esqueleto generado por `scripts/evaluar.py`: una fila por ensayo no superado. La causa técnica (enrutamiento, recuperación, prompt, datos, umbral o infraestructura) y la familia de MAST (diseño del sistema, desalineación entre agentes o verificación de la tarea) se llenan en el análisis (sección 6.6).

| Conjunto | Escenario | Ensayo | Fallaron | Juez | Causa | MAST |
|---|---|---|---|---|---|---|
| principal | GEN-02 | 1 | «declaraciones»; responder (estado: escalada; datos por confirmar: False) | incorrecta: La respuesta no contesta la pregunta: en lugar de decir que el asistente no presenta declaraciones ni hace pagos, transfiere a un funcionario sin necesidad y omite lo esencial de la referencia. No afirma que pueda pagar ni declarar, ni contiene afirmaciones fácticas sin fuente. |  |  |
| principal | IPU-04 | 1 | — | parcialmente correcta, alucinación: La respuesta acierta en la base gravable (avalúo catastral o autoavalúo), cita normas que la sustentan y no da una tarifa única. Omite que el IPU fusiona varios tributos (Ley 44 de 1990, art. 1) y el rango del 5 al 16 por mil, y menciona categorías de destino que no aparecen en las fuentes. |  |  |
