# Lista de figuras y capturas (borrador)

## Figuras

| Figura | Archivo | Origen |
|---|---|---|
| Grafo implementado (8 nodos y 8 transiciones) | `docs/figuras/grafo_implementado.mmd` | `scripts/exportar_grafo.py` (B4) |
| Latencias de la corrida 1 | `reports/corrida-1/latencias.png` | `scripts/evaluar.py` |
| Matriz de confusión del sistema, corrida 1 | `reports/corrida-1/matriz_confusion.png` | ídem |
| Matriz de confusión de componentes, corrida 1 | `reports/corrida-1/matriz_confusion_componentes.png` | ídem |
| Latencias de la corrida 2 | `reports/corrida-2/latencias.png` | ídem |
| Matriz de confusión del sistema, corrida 2 | `reports/corrida-2/matriz_confusion.png` | ídem |
| Latencias de la corrida 3 (la que se reporta) | `reports/corrida-3/latencias.png` | ídem (B16) |
| Matriz de confusión del sistema, corrida 3 | `reports/corrida-3/matriz_confusion.png` | ídem (B16) |
| Matriz de confusión de componentes, corrida 3 | `reports/corrida-3/matriz_confusion_componentes.png` | ídem (B16) |

## Capturas de la interfaz (B11)

En `docs/capturas/`, a 1280 y 390 px; algunas también en modo oscuro: la OVT simulada; el widget al
iniciar, con una respuesta, con un recibo, fuera de horario y escalado; y la consola con la bandeja y
las métricas. El índice está en `docs/capturas/README.md`.

Límites de estas capturas (`docs/capturas/README.md`), que el documento debe respetar:

- usan la API simulada en el navegador (`web/tests/simulador.js`), no el backend; los textos que
  muestran se copiaron tal cual del sistema;
- las cifras de la consola son de ejemplo y no son resultados (`scripts/metricas_de_ejemplo.py`);
- los casos de la bandeja son de ejemplo; solo sus textos fijos salen del sistema;
- `widget_respuesta` muestra el aviso de sesión ante una consulta personal sin sesión, no una
  respuesta sobre normas.

Por eso no se presentan como resultados: las de métricas y la de una respuesta con fuentes se toman
en B16.

## Capturas definitivas (B16)

En `docs/capturas/definitivas/`, a 1280 y 390 px, tomadas después de la corrida 3 contra el sistema
desplegado sin modo de evaluación, con el sistema real (no la API simulada). Las 24 de B11 no se
repitieron, porque la interfaz no cambió desde que se tomaron. Pies de figura sugeridos
(`docs/capturas/definitivas/README.md`):

| Captura | Pie de figura |
|---|---|
| `widget_respuesta_normas_1280.png` y `_390.png` | Respuesta del sistema multiagente de IA a una consulta conceptual sobre el impuesto predial, con sus citas y la lista de fuentes, en escritorio y en celular |
| `consola_metricas_final_1280.png` y `_390.png` | Consola de administración con el registro acumulado del despliegue (670 turnos, 89 conversaciones escaladas, latencias p50 de 5.475 ms y p95 de 10.648 ms) |

La matriz de confusión de la consola aparece vacía («turnos etiquetados: 0») porque la imagen de
producción no trae los escenarios, que son las etiquetas; la matriz de la corrida 3 es la figura de
`reports/corrida-3/matriz_confusion.png`. Las cifras de la consola son del historial del despliegue
(corridas 1, 2 y 3 y las verificaciones), no solo de la corrida 3. La consola muestra «v0.9.0», la
versión que declara el código evaluado (`d3dab00`); la etiqueta `v1.0.0` marca la entrega.
