# ADR-13 · Escalamiento antes de calcular la confianza

**Estado:** aprobada, octubre de 2026. **Fuente:** sección 2 de la especificación técnica v6.

## Contexto

Un caso puede escalar desde el orquestador, antes de que exista el nivel de confianza (OC-08).

## Decisión

En ese caso se registra `nivel_confianza = 0.0` con su motivo.

## Alternativas

Permitir un nivel nulo en el esquema.

## Consecuencias

No cambia el esquema y el registro del caso no falla.

## Cambio en el documento de grado

Decide OC-08.
