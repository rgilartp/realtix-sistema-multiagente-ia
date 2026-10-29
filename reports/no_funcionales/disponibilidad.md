# Disponibilidad (RNF-06 · Horario de atención)

Generado por `disponibilidad.py` desde `salud.log` (monitor del servidor cada 5 minutos; días relativos al primer chequeo, hora de Colombia). No se edita a mano.

Periodo: 42,6 horas, 512 chequeos. Meta: 99 % en horario hábil; resultado: **no cumple**.

| Medida | Chequeos con 200 | Disponibilidad |
|---|---|---|
| **Oficial: horario hábil, todo el registro** | 130 de 152 | 85,53 % |
| Todas las horas | 485 de 512 | 94,73 % |
| Horario hábil sin las ventanas de despliegue | 115 de 137 | 83,94 % |
| Horario hábil desde la corrección del PR #54 | 130 de 130 | 100,00 % |

Fallas: 27 (códigos 502; commits `4e94e7a`); 22 en horario hábil, 27 antes de la corrección del PR #54 y 2 en una ventana de despliegue. Despliegues marcados: 9.
