# ADR-18 · POST /api/v1/escalamiento como botón

**Estado:** aprobada, octubre de 2026. **Fuente:** sección 2 de la especificación técnica v6.

## Contexto

La Tabla 8 de arquitectura dice que el punto de acceso registra un caso escalado, y `nodo_escalamiento` también los registra.

## Decisión

`POST /api/v1/escalamiento` es el botón «Hablar con un funcionario»: marca la solicitud explícita y ejecuta el grafo, sin registrar el caso por su cuenta.

## Alternativas

Que el punto de acceso registre el caso directamente.

## Consecuencias

Un solo punto registra casos (`nodo_escalamiento`), sin duplicados.

## Cambio en el documento de grado

Precisa la Tabla 8.
