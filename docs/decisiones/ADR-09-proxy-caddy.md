# ADR-09 · Proxy Caddy con HTTPS automático

**Estado:** aprobada, octubre de 2026. **Fuente:** sección 2 de la especificación técnica v6.

## Contexto

Let's Encrypt no emite certificados para los nombres `amazonaws.com` de EC2, y un certificado exportable de ACM tiene costo.

## Decisión

Proxy Caddy con HTTPS automático (Let's Encrypt) y nombre gratuito en DuckDNS, en lugar de Nginx con certificado de ACM.

## Alternativas

Nginx con certificado de ACM; Nginx con Certbot.

## Consecuencias

Cero costo y renovación automática del certificado.

## Cambio en el documento de grado

Tabla 9, secciones 9.2 y 9.3 y Figura 3 de arquitectura.
