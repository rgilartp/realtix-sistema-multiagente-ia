# Reporte de la verif-fix-anclaje-y-citas

Generado por `scripts/evaluar.py` a partir de `resultados.jsonl` y `juez.jsonl`; no se edita a mano. Un escenario se supera si pasa todas las verificaciones de código y el juez lo califica correcta o parcialmente correcta, sin alucinación (sección 6.4). El intervalo de Wilson usa n = escenarios, porque los ensayos de un mismo escenario no son independientes (ADR-24).

Commit evaluado: `—`.

Huella del juez: `afecd5c1b4f62d52fc605ac6b350363cddee4604ae704f30247703146aa39805`.

## Escenarios del nivel de sistema

3 escenarios, 3 ensayos.

| Tasa | Valor | Wilson 95 % (n = escenarios) | Bootstrap 95 % |
|---|---|---|---|
| Meta (correcta o parcial, sin alucinación) | 33,3 % | 6,1 % a 79,2 % | 0,0 % a 100,0 % |
| Estricta | 33,3 % | 6,1 % a 79,2 % | 0,0 % a 100,0 % |

Verificaciones de código superadas: 66,7 %. Veredictos del juez: correcta, 1; parcialmente correcta, 1; incorrecta, 1. Con alucinación: 33,3 %; cita en 66,7 %, cita que sustenta en 66,7 %, cobertura completa en 33,3 % y claridad media de 4,00.

| Latencia | Turnos | p50 servidor | p95 servidor | p50 cliente | p95 cliente | Meta | Bajo la meta |
|---|---|---|---|---|---|---|---|
| simple | 0 | — | — | — | — | 8.000 | 0 |
| rag | 3 | 7.326 | 8.251 | 7.368 | 8.261 | 15.000 | 3 |

## Enrutamiento

![Matriz de confusión](matriz_confusion.png)

### Nivel de sistema (primer turno)

| Categoría | Soporte | Precisión | Exhaustividad | F1 |
|---|---|---|---|---|
| ipu | 2 | 100,0 % | 100,0 % | 100,0 % |
| general | 1 | 100,0 % | 100,0 % | 100,0 % |

![Latencias](latencias.png)
