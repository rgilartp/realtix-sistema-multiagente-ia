# Calibración descartada (muestra de la corrida 2)

Primer intento de la calibración del juez con personas (R2, A6). **No se usa en el kappa.**

- **Motivo:** Rodolfo confirmó que las dos hojas de calificación se llenaron con ayuda de un chat
  externo de IA. La sección 6.4 y A6 exigen que cada evaluador califique por su lado y sin ayuda de
  ninguna IA, así que estas calificaciones no miden el acuerdo entre personas y el juez.
- **Qué hay aquí:** la muestra exportada de la corrida 2 (`muestra.csv`, sin calificaciones, y
  `clave.json`) y las dos hojas devueltas (`rodolfo/` y `dayanna/`), tal como llegaron.
- **Qué la reemplaza:** una muestra nueva con las respuestas de la corrida 2b, con el mismo
  procedimiento, en `reports/calibracion/`. `scripts/calibracion.py` no lee esta carpeta.
