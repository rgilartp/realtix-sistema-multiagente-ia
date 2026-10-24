# ADR-11 · Registro propio de interacciones

**Estado:** aprobada, octubre de 2026. **Fuente:** sección 2 de la especificación técnica v6.

## Contexto

El plan gratuito de LangSmith guarda las trazas solo 14 días, y las métricas del OE4 y la auditoría necesitan datos durables (decisión D5).

## Decisión

Registro propio de interacciones en PostgreSQL, sin texto de los mensajes ni datos personales, para métricas y auditoría; LangSmith para las trazas.

## Alternativas

Solo LangSmith; un plan pago de LangSmith.

## Consecuencias

`/admin/metricas` se calcula del registro propio (RF-OBS-02 y RF-OBS-03); se cumple RNF-05 · Registro auditable sin datos personales.

## Cambio en el documento de grado

Decide D5.
