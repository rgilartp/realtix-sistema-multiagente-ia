# Reporte de la verif-fix-ica-3

Generado por `scripts/evaluar.py` a partir de `resultados.jsonl` y `juez.jsonl`; no se edita a mano. Un escenario se supera si pasa todas las verificaciones de código y el juez lo califica correcta o parcialmente correcta, sin alucinación (sección 6.4). El intervalo de Wilson usa n = escenarios, porque los ensayos de un mismo escenario no son independientes (ADR-24).

Commit evaluado: `—`.

Huella del juez: `afecd5c1b4f62d52fc605ac6b350363cddee4604ae704f30247703146aa39805`.

## Escenarios del nivel de sistema

6 escenarios, 6 ensayos.

| Tasa | Valor | Wilson 95 % (n = escenarios) | Bootstrap 95 % |
|---|---|---|---|
| Meta (correcta o parcial, sin alucinación) | 83,3 % | 43,6 % a 97,0 % | 50,0 % a 100,0 % |
| Estricta | 66,7 % | 30,0 % a 90,3 % | 33,3 % a 100,0 % |

Verificaciones de código superadas: 83,3 %. Veredictos del juez: correcta, 4; parcialmente correcta, 1; incorrecta, 1. Con alucinación: 16,7 %; cita en 100,0 %, cita que sustenta en 83,3 %, cobertura completa en 66,7 % y claridad media de 4,00.

| Latencia | Turnos | p50 servidor | p95 servidor | p50 cliente | p95 cliente | Meta | Bajo la meta |
|---|---|---|---|---|---|---|---|
| simple | 0 | — | — | — | — | 8.000 | 0 |
| rag | 6 | 7.662 | 11.985 | 7.682 | 12.099 | 15.000 | 6 |

## Enrutamiento

![Matriz de confusión](matriz_confusion.png)

### Nivel de sistema (primer turno)

| Categoría | Soporte | Precisión | Exhaustividad | F1 |
|---|---|---|---|---|
| ica | 6 | 100,0 % | 100,0 % | 100,0 % |

![Latencias](latencias.png)
