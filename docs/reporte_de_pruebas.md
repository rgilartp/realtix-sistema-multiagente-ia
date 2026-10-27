# Reporte de pruebas del OE4 (esqueleto para B16)

Reporte de la ejecución del plan de pruebas (`docs/plan_de_pruebas.md`), con la estructura del
reporte de avance y de cierre del programa CTFL v4.0.1 del ISTQB. Se llena en B16 con la corrida 3
(la que se reporta, sección 6.10). Cada cifra lleva su archivo de origen en `reports/`. Lo que falta
dice **PENDIENTE (corrida 3)**, **PENDIENTE (calibración)** o **PENDIENTE (usabilidad)**.

## 1. Resumen

- Objeto: el sistema multiagente de IA desplegado, con datos sintéticos.
- Versión evaluada: **PENDIENTE (corrida 3)** (commit; sin cambios de código desde la última
  fusión).
- Huella del juez: la de `reports/calibracion/huella_juez.txt` (juez v3, ADR-25), exigida con
  `--exigir-huella`.
- Resultado frente a la meta de RNF-16 · Tasa de respuestas correctas (85 %): **PENDIENTE (corrida
  3)**.

## 2. Contexto y desviaciones del plan

- Corridas 1 y 2 y sus correcciones: `reports/corrida-1/`, `docs/resumenes/correcciones-corrida-1.md`,
  `reports/corrida-2/` y `docs/resumenes/b15.md`.
- Correcciones del instrumento después de la corrida 1 y juez v3: ADR-25.
- Desviaciones frente al plan: **PENDIENTE (corrida 3)** (por ejemplo, la segunda ronda de
  correcciones y lo que quedó propuesto).

## 3. Criterios de entrada de la corrida 3

| Criterio | Cómo se verifica | Resultado |
|---|---|---|
| El sistema desplegado responde `/health` | `curl https://<subdominio>.duckdns.org/health` | PENDIENTE (corrida 3) |
| CI en verde | `gh run list --branch main --workflow CI` | PENDIENTE (corrida 3) |
| Corpus cargado | Salida de la ingesta de `deploy/desplegar.sh` | PENDIENTE (corrida 3) |
| Juez calibrado | `tests/test_preparacion_b16.py` y `--exigir-huella` | PENDIENTE (corrida 3) |
| Sin cambios de código desde la última fusión | `git log` frente al commit desplegado | PENDIENTE (corrida 3) |

## 4. Resultados del nivel de sistema (corrida 3)

- Tasa de la meta y estricta, con Wilson (n = escenarios) y bootstrap: **PENDIENTE (corrida 3)**.
- pass@1 promedio, pass@3 y pass^3: **PENDIENTE (corrida 3)**.
- R1 (generalización), R3 y R4, aparte: **PENDIENTE (corrida 3)**.
- Veredictos del juez, alucinación, citas y claridad: **PENDIENTE (corrida 3)**.

## 5. Componentes e integración

- Enrutamiento: precisión, exhaustividad y F1 por clase, matriz de confusión, kappa y exactitud de la
  clase mayoritaria: **PENDIENTE (corrida 3)**.
- Agentes contra su nodo: **PENDIENTE (corrida 3)**.
- RAGAS, con y sin sesión, frente a Bahçeci y colaboradores: **PENDIENTE (corrida 3)**.

## 6. Pruebas no funcionales

Las de B15 están en `reports/no_funcionales/README.md`; en B16 se repiten las que dependen del
despliegue: **PENDIENTE (corrida 3)**. RNF-06 · Horario de atención (disponibilidad con el
historial del monitor): **PENDIENTE (corrida 3)**.

## 7. Calibración del juez

Kappa entre el juez y el consenso (binario y ponderado de 3 niveles) y entre los evaluadores, con
intervalos por bootstrap (`scripts/calibracion.py kappa`): **PENDIENTE (calibración)**.

## 8. Usabilidad

SUS de cada evaluador y problemas de la evaluación heurística (`docs/usabilidad/`): **PENDIENTE
(usabilidad)**.

## 9. Análisis de fallas

Causa técnica y familia de MAST de cada falla de la corrida 3 (`reports/corrida-3/fallas.md`), con
la evolución desde las corridas 1 y 2: **PENDIENTE (corrida 3)**.

## 10. Latencia y costo

- p50 y p95 del servidor y del cliente, con y sin recuperación: **PENDIENTE (corrida 3)**.
- Costo de la corrida, costo por consulta y costo total del proyecto: **PENDIENTE (corrida 3)**.

## 11. Trazabilidad y criterios de salida

| Criterio de salida (sección 6.9) | Resultado |
|---|---|
| Tasa de escenarios superados de 85 % o más | PENDIENTE (corrida 3) |
| Ningún escenario de acceso ni de trazas fallido | PENDIENTE (corrida 3) |
| Latencias medidas | PENDIENTE (corrida 3) |
| Matriz de trazabilidad completa (`reports/trazabilidad.md` y `.csv`) | PENDIENTE (corrida 3) |
| Reporte generado | PENDIENTE (corrida 3) |

## 12. Conclusiones

**PENDIENTE (corrida 3).**
