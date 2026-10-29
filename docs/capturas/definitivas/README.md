# Capturas definitivas (B16)

Se toman con el sistema multiagente de IA congelado de B16; no se tomaron en la preparación. Las
de la API simulada (`docs/capturas/`, B11) se vuelven a tomar con el mismo comando si la interfaz
cambió; las que necesitan el sistema real se toman con `web/tests/capturas_reales.spec.js`.

| Captura | Por qué es definitiva | Cómo se genera |
|---|---|---|
| `widget_respuesta_normas_1280.png` y `_390.png` | La respuesta a una consulta sobre normas, con su lista de fuentes, del sistema corregido (en B11 se dejó para B16; `docs/capturas/README.md`) | `capturas_reales.spec.js`, en horario hábil |
| `consola_metricas_final_1280.png` y `_390.png` | La consola con métricas reales (en B11 eran de ejemplo). Muestra el historial acumulado del despliegue (corridas 1, 2 y 3 y las verificaciones), no solo la corrida 3: el pie de figura lo dice así, y las cifras de la corrida 3 se toman de `reports/corrida-3/matriz_confusion*.png` | ídem, con `TOKEN_ADMIN`; corre antes que las consultas del widget |
| Las 24 de `docs/capturas/` (B11) | Se repiten solo si la interfaz cambió desde B11 | `cd web && npm run build && npm run capturas` |
| Figuras de la corrida 3 (`latencias.png`, `matriz_confusion.png`, `matriz_confusion_componentes.png`) | Las de la corrida que se reporta | `scripts/evaluar.py` las genera en `reports/corrida-3/` |

## Guion (Rodolfo, en su equipo, en horario hábil)

1. `cd web && npm run build`
2. Escribe el token de administrador en tu terminal, sin guardarlo en ningún archivo:
   `read -s TOKEN_ADMIN && export TOKEN_ADMIN`
3. `CAPTURAS_REALES=1 URL_REAL=https://<subdominio>.duckdns.org npx playwright test tests/capturas_reales.spec.js`
   Si falta `URL_REAL` o `TOKEN_ADMIN`, el guion falla con un mensaje (no se salta en silencio).
4. Revisa `docs/capturas/definitivas/`, borra `TOKEN_ADMIN` de la sesión y los informes de
   Playwright: `unset TOKEN_ADMIN && rm -rf test-results`.

El token nunca se escribe en la página: el guion lo agrega como cabecera a la petición de las
métricas, así no aparece en las capturas ni en los informes de error. Las dos consultas del widget
son reales: gastan unos centavos de API y quedan como dos conversaciones en el registro del
despliegue.

Las consultas del guion no son de ningún escenario (A8).

## Revisión y pies de figura

Las cuatro se tomaron contra el sistema sin modo de evaluación (commit `536e018`, que es `d3dab00` más
documentos). Se revisaron: rótulo de entorno de pruebas visible, token de administrador enmascarado,
sin marcas ni nombres reales, datos sintéticos y sin metadatos en los PNG.

| Captura | Pie de figura sugerido |
|---|---|
| `widget_respuesta_normas_1280.png` y `_390.png` | Respuesta del sistema multiagente de IA a una consulta conceptual sobre el impuesto predial, con sus citas y la lista de fuentes, en escritorio y en celular |
| `consola_metricas_final_1280.png` y `_390.png` | Consola de administración con el registro acumulado del despliegue (670 turnos, 89 conversaciones escaladas, latencias p50 de 5.475 ms y p95 de 10.648 ms). La matriz de confusión aparece vacía («turnos etiquetados: 0») porque la imagen de producción no trae los escenarios, que son las etiquetas (`.dockerignore` excluye `tests`); la matriz de la corrida 3 está en `reports/corrida-3/matriz_confusion.png` y `matriz_confusion_componentes.png` |

La consola muestra «v0.9.0», la versión que declara el código evaluado; la etiqueta `v1.0.0` marca la
entrega, que solo suma documentos, reportes y capturas.
