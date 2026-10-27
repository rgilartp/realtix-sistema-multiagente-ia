# Fallas de la regresion-correcciones-corrida-1

Esqueleto generado por `scripts/evaluar.py`: una fila por ensayo no superado. La causa técnica (enrutamiento, recuperación, prompt, datos, umbral o infraestructura) y la familia de MAST (diseño del sistema, desalineación entre agentes o verificación de la tarea) se llenan en el análisis (sección 6.6).

| Conjunto | Escenario | Ensayo | Fallaron | Juez | Causa | MAST |
|---|---|---|---|---|---|---|
| principal | IPU-09 | 1 | «IPC»; «8 puntos»; «Ley 1995»; categoría ipu (hubo: general); responder (estado: aviso_sesion; datos por confirmar: False) | incorrecta: El asistente no respondió la pregunta general sobre los topes de incremento del predial (IPC+8, 50 %, IPC para estratos 1 y 2 según la Ley 1995 de 2019), que no requería datos de la cuenta; omite todo lo esencial de la referencia. |  |  |
| principal | IPU-13 | 1 | «30 de abril» | parcialmente correcta: Responde correctamente que sí se puede pagar con factura sin declarar y sustenta todo en los arts. 224 y 227 recuperados. Omite los plazos de la referencia: expedición de facturas hasta el 30 de abril de 2026 y pago hasta el 10 de julio de 2026. |  |  |
| principal | MULTI-01 | 1 | — | parcialmente correcta, alucinación: Las cifras y fechas de predial e ICA coinciden con las herramientas, la referencia y la Resolución SDH-000195 de 2025, art. 1, y los saldos no se mezclan. Sin embargo, la afirmación sobre intereses de mora si se paga tarde no sale de ninguna fuente recibida. |  |  |
