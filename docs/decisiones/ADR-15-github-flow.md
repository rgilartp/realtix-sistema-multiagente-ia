# ADR-15 · GitHub Flow en el plan gratuito

**Estado:** aprobada, octubre de 2026. **Fuente:** sección 2 de la especificación técnica v6.

## Contexto

El plan Free de GitHub no protege ramas en repositorios privados.

## Decisión

Un PR por bloque, Conventional Commits, merge commits, ganchos que impiden commits directos a `main` y CI en cada PR.

## Alternativas

Repositorio público; un plan pago.

## Consecuencias

La protección de `main` depende de los ganchos locales y de la disciplina del protocolo (sección 0.2); la CI revisa cada PR (RNF-11 · Código versionado).

## Cambio en el documento de grado

Ninguno.
