# ADR-01 · Desarrollo con Claude Code en WSL 2

**Estado:** aprobada, octubre de 2026. **Fuente:** sección 2 de la especificación técnica v6.

## Contexto

El equipo tiene un solo operador, Rodolfo, que desarrolla en su PC con Windows. El servidor del MVP corre Ubuntu.

## Decisión

Se desarrolla con Claude Code en WSL 2 (Ubuntu 24.04), en el PC de Rodolfo, desde VS Code, con Docker Engine dentro de WSL.

## Alternativas

Desarrollo directo en Windows; desarrollo en un servidor remoto.

## Consecuencias

Los commits llevan la identidad de Rodolfo y su firma; el sistema operativo de desarrollo es el mismo del servidor.

## Cambio en el documento de grado

Ninguno.
