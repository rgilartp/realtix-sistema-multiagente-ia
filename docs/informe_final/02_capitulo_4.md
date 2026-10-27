# Capítulo 4 · Actividades de la fase 3 (borrador)

Una sección por actividad de la fase 3 (sección 8.18 de la especificación): qué se construyó, qué RF
y RNF cubre, cómo se verificó y sus cifras, cada una con su archivo de origen. Las capturas están en
`05_figuras_y_capturas.md`.

## 4.1 Base sintética de RealSit

**Qué se construyó.** Una base SQLite sintética con el esquema v2 del contrato de RealSit, abierta
siempre en solo lectura (`mode=ro`, ADR-05), y un adaptador con los siete métodos de la Tabla 7, en
el que la regla de acceso a predios propios quedó en un solo lugar. El generador produjo exactamente 500
predios con cuatro vigencias del impuesto predial unificado (2.000 obligaciones) y las obligaciones
del ICA de los contribuyentes con actividad, más 12 usuarios de prueba fijos con sus valores
esperados escritos a mano desde la norma. La base se identificó con una huella SHA-256 sobre su
contenido (`docs/resumenes/b03.md`). Para el agente OCR se generaron recibos sintéticos con los
ocho campos de la plantilla y la leyenda de documento sintético, sin marcas reales, y variantes
degradadas (`docs/resumenes/b10.md`).

**Requerimientos:** RF-SYS-02 · Alcance de solo lectura; RNF-04 · Uso exclusivo de datos
sintéticos; RF-OCR-06 · Plantilla sintética de recibo.

**Cómo se verificó.** Pruebas de contrato del adaptador y de los 12 usuarios de prueba frente a sus
valores esperados (`docs/resumenes/b03.md`). La huella de la base fue idéntica antes y después de la
corrida 1 (`reports/corrida-1/constancias.md`) y de la corrida 2
(`reports/no_funcionales/huella_realsit.txt`, PR de B15):
`4479d0369ba967a2d8ed40fb6e7d12bff1ed497ad86ce230093f0c857312d0a2`.

## 4.2 Base de conocimiento e ingesta

**Qué se construyó.** Un flujo de curaduría que descargó las normas, las cortó por artículo, las
contrastó fila por fila con sus fuentes y produjo los datos por año gravable de `datos/` (ADR-06):
el predial de 2026 y de 2027, el ICA de 2026 (486 actividades con tarifa) y de 2027 (447 de tarifa
fija y 28 de tarifa progresiva), el calendario, los regímenes del ICA, la UVT y el SMMLV
(`docs/resumenes/b02.md`). La base de conocimiento quedó en cuatro colecciones (`normativa_ipu`,
`normativa_ica`, `normativa_datos` y `plataforma_general`, esta última con el manual sintético de la
OVT simulada y un glosario con fuente en cada término, ADR-19). La ingesta, idempotente, segmentó
las normas en fragmentos de un artículo con sus metadatos y sus notas de vigencia, y calculó los
embeddings con `text-embedding-3-large` (`docs/resumenes/b08.md`). La recuperación combinó la
búsqueda vectorial en ChromaDB con BM25 en español, fusionadas por rango recíproco (RRF, k = 60;
ADR-04).

**Requerimientos:** RF-OBS-04 · Actualización de la base vectorial; RF-GEN-03 · Respuesta sustentada
en fuentes; RF-IPU-05 · Citación de la norma.

**Cómo se verificó y cifras.**

- La ingesta inicial costó US$0,05; repetida no gastó nada y, al cambiar la segmentación, solo pagó
  los textos nuevos (US$0,02). La mediana de una consulta fue de 423 ms (`docs/resumenes/b08.md`).
- Una revisión externa de la recuperación llevó la base de 1.117 a 1.148 fragmentos
  (`docs/resumenes/fix-recuperacion.md`); ese corpus (`408d90bdb6af2d40`) fue el de las corridas 1 y
  2 (`reports/corrida-1/criterios_de_entrada.md` y, para la corrida 2, la sección «Despliegue» de
  `docs/resumenes/correcciones-corrida-1.md` y `reports/no_funcionales/volumenes.json`, con 1.148
  fragmentos).
- Un verificador automático confirmó las 167 cifras de las respuestas de referencia: 48 con los datos
  por año gravable, 106 con el usuario de prueba y el adaptador, 4 con las normas citadas, 2 con los
  mensajes del contribuyente y 7 derivadas (sumas, base por tarifa y el siguiente día hábil)
  (`docs/resumenes/b12.md`).
