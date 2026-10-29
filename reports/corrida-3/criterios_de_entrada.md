# Criterios de entrada de la corrida 3

Sección 6.9 de la especificación y ADR-24 (A5, A7 y A9). Cada criterio se comprobó antes de lanzar la
corrida contra el despliegue (commit `d3dab00`, código congelado). La misma tabla está en
`docs/reporte_de_pruebas.md`, sección 3.

| Criterio | Cómo se verifica | Resultado |
|---|---|---|
| El sistema desplegado responde `/health` | `curl https://<subdominio>.duckdns.org/health` | Cumple: `ok`, con PostgreSQL, Chroma y RealSit en `ok`, antes y después de la corrida |
| CI en verde | `gh run list --branch main --workflow CI` | Cumple: CI en verde en el commit desplegado y en `main` |
| Corpus cargado | Salida de la ingesta de `deploy/desplegar.sh` | Cumple: 1.149 fragmentos (73, 562, 491 y 23 por colección), sin embeddings nuevos |
| Juez calibrado | `tests/test_preparacion_b16.py` y `--exigir-huella` | Cumple: la huella del juez es la de la calibración (`afecd5c1…`) |
| Sin cambios de código desde la última fusión | `git log` frente al commit desplegado | Cumple: `d3dab00`; lo posterior a la corrida son documentos, reportes y, en el cierre de B16, el instrumento de evaluación (`src/evaluacion` y `scripts`), no el código del sistema |
| Referencias aprobadas, incluidas las de R1 (nuevas en la corrida 3) | Campo de aprobación de cada escenario; la corrida se detiene sin `--sin-aprobar` | Cumple: los 60 aprobados por Rodolfo (PR #67), R1 aprobadas en B15, R3 y R4 desde la corrida 1 |
| Verificador de referencias (A7) sin nada sin resolver | `uv run python scripts/verificar_referencias.py` | Cumple: 65 escenarios y 171 cifras, 0 sin resolver |
| LangSmith encendido (la corrida usa `--trazas`, RNF-05 · Registro auditable) | Trazas de una prueba de humo | Cumple: 4.422 ejecuciones de la corrida revisadas en el servidor |
| Modo de evaluación encendido solo durante la corrida (A9) | `desplegar.sh --evaluacion` al empezar y sin él al terminar, verificado desde afuera | Cumple: se encendió para la 2d, siguió en la corrida 3 y en las no funcionales, y se apagó al terminar; desde afuera, el reloj simulado se ignora y la meta no trae campos de evaluación |
