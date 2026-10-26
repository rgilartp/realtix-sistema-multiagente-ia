# Capturas de la web (B11)

Capturas de la OVT simulada, el widget y la consola, cada una en 1280 px (`_1280`) y en 390 px
(`_390`). Se toman con Playwright: `cd web && npm run build && npm run capturas`.

- **Las capturas usan la API simulada en el navegador** (`web/tests/simulador.js`), no el backend.
  Los textos que muestran se copiaron tal cual del sistema:
  - el aviso fuera de horario, generado con `Horario.aviso_fuera_de_horario` para el sábado 3 de
    octubre de 2026 a las 10:00;
  - los avisos de transferencia (`AVISO_TRANSFERENCIA` y `PREFACIOS` de `nodo_escalamiento`);
  - el resumen del caso (`construir_resumen`);
  - la confirmación del recibo de OCR-01.
- **Las fechas** son las del reloj de los escenarios aprobados en B6: los casos de la bandeja son del
  jueves 1 de octubre de 2026.
- **Las cifras de la consola son de ejemplo y no son resultados.** Salen de
  `scripts/metricas_de_ejemplo.py`, que pasa una matriz de ejemplo por `calcular_metricas`, el
  mismo cálculo de `/admin/metricas`; por eso la exactitud, el total etiquetado, la precisión, la
  exhaustividad y el F1 son coherentes entre sí. Las duraciones son las de la medición de B9.
- **La captura de las métricas para el documento de grado se tomará en B16**, con la corrida final.
- **`widget_respuesta` muestra el aviso de sesión** (`AVISO_SESION`, texto fijo del código) ante
  «¿Cuánto debo de mi predio?» sin sesión (ACC-02).
- **La captura con una respuesta sobre normas y la de la lista de fuentes se tomarán en B16**, con el
  sistema corregido. Las respuestas reales a «¿Qué es el impuesto predial?» y a la pregunta de GEN-02
  tienen fallas conocidas (ver `docs/resumenes/b11.md`, «Fallas conocidas»). La lista de fuentes se
  revisa en las pruebas con un texto neutro, que no se usa en ninguna captura.