- Después de la corrida 2 se propuso fusionar la búsqueda del orquestador y el texto del
  contribuyente: sin modelos, las fuentes esperadas recuperadas subieron de 40 a 42 de 69
  (`reports/recuperacion_fusion.json`, PR #49). Quedó pendiente de una decisión, sin fusionar.

## 4.3 Orquestador y grafo

**Qué se construyó.** El grafo de LangGraph con ocho nodos y ocho transiciones (ADR-14), el estado
compartido con los 14 campos de la Tabla 3 y tres auxiliares del turno (ADR-23), y funciones puras de
enrutamiento (`docs/resumenes/b04.md`). El orquestador, con Claude Sonnet 5.5 (ADR-02), clasificó
cada consulta en una salida estructurada con sus partes y marcas, y el código decidió las reglas de
acceso (`docs/resumenes/b07.md`). Desde las correcciones de la corrida 1, la API reportó la categoría
de la clasificación y no la del agente que respondió (F2, `docs/resumenes/correcciones-corrida-1.md`).

**Requerimientos:** RF-ORQ-01 · Clasificación de la consulta; RF-ORQ-03 · Consultas multiagente;
RF-ORQ-05 · Modelo de razonamiento; RF-ORQ-06 · Prevención de bucles.

**Cómo se verificó y cifras.** Con 100 consultas etiquetadas (20 por categoría), el clasificador
tuvo una exactitud de 99,0 %, un kappa de 0,99 y un F1 macro de 99,0 %, frente a una exactitud de
20,0 % de la clase mayoritaria (`reports/corrida-1/reporte.md`, componentes). Una prueba exigió que
la figura del grafo coincidiera con el grafo implementado (`docs/figuras/grafo_implementado.mmd`).

## 4.4 Agentes con RAG

**Qué se construyó.** Los agentes del impuesto predial, de industria y comercio y de información
general, con Claude Haiku 5.5, recuperaron los fragmentos de su colección y consultaron el adaptador
y los servicios de dominio mediante herramientas; una segunda llamada entregó la respuesta
estructurada, a la que el código agregó, sin modificarlas, las notas y las fuentes
(`docs/resumenes/b07.md`). Los servicios de dominio (nivel de confianza, liquidación estimada,
estimación del ICA, régimen y fechas, resumen, acceso, horario y minimización) se escribieron sin
LangGraph y calcularon todo con `datos/` (`docs/resumenes/b05.md`). Después de la corrida 1 se agregaron,
entre otras, la regla de la periodicidad registrada del ICA, un verificador de citas sin modelo con
una reescritura, herramientas de tarifas por año sin sesión y el rechazo previo de un predio ajeno
(`docs/resumenes/correcciones-corrida-1.md`). Las correcciones de la corrida 2 quedaron propuestas,
sin fusionar (PR #49 a #51).

**Requerimientos:** RF-IPU-01 · Consultas conceptuales de IPU; RF-IPU-02 · Estado de cuenta e
historial; RF-IPU-03 · Liquidación estimada; RF-IPU-04 · Plazos y descuentos; RF-IPU-05 · Citación
de la norma; RF-ICA-01 · Consultas conceptuales de ICA; RF-ICA-02 · Estimación por actividad;
RF-ICA-03 · Fechas de declaración; RF-ICA-04 · Retenciones fuera de alcance; RF-GEN-01 · Consultas
transversales; RF-GEN-02 · Explicación en lenguaje sencillo; RF-GEN-03 · Respuesta sustentada en
fuentes; RF-ESC-01 · Cálculo del nivel de confianza; RNF-03 · Protección de datos personales.

**Cómo se verificó y cifras.**

- Ningún nombre ni documento llegó a los modelos (pruebas del anonimizador).
- La prueba de humo con modelos reales recorrió 12 escenarios, con una mediana de 5,7 s en las
  consultas simples y de 7,0 s con recuperación, por unos US$0,09 (`docs/resumenes/b07.md`).
- En el nivel de componentes de la corrida 1, los agentes, corridos directo contra su nodo, superaron
  19 de 34 escenarios (`reports/corrida-1/metricas.json`).

## 4.5 Agente OCR

**Qué se construyó.** Un agente OCR que rechazó por código los documentos de baja resolución,
recortados o desenfocados; leyó los demás con el modelo de visión y salida estructurada; presentó
los seis campos para que el contribuyente los confirmara, y, tras la confirmación, los contrastó con
la obligación registrada sin modificarla (`docs/resumenes/b10.md`).

**Requerimientos:** RF-OCR-01 · Carga de archivos; RF-OCR-02 · Extracción de campos; RF-OCR-03 ·
Confirmación de datos extraídos; RF-OCR-04 · Rechazo de documentos ilegibles; RF-OCR-05 · Modelo de
visión; RF-OCR-06 · Plantilla sintética de recibo; RF-UI-04 · Carga desde la conversación; RF-AUT-02
· Restricción a predios propios.

**Cómo se verificó y cifras.** Con el modelo de visión, la exactitud fue del 100 % en los seis campos
de los 20 documentos legibles (10 recibos en PNG y en PDF), y los seis documentos degradados o de
otro tipo se rechazaron con su motivo, por US$0,0088 (`docs/resumenes/b10.md`,
`reports/b10_ocr.json`).

## 4.6 Escalamiento

**Qué se construyó.** El escalamiento por baja confianza (ADR-17: 0,4 × similitud + 0,4 ×
suficiencia + 0,2 × cobertura, umbral de 0,7), por solicitud explícita, por un tema fuera del MVP o
por una falla de servicio. Un caso que escalaba antes de la confianza quedó con nivel 0,0 y su motivo
(ADR-13). Solo `nodo_escalamiento` registró el caso, con un resumen para el funcionario (ADR-18), y
la conversación escalada pasó a modo humano (ADR-12). La API recibió un botón de escalamiento
(`docs/resumenes/b04.md`, `b05.md` y `b09.md`).

**Requerimientos:** RF-ESC-01 · Cálculo del nivel de confianza; RF-ESC-02 · Activación del
escalamiento; RF-ESC-03 · Resumen del caso; RF-ESC-04 · Tiempo de entrega del resumen; RF-ESC-05 ·
Notificación al contribuyente; RNF-08 · Tiempos de espera y degradación.

**Cómo se verificó y cifras.** En la corrida 2, ocho fallas inyectadas (orquestador, modelo,
recuperación y adaptador, por tiempo y por error) escalaron por «fallo de servicio» sin mostrar un
error técnico (`reports/no_funcionales/fallas_inyectadas.json`, PR de B15). El umbral se revisó con
las corridas 1 y 2 (`reports/umbral/propuesta.md`, PR de B15): **PENDIENTE (calibración)** la aprobación del
valor.

## 4.7 Interfaz

**Qué se construyó.** La interfaz web con Vite, React y Tailwind (ADR-08): una OVT simulada rotulada
como entorno de pruebas, el widget en un iframe (aviso de IA, interlocutor, fuentes, aviso de fuera
de horario, carga del recibo y botón para hablar con un funcionario) y la consola con la bandeja de
casos y las métricas de enrutamiento. La identidad visual propia, «Formulario y sello», usó los
colores de Realtix sin su logo ni su nombre y cumplió el contraste WCAG 2.2 AA en modo claro y
oscuro (`docs/resumenes/b11.md`).

**Requerimientos:** RF-UI-01 · Widget embebible; RF-UI-02 · Contexto de la sesión; RF-UI-03 ·
Identificación del interlocutor; RF-UI-04 · Carga desde la conversación; RF-SYS-06 · Aviso de
interacción con IA (provisional); RF-ESC-05 · Notificación al contribuyente; RNF-07 · Aviso fuera de horario.

**Cómo se verificó.** Seis flujos con Playwright en 1280 y 390 px, pruebas del cambio de tema y del
ancho mínimo de 360 px, y la medición automática del contraste en la integración continua
(`docs/resumenes/b11.md`). La usabilidad con el SUS y la evaluación heurística: **PENDIENTE
(usabilidad)**.

## 4.8 Observabilidad

**Qué se construyó.** El registro propio de interacciones sin datos personales y las trazas de
LangSmith con el identificador de conversación (ADR-11); la matriz de confusión y las métricas de
precisión y tiempo en la consola; y un verificador automático de trazas que busca los documentos y
los nombres de los usuarios de prueba (`docs/resumenes/b09.md` y `b12.md`).

**Requerimientos:** RF-OBS-01 · Traza del flujo entre agentes; RF-OBS-02 · Matriz de confusión de
enrutamiento; RF-OBS-03 · Métricas de precisión y tiempo; RF-OBS-04 · Actualización de la base
vectorial; RF-OBS-05 · Ejecución repetible de pruebas; RNF-05 · Registro auditable.

**Cómo se verificó y cifras.** Ninguna traza tuvo identificadores: 1.279 ejecuciones de 63
conversaciones en la corrida 1 (`reports/corrida-1/constancias.md`) y 1.277 ejecuciones de 63
conversaciones en la corrida 2 (`reports/corrida-2/trazas.json`, PR de B15).

## 4.9 Despliegue

**Qué se construyó.** El sistema multiagente de IA se empaquetó en contenedores y se desplegó en una
instancia EC2 m7i-flex.large con Docker Compose (ADR-10), detrás de un proxy Caddy con HTTPS
automático y DuckDNS (ADR-09), cabeceras de seguridad y límites de tamaño. La imagen del backend se construyó
en varias etapas, sin secretos ni privilegios; la configuración no secreta se versionó y los
secretos quedaron en un archivo de entorno. Un flujo de GitHub Actions revisó `/health` cada 15
minutos en el horario hábil (`docs/resumenes/b13.md`).

**Requerimientos:** RNF-02 · Escalamiento horizontal; RNF-06 · Horario de atención; RNF-12 ·
Imágenes de contenedor; RNF-13 · Orquestación con Compose; RNF-14 · Configuración por entorno;
RNF-15 · Volúmenes persistentes.

**Cómo se verificó y cifras.** La carga de la base de conocimiento en el servidor costó US$0,05
(`docs/resumenes/b13.md`). En B15, una conversación continuó en la otra réplica, y el corpus, las
conversaciones y los casos persistieron después de reiniciar y de recrear los contenedores
(`reports/no_funcionales/README.md`, `replicas.json` y `volumenes.json`, PR de B15). La
disponibilidad medida por el monitor: **PENDIENTE (corrida 3)**.
