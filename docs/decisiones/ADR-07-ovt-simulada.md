# ADR-07 · OVT simulada con token HMAC

**Estado:** aprobada, octubre de 2026. **Fuente:** sección 2 de la especificación técnica v6.

## Contexto

No hay acceso a la OVT real de RealSit y la autenticación está delegada en su sesión.

## Decisión

Página de pruebas, rotulada como simulación y sin marcas reales, que entrega un token de sesión firmado con HMAC-SHA256 (contribuyente, emisión y vencimiento de 2 horas).

## Alternativas

Usuario y contraseña propios; omitir la autenticación en el MVP.

## Consecuencias

Permite demostrar RF-AUT-01 a RF-AUT-04 sin acceso a la OVT real. Solo se activa con `OVT_SIMULADA_ACTIVA=true`.

## Cambio en el documento de grado

Sección 6.1 de arquitectura (se precisa).
