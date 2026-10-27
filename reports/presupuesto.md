# Presupuesto de las corridas (B12)

Generado por `scripts/estimar_costos.py`. Precios oficiales en US$ por millón de tokens (entrada / salida), comprobados en octubre de 2026 en la página de cada proveedor:

- `claude-sonnet-5-5`: 2 / 10
- `claude-haiku-5-5`: 0,10 / 0,50
- `claude-opus-5-5`: 4 / 20
- `text-embedding-3-large`: 0,13 / 0
- `gpt-4o-mini`: 0,15 / 0,60
- `gpt-4,1-mini`: 0,40 / 1,60

Costos unitarios medidos (se toma el mayor de B9 y de la mini corrida para el turno):

- turno del sistema: US$0.0083; calificación del juez: US$0.0205;
- caso de RAGAS (`gpt-4.1-mini` y embeddings): US$0.0200;
- clasificación del orquestador: US$0.0056; respuesta de un agente: US$0.0030.

Conteos: 60 escenarios con 62 turnos; 100 consultas de enrutamiento; 34 escenarios de agente; unos 20 casos de RAGAS por ensayo; R3 con 9 turnos y R4 con 2.

| Concepto | Anthropic (US$) | OpenAI (US$) |
|---|---|---|
| Gastado hasta B11 | 1,21 | 0,08 |
| B12: validación de evaluadores, pruebas de RAGAS y mini corrida | 0,22 | 0,09 |
| Corrida 1: 60 × 1 ensayo, juez y componentes | 3,10 | 0,00 |
| Corrida 2: 60 × 1 ensayo y juez | 1,75 | 0,00 |
| Corrida 3: 60 × 3, juez, componentes y RAGAS × 3 | 6,59 | 1,20 |
| Reserva para las correcciones (escenarios afectados) | 2,00 | 0,20 |
| **Subtotal sin mejoras** | **14,87** | **1,57** |
| R2 · muestra de 30 estratificada (usa los veredictos ya pagados) | 0,00 | 0,00 |
| R4 · 2 de seguridad, en las corridas 1 y 2 y × 3 en la 3 | 0,29 | 0,00 |
| R3 · 3 encadenados, en las corridas 1 y 2 y × 3 en la 3 | 0,68 | 0,00 |
| R1 · 10 variantes × 3 ensayos, solo en la corrida 3 | 0,86 | 0,60 |
| **Total con R1 a R4** | **16,71 de 25** | **2,17 de 10** |

Las cuatro mejoras caben: margen de US$8,29 en Anthropic. Si una corrida real se acerca al tope, el orden de prioridad es R2, R4, R3 y R1. `scripts/evaluar.py --tope-usd` detiene una corrida que supere lo previsto.
