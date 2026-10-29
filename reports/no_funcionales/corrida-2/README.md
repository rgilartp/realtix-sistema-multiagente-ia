# Pruebas no funcionales (sección 6.7; B15)

Se hicieron contra el sistema multiagente de IA desplegado (`https://tg2-multiagente.duckdns.org`,
commit `4e94e7a`). Las que necesitan las cabeceras del modo de evaluación se corrieron en la ventana
de la corrida 2; después el modo se apagó y se comprobó desde afuera.

| Requerimiento | Prueba | Resultado | Evidencia |
|---|---|---|---|
| RNF-01 · Tiempo de respuesta | p50 y p95 de los turnos de la corrida 2 (servidor y cliente), separados por si hubo fragmentos | Con RAG: p50 de 6.373 ms y p95 de 12.372 ms; 39 de 39 bajo 15 s. Sin fragmentos: p50 de 2.162 ms y p95 de 8.782 ms; 18 de 19 bajo 8 s. El que pasó los 8 s fue la clasificación del orquestador (8.766 ms) en un escalamiento | `reports/corrida-2/reporte.md`, `latencias.png` |
| RNF-02 · Escalamiento horizontal | `--scale backend=2`; el turno 1 lo atendió `backend-2`; con `backend-2` detenido, el turno 2 de la misma conversación lo atendió `backend-1` | **Cumple:** los dos turnos respondidos y registrados en la misma conversación | `replicas.json`: los turnos los escribe `scripts/no_funcionales.py turno`; el bloque `servidor` (qué réplica atendió cada turno, por los registros de acceso de cada contenedor, y los 2 turnos en el almacén) lo agregó el operador con los comandos de Compose |
| RNF-06 · Horario de atención | Unitarias con reloj fijo (CI); monitor de `/health` cada 5 minutos, todos los días, desde el crontab del servidor (`~/monitor_salud/salud.log`: hora UTC, código HTTP, tiempo en ms y commit). El workflow `.github/workflows/monitor.yml` se deja, pero GitHub nunca disparó su `schedule` (1 ejecución, la manual de B13) | Las unitarias pasan en la CI. El primer chequeo del monitor encontró un 502: una fuga de conexiones en `/health` (PR #54; causa en `docs/resumenes/b15.md`). La disponibilidad se calcula en B16, en el horario hábil y en total, marcando los despliegues | CI; `salud.log` (se copia a esta carpeta en B16) |
| RNF-08 · Tiempos de espera y degradación | `X-Falla-Inyectada` en el orquestador, el modelo, la recuperación y el adaptador, por tiempo y por error | **8 de 8:** siempre escala por «fallo de servicio» con HTTP 200 y sin un error técnico a la vista | `fallas_inyectadas.json` (`scripts/no_funcionales.py fallas`) |
| RNF-15 · Volúmenes persistentes | Conteos antes y después de `docker compose restart` y de `up --force-recreate` | **Cumple:** corpus (73, 562, 491 y 22 fragmentos por colección), 142 conversaciones, 159 interacciones, 24 casos y los puntos de control, iguales en los tres conteos; `/health` en `ok` | `volumenes.json` |
| RF-SYS-02 · Alcance de solo lectura | Huella de RealSit antes y después de la corrida 2 | **Idéntica:** `4479d0369ba967a2d8ed40fb6e7d12bff1ed497ad86ce230093f0c857312d0a2`, igual a `src/data/huella_realsit.sha256` | `huella_realsit.txt` (salida de `deploy/desplegar.sh` en los dos despliegues) |
| RNF-03 · Protección de datos personales y RNF-05 · Registro auditable | Prueba de minimización; revisión automática de las trazas; lista de chequeo de la Ley 1581 | **Cumple:** 1.277 ejecuciones de 63 conversaciones de la corrida 2, ninguna con identificadores | `reports/corrida-2/trazas.json`, `ley_1581.md` |

**Modo de evaluación (A9).** Se encendió con `./deploy/desplegar.sh --version main --evaluacion`
solo para la corrida 2, las fallas inyectadas y la prueba de réplicas, y se apagó con
`./deploy/desplegar.sh --version main` apenas terminó la parte de la corrida que usa el servidor
(«Desplegado: v0.9.0-59-g4e94e7a (modo de evaluación: false)»). Desde afuera, una petición con
`X-Reloj-Simulado` recibió el aviso de fuera de horario con el reloj real, sin `tokens_por_modelo`,
`contextos` ni `herramientas`.
