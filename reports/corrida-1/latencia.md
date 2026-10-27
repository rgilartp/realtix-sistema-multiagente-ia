# Latencia de la corrida 1 (RNF-01 · Tiempo de respuesta)

Turnos que llegaron a los agentes, separados por si recuperaron fragmentos (RAG) o no. Las cifras
son del servidor (`meta.tiempos_ms`) y del cliente, en ms, para los 60 escenarios (las de R3 y R4
están en `reporte.md`).

| Tipo | Turnos | p50 servidor | p95 servidor | p50 cliente | p95 cliente | Máximo servidor | Límite | Bajo el límite |
|---|---|---|---|---|---|---|---|---|
| Simple | 18 | 1.772 | 5.200 | 1.846 | 5.113 | 5.200 | 8.000 | 18 de 18 |
| Con RAG | 40 | 6.333 | 10.499 | 6.301 | 10.334 | 12.985 | 15.000 | 40 de 40 |

**Comparación.**

| Medición | Con RAG: p50 | Con RAG: p95 | Máximo |
|---|---|---|---|
| B9 (API local, 6 consultas) | — | — | 8.600 |
| Mini corrida de B12 (API local en WSL 2, 3 turnos) | 12.422 | 16.178 | 16.178 |
| Corrida 1 (servidor en us-east-1, 40 turnos) | 6.333 | 10.499 | 12.985 |

**Desglose por nodo** (los 71 turnos con agentes de los tres conjuntos, del servidor):

| Tramo | Simple p50 | Simple p95 | Con RAG p50 | Con RAG p95 |
|---|---|---|---|---|
| Orquestador (Sonnet 5.5) | 1.659 | 2.334 | 1.736 | 2.519 |
| Agentes (Haiku 5.5, con herramientas y recuperación) | 3 | 1.400 | 4.557 | 8.740 |
| Tokens de salida de Haiku | 0 | 110 | 676 | 1.653 |

**Lectura.**

- RNF-01 se cumple en todos los turnos: el p95 con RAG queda en 10,5 s, frente al límite de 15 s.
- Los picos de la mini corrida no se repitieron:
  - entonces, el orquestador tardó de 8,7 a 9,3 s en dos de los tres turnos con RAG; en el servidor
    su máximo fue de 2,8 s, con los mismos tokens (unos 2.650 de entrada y 150 de salida);
  - la causa probable es el entorno local: la red desde WSL 2 hasta la API y una variación puntual
    de la API de ese momento. No es un costo del grafo.
- El p95 lo pone el agente, no el orquestador. Crece con:
  - la longitud de la respuesta (el p95 de salida de Haiku es de 1.653 tokens);
  - una segunda llamada al modelo después de las herramientas.
- **No hace falta una corrección por latencia.** Si en la corrida 2 el p95 con RAG pasara de 12 s,
  la corrección general sería limitar la longitud de las respuestas, con `max_tokens` del agente y
  una instrucción de brevedad. Las respuestas largas son también una observación del juez (detalles
  que nadie pidió).
