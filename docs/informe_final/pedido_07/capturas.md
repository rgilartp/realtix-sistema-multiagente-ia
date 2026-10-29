# Capturas que existen y las que faltan (pedido 07)

Todas están en `docs/capturas/`, cada una a 1280 px (escritorio, `_1280`) y a 390 px (celular,
`_390`). El índice y los límites de cada grupo están en `docs/capturas/README.md` (B11) y en
`docs/capturas/definitivas/README.md` (B16).

## Capturas de B11 (26 PNG, con la API simulada en el navegador)

Las cifras de la consola y los casos de la bandeja son de ejemplo: no son resultados. Los textos
del sistema que aparecen se copiaron tal cual del código.

| Captura | Qué muestra |
|---|---|
| `ovt_simulada` (y `_oscuro`) | La OVT simulada: el rótulo «Entorno simulado de pruebas», el selector del usuario de prueba, las cuatro tarjetas de «Qué puedes probar» y el botón del asistente tributario |
| `widget_inicio` (y `_oscuro`) | El widget al abrir: el aviso de IA y, debajo, el aviso de datos personales (Ley 1581 de 2012); «Te atiende un asistente de IA», el botón «Hablar con un funcionario» y la conversación vacía |
| `widget_respuesta` (y `_oscuro`) | El aviso de sesión ante «¿Cuánto debo de mi predio?» sin sesión iniciada (ACC-02); no es una respuesta sobre normas |
| `widget_fuera_de_horario` (y `_oscuro`) | El aviso de fuera de horario con la próxima apertura (lunes 5 de octubre de 2026, 8:00 a. m.), firmado por «Sistema» |
| `widget_recibo` | Un recibo adjunto con sesión y la confirmación de los datos leídos («¿Es correcto?»), con el texto de OCR-01 |
| `widget_escalado` | El aviso de transferencia después del botón «Hablar con un funcionario»: «Tu caso está con un funcionario» y el botón ya deshabilitado |
| `consola_bandeja` | La bandeja de casos de solo lectura, con dos casos de ejemplo y el detalle de uno: resumen, resumen estructurado y conversación |
| `consola_metricas` (y `_oscuro`) | Las métricas de enrutamiento y de tiempo, con una matriz de ejemplo (`scripts/metricas_de_ejemplo.py`) |

Son 8 vistas en modo claro (16 PNG) y 5 de ellas también en modo oscuro (10 PNG). La de
`widget_inicio` en modo oscuro se agregó con el aviso de datos personales (PR #58);
`docs/capturas/README.md` todavía habla de cuatro vistas en modo oscuro.

## Capturas definitivas de B16 (4 PNG, con el sistema real desplegado)

Se tomaron después de la corrida 3, sin el modo de evaluación (`web/tests/capturas_reales.spec.js`).

| Captura | Qué muestra |
|---|---|
| `definitivas/widget_respuesta_normas` | La respuesta real a una consulta conceptual sobre el impuesto predial, con sus citas y la lista de fuentes |
| `definitivas/consola_metricas_final` | La consola con el registro acumulado del despliegue: 670 turnos, 89 conversaciones escaladas, p50 de 5.475 ms y p95 de 10.648 ms. La matriz de confusión aparece vacía porque la imagen de producción no trae los escenarios, que son las etiquetas |

## Figuras que no son capturas

- `reports/corrida-3/latencias.png`, `matriz_confusion.png` y `matriz_confusion_componentes.png`
  (corrida 3).
- `grafo_compilado.png` de esta carpeta (el grafo compilado, punto 8 del pedido).

## Capturas que no existen

| Captura | Por qué no existe |
|---|---|
| Traza de LangSmith | No se tomó ninguna. La revisión de las trazas de la corrida 3 es un conteo: 4.422 ejecuciones revisadas y ninguna con identificadores (`reports/corrida-3/trazas.json`) |
| Rechazo de un predio ajeno | No se tomó. El rechazo se verificó con ACC-01 y SEG-01 en la corrida 3 (`docs/informe_final/pedido_07/escenarios.csv`, estado `rechazo_acceso`) |
| Respuesta con datos de la cuenta, con sesión | No se guardó: en B11 la respuesta real traía la fecha del día (`docs/resumenes/b11.md`) |
| Recibo leído por el sistema real | La de `widget_recibo` usa la API simulada |
| Caso escalado real en la bandeja | Los casos de `consola_bandeja` son de ejemplo |
| Respuesta del funcionario en el widget | No está construida: la bandeja es de solo lectura (sección 3.6 de la especificación, opcional) |

El pedido nombra la traza de LangSmith y el rechazo de un predio ajeno. Las otras cuatro filas son
capturas que el sistema no tiene; el chat de documentos debe cotejar el resto de su lista con las
tablas de arriba.
