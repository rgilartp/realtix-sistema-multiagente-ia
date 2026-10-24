# ADR-17 · Valores iniciales del nivel de confianza

**Estado:** aprobada, octubre de 2026. **Fuente:** sección 2 de la especificación técnica v6.

## Contexto

La arquitectura deja los pesos y el umbral para calibrar en la Fase 4.

## Decisión

Pesos de 0,4 (similitud), 0,4 (suficiencia) y 0,2 (cobertura); umbral de 0,7; la falta de cobertura escala siempre.

## Alternativas

Pesos iguales; un umbral más bajo.

## Consecuencias

Punto de partida configurable (`UMBRAL_CONFIANZA` y `PESO_*`); se calibra con las corridas 1 y 2.

## Cambio en el documento de grado

Decide el valor inicial pendiente.
