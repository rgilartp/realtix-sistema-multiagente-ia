# ADR-12 · Modo humano de una conversación escalada

**Estado:** aprobada, octubre de 2026. **Fuente:** sección 2 de la especificación técnica v6.

## Contexto

Hacía falta decidir qué pasa con los mensajes nuevos de una conversación ya escalada (decisión D6).

## Decisión

Una conversación escalada ya no la atienden los agentes; los mensajes nuevos quedan en el caso, y la API responde con `interlocutor: "sistema"` y un aviso de que el caso está en manos de un funcionario.

## Alternativas

Que los agentes sigan respondiendo; cerrar la conversación.

## Consecuencias

Coherente con RF-ESC-05 · Notificación al contribuyente y RF-UI-03 · Identificación del interlocutor.

## Cambio en el documento de grado

Decide D6.
