# Reporte de la verif-ocr-primero-el-tipo

Generado por `scripts/evaluar.py` a partir de `resultados.jsonl` y `juez.jsonl`; no se edita a mano. Un escenario se supera si pasa todas las verificaciones de código y el juez lo califica correcta o parcialmente correcta, sin alucinación (sección 6.4). El intervalo de Wilson usa n = escenarios, porque los ensayos de un mismo escenario no son independientes (ADR-24).

Commit evaluado: `—`.

Huella del juez: `afecd5c1b4f62d52fc605ac6b350363cddee4604ae704f30247703146aa39805`.

## Escenarios del nivel de sistema

7 escenarios, 7 ensayos.

| Tasa | Valor | Wilson 95 % (n = escenarios) | Bootstrap 95 % |
|---|---|---|---|
| Meta (correcta o parcial, sin alucinación) | 100,0 % | 64,6 % a 100,0 % | 100,0 % a 100,0 % |
| Estricta | 85,7 % | 48,7 % a 97,4 % | 57,1 % a 100,0 % |

Verificaciones de código superadas: 100,0 %. Veredictos del juez: correcta, 6; parcialmente correcta, 1; incorrecta, 0. Con alucinación: 0,0 %; cita en 14,3 %, cita que sustenta en 14,3 %, cobertura completa en 85,7 % y claridad media de 5,00.

| Latencia | Turnos | p50 servidor | p95 servidor | p50 cliente | p95 cliente | Meta | Bajo la meta |
|---|---|---|---|---|---|---|---|
| simple | 7 | 4.724 | 6.185 | 4.775 | 6.212 | 8.000 | 7 |
| rag | 0 | — | — | — | — | 15.000 | 0 |

## R3 · Escenarios encadenados

1 escenarios, 1 ensayos.

| Tasa | Valor | Wilson 95 % (n = escenarios) | Bootstrap 95 % |
|---|---|---|---|
| Meta (correcta o parcial, sin alucinación) | 0,0 % | 0,0 % a 79,3 % | 0,0 % a 0,0 % |
| Estricta | 0,0 % | 0,0 % a 79,3 % | 0,0 % a 0,0 % |

Verificaciones de código superadas: 100,0 %. Veredictos del juez: correcta, 0; parcialmente correcta, 1; incorrecta, 0. Con alucinación: 100,0 %; cita en 100,0 %, cita que sustenta en 100,0 %, cobertura completa en 0,0 % y claridad media de 3,00.

| Latencia | Turnos | p50 servidor | p95 servidor | p50 cliente | p95 cliente | Meta | Bajo la meta |
|---|---|---|---|---|---|---|---|
| simple | 1 | 3.757 | 3.757 | 3.774 | 3.774 | 8.000 | 1 |
| rag | 1 | 9.561 | 9.561 | 9.580 | 9.580 | 15.000 | 1 |

## Enrutamiento

![Matriz de confusión](matriz_confusion.png)

### Nivel de sistema (primer turno)

| Categoría | Soporte | Precisión | Exhaustividad | F1 |
|---|---|---|---|---|
| ocr | 7 | 100,0 % | 100,0 % | 100,0 % |

![Latencias](latencias.png)
