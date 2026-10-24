# ADR-14 · Cuatro casos de enrutamiento sin transiciones nuevas

**Estado:** aprobada, octubre de 2026. **Fuente:** sección 2 de la especificación técnica v6.

## Contexto

Cuatro situaciones no tenían transición propia en la Tabla 2 de arquitectura (sección 5.2 del contexto).

## Decisión

Se resuelven sin transiciones nuevas (sección 3.4): aviso de sesión requerida por `nodo_general`; predio ajeno como respuesta válida sin escalar; «no corresponde» con el tope alcanzado escala; la consulta multiagente escalada entrega las partes ya resueltas.

## Alternativas

Agregar transiciones al grafo.

## Consecuencias

Se mantienen los 8 nodos y las 8 transiciones (D2).

## Cambio en el documento de grado

Decide la sección 5.2 del contexto.
