# Fallas de la mini-corrida

Esqueleto generado por `scripts/evaluar.py`: una fila por ensayo no superado. La causa técnica (enrutamiento, recuperación, prompt, datos, umbral o infraestructura) y la familia de MAST (diseño del sistema, desalineación entre agentes o verificación de la tarea) se llenan en el análisis (sección 6.6).

| Conjunto | Escenario | Ensayo | Fallaron | Juez | Causa | MAST |
|---|---|---|---|---|---|---|
| principal | AMB-02 | 1 | «5.166.000»; «2.646.000»; no escala; responder (estado: escalada; datos por confirmar: False) | incorrecta: El asistente transfirió la consulta a un funcionario en ambos turnos y no dio el saldo de $5.166.000 con sus dos obligaciones vencidas ni el predial 2026 liquidado en $2.646.000, por lo que omitió lo esencial de la referencia. No inventó datos ni pidió de nuevo la matrícula. |  |  |
| principal | GEN-02 | 1 | — | parcialmente correcta, alucinación: Responde bien que el asistente no presenta declaraciones, no hace pagos ni modifica datos, con cita pertinente. Sin embargo, afirma sin sustento en las fuentes que esos trámites se hacen en la Oficina Virtual Tributaria y omite que sus respuestas son orientativas, sin asesoría personalizada, y los temas que sí atiende. |  |  |
