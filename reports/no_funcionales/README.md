# Pruebas no funcionales (sección 6.7; B16, corrida 3)

Contra el sistema multiagente de IA desplegado (`https://tg2-multiagente.duckdns.org`, commit
`d3dab00`). Las que necesitan las cabeceras del modo de evaluación se corrieron en la ventana de la
corrida 3; después el modo se apagó (`./deploy/desplegar.sh --version main`) y se comprobó desde
afuera. Las de B15 (corrida 2) están en `corrida-2/`.

| Requerimiento | Prueba | Resultado | Evidencia |
|---|---|---|---|
| RNF-01 · Tiempo de respuesta | p50 y p95 de los turnos de la corrida 3 (servidor y cliente), con y sin fragmentos | Sin fragmentos: p50 de 2.299 ms y p95 de 3.934 ms; 54 de 54 bajo 8 s. Con RAG: p50 de 6.379 ms y p95 de 13.393 ms; 120 de 120 bajo 15 s | `reports/corrida-3/reporte.md`, `latencias.png` |
| RNF-02 · Escalamiento horizontal | `--scale backend=2`; el turno 1 lo atendió `backend-1`; con `backend-1` detenido, el turno 2 de la misma conversación lo atendió `backend-2` | **Cumple:** los dos turnos respondidos y registrados en la misma conversación | `replicas.json` |
| RNF-06 · Horario de atención | Unitarias con reloj fijo (CI); monitor de `/health` cada 5 minutos desde el crontab del servidor | **No cumple el 99 %:** 85,53 % en horario hábil (130 de 152 chequeos, 42,6 horas); 100 % desde la corrección del PR #54 (los 27 fallos fueron 502 de la fuga de `/health`) | `disponibilidad.md`, `disponibilidad.json`, `salud.log` (días relativos), `disponibilidad.py` |
| RNF-08 · Tiempos de espera y degradación | `X-Falla-Inyectada` en el orquestador, el modelo, la recuperación y el adaptador, por tiempo y por error | **8 de 8:** siempre escala por «fallo de servicio», con HTTP 200 y sin error técnico visible | `fallas_inyectadas.json` |
| RNF-15 · Volúmenes persistentes | Conteos antes y después de `docker compose restart` y de `up --force-recreate` | **Cumple:** 594 conversaciones, 669 interacciones, 88 casos, 3.854 puntos de control y 1.149 fragmentos, iguales en los tres conteos | `volumenes.json` |
| RF-SYS-02 · Alcance de solo lectura | Huella de RealSit antes y después de la corrida 3 | **Idéntica:** `4479d0369ba967a2d8ed40fb6e7d12bff1ed497ad86ce230093f0c857312d0a2` | `huella_realsit.txt` |
| RNF-03 · Protección de datos personales y RNF-05 · Registro auditable | Revisión automática de las trazas de la corrida | **Cumple:** 4.422 ejecuciones, ninguna con identificadores | `reports/corrida-3/trazas.json`, `ley_1581.md` |

**Modo de evaluación (A9).** Se encendió para la corrida 2d y siguió en la corrida 3 y en estas
pruebas; durante las réplicas y los volúmenes se mantuvo con `REALTIX_MODO_EVALUACION=true`. Al
terminar, `./deploy/desplegar.sh --version main` lo apagó («modo de evaluación: false»), y desde
afuera una petición con `X-Reloj-Simulado` recibió una respuesta con el reloj real y sin `contextos`,
`herramientas` ni `tokens_por_modelo`.
