# ADR-23 · Campos auxiliares del turno en `AgentState`

**Estado:** aceptada, octubre de 2026 (propuesta de B4; Rodolfo la aprobó y la corrección posterior agregó `parte_actual`). **Fuente:** sección 3.1 de la especificación técnica v6 («se permiten campos auxiliares del turno»).

## Contexto

La Tabla 3 define 14 campos. Para RF-SYS-06 (pregunta por la IA), RF-AUT-04 (sesión requerida) y los cuatro casos de la sección 3.4, los nodos necesitan intercambiar señales que los 14 campos no expresan, sin agregar nodos ni transiciones (ADR-14).

## Decisión

Cuatro campos auxiliares, todos del turno (se reinician en cada mensaje):

- `marcas`: diccionario con las banderas del turno: `sesion_requerida`, `solicitud_explicita`, `pregunta_ia`, `tributario_fuera_mvp`, `municipio_distinto`, `no_tributario`, `reclasificar`, `fallo_servicio`, `confianza_calculada` y `registro_fallido`.
- `respuesta_final`: texto que entrega `nodo_respuesta` o `nodo_escalamiento` a la interfaz.
- `categorias_descartadas`: categorías que un worker declaró «no corresponde» en el turno, para que la reclasificación no las repita.
- `parte_actual`: la parte que atiende el worker, con su `categoria` y su `texto`. El orquestador la fija con la primera parte o con la pendiente que saca de la lista. Cada agente responde su parte (sección 3.3) y anota en su respuesta parcial la `parte` que contestó; al reclasificar, el orquestador clasifica solo el texto de la parte rechazada, no el mensaje completo, y descarta cualquier pareja (categoría, parte) que ya haya respondido en el turno, de modo que ninguna categoría responde dos veces la misma parte. Si no queda ninguna pareja nueva, escala con «sin cobertura».

Cada respuesta parcial lleva además, anotados por `nodo_confianza`, su `nivel`, el `origen` de ese nivel cuando B5 lo agregue y `aprobada`: solo las partes aprobadas se muestran al contribuyente, también cuando se escala (sección 3.4, caso 4); las rechazadas van en el resumen para el funcionario. Esas anotaciones viven dentro de `respuestas_parciales` y no agregan campos.

La oferta de transferencia tras la pregunta por la IA se guarda en `datos_extraidos` (campo que sí se conserva entre turnos), para tratar un «sí» posterior como solicitud explícita.

`intentos_clasificacion` se acumula por conversación (sección 3.1), así que el tope de 2 reclasificaciones vale para toda la conversación y no por turno (Rodolfo lo confirmó al aprobar la propuesta); si en B7 se quisiera un tope por turno, se consulta antes.

## Alternativas

Usar solo los 14 campos, codificando las marcas dentro de `motivo_escalamiento` o `respuestas_parciales`; se descartó por frágil.

## Consecuencias

Se mantienen los 8 nodos y las 8 transiciones, y los 14 campos de la Tabla 3 con su ciclo de vida. `AgentState` queda con 14 + 4 campos. Las funciones de enrutamiento siguen siendo puras: solo leen el estado.

## Cambio en el documento de grado

Ninguno: la sección 3.1 de la especificación ya permite los campos auxiliares.
