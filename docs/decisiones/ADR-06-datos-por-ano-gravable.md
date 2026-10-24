# ADR-06 · Tarifas y plazos por año gravable

**Estado:** aprobada, octubre de 2026. **Fuente:** sección 2 de la especificación técnica v6.

## Contexto

Las tarifas del predial y del ICA cambian desde 2027 (Acuerdo 1084 de 2026) y el calendario cambia cada año (adenda, sección 3.2).

## Decisión

Tarifas y plazos por año gravable, en archivos de datos versionados en `datos/` con fuente y mes de consulta (sección 4.3).

## Alternativas

Tarifas escritas en el código; una sola tabla sin vigencias.

## Consecuencias

La liquidación, la estimación del ICA y el RAG dicen lo mismo, con la norma del año de la consulta. Si un año no tiene datos, el sistema multiagente de IA lo dice y no estima.

## Cambio en el documento de grado

Ninguno.
