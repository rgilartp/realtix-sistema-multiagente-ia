# ADR-10 · Servidor EC2 m7i-flex.large

**Estado:** aprobada, octubre de 2026. **Fuente:** sección 2 de la especificación técnica v6.

## Contexto

El MVP se despliega en AWS sin presupuesto propio de infraestructura.

## Decisión

EC2 m7i-flex.large (2 vCPU y 8 GiB) en us-east-1, en una cuenta nueva de AWS con el plan Free.

## Alternativas

Instancias más pequeñas del plan Free; otro proveedor de nube.

## Consecuencias

Es elegible para el plan Free y se paga con sus créditos; alcanza para los cuatro contenedores.

## Cambio en el documento de grado

Presupuesto.
