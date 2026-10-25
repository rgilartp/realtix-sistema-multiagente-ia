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
| Tabla 19 (fuentes) | Acuerdo 65 de 2002, art. 3, «en su texto vigente» para las tarifas de ICA de 2026 | El texto vigente en 2026 se arma con el texto original del art. 3 del Acuerdo 65, los arts. 6 y 7 del Acuerdo 780 de 2020, el art. 4 del Acuerdo 816 de 2021, la Resolución SDH-000265 de 2021 (CIIU y tarifas de 2024), el Acuerdo 98 de 2003 y el art. 44 del Acuerdo 1019 de 2025 (SIMPLE); el Acuerdo 98, el art. 7 del Acuerdo 780 y el art. 44 del Acuerdo 1019 los derogó el art. 52 del Acuerdo 1084. Diez CIIU chocaban entre la resolución y el Acuerdo 780: prevalece la resolución (fila siguiente) | Aprobado por Rodolfo en la parada de B2 |
| Tabla 19 (fuentes), art. 6 del Acuerdo 780 | El art. 6 del Acuerdo 780 sube a 8,66 por mil a los servicios prestados por contratistas de construcción, constructores y urbanizadores | Para los CIIU 4111, 4112, 4311, 4312, 4321, 4322, 4329 y 39002 se aplica 6,9 por mil, y para 4330 y 4390, 7,6 por mil, según la Resolución SDH-000265 de 2021, art. 1 (clasificación oficial por CIIU de la Secretaría de Hacienda): es la clasificación con la que Hacienda aplica ese artículo, se expidió después del acuerdo y no tiene modificaciones ni nulidades, y el art. 21 del Acuerdo 1084 conserva la misma agrupación para 2027. Cada fila lleva una nota para el agente | Decisión de Rodolfo en la parada de B2 |
| Tabla 19 (fuentes) | Ley 14 de 1983 en su texto vigente compilado | Texto del Régimen Legal de Bogotá (i=267), con sus notas de vigencia. Los arts. 33 y 36 muestran el texto de 1983 aunque la Ley 1819 de 2016 (arts. 342 y 345) los modificó: se marcan como texto anterior, no vigente, y los arts. 342 y 345 de la Ley 1819 se cargan en `normativa_ica` | Aprobado |
| Tabla 19 y bibliografía | Enlace del Acuerdo 1084 de 2026 con el nombre del archivo dañado | Copia del texto firmado en el INCP (`incp.org.co/?p=136894`); el Régimen Legal de Bogotá ya trae el texto de sus arts. 20 y 21 dentro de los Acuerdos 105 de 2003 y 65 de 2002 | Aprobado |
| Tabla 19 y marco jurídico | Resolución SDH-000195 de 2025 como fuente de calendario; resolución de rangos de 2026 sin número | La resolución de rangos del predial de 2026 es la SDH-000194 de 2025 | Aprobado |
| Marco jurídico, Acuerdo 1084 | Tarifas nuevas del ICA: «las 9 tarifas nuevas» | El art. 21 trae 475 actividades: 447 de tarifa fija, con 8 tarifas distintas (4, 7, 8, 10, 11, 12, 13 y 19 por mil), y 28 actividades financieras con tarifa progresiva de 20, 19 y 18 por mil | Aprobado |
| Marco jurídico, Acuerdo 1084 | Sobretasa de alumbrado: tarifas y topes por transcribir | Tarifas de 0 a 1 por mil según la categoría y topes de 600 UVT (residenciales) y 1.200 UVT (demás predios) | Aprobado |
| Marco jurídico, Acuerdo 1084, art. 7 | Reducción del 60 % de intereses y sanciones, «por verificar» (fuente secundaria) | Verificada en el PDF: se paga el 100 % del capital y el 40 % de intereses y sanciones hasta el 21 de diciembre de 2026 | Aprobado |
| Marco jurídico, Acuerdo 1084, art. 21 | Tarifas nuevas del ICA desde el bimestre siguiente a la aprobación del acuerdo, «falta confirmar la fecha» | El acuerdo se aprobó en plenaria el 28 de septiembre de 2026 y se firmó el 8 de octubre de 2026, ambas fechas dentro del bimestre 5; las tarifas del art. 21 aplican a los bimestrales desde el bimestre 6 de 2026 (noviembre-diciembre, que se declara a más tardar el 12 de febrero de 2027) y a los anuales desde el 1 de enero de 2027 | Aprobado |
| Tabla 19 (fuentes) | Decreto 474 de 2016 y Decreto 807 de 1993 sin versión compilada | Texto del Régimen Legal de Bogotá con sus notas de vigencia; el Decreto 474 está compilado por el Decreto 639 de 2025, que no se carga | Aprobado |
| Tabla 19 (fuentes) | Ley 1581 de 2012 | Se cargan los artículos 1 a 30 | Aprobado |

Fuente: sección 9 de la especificación técnica v6.
