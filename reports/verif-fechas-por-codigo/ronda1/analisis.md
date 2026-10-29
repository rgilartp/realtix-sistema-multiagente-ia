# Sondas de fechas por código: análisis (PARADA)

Resultado oficial, con las verificaciones fijadas antes de correr (`sondas.yaml`, `sondas.py`):
**22 de 34 respuestas pasan** (`resumen.md`). La regla pedía que pasaran todas: PARADA. No se
ajustó nada.

## Lo que encontraron las verificaciones

| Respuestas | Qué pasó | ¿Error del sistema? |
|---|---|---|
| 03.1, 03.2, 06.2, 11.2, 16.2 | La respuesta dice la fecha de hoy en la misma oración del plazo vencido («hoy es 20 de abril de 2026, así que ese plazo ya venció»). La regla lo permite («puedes decir la fecha de hoy»), pero la verificación «ninguna fecha igual o posterior a hoy dada como vencida» contó la fecha de hoy | No: error de la verificación |
| 06.1, 11.1 | El «ya venció» va en la oración siguiente, que empieza por «Como hoy es…»; la verificación solo unía las que empiezan por «ese», «esa», «ya» y similares | No: error de la verificación |
| 15.1 | «Ya pasaron las de abril… (la del 9 de octubre de 2026 ya venció)» se unió, por empezar con «Ya», a la oración que lista todas las fechas, incluida la próxima | No: error de la verificación |
| 16.1 | La oración se partió en «art. 3)», y el «venció» quedó en la siguiente | No: error de la verificación |
| 09.2 | Respuesta correcta («Hoy es 5 de octubre de 2026: la cuota 3 ya venció, así que la próxima… es el 4 de diciembre de 2026»), con la cuota vencida y la próxima en la misma oración. **Pero no llamó la herramienta de fechas**: tomó las fechas de un fragmento y decidió por su cuenta que la cuota 3 ya venció (acertó) | Sí, en parte: no siguió la regla de llamar la herramienta |
| 12.1, 12.2 | Sin sesión, «¿Ya se me venció la declaración anual del ICA de 2026?» recibió el aviso de iniciar sesión, sin la fecha (26 de febrero de 2027) | Sí: la consulta se tomó como personal y pidió sesión; no es un error de relación con hoy, pero no da la fecha |

Además, aunque pasaron, 10.1 y 10.2 (facturas, 29 de abril) y 11.1 respondieron **sin llamar la
herramienta de fechas**: en total, 4 de 34 respuestas tomaron la fecha de un fragmento y decidieron
solas si ya pasó (acertaron en las 4). 9 de las 34 tuvieron una reescritura del verificador (por
citas o por expresiones relativas: el registro no distingue cuál).

Ninguna de las 34 respuestas finales trae una expresión relativa a hoy, y ninguna dio como vencida
una fecha posterior a hoy.

## Recalificación informativa (no cambia el resultado)

Con la verificación corregida en esos cuatro puntos (la fecha de hoy no cuenta, no se parte en
«art.», «Como…» retoma la anterior y «Ya…» no une), sobre las mismas respuestas guardadas y sin
llamar modelos: **30 de 34**. Las 4 que siguen fallando son 09.2 y 12.1 y 12.2 (las de arriba) y
16.1 (la corrección del corte en «art.» no cubrió ese caso; la respuesta es correcta).

Costo de las sondas: US$0,31.
