# Reporte de la corrida-2c

Generado por `scripts/evaluar.py` a partir de `resultados.jsonl` y `juez.jsonl`; no se edita a mano. Un escenario se supera si pasa todas las verificaciones de código y el juez lo califica correcta o parcialmente correcta, sin alucinación (sección 6.4). El intervalo de Wilson usa n = escenarios, porque los ensayos de un mismo escenario no son independientes (ADR-24).

Commit evaluado: `b52b8a8`.

Huella del juez: `afecd5c1b4f62d52fc605ac6b350363cddee4604ae704f30247703146aa39805`.

## Escenarios del nivel de sistema

60 escenarios, 60 ensayos.

| Tasa | Valor | Wilson 95 % (n = escenarios) | Bootstrap 95 % |
|---|---|---|---|
| Meta (correcta o parcial, sin alucinación) | 83,3 % | 72,0 % a 90,7 % | 73,3 % a 91,7 % |
| Estricta | 75,0 % | 62,8 % a 84,2 % | 63,3 % a 85,0 % |

Verificaciones de código superadas: 93,3 %. Veredictos del juez: correcta, 45; parcialmente correcta, 12; incorrecta, 3. Con alucinación: 10,0 %; cita en 61,7 %, cita que sustenta en 60,0 %, cobertura completa en 78,3 % y claridad media de 4,68.

| Latencia | Turnos | p50 servidor | p95 servidor | p50 cliente | p95 cliente | Meta | Bajo la meta |
|---|---|---|---|---|---|---|---|
| simple | 18 | 2.576 | 4.585 | 2.533 | 4.434 | 8.000 | 18 |
| rag | 40 | 6.475 | 12.197 | 6.255 | 11.643 | 15.000 | 40 |

## R3 · Escenarios encadenados

3 escenarios, 3 ensayos.

| Tasa | Valor | Wilson 95 % (n = escenarios) | Bootstrap 95 % |
|---|---|---|---|
| Meta (correcta o parcial, sin alucinación) | 66,7 % | 20,8 % a 93,9 % | 0,0 % a 100,0 % |
| Estricta | 0,0 % | 0,0 % a 56,1 % | 0,0 % a 0,0 % |

Verificaciones de código superadas: 100,0 %. Veredictos del juez: correcta, 0; parcialmente correcta, 3; incorrecta, 0. Con alucinación: 33,3 %; cita en 100,0 %, cita que sustenta en 66,7 %, cobertura completa en 33,3 % y claridad media de 4,33.

| Latencia | Turnos | p50 servidor | p95 servidor | p50 cliente | p95 cliente | Meta | Bajo la meta |
|---|---|---|---|---|---|---|---|
| simple | 1 | 3.729 | 3.729 | 3.917 | 3.917 | 8.000 | 1 |
| rag | 7 | 6.346 | 15.710 | 6.106 | 14.962 | 15.000 | 6 |

## R4 · Seguridad

2 escenarios, 2 ensayos.

| Tasa | Valor | Wilson 95 % (n = escenarios) | Bootstrap 95 % |
|---|---|---|---|
| Meta (correcta o parcial, sin alucinación) | 100,0 % | 34,2 % a 100,0 % | 100,0 % a 100,0 % |
| Estricta | 100,0 % | 34,2 % a 100,0 % | 100,0 % a 100,0 % |

Verificaciones de código superadas: 100,0 %. Veredictos del juez: correcta, 2; parcialmente correcta, 0; incorrecta, 0. Con alucinación: 0,0 %; cita en 0,0 %, cita que sustenta en 0,0 %, cobertura completa en 100,0 % y claridad media de 5,00.

| Latencia | Turnos | p50 servidor | p95 servidor | p50 cliente | p95 cliente | Meta | Bajo la meta |
|---|---|---|---|---|---|---|---|
| simple | 2 | 1.885 | 2.659 | 1.884 | 2.613 | 8.000 | 2 |
| rag | 0 | — | — | — | — | 15.000 | 0 |

## Enrutamiento

![Matriz de confusión](matriz_confusion.png)

### Nivel de sistema (primer turno)

| Categoría | Soporte | Precisión | Exhaustividad | F1 |
|---|---|---|---|---|
| ipu | 22 | 100,0 % | 100,0 % | 100,0 % |
| ica | 11 | 100,0 % | 100,0 % | 100,0 % |
| general | 12 | 100,0 % | 100,0 % | 100,0 % |
| ocr | 7 | 100,0 % | 100,0 % | 100,0 % |
| fuera_de_alcance | 5 | 100,0 % | 100,0 % | 100,0 % |

## Trazas (RNF-05)

1284 ejecuciones revisadas; 0 con identificadores de los usuarios de prueba.

![Latencias](latencias.png)
