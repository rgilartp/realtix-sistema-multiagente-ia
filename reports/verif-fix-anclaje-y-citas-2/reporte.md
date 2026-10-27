# Reporte de la verif-fix-anclaje-y-citas-2

Generado por `scripts/evaluar.py` a partir de `resultados.jsonl` y `juez.jsonl`; no se edita a mano. Un escenario se supera si pasa todas las verificaciones de código y el juez lo califica correcta o parcialmente correcta, sin alucinación (sección 6.4). El intervalo de Wilson usa n = escenarios, porque los ensayos de un mismo escenario no son independientes (ADR-24).

Commit evaluado: `—`.

Huella del juez: `afecd5c1b4f62d52fc605ac6b350363cddee4604ae704f30247703146aa39805`.

## Escenarios del nivel de sistema

2 escenarios, 2 ensayos.

| Tasa | Valor | Wilson 95 % (n = escenarios) | Bootstrap 95 % |
|---|---|---|---|
| Meta (correcta o parcial, sin alucinación) | 50,0 % | 9,5 % a 90,5 % | 0,0 % a 100,0 % |
| Estricta | 0,0 % | 0,0 % a 65,8 % | 0,0 % a 0,0 % |

Verificaciones de código superadas: 50,0 %. Veredictos del juez: correcta, 0; parcialmente correcta, 1; incorrecta, 1. Con alucinación: 0,0 %; cita en 50,0 %, cita que sustenta en 50,0 %, cobertura completa en 0,0 % y claridad media de 3,50.

| Latencia | Turnos | p50 servidor | p95 servidor | p50 cliente | p95 cliente | Meta | Bajo la meta |
|---|---|---|---|---|---|---|---|
| simple | 0 | — | — | — | — | 8.000 | 0 |
| rag | 2 | 6.383 | 7.840 | 6.433 | 7.892 | 15.000 | 2 |

## Enrutamiento

![Matriz de confusión](matriz_confusion.png)

### Nivel de sistema (primer turno)

| Categoría | Soporte | Precisión | Exhaustividad | F1 |
|---|---|---|---|---|
| ipu | 1 | 100,0 % | 100,0 % | 100,0 % |
| general | 1 | 100,0 % | 100,0 % | 100,0 % |

![Latencias](latencias.png)
