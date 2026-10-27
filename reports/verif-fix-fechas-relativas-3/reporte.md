# Reporte de la verif-fix-fechas-relativas-3

Generado por `scripts/evaluar.py` a partir de `resultados.jsonl` y `juez.jsonl`; no se edita a mano. Un escenario se supera si pasa todas las verificaciones de código y el juez lo califica correcta o parcialmente correcta, sin alucinación (sección 6.4). El intervalo de Wilson usa n = escenarios, porque los ensayos de un mismo escenario no son independientes (ADR-24).

Commit evaluado: `—`.

Huella del juez: `afecd5c1b4f62d52fc605ac6b350363cddee4604ae704f30247703146aa39805`.

## Escenarios del nivel de sistema

13 escenarios, 13 ensayos.

| Tasa | Valor | Wilson 95 % (n = escenarios) | Bootstrap 95 % |
|---|---|---|---|
| Meta (correcta o parcial, sin alucinación) | 92,3 % | 66,7 % a 98,6 % | 76,9 % a 100,0 % |
| Estricta | 76,9 % | 49,7 % a 91,8 % | 53,8 % a 100,0 % |

Verificaciones de código superadas: 100,0 %. Veredictos del juez: correcta, 10; parcialmente correcta, 3; incorrecta, 0. Con alucinación: 7,7 %; cita en 100,0 %, cita que sustenta en 92,3 %, cobertura completa en 84,6 % y claridad media de 4,46.

| Latencia | Turnos | p50 servidor | p95 servidor | p50 cliente | p95 cliente | Meta | Bajo la meta |
|---|---|---|---|---|---|---|---|
| simple | 0 | — | — | — | — | 8.000 | 0 |
| rag | 14 | 7.772 | 12.047 | 7.780 | 12.056 | 15.000 | 14 |

## R3 · Escenarios encadenados

3 escenarios, 3 ensayos.

| Tasa | Valor | Wilson 95 % (n = escenarios) | Bootstrap 95 % |
|---|---|---|---|
| Meta (correcta o parcial, sin alucinación) | 66,7 % | 20,8 % a 93,9 % | 0,0 % a 100,0 % |
| Estricta | 66,7 % | 20,8 % a 93,9 % | 0,0 % a 100,0 % |

Verificaciones de código superadas: 100,0 %. Veredictos del juez: correcta, 2; parcialmente correcta, 1; incorrecta, 0. Con alucinación: 33,3 %; cita en 100,0 %, cita que sustenta en 66,7 %, cobertura completa en 100,0 % y claridad media de 4,67.

| Latencia | Turnos | p50 servidor | p95 servidor | p50 cliente | p95 cliente | Meta | Bajo la meta |
|---|---|---|---|---|---|---|---|
| simple | 1 | 4.527 | 4.527 | 4.538 | 4.538 | 8.000 | 1 |
| rag | 7 | 7.160 | 8.468 | 7.172 | 8.477 | 15.000 | 7 |

## Enrutamiento

![Matriz de confusión](matriz_confusion.png)

### Nivel de sistema (primer turno)

| Categoría | Soporte | Precisión | Exhaustividad | F1 |
|---|---|---|---|---|
| ipu | 11 | 100,0 % | 100,0 % | 100,0 % |
| ica | 2 | 100,0 % | 100,0 % | 100,0 % |

![Latencias](latencias.png)
