# ADR-03 · Confianza, respuesta y escalamiento sin modelo

**Estado:** aprobada, octubre de 2026. **Fuente:** sección 2 de la especificación técnica v6.

## Contexto

La arquitectura asignaba un modelo al nodo de confianza para verificar la cobertura de alcance. RF-ESC-04 pide el resumen del caso en menos de 5 segundos.

## Decisión

`nodo_confianza`, `nodo_respuesta` y `nodo_escalamiento` son código determinista. La cobertura se deriva de la clasificación del orquestador y de lo que declara el agente; la respuesta multiagente se consolida con una plantilla.

## Alternativas

Usar Sonnet en el nodo de confianza y en la consolidación.

## Consecuencias

Menos latencia (RNF-01 · Tiempo de respuesta) y menos costo; el resultado se prueba sin modelo; el resumen cumple los 5 segundos de RF-ESC-04.

## Cambio en el documento de grado

Secciones 3.4 y 8.3 de arquitectura.
