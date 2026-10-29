# Disponibilidad (RNF-06 · Horario de atención)

Generado por `disponibilidad.py` desde `salud.log` (monitor del servidor cada 5 minutos; días relativos al primer chequeo, hora de Colombia). No se edita a mano.

Periodo: 43,0 horas, 517 chequeos. Meta: 99 % en horario hábil; resultado: **no cumple**.

| Medida | Chequeos con 200 | Disponibilidad |
|---|---|---|
| **Oficial: horario hábil, todo el registro** | 135 de 157 | 85,99 % |
| Todas las horas | 490 de 517 | 94,78 % |
| Horario hábil sin las ventanas de despliegue | 120 de 142 | 84,51 % |
| Horario hábil desde la corrección del PR #54 | 135 de 135 | 100,00 % |

Fallas: 27 (códigos 502; commits `4e94e7a`); 22 en horario hábil, 27 antes de la corrección del PR #54 y 2 en una ventana de despliegue. Despliegues marcados: 9.
