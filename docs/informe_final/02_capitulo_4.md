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
  (`reports/recuperacion_fusion.json`, PR #49). Se cerró sin fusionar, como trabajo futuro: la
  ganancia era pequeña, duplicaba la latencia del agente general y cambiaba la similitud que alimenta
  la confianza (`docs/resumenes/b15.md`).
- Una verificación tributaria externa revisó, afirmación por afirmación, las respuestas de referencia
  y las notas fijas contra la base, los datos y las fuentes oficiales. No encontró cifras erradas; se
  precisaron citas, vigencias y redacciones de 19 escenarios y de los 3 encadenados (por ejemplo, el
  Decreto 474 de 2016, derogado, por el Decreto 639 de 2025, art. 226, que lo compiló), y el
  verificador de referencias confirmó 171 cifras sin discrepancias (PR #67). En la base, el art. 55
  del Decreto 352 de 2002 (el sistema preferencial de 2002) dejó de salir en las búsquedas, y el
  glosario sumó el parágrafo 3 del art. 26 del Acuerdo 1084 de 2026 y la entrada del código CIIU con
  su fuente oficial de la DIAN (PR #64 y #68).

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
(`docs/resumenes/correcciones-corrida-1.md`).

Después de la corrida 2 y de la usabilidad se fusionaron, con su caso de regresión y su verificación
con el juez:

- la regla del agente general sobre el canal de un trámite: no dice dónde ni cómo se hace si ningún
  fragmento lo dice, e indica el botón «Hablar con un funcionario» (PR #51);
- la nota del ICA que dice cuándo aplican el complementario de avisos y tableros y la sobretasa
  bomberil, calculada por código con los ingresos del periodo y la UVT del año (PR #63), y la lista
  de fuentes completa, con las normas que citan las notas y la fuente de la clasificación del CIIU
  (PR #65);
- los textos fijos precisados por la verificación tributaria (el alcance del canal incluye los datos
  personales; la aproximación al múltiplo de mil la hacen la declaración y los recibos de pago; la
  nota bomberil sin datos no afirma que el umbral no se ha publicado; PR #68).

**Fechas y reglas por código.** En la corrida 2 el modelo dijo «mañana» con 8 días de diferencia
(ICA-07), y en la 2b dio como pasadas cuotas futuras del SPAC (IPU-08). Un primer intento entregó al
modelo la frase relativa a hoy calculada por código (PR #50); en la corrida 2c el modelo la usó para
concluir sin fuente que «no se puede pagar» (MULTI-02), y se revirtió. Por decisión de los autores, el
sistema no relaciona fechas con el día de la consulta: da la fecha exacta y, cuando importa, «ya
venció» o «aún no vence» según lo que calcula el código, porque cada fecha de las herramientas trae
si ya pasó con el reloj del turno; un verificador sin modelo pide una reescritura si la respuesta
dice «hoy», «mañana», «hace N días» o nombra los fragmentos o las herramientas (PR #72). Con la misma
idea, las herramientas del ICA entregan la regla que define la periodicidad, tal como está en los
datos y con su fuente, para que el modelo la copie (el modelo había invertido la regla de los 391
UVT en ICA-08 y MULTI-02), y la descripción de las tarifas del predial se hace con la herramienta de
tarifas de los tres destinos y con los fragmentos (PR #73). La indicación de dónde encontrar el
código CIIU en el agente del ICA se probó y se revirtió, porque el juez la marcó sin fuente (PR #66):
quedó en el glosario y como trabajo futuro.

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
- Sondas de fechas, sin juez, con el reloj simulado el día antes, el mismo día y el día después de
  cada plazo (34 respuestas por ronda, `reports/verif-fechas-por-codigo/`): en la repetición final
  ninguna respuesta relacionó una fecha con el día de la consulta, trajo una referencia interna o dio
  un estado de fecha equivocado; 2 de 34 no llamaron la herramienta de fechas, sin error. Las
  reescrituras del verificador bajaron de 23 a 9 de 34 al presentar al modelo la fecha como «fecha de
  la consulta (no la menciones)».
- Verificación de las reglas por código (`reports/verif-reglas-por-codigo/` y
  `reports/verif-reglas-por-codigo-2/`): 6 de 6 escenarios superados con el juez y ninguna inversión
  de la regla de los 391 UVT ni descripción de tarifas sin fuente en 6 preguntas nuevas.

## 4.5 Agente OCR

**Qué se construyó.** Un agente OCR que leyó el documento con el modelo de visión y salida
estructurada; presentó los seis campos para que el contribuyente los confirmara, y, tras la
confirmación, los contrastó con la obligación registrada sin modificarla (`docs/resumenes/b10.md`).
Por un hallazgo de la usabilidad, el modelo decide primero si el documento es un recibo predial y
después se revisan por código la resolución y el desenfoque; la proporción de la imagen solo cuenta
como recorte cuando además faltan campos, para que un recibo apaisado completo no se rechace (PR
#59). El widget reduce las fotos pesadas antes de subirlas y el backend las reduce antes del modelo
(PR #60), y una imagen de más de 25 millones de píxeles se rechaza como ilegible antes de
decodificarse (PR #69).

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
las corridas 1 y 2 (`reports/umbral/propuesta.md`) y los autores aprobaron 0,70, sin cambio
(`docs/resumenes/b15.md`). Por la usabilidad, el aviso al escalar dice que el caso quedó registrado,
con un número corto que el funcionario busca en la bandeja, sin prometer un contacto que el sistema
no hace (PR #62); el botón de escalamiento lleva el mismo límite por dirección IP que el chat (PR
#69).

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
(`docs/resumenes/b11.md`). Antes de la usabilidad se rediseñó la interfaz (rótulo delgado,
encabezado de portal con interruptor de tema y tarjetas de «Qué puedes probar», PR #55); después,
la lista de usuarios de prueba se ajustó al modo oscuro (PR #57) y el widget sumó un aviso de datos
personales debajo del aviso de IA (PR #58). Los dos autores aplicaron las tareas, el SUS y la
evaluación heurística, cada uno por su lado (`docs/usabilidad/rodolfo/` y `docs/usabilidad/dayanna/`):
el puntaje del SUS y el resumen de las heurísticas: **PENDIENTE (B16)**.

## 4.8 Observabilidad

**Qué se construyó.** El registro propio de interacciones sin datos personales y las trazas de
LangSmith con el identificador de conversación (ADR-11); la matriz de confusión y las métricas de
precisión y tiempo en la consola; y un verificador automático de trazas que busca los documentos y
los nombres de los usuarios de prueba (`docs/resumenes/b09.md` y `b12.md`).

**Requerimientos:** RF-OBS-01 · Traza del flujo entre agentes; RF-OBS-02 · Matriz de confusión de
enrutamiento; RF-OBS-03 · Métricas de precisión y tiempo; RF-OBS-04 · Actualización de la base
vectorial; RF-OBS-05 · Ejecución repetible de pruebas; RNF-05 · Registro auditable.

**Cómo se verificó y cifras.** Ninguna traza tuvo identificadores: 1.279 ejecuciones de 63
conversaciones en la corrida 1 (`reports/corrida-1/constancias.md`), 1.277 en la corrida 2
(`reports/corrida-2/trazas.json`), 1.284 en la 2c y 1.285 en la 2d (`trazas.json` de cada una). La
auditoría de seguridad encontró que el anonimizador de las trazas no enmascaraba la imagen del
recibo ni los nombres declarados («me llamo…»), la causa de que las trazas de un incidente de datos
reales de la usabilidad guardaran la imagen (`docs/resumenes/b15.md`, punto 9). Desde el PR #69, las
trazas cambian las imágenes por «[IMAGEN]» y enmascaran esos nombres, con un anonimizador propio que
no cambia lo que ven el juez y los agentes (la huella del juez no cambió); una prueba sin red
confirmó lo que envía de verdad el cliente de LangSmith, y en la corrida 2c ninguna de las 178
ejecuciones de los escenarios con recibo traía la imagen (`reports/corrida-2c/analisis.md`).

## 4.9 Despliegue

**Qué se construyó.** El sistema multiagente de IA se empaquetó en contenedores y se desplegó en una
instancia EC2 m7i-flex.large con Docker Compose (ADR-10), detrás de un proxy Caddy con HTTPS
automático y DuckDNS (ADR-09), cabeceras de seguridad y límites de tamaño. La imagen del backend se construyó
en varias etapas, sin secretos ni privilegios; la configuración no secreta se versionó y los
secretos quedaron en un archivo de entorno (`docs/resumenes/b13.md`). Como GitHub nunca disparó el
flujo programado que revisaba `/health`, el monitor de disponibilidad pasó al crontab del servidor,
cada 5 minutos; su primer chequeo encontró un 502 por una fuga de conexiones en `/health`, que se
corrigió (PR #54; `docs/resumenes/b15.md`). Los avisos de seguridad de las dependencias se
atendieron con certifi actualizado y Chroma sin puerto publicado en el servidor (PR #56, ADR-26), y
los puntos de acceso que llaman modelos y el botón de escalamiento tienen un límite por dirección IP
(10 por minuto y 200 por día; PR #61 y #69).

Una auditoría de seguridad rápida y estática (12 agentes, sin ejecutar ataques) no confirmó
hallazgos y dejó cuatro pistas: tres se corrigieron (imágenes enormes, límite del botón y trazas) y
la cuarta quedó como riesgo aceptado de la ventana del modo de evaluación. De sus 23 notas de
refuerzo, 3 se aplicaron (acciones de la integración continua fijadas por su commit, suma de
gitleaks fijada en el repositorio y huella de la clave de Docker en la preparación del servidor), 4
se verificaron y 16 quedaron como trabajo futuro, con su motivo (`docs/resumenes/auditoria_seguridad.md`,
PR #69 y #70).

**Requerimientos:** RNF-02 · Escalamiento horizontal; RNF-06 · Horario de atención; RNF-12 ·
Imágenes de contenedor; RNF-13 · Orquestación con Compose; RNF-14 · Configuración por entorno;
RNF-15 · Volúmenes persistentes.

**Cómo se verificó y cifras.** La carga de la base de conocimiento en el servidor costó US$0,05
(`docs/resumenes/b13.md`). En B15, una conversación continuó en la otra réplica, y el corpus, las
conversaciones y los casos persistieron después de reiniciar y de recrear los contenedores
(`reports/no_funcionales/README.md`, `replicas.json` y `volumenes.json`). La disponibilidad
medida por el monitor: **PENDIENTE (corrida 3)**.

## 4.10 Evaluación antes de la corrida final

**Qué se hizo.** Después de las correcciones, cuatro corridas contra el sistema desplegado, con el
modo de evaluación encendido solo durante cada una y el juez v3 congelado (`afecd5c1…`), y la
calibración del juez con personas.

**Requerimientos:** RNF-16 · Tasa de respuestas correctas; RF-OBS-05 · Ejecución repetible de
pruebas; RNF-01 · Tiempo de respuesta; RNF-05 · Registro auditable.

**Cifras.**

| Corrida | Qué verificó | Superados de 60 (Wilson del 95 %) | Estricta | R3 y R4 |
|---|---|---|---|---|
| 2 (`reports/corrida-2/`) | Correcciones de la corrida 1, con RAGAS | 53 (88,3 %; 77,8 % a 94,2 %) | 75,0 % | 3 de 3 y 2 de 2 |
| 2b (`reports/corrida-2b/`) | Correcciones de la usabilidad y de la revisión externa | 52 (86,7 %; 75,8 % a 93,1 %) | 75,0 % | 3 de 3 y 2 de 2 |
| 2c (`reports/corrida-2c/`) | Verificación tributaria, fechas relativas (#50) y auditoría | 50 (83,3 %; 72,0 % a 90,7 %) | 75,0 % | 2 de 3 y 2 de 2 |
| 2d (`reports/corrida-2d/`) | Código congelado, con las fechas y las reglas por código | 55 (91,7 %; 81,9 % a 96,4 %) | 75,0 % | 3 de 3 y 2 de 2 |

- Cada ensayo general tuvo una regla fijada antes de ver el resultado. La 2c quedó por debajo (50 de
  60): se analizó cada falla sin corregir nada por cuenta propia, y una sola fue probablemente de un
  cambio de esa ronda (MULTI-02, por las frases relativas a hoy del PR #50). La 2d cumplió la regla:
  sin errores técnicos, latencias dentro de las metas (p95 de 4.424 ms sin fragmentos y de 11.852 ms
  con RAG), trazas sin identificadores y ninguna respuesta que relacionara una fecha con el día de la
  consulta (`reports/corrida-2d/analisis.md`).
- En la 2b, una sola regresión se debió a un cambio del día (la regla del CIIU en el agente del ICA)
  y se revirtió (PR #66).
- **Calibración del juez (A6).** Dos evaluadores calificaron a ciegas y sin ayuda de IA 30 respuestas
  de la corrida 2b, estratificadas por el veredicto del juez (una primera muestra, de la corrida 2, se
  descartó porque sus hojas se llenaron con ayuda de un chat externo de IA). El kappa del juez frente
  al consenso fue de −0,062 (binario) y de 0,062 (ponderado de 3 niveles), con un acuerdo observado
  de 22 de 30; entre los evaluadores, 0,000 y −0,111, con un acuerdo de 29 de 30. El valor bajo se
  debe a que las personas aprobaron casi todas las respuestas (paradoja del kappa; PABAK binario de
  0,47 y 0,93): en 7 de las 8 diferencias binarias, el juez fue más estricto que el consenso
  (`docs/resumenes/b15.md`, `reports/calibracion/kappa.json`).
