# ADR-02 · Modelos de cada nodo

**Estado:** aprobada, octubre de 2026. **Fuente:** sección 2 de la especificación técnica v6.

## Contexto

Los documentos FINAL fijan Claude Sonnet 4.6 y Claude Haiku 4.5. Haiku 4.5 tenía retiro tentativo a partir de octubre de 2026. Los modelos 5.5 cuestan menos: Haiku 5.5 cobra $0,10 y $0,50 por millón de tokens de entrada y de salida con prompts de hasta 100.000 tokens, frente a $1 y $5 de Haiku 4.5, y tienen soporte anunciado al menos hasta 2027.

## Decisión

`claude-sonnet-5-5` en el orquestador; `claude-haiku-5-5` en los agentes de IPU, ICA, información general y OCR; `claude-opus-5-5` solo como juez de la evaluación. `claude-sonnet-4-6` y `claude-haiku-4-5-20251001` quedan como alternativa por configuración (RF-SYS-04 · Modelo sustituible).

## Alternativas

Mantener Sonnet 4.6 y Haiku 4.5.

## Consecuencias

Menor costo y sin riesgo de retiro durante el proyecto. La API de los modelos 5.5 rechaza `temperature`, `top_p` y `top_k` distintos del valor por defecto y el prefijo de respuesta (sección 3.2).

## Cambio en el documento de grado

RF-ORQ-05, RF-OCR-05, sección 3.3 de requerimientos y sección 8.3 de arquitectura.
