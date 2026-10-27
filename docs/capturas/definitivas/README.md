# Capturas definitivas (B16)

Se toman con el sistema multiagente de IA congelado de B16; no se tomaron en la preparación. Las
de la API simulada (`docs/capturas/`, B11) se vuelven a tomar con el mismo comando si la interfaz
cambió; las que necesitan el sistema real se toman con `web/tests/capturas_reales.spec.js`.

| Captura | Por qué es definitiva | Cómo se genera |
|---|---|---|
| `widget_respuesta_normas_1280.png` y `_390.png` | La respuesta a una consulta sobre normas, con su lista de fuentes, del sistema corregido (en B11 se dejó para B16; `docs/capturas/README.md`) | `capturas_reales.spec.js`, en horario hábil |
| `consola_metricas_final_1280.png` y `_390.png` | Las métricas reales de enrutamiento de la consola, después de la corrida 3 (en B11 eran de ejemplo) | ídem, con `TOKEN_ADMIN` |
| Las 24 de `docs/capturas/` (B11) | Se repiten solo si la interfaz cambió desde B11 | `cd web && npm run build && npm run capturas` |
| Figuras de la corrida 3 (`latencias.png`, `matriz_confusion.png`, `matriz_confusion_componentes.png`) | Las de la corrida que se reporta | `scripts/evaluar.py` las genera en `reports/corrida-3/` |

## Guion (Rodolfo, en su equipo, en horario hábil)

1. `cd web && npm run build`
2. Escribe el token de administrador en tu terminal, sin guardarlo en ningún archivo:
   `read -s TOKEN_ADMIN && export TOKEN_ADMIN`
3. `CAPTURAS_REALES=1 URL_REAL=https://<subdominio>.duckdns.org npx playwright test tests/capturas_reales.spec.js`
4. Revisa `docs/capturas/definitivas/` y borra `TOKEN_ADMIN` de la sesión: `unset TOKEN_ADMIN`.

Las consultas del guion no son de ningún escenario (A8).
