# Repetición única (ronda 3 de las sondas de fechas): análisis

Con el código congelado de los PR #72 y #73 y la regla fijada antes de correr
(`regla_ronda3.md`). Rondas anteriores en `ronda1/` y `ronda2/`.

**Resultado: sin PARADA.** La verificación automática dio 30 de 34 (`resumen.md`); las 4 señaladas
se leyeron y ninguna es un error real del sistema:

| Respuesta | Qué dice | Lectura |
|---|---|---|
| 07.2 (1 de octubre) | «la Cuota 1 venció el 5 de junio de 2026, la Cuota 2 venció el 14 de agosto de 2026, la Cuota 3 vence el 2 de octubre de 2026 y la Cuota 4 vence el 4 de diciembre de 2026» | Estados correctos; la verificación no separa varias fechas en una oración |
| 08.2 (2 de octubre) | «2 de octubre de 2026 (aún no vence)», con las anteriores «(ya venció)» | Estados correctos (una fecha igual a la consulta no ha pasado); misma limitación |
| 11.1 (4 de mayo) | «el pago sin descuento vence el 10 de julio de 2026, y el descuento por pronto pago ya venció el 17 de abril de 2026» | Estados correctos; misma limitación |
| 11.2 (4 de mayo) | Da la fecha (30 de abril de 2026) y dice que no puede confirmar si las facturas se expidieron; no afirma ningún estado | Sin error: no llamó la herramienta y no dio un estado |

- (a) Ninguna respuesta relaciona una fecha con el día de la consulta; (b) ninguna trae una
  referencia interna; (c) ningún estado de fecha equivocado.
- Respuestas que no llamaron la herramienta de fechas: **2 de 34** (10.2 y 11.2, la pregunta de
  las facturas). La 10.2 acertó; la 11.2 no dio estado.
- Reescrituras del verificador: **9 de 34** (en la ronda 2 fueron 23), después de cambiar «Fecha de
  hoy» por «Fecha de la consulta (no la menciones en la respuesta)».
- Latencia del servidor: p50 de 6.018 ms, p95 de 8.537 ms y máxima de 8.759 ms.
- Costo: US$0,31.
