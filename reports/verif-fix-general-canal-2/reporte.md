# Reporte de la verif-fix-general-canal-2

Generado por `scripts/evaluar.py` a partir de `resultados.jsonl` y `juez.jsonl`; no se edita a mano. Un escenario se supera si pasa todas las verificaciones de código y el juez lo califica correcta o parcialmente correcta, sin alucinación (sección 6.4). El intervalo de Wilson usa n = escenarios, porque los ensayos de un mismo escenario no son independientes (ADR-24).

Commit evaluado: `—`.

Huella del juez: `afecd5c1b4f62d52fc605ac6b350363cddee4604ae704f30247703146aa39805`.

## Escenarios del nivel de sistema

8 escenarios, 8 ensayos.

| Tasa | Valor | Wilson 95 % (n = escenarios) | Bootstrap 95 % |
|---|---|---|---|
| Meta (correcta o parcial, sin alucinación) | 100,0 % | 67,6 % a 100,0 % | 100,0 % a 100,0 % |
| Estricta | 75,0 % | 40,9 % a 92,9 % | 37,5 % a 100,0 % |

Verificaciones de código superadas: 100,0 %. Veredictos del juez: correcta, 6; parcialmente correcta, 2; incorrecta, 0. Con alucinación: 0,0 %; cita en 87,5 %, cita que sustenta en 87,5 %, cobertura completa en 75,0 % y claridad media de 5,00.

| Latencia | Turnos | p50 servidor | p95 servidor | p50 cliente | p95 cliente | Meta | Bajo la meta |
|---|---|---|---|---|---|---|---|
| simple | 1 | 1.613 | 1.613 | 1.622 | 1.622 | 8.000 | 1 |
| rag | 7 | 5.509 | 10.330 | 5.517 | 10.361 | 15.000 | 7 |

## Enrutamiento

![Matriz de confusión](matriz_confusion.png)

### Nivel de sistema (primer turno)

| Categoría | Soporte | Precisión | Exhaustividad | F1 |
|---|---|---|---|---|
| general | 8 | 100,0 % | 100,0 % | 100,0 % |

![Latencias](latencias.png)
