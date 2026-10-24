# ADR-16 · Modo de evaluación con reloj inyectable

**Estado:** aprobada, octubre de 2026. **Fuente:** sección 2 de la especificación técnica v6.

## Contexto

Las corridas de prueba pueden caer fuera del horario de atención; sin un reloj controlable, el sistema multiagente de IA se niega a responder, como exige RNF-06 · Horario de atención.

## Decisión

Reloj inyectable (`X-Reloj-Simulado`), horario configurable y `X-Escenario-Id`; solo se activa por configuración (`MODO_EVALUACION`).

## Alternativas

Desactivar el horario en las pruebas.

## Consecuencias

Las corridas son repetibles (RF-OBS-05) sin debilitar el horario en producción.

## Cambio en el documento de grado

Ninguno.
