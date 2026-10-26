# Índice de escenarios

Generado por `scripts/generar_hoja_escenarios.py`; no se edita a mano. 60 escenarios del nivel de sistema (sección 6.3 de la especificación).

| Escenario | Grupo | RF | HU | Origen |
|---|---|---|---|---|
| AIA-01 · Aviso de IA al iniciar la conversación | aviso_ia | RF-SYS-06, RF-UI-03 | HU-12 | adenda-1 |
| AIA-02 · Pregunta si habla con una persona | aviso_ia | RF-SYS-06, RF-ESC-02 | HU-12, HU-10 | adenda-2 |
| ACC-01 · Estado de cuenta de un predio ajeno con matrícula válida | acceso | RF-AUT-02, RF-AUT-01 | HU-18 | adenda-3, CA-04 |
| ACC-02 · Estado de cuenta sin sesión iniciada | acceso | RF-AUT-04, RF-AUT-01 | HU-18 | adenda-4, CA-05 |
| ACC-03 · Token de sesión inválido o vencido | acceso | RF-AUT-01, RF-AUT-04 | HU-18 | especificacion-6.3 |
| ACC-04 · Consulta general sin sesión | acceso | RF-AUT-03, RF-ICA-02 | HU-02 | especificacion-6.3 |
| IPU-01 · Estado de cuenta de un predio propio con una obligación vencida | ipu | RF-IPU-02, RF-AUT-01 | HU-05 | CA-01 |
| IPU-02 · Historial de pagos de un predio con cuotas del SPAC | ipu | RF-IPU-02, RF-AUT-01 | HU-06 | CA-02 |
| IPU-03 · Estado de cuenta de un predio al día | ipu | RF-IPU-02, RF-AUT-01 | HU-05 | CA-03 |
| IPU-04 · Qué es el predial y cómo se calcula | ipu | RF-IPU-01, RF-IPU-05 | HU-01 | especificacion-6.3 |
| IPU-05 · Cuándo se causa el predial y cuál es su período | ipu | RF-IPU-01, RF-IPU-05 | HU-01 | especificacion-6.3 |
| IPU-06 · Tarifas preferenciales de los estratos 1, 2 y 3 en 2026 | ipu | RF-IPU-01, RF-IPU-05 | HU-01, HU-03 | especificacion-6.3 |
| IPU-07 · Hasta cuándo se paga el predial con descuento en 2026 | ipu | RF-IPU-04, RF-IPU-05 | HU-03 | adenda-5 |
| IPU-08 · Plazo del predial de 2026 | ipu | RF-IPU-04, RF-IPU-05 | HU-03 | adenda-6 |
| IPU-09 · Cuánto puede subir el predial (Ley 1995) | ipu | RF-IPU-04, RF-IPU-05 | HU-03 | adenda-7 |
| IPU-10 · Estimación del predial de 2026 | ipu | RF-IPU-03, RF-AUT-01, RNF-09 | HU-07 | adenda-8 |
| IPU-11 · Estimación del predial de 2027 | ipu | RF-IPU-03, RF-AUT-01, RNF-09 | HU-07 | adenda-8 |
| IPU-12 · Cómo se notifica la factura del predial | ipu | RF-IPU-04, RF-IPU-05 | HU-03 | adenda-9 |
| IPU-13 · Pagar el predial sin declarar | ipu | RF-IPU-04, RF-IPU-05 | HU-03 | adenda-10 |
| IPU-14 · Beneficio de intereses y sanciones de 2026 | ipu | RF-IPU-04, RF-IPU-05 | HU-03 | especificacion-6.3 |
| IPU-15 · Cuotas del SPAC pagadas y pendientes | ipu | RF-IPU-02, RF-IPU-04, RF-AUT-01 | HU-05, HU-03 | especificacion-6.3 |
| ICA-01 · Qué es el ICA y quién lo paga | ica | RF-ICA-01 | HU-02 | especificacion-6.3 |
| ICA-02 · Base gravable del ICA | ica | RF-ICA-01 | HU-02 | especificacion-6.3 |
| ICA-03 · Periodicidad de la declaración del ICA en 2026 | ica | RF-ICA-01, RF-ICA-03 | HU-02, HU-03 | especificacion-6.3 |
| ICA-04 · Estimación anual del ICA de 2026 en régimen preferencial | ica | RF-ICA-02, RF-AUT-01 | HU-07 | especificacion-6.3 |
| ICA-05 · Estimación bimestral del ICA de 2026 | ica | RF-ICA-02, RF-AUT-01 | HU-07 | especificacion-6.3 |
| ICA-06 · Estimación del ICA de 2027 | ica | RF-ICA-02, RF-AUT-01 | HU-07 | especificacion-6.3 |
| ICA-07 · Fechas de declaración del ICA bimestral en 2026 | ica | RF-ICA-03, RF-AUT-01 | HU-03 | especificacion-6.3 |
| ICA-08 · Fecha de declaración del ICA anual en 2026 | ica | RF-ICA-03, RF-AUT-01 | HU-03 | especificacion-6.3 |
| ICA-09 · Régimen y periodicidad del ICA en 2027 | ica | RF-ICA-03, RF-ICA-01 | HU-03 | adenda-11 |
| ICA-10 · Consulta sobre retención de ICA | ica | RF-ICA-04, RF-ESC-02 | HU-10 | adenda-12 |
| GEN-01 · Cómo entrar a la OVT simulada | general | RF-GEN-01, RF-GEN-03 | HU-04 | especificacion-6.3 |
| GEN-02 · Qué puede hacer el asistente | general | RF-GEN-01, RF-GEN-03 | HU-04 | especificacion-6.3 |
| GEN-03 · Qué es la sobretasa de alumbrado público | general | RF-GEN-02, RF-GEN-03 | HU-04 | especificacion-6.3 |
| GEN-04 · Qué es el SPAC | general | RF-GEN-02, RF-GEN-03 | HU-04 | especificacion-6.3 |
| GEN-05 · Qué es el IVIUR | general | RF-GEN-02, RF-GEN-03 | HU-04 | especificacion-6.3 |
| GEN-06 · Qué es un dato personal | general | RF-GEN-02, RF-GEN-03 | HU-04, HU-18 | especificacion-6.3 |
| GEN-07 · Derechos del titular de los datos personales | general | RF-GEN-01, RF-GEN-03 | HU-18 | especificacion-6.3 |
| OCR-01 · Recibo válido de un predio residencial sin pagar | ocr | RF-OCR-02, RF-OCR-03, RF-OCR-06, RF-UI-04 | HU-08 | especificacion-6.3 |
| OCR-02 · Recibo válido de un predio al día | ocr | RF-OCR-02, RF-OCR-03, RF-OCR-06 | HU-08 | especificacion-6.3 |
| OCR-03 · Recibo válido de un lote | ocr | RF-OCR-02, RF-OCR-03, RF-OCR-06 | HU-08 | especificacion-6.3 |
| OCR-04 · Recibo desenfocado | ocr | RF-OCR-04, RF-OCR-06 | HU-09 | especificacion-6.3 |
| OCR-05 · Recibo recortado y de baja resolución | ocr | RF-OCR-04, RF-OCR-06 | HU-09 | especificacion-6.3 |
| OCR-06 · Documento que no es un recibo predial | ocr | RF-OCR-04, RF-OCR-06 | HU-09 | especificacion-6.3 |
| OCR-07 · Confirmación de los datos con contraste contra el adaptador | ocr | RF-OCR-03, RF-OCR-02, RF-AUT-02 | HU-08 | especificacion-6.3 |
| FA-01 · Pregunta no tributaria: el clima | fuera_de_alcance | RF-GEN-04 | HU-14 | adenda-13 |
| FA-02 · Pregunta no tributaria: licencia de conducción | fuera_de_alcance | RF-GEN-04 | HU-14 | especificacion-6.3 |
| FA-03 · Tributo fuera del MVP: renta | fuera_de_alcance | RF-ESC-02, RF-SYS-03 | HU-10, HU-14 | especificacion-6.3 |
| FA-04 · Tributo fuera del MVP: impuesto de vehículos | fuera_de_alcance | RF-ESC-02, RF-SYS-03 | HU-10, HU-14 | especificacion-6.3 |
| FA-05 · Predial en un municipio distinto de Bogotá | fuera_de_alcance | RF-ESC-02, RF-SYS-03 | HU-10, HU-14 | especificacion-6.3 |
| MULTI-01 · Predial e ICA de una persona jurídica | multiagente | RF-ORQ-03, RF-IPU-02, RF-ICA-03 | HU-05, HU-03 | especificacion-6.3 |
| MULTI-02 · Estimar el predial y conocer la fecha del ICA | multiagente | RF-ORQ-03, RF-IPU-03, RF-ICA-03 | HU-07, HU-03 | especificacion-6.3 |
| MULTI-03 · Qué son el predial y el ICA | multiagente | RF-ORQ-03, RF-IPU-01, RF-ICA-01 | HU-01, HU-02 | especificacion-6.3 |
| ESC-01 · Solicitud explícita de un funcionario | escalamiento | RF-ESC-02, RF-ESC-03, RF-ESC-05 | HU-10, HU-11, HU-12 | especificacion-6.3 |
| AMB-01 · Consulta ambigua con dos predios | ambiguas_varios_turnos | RF-IPU-02, RF-AUT-02 | HU-05, HU-13 | especificacion-6.3 |
| AMB-02 · Referencia a un mensaje anterior | ambiguas_varios_turnos | RF-UI-02, RF-IPU-02 | HU-13, HU-05 | especificacion-6.3 |
| HOR-01 · Mensaje en domingo | horario | RNF-06, RNF-07 | HU-10 | especificacion-6.3 |
| HOR-02 · Mensaje en un día festivo | horario | RNF-06, RNF-07 | HU-10 | especificacion-6.3 |
| ROB-01 · Falla o tiempo vencido del modelo | robustez | RNF-08, RF-ESC-02 | HU-10 | adenda-14 |
| ROB-02 · El adaptador de datos no responde | robustez | RNF-08, RF-IPU-02 | HU-10 | CA-06 |
