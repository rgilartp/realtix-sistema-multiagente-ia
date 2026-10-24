# ADR-08 · Widget en iframe y consola web

**Estado:** aprobada, octubre de 2026. **Fuente:** sección 2 de la especificación técnica v6.

## Contexto

El widget se inserta en una página ajena (la OVT). Dentro de Shadow DOM, Tailwind 4 pierde bordes, anillos y sombras sin un complemento adicional.

## Decisión

Widget en iframe (React 19, Vite 8 y Tailwind 4) y consola web para el funcionario y el administrador.

## Alternativas

Shadow DOM; un script sin aislamiento.

## Consecuencias

El iframe aísla estilos y scripts; la cabecera `frame-ancestors` limita dónde se puede insertar.

## Cambio en el documento de grado

Sección 4 de arquitectura.
