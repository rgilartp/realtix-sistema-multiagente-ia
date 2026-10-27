# Criterios de entrada de la corrida 1

Sección 6.9 de la especificación y ADR-24 (A5, A7 y A9). Cada criterio se comprobó justo antes de
lanzar la corrida, con la salida real resumida.

| # | Criterio | Evidencia | Resultado |
|---|---|---|---|
| 1 | El sistema desplegado responde `/health` | `curl https://tg2-multiagente.duckdns.org/health` → `{"estado":"ok","version":"0.9.0","dependencias":{"postgres":"ok","chroma":"ok","realsit":"ok"}}`; el paso 6/6 de `desplegar.sh` lo repitió por HTTPS | Cumple |
| 2 | La CI está en verde | `gh run list --branch main --workflow CI`: el último (PR #36, el de `v0.9.0`) terminó en `success`. En la rama del bloque, `uv run pytest -q` da 640 aprobadas y 8 omitidas (las de siempre: servicios o claves), y ruff no encuentra nada | Cumple |
| 3 | El corpus está cargado | La ingesta de `desplegar.sh` en el servidor y la local (la usan los componentes) dan la misma versión del corpus, `408d90bdb6af2d40`, con 1.148 fragmentos (normativa_datos 73, normativa_ica 562, normativa_ipu 491, plataforma_general 22) y 0 por embeber: US$0 | Cumple |
| 4 | Los escenarios y sus referencias están revisados | Los 60 escenarios llevan `aprobado_por` (de B6). CAD-01 a CAD-03, SEG-01 y SEG-02 los aprobó Rodolfo al lanzar B14; en SEG-02 se aceptan la categoría `general` o `fuera_de_alcance` y el comportamiento `responder` o `informar_fuera_de_alcance`, porque lo que se mide es que no revele nada (sus verificaciones de seguridad no cambian). `scripts/evaluar.py` no corre una referencia sin aprobar | Cumple |
| 5 | Verificador de referencias (A7) | `uv run python scripts/verificar_referencias.py` → «65 escenarios y 167 cifras verificadas; escenarios con algo sin resolver: 0», código de salida 0 (`reports/verificacion_referencias.md`) | Cumple |
| 6 | Huella del juez (A5) | `925788b38ffe143521296c3ef892742b84e024893e0b95a53f4f7a59ca8ed170`, la misma de las calificaciones de la mini corrida de B12. Queda en `metricas.json` y en `reporte.md` | Cumple |

## Comprobaciones adicionales

- **Versión evaluada:** `./deploy/desplegar.sh --version v0.9.0 --evaluacion` desplegó
  `805f2efb9600b1262a25ecd3e2a1e481eee3a057` (`git rev-parse HEAD` en el servidor), el commit de la
  etiqueta `v0.9.0`. Queda en `metricas.json` (`commit_evaluado`) y en `reporte.md`.
- **Huella de RealSit antes de la corrida (RF-SYS-02):**
  `4479d0369ba967a2d8ed40fb6e7d12bff1ed497ad86ce230093f0c857312d0a2`, igual a
  `src/data/huella_realsit.sha256`. La de después está en `modo_evaluacion.md`.
- **Monitor de `/health` (RNF-06):** aprobado por Rodolfo tal como quedó en B13 (cada 15 minutos,
  de lunes a viernes, de 8:00 a. m. a 4:45 p. m. en Bogotá).
