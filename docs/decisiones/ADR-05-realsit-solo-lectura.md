# ADR-05 · Base de RealSit en solo lectura y almacén propio

**Estado:** aprobada, octubre de 2026. **Fuente:** sección 2 de la especificación técnica v6.

## Contexto

En 6.3.1 la base sintética guardaba también conversaciones y casos escalados (H-02, OC-08).

## Decisión

La base sintética de RealSit se abre en solo lectura (SQLite, `mode=ro`). Conversaciones, casos escalados, mensajes del funcionario y registro de interacciones van en PostgreSQL, junto al checkpointer.

## Alternativas

Escribir en la base sintética; un segundo archivo SQLite.

## Consecuencias

RF-SYS-02 · Alcance de solo lectura queda garantizado por construcción; el backend no guarda estado y se puede replicar (RNF-02 · Escalamiento horizontal); resuelve H-02 y OC-08.

## Cambio en el documento de grado

Sección 5.1, Figura 2 y sección 9.2 de arquitectura.
