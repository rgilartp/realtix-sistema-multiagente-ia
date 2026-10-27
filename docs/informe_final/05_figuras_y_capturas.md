# Lista de figuras y capturas (borrador)

## Figuras

| Figura | Archivo | Origen |
|---|---|---|
| Grafo implementado (8 nodos y 8 transiciones) | `docs/figuras/grafo_implementado.mmd` | `scripts/exportar_grafo.py` (B4) |
| Latencias de la corrida 1 | `reports/corrida-1/latencias.png` | `scripts/evaluar.py` |
| Matriz de confusión del sistema, corrida 1 | `reports/corrida-1/matriz_confusion.png` | ídem |
| Matriz de confusión de componentes, corrida 1 | `reports/corrida-1/matriz_confusion_componentes.png` | ídem |
| Latencias de la corrida 2 | `reports/corrida-2/latencias.png` (PR #48) | ídem |
| Matriz de confusión del sistema, corrida 2 | `reports/corrida-2/matriz_confusion.png` (PR #48) | ídem |
| Figuras de la corrida 3 | **PENDIENTE (corrida 3)** | B16 |

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

**PENDIENTE (corrida 3):** las capturas definitivas con el sistema congelado de B16 (lista y guion
en el PR de preparación de B16).
