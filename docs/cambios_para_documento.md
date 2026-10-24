# Registro de cambios para el documento de grado

Cambios del desarrollo frente al documento de grado, para el chat de documentos. Se mantiene en cada
bloque y se entrega completo en B17 (sección 9 de la especificación técnica).

| Sección del documento | Qué dice hoy | Qué queda en el desarrollo | Estado |
|---|---|---|---|
| 1.5.2.1.3 (ejemplo de costo) | Sonnet 4.6 y Haiku 4.5, con tres llamadas por consulta | Sonnet 5.5 y Haiku 5.5, con dos o tres llamadas; el costo real se mide en el OE4 | Por medir |
| 1.5.2.8.3 | Respuestas de referencia de un experto tributario | Redactadas por los autores a partir de fuentes oficiales | Aprobado (ADR-22) |
| 1.6.4.1 | Reunión con las partes interesadas | Los resultados se presentan al director; Realtix no participa | Por confirmar con el equipo |
| 3.2, Anexos B y C (RF-ORQ-05 y RF-OCR-05) | Sonnet 4.6 en el orquestador y en el nodo de confianza; Haiku 4.5 en los agentes y en el OCR | Sonnet 5.5 en el orquestador; Haiku 5.5 en los agentes y en el OCR; nodo de confianza sin modelo | Aprobado (ADR-02 y ADR-03) |
| 3.4, Tabla 18 | La cobertura de alcance la verifica el modelo del nodo de confianza | Se deriva de la clasificación del orquestador y de lo que declara el agente | Aprobado (ADR-03) |
| 3.5 | Conversacion y CasoEscalado son propias del sistema multiagente de IA | Viven en PostgreSQL junto al checkpointer; la base sintética se abre en solo lectura | Aprobado (ADR-05) |
| 3.6 y Tabla 19 | Fragmentos de 400 a 800 tokens con solape; fuentes de la Tabla 19; manuales públicos de la OVT | Un fragmento por artículo de hasta 800 tokens, con solape solo en los largos; se suman el Acuerdo 780 de 2020 y la resolución de rangos de 2026; manual de la OVT simulada y glosario | Aprobado (ADR-04, ADR-19 y ADR-20) |
| 3.8 y Tabla 22 | Siete puntos de acceso REST | Los siete, más los de mensajes del widget, bandeja y sesión simulada | Aprobado |
| 3.9 y Tabla 23 | Proxy Nginx | Proxy Caddy con HTTPS automático y nombre en DuckDNS | Aprobado (ADR-09) |
| Fase 4 (rúbrica de usabilidad) | Aplicada a usuarios | SUS y evaluación heurística de los dos autores | Aprobado (ADR-21) |

Fuente: sección 9 de la especificación técnica v6.
