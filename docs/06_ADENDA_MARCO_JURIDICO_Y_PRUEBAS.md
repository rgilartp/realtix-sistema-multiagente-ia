# Adenda 06 — Marco jurídico final y compromisos de pruebas del documento

> **Proyecto:** sistema multiagente de IA para el soporte del proceso de facturación de Realtix.
> **Fecha:** octubre de 2026. **De:** chat de documentos. **Para:** chat de desarrollo (OE3 y OE4).
> **Precedencia:** en lo normativo, en el contenido de la base de conocimiento y en lo que el documento
> promete medir en el OE4, esta adenda prevalece sobre `02_PLAN_DESARROLLO_OE3.md` y
> `05_CONTEXTO_PROYECTO_REALTIX_v2.md` cuando no coincidan. El resto del paquete sigue vigente.
> Los números entre corchetes son las citas del documento de grado (bibliografía de 129 referencias).

---

## 1. Lo esencial

1. **Requerimiento nuevo, provisional: aviso de interacción con IA (RF-SYS-06).** El marco jurídico
   recoge el principio de transparencia de la OCDE: que las personas sepan cuándo interactúan con un
   sistema de IA. El equipo confirmó que el aviso estará presente. Se implementa desde ya; el equipo lo
   agregará formalmente al documento de requerimientos en la fase correspondiente (sección 4.1).
2. **Base de conocimiento.** El marco jurídico final dice qué normas la alimentan. Hay fuentes nuevas,
   todas en su texto vigente, y las tarifas y los plazos deben guardarse por año gravable (sección 3).
3. **Pendientes del plan resueltos.** El plan pedía identificar los acuerdos con las tarifas vigentes y
   el calendario tributario. Ya están identificados y verificados contra los documentos oficiales
   (sección 3.3).
4. **La Ley 1995 de 2019 sigue vigente**, por la Ley 2294 de 2023, artículo 49, parágrafo 3. RF-IPU-04
   no cambia, y el agente nunca debe decir que esa ley venció.
5. **El control de acceso tiene doble fundamento legal:** la reserva de la información tributaria
   (Decreto Distrital 807 de 1993, art. 18) y la Circular Externa 002 de 2024 de la SIC, según la cual
   un dato accesible al público no es, por eso, un dato público.
6. **Privacidad:** datos sintéticos, trazas sin identificadores y solo los datos necesarios en cada
   llamada a los modelos.
7. **Fuera del alcance, solo para producción:** estudio de impacto de privacidad, contrato de
   transmisión con los proveedores externos y revisión del Registro Nacional de Bases de Datos
   (sección 5). No se construye nada de esto, pero debe quedar documentado.
8. **OE4.** El documento ya compromete niveles de prueba, métricas, LLM-as-judge y una rúbrica de
   usabilidad con usuarios. El plan de pruebas debe medir exactamente eso (sección 6).
9. **Corrección en el documento.** Las categorías de enrutamiento son las cinco de RF-ORQ-01; el
   escalamiento es una transición, no una categoría (sección 7).

---

## 2. Normas del marco jurídico y qué le exigen al sistema

**Papel:** C = condición que el sistema cumple; B = alimenta la base de conocimiento.

| Norma (cita en el documento) | Papel | Qué implica para el desarrollo |
|---|---|---|
| Acuerdo de confidencialidad con Realtix | C | Solo datos sintéticos en desarrollo y pruebas (RNF-04). Ninguna documentación privada de RealSit; `plataforma_general` solo con material público de la OVT. |
| Ley 1581 de 2012 [104] | C + B | Sus principios se aplican así: acceso y circulación restringida y confidencialidad (RF-AUT-01 y 02); finalidad y minimización (RNF-03); seguridad (RNF-05 y HTTPS). Su texto va en `normativa_datos`. |
| Decreto 1377 de 2013 [105] | B (C en producción) | El documento dice que forma parte de la base del agente de información general. Se carga a través de su texto compilado en el Decreto 1074 (fila siguiente). Sus procedimientos solo rigen con datos reales. |
| Decreto 1074 de 2015 [106] | B (C en producción) | Texto vigente que se carga en `normativa_datos`: el capítulo 25 compila el Decreto 1377 y el 26 regula el Registro Nacional de Bases de Datos. Las reglas de transmisión internacional están en la sección 5. |
| Circular Externa 002 de 2024 de la SIC [107] | C | Privacidad desde el diseño (datos sintéticos, trazas sin identificadores); seguridad auditable (registro de interacciones); información al titular (aviso RF-SYS-06). Su aclaración sobre datos accesibles al público sustenta RF-AUT-02. El estudio de impacto está en la sección 5. |
| Ley 14 de 1983 [45] | B | `normativa_ica` (RF-ICA-01): hecho generador, base gravable y periodicidad. Usar el texto vigente, no el original de 1983. |
| Ley 44 de 1990 [14], con la Ley 1450 de 2011, art. 23 | B | `normativa_ipu` (RF-IPU-01): base gravable, sujetos pasivos y rango de tarifas de 5 a 16 por mil. |
| Decreto Ley 1421 de 1993 [108], con el Acuerdo 648 y el Decreto 474 de 2016 [109] | B | `normativa_ipu`. Régimen especial de Bogotá, municipio piloto (arts. 12, num. 3; 155 y 162). Sistema mixto: el predial se paga con la factura o mediante declaración. |
| Decreto Distrital 807 de 1993 [110] | C + B | El art. 18 (reserva de la información tributaria) fundamenta RF-AUT-01 y 02. Sus normas de procedimiento van en `normativa_ipu` y `normativa_ica` en su texto vigente: el Acuerdo 1084 de 2026 reemplazó el art. 27 y derogó los arts. 7 y 8. |
| Decreto Distrital 352 de 2002 [111] | B | Fuente principal de las reglas de Bogotá. El capítulo I (predial, arts. 13 a 30) va en `normativa_ipu`; el capítulo II (industria y comercio, avisos y tableros, arts. 31 a 59) va en `normativa_ica`. |
| Ley 1819 de 2016, art. 354 [44] | B | `normativa_ipu`: qué es la factura del predial, cómo se notifica y cuándo es título ejecutivo para el cobro coactivo. |
| Ley 1995 de 2019 [112] y Ley 2294 de 2023, art. 49, par. 3 [21] | B | `normativa_ipu` (RF-IPU-04): topes al aumento anual del predial y razón de su vigencia. |
| Resolución SDH-000195 de 2025 [113] | B | Calendario del año gravable 2026 (RF-IPU-04, RF-ICA-03). Rige solo para 2026: se reemplaza cada año por reingesta (RF-OBS-04). |
| Acuerdo 1084 de 2026 [114] | B | Tarifas nuevas de predial e industria y comercio, regímenes del ICA desde 2027, sobretasa de alumbrado desde 2027 y notificación de facturas (sección 3.3). |
| OECD AI Principles [115]; Colombia los adoptó (CONPES 4144 [3]) | C | Supervisión humana: escalamiento (RF-ESC). Transparencia: aviso RF-SYS-06 y respuestas sustentadas en fuentes (RF-GEN-03, RF-IPU-05). Robustez: RNF-08. Trazabilidad: RNF-05 y RF-OBS-01. |

El CONPES 3975 salió del marco: no impone obligaciones ni alimenta la base. El CONPES 4144 queda solo
como contexto y tampoco va a la base.

---

## 3. Base de conocimiento

### 3.1 Colecciones con las fuentes del marco final

| Colección | Fuentes (texto vigente) | Agente |
|---|---|---|
| `normativa_ipu` | Ley 44 de 1990 (con Ley 1450 de 2011, art. 23); Ley 1995 de 2019 y Ley 2294 de 2023, art. 49, par. 3; Ley 1819 de 2016, art. 354; Decreto Ley 1421 de 1993 (arts. 12, 155 y 162); Acuerdo 648 y Decreto 474 de 2016; Decreto Distrital 352 de 2002, cap. I; Decreto Distrital 807 de 1993; Acuerdo 105 de 2003, art. 2 (tarifas hasta 2026); artículos de predial del Acuerdo 1084 de 2026; Resolución SDH-000195 de 2025 (arts. 3 a 6) | `nodo_ipu` |
| `normativa_ica` | Ley 14 de 1983; Decreto Distrital 352 de 2002, cap. II; Decreto Distrital 807 de 1993; Acuerdo 65 de 2002, art. 3 (tarifas anteriores); artículos de industria y comercio del Acuerdo 1084 de 2026 (21, 24, 25 y 26); artículos del ICA de la Resolución SDH-000195 de 2025 | `nodo_ica` |
| `normativa_datos` | Ley 1581 de 2012; Decreto 1074 de 2015, caps. 25 y 26, con el metadato de origen «Decreto 1377 de 2013» en el cap. 25; opcional: Circular Externa 002 de 2024 de la SIC | `nodo_general` |
| `plataforma_general` | Sin cambios: manuales públicos de la OVT y glosario | `nodo_general` |

**Reparto del Acuerdo 1084 de 2026:**
- Predial: arts. 10 a 18 (sobretasa de alumbrado), 20 (tarifas), 27 (notificaciones) y 35 (facturación
  en bienes exentos).
- Industria y comercio: arts. 21 (tarifas), 24 (régimen SIMPLE), 25 (retención) y 26 (regímenes).
- Incentivos de los arts. 1 a 8: se reparten según el impuesto. El de delineación urbana (art. 6) queda
  fuera, porque el alcance es solo predial e industria y comercio (RF-SYS-03).

**Ojo con el PDF del Acuerdo 1084:** es un PDF escaneado, sin capa de texto. La ingesta necesita OCR, y
las tablas de tarifas deben transcribirse y verificarse a mano contra el PDF.

### 3.2 Reglas de curaduría

- Cargar siempre el texto vigente compilado, con sus notas de modificación. Registrar la URL y la fecha
  de consulta de cada documento; el documento de grado las usa en la bibliografía.
- Cada fragmento lleva como metadatos la norma, el artículo y la colección. Las tarifas y los plazos
  llevan además su vigencia: año gravable desde y hasta.
- El agente aplica las tarifas y los plazos del año gravable de la consulta. Si el contribuyente no lo
  dice, usa el año en curso y lo dice en la respuesta.
- No agregar a la base fuentes que no estén en el marco jurídico sin avisar al chat de documentos. Así
  el documento y la base siguen coincidiendo.
- El calendario se reemplaza cada año por reingesta, sin tocar el código (RF-OBS-04).

### 3.3 Datos verificados

Estos datos se verificaron en octubre de 2026 contra los PDF oficiales: la Resolución SDH-000195
de 2025, firmada digitalmente, y la copia escaneada del texto firmado del Acuerdo 1084 de 2026. Sirven
también como respuestas de referencia en las pruebas.

| Dato | Valor | Fuente |
|---|---|---|
| Plazo del predial 2026 | Declarar y pagar a más tardar el 10 de julio de 2026 | Res. SDH-000195, art. 3 |
| Predial 2026 con factura | Pago total a más tardar el 10 de julio de 2026; facturas expedidas a más tardar el 30 de abril de 2026 | Res. SDH-000195, art. 4 |
| Pronto pago del predial 2026 | 10 % de descuento pagando todo a más tardar el 17 de abril de 2026; también aplica a quien se acogió al SPAC y paga todo en esa fecha | Res. SDH-000195, art. 6 |
| SPAC 2026 (pago por cuotas) | Declaración inicial hasta el 8 de mayo de 2026; cuotas el 5 de junio, 14 de agosto, 2 de octubre y 4 de diciembre de 2026 | Res. SDH-000195, art. 5 |
| ICA 2026, régimen común con impuesto a cargo de 2025 mayor a 391 UVT ($19.471.409) | Bimestral, con vencimientos el 10 de abril, 12 de junio, 21 de agosto, 9 de octubre y 11 de diciembre de 2026, y el 12 de febrero de 2027 | Res. SDH-000195, art. 1 |
| ICA 2026, régimen común de hasta 391 UVT y régimen preferencial | Una declaración anual a más tardar el 26 de febrero de 2027 | Res. SDH-000195 |
| Topes al aumento del predial | En predios con avalúo actualizado, máximo IPC más 8 puntos frente al año anterior. Hay topes propios para predios sin actualizar y para vivienda de estratos 1 y 2 con avalúo de hasta 135 SMMLV | Ley 1995, art. 2; vigente por Ley 2294, art. 49, par. 3 |
| Tarifas nuevas del predial | Rigen desde el predial de 2027, porque el de 2026 se facturó antes de que se expidiera el acuerdo. Ver la fila siguiente | Acuerdo 1084, art. 20 |
| Valores de las tarifas nuevas del predial | Residenciales generales desde 5,5 por mil. Preferenciales: estratos 1 y 2 con base de 16 a 107 SMMLV, 1 por mil; estratos 1 y 2 con base de más de 107 a 135 SMMLV y estrato 3 hasta 135 SMMLV, 3 por mil. Estratos 1 y 2 con base menor de 16 SMMLV, excluidos. Residenciales rurales de más de 135 SMMLV, 6,5 por mil. Desde 2027 los rangos se actualizan cada año con el IVIUR | Acuerdo 1084, art. 20 |
| Tarifas nuevas del ICA | A quien declara una vez al año, desde el 1 de enero de 2027. A quien declara cada dos meses, desde el bimestre siguiente a la aprobación del acuerdo; falta confirmar la fecha de aprobación en plenaria para fijar el bimestre exacto | Acuerdo 1084, art. 21 |
| Regímenes del ICA desde el 1 de enero de 2027 | Común: impuesto a cargo del año anterior mayor a 391 UVT; declara y paga cada dos meses. Preferencial: hasta 391 UVT; declara una vez al año. Quien empieza actividades está en el preferencial el primer año. Un preferencial con ingresos netos menores a 1.933 UVT no declara, y su impuesto es igual a lo retenido | Acuerdo 1084, art. 26 (reemplaza el art. 27 del Decreto 807) |
| Retención de ICA | Quien tuvo ingresos netos en Bogotá menores a 1.933 UVT no está sujeto a retención por pagos con tarjeta. La retención sigue fuera del alcance del MVP: escalar (RF-ICA-04) | Acuerdo 1084, art. 25 |
| ICA en el régimen SIMPLE | Tarifas consolidadas propias desde el 1 de enero de 2027 | Acuerdo 1084, art. 24 |
| Sobretasa de alumbrado público | Desde el 1 de enero de 2027. Sujetos: los contribuyentes del predial. Base: la misma del predial. Tarifas y topes en los arts. 14 y 15 | Acuerdo 1084, arts. 10 a 15 |
| Notificación de las facturas | Publicación en el Registro Distrital y, al mismo tiempo, en la página web de la Secretaría Distrital de Hacienda. El envío a la dirección del contribuyente es solo divulgación adicional | Acuerdo 1084, art. 27, num. 3 |
| Notificación electrónica | Solo si el contribuyente registró un correo en el RIT; empieza a regir cuando la Administración Distrital la reglamente | Acuerdo 1084, art. 28 |
| Vigencia del Acuerdo 1084 | Rige desde su publicación. Deroga, entre otros, los arts. 7 y 8 del Decreto 807. Los Acuerdos 111 de 2003 y 399 de 2009 quedan derogados desde el 1 de enero de 2027 | Acuerdo 1084, art. 52 |

---

## 4. Requerimientos

### 4.1 Nuevo (provisional): RF-SYS-06

| ID | Nombre | Descripción | Prioridad |
|---|---|---|---|
| RF-SYS-06 | Aviso de interacción con IA | El sistema multiagente de IA deberá informar al contribuyente, al inicio de cada conversación, que lo atiende un sistema de inteligencia artificial y que puede pedir en cualquier momento la atención de un funcionario. | Alta |

- **Origen:** principio de transparencia de la OCDE [115] e información al titular, de la Circular
  Externa 002 de 2024 de la SIC [107].
- **Criterios de aceptación:**
  - El aviso aparece en el widget antes de la primera respuesta, o junto con ella, en toda
    conversación nueva.
  - Si el contribuyente pregunta si habla con una persona, el sistema responde que es un sistema de IA
    y ofrece el escalamiento (RF-ESC-02).
  - Tiene su escenario en el plan de pruebas del OE4.
- **Formalización:** el equipo lo agregará al documento de requerimientos en la fase correspondiente. Si
  prefiere agruparlo con la interfaz, puede quedar como RF-UI-05. Mientras tanto, se implementa y entra
  en la matriz de trazabilidad marcado como provisional.

### 4.2 Requerimientos que el marco refuerza (su texto no cambia)

| Requerimiento | Qué añade el marco | Implicación |
|---|---|---|
| RF-AUT-01 a 04 | Reserva tributaria (Decreto 807, art. 18) y Circular SIC | La matrícula catastral es pública, pero no da acceso. El rechazo no revela datos (D3). Escenario obligatorio en las pruebas. |
| RNF-03 | Ley 1581 (finalidad, minimización) y ponderación de la Circular SIC | En cada llamada a un modelo, enviar solo los datos del contribuyente necesarios para esa respuesta; nada de nombre ni documento si no hacen falta. |
| RNF-05 | Ley 1581 (seguridad) y Circular SIC (seguridad auditable) | Trazas de LangSmith con el identificador de conversación, sin identificadores personales. Conviene una prueba automática que revise las trazas. |
| RF-IPU-04 | Ley 1995 vigente y Resolución SDH-000195 | Plazos y descuentos del año gravable; topes al aumento. No decir que la Ley 1995 venció. |
| RF-IPU-03 y RF-ICA-02 | Acuerdo 1084 (tarifas desde 2027) | Estimar con la tarifa del año gravable de la consulta; conservar la nota de estimación no vinculante. |
| RF-ICA-03 | Resolución SDH-000195 y Acuerdo 1084 (regímenes desde 2027) | Fechas según el régimen y el año. |
| RF-IPU-05 y RF-GEN-03 | OCDE: entender en qué se basa una respuesta | Citar la norma en el predial y responder solo con fuentes de la base. Sugerencia opcional: aplicar también la cita de la norma al agente de ICA, que hoy no tiene un requerimiento equivalente. |
| RNF-08 | OCDE: robustez | Ante tiempo vencido o falla de un servicio, escalar en lugar de mostrar un error. |
| RF-ESC-01 a 05, RF-OBS-01 | OCDE: supervisión humana y trazabilidad | Sin cambios; son la evidencia de que se cumplen esos principios. |
| RF-ICA-04 | El Acuerdo 1084 cambia reglas de retención (art. 25) | La retención sigue fuera del alcance: escalar. |

---

## 5. Solo para la operación con datos reales (no se construye; se documenta)

- **Estudio de impacto de privacidad** (Circular SIC 002 de 2024, instrucción II). Debe hacerse antes de
  procesar datos reales. Su contenido mínimo es la descripción del tratamiento, la evaluación de riesgos
  y las medidas para mitigarlos. El documento de grado lo deja como requisito previo a la operación.
- **Transmisión internacional** (Decreto 1074 de 2015, arts. 2.2.2.25.5.1 y 2.2.2.25.5.2). Enviar en
  producción datos personales a Anthropic, a OpenAI o a LangSmith sería una transmisión a un encargado
  en el exterior. No exige informar al titular ni pedir su consentimiento si existe un contrato de
  transmisión. Ojo: a OpenAI también llega el texto de la pregunta del contribuyente, porque la búsqueda
  vectorial la convierte en embedding.
- **Registro Nacional de Bases de Datos** (Decreto 1074, cap. 26). Evaluar si las bases nuevas que crea
  el sistema (conversaciones y casos escalados) deben inscribirse.
- En el MVP nada de esto aplica, porque solo hay datos sintéticos (RNF-04). Conviene dejarlo escrito en
  el README y en el reporte del OE3 como condición para producción.

---

## 6. Plan de pruebas del OE4: lo que el documento ya promete

### 6.1 Compromisos explícitos del documento

- **Meta del OE4:** al menos 85 % de escenarios de prueba superados (tabla de indicadores del capítulo 1;
  RNF-16, con LLM-as-judge).
- **Fase 4 (sección 1.6.4):** diseño del plan y de los escenarios por categoría; ejecución sobre el
  sistema desplegado; evaluación automática con LLM-as-judge; métricas de enrutamiento, alucinaciones y
  tiempo de respuesta; correcciones iterativas, y reporte de pruebas.
- **Herramientas del OE4 (tabla de la sección 1.6.5):** casos asociados a los requerimientos,
  LLM-as-judge, matriz de confusión para el enrutamiento y **una rúbrica de usabilidad aplicada a
  usuarios**. La rúbrica no está en el plan de desarrollo, así que hay que definir el instrumento y
  aplicarlo. El documento organiza los atributos no funcionales con la ISO/IEC 25010, que incluye la
  usabilidad.

### 6.2 Estructura del plan según el ISTQB (secciones 1.5.1.9 y 1.5.2.7)

El documento cita el programa Certified Tester Foundation Level v4.0.1 del ISTQB [46]. Según ese
programa, el plan del OE4 debería cubrir:
- el contexto y el alcance;
- los supuestos y las restricciones;
- los interesados y la forma de comunicarse con ellos;
- los riesgos;
- el enfoque: niveles, tipos y técnicas de prueba, criterios de entrada y de salida, métricas, y datos
  y entorno;
- el presupuesto y el cronograma.

Niveles que el documento compromete:
- **Componentes (pruebas unitarias de agentes).** El orquestador recibe consultas etiquetadas con su
  categoría; cada agente especializado recibe consultas con respuesta de referencia.
- **Integración de componentes (pipeline RAG).** Las respuestas deben estar fundamentadas en el contexto
  recuperado, sin información ausente de la base.
- **Sistema (de extremo a extremo).** Conversaciones de varios turnos, preguntas ambiguas, consultas
  fuera de dominio y escalamiento.
- **Atributos no funcionales.** Se miden con la ISO/IEC 25010: eficiencia de desempeño, usabilidad,
  fiabilidad y seguridad.

### 6.3 Vocabulario de evaluación de agentes

Este es el documento sobre pruebas que el marco teórico destaca: «Demystifying evals for AI agents», de
Anthropic (enero de 2026) [102].
- **Conceptos.** Una tarea es un caso de prueba con entradas y criterio de éxito definidos. Un ensayo
  (trial) es cada intento del agente sobre la tarea. El evaluador (grader) puede ser código, un modelo o
  una persona.
- **Tipos de evaluador.** El código es rápido y repetible, pero castiga respuestas válidas que tienen
  otra forma. Un modelo es flexible y escala, pero debe calibrarse con personas. Las personas dan la
  mejor calidad, con más costo y más lentitud.
- **pass@k y pass^k.** pass@k es acertar al menos una vez en k intentos; pass^k es acertar en los k.
  Como el sistema atiende contribuyentes, conviene reportar pass^k, que mide consistencia: cada tarea se
  ejecuta varias veces.
- **Arranque.** Empezar con 20 a 50 tareas sencillas tomadas de fallas reales.

### 6.4 Métricas que el documento define (sección 1.5.2.8)

| Capa | Métrica | Cómo se calcula |
|---|---|---|
| Enrutamiento | Precisión, exhaustividad y F1 por clase (ecuaciones 1 a 3) y matriz de confusión | Con las cinco clases de RF-ORQ-01 (RF-OBS-02 y 03). Las clases no están balanceadas, así que se interpretan junto con la matriz (advertencia de Powers [47]). |
| Recuperación | Precisión del contexto (ecuaciones 4 y 5) y exhaustividad del contexto (ecuación 6) | Con RAGAS [103]. |
| Generación | Fidelidad (ecuación 7; mide alucinaciones) y relevancia de la respuesta (ecuación 8) | Con RAGAS. La relevancia genera tres preguntas desde la respuesta y promedia su similitud coseno con la consulta. |
| Generación | Exactitud de la respuesta | LLM-as-judge guiado por referencia, contra respuestas redactadas por un experto tributario. |
| Operativas | Latencia por solicitud y costo por consulta | Latencia frente a RNF-01: menos de 8 s en consultas simples y de 15 s con RAG. Costo (ecuación 9): suma, en todas las llamadas de la consulta, de los tokens de entrada y salida por el precio por millón de cada modelo. Se sigue en LangSmith. |

**Referencia para comparar en el reporte.** Es la que ya está en el documento: el chatbot de Bahçeci y
colaboradores [64] obtuvo:
- 92,63 % de fidelidad;
- 91,31 % de relevancia de la respuesta;
- 75,20 % de precisión del contexto;
- 86,60 % de exhaustividad del contexto.

Atendía unas cuatro solicitudes por minuto, con una latencia cercana a 4.000 ms.

### 6.5 LLM-as-judge: cuidados que menciona el documento (Zheng et al. [48])

- **Modalidades.** Comparación por pares, puntuación de una sola respuesta y calificación guiada por
  referencia. Esta última es la que el documento compromete para la exactitud.
- **Sesgos.** El juez puede favorecer una respuesta por su posición, por su extensión o por haberla
  generado él mismo, y su razonamiento es limitado.
- **Mitigación sugerida:**
  - alternar el orden en las comparaciones por pares;
  - preferir la calificación con referencia;
  - evitar que el juez sea el mismo modelo que generó la respuesta o, si lo es, declararlo como
    limitación;
  - calibrar el juez con una muestra calificada por personas.
- **Rúbrica de referencia, la que usó Anthropic [36]:** fidelidad a las fuentes, citas que sí sustentan
  lo dicho, cobertura de lo pedido, prioridad a las fuentes primarias y uso mesurado de las
  herramientas.

### 6.6 Análisis de fallas

Clasificar las fallas con la taxonomía MAST que cita el documento [99]: 14 modos de falla en tres
grupos, que son el diseño del sistema, la desalineación entre agentes y la verificación de la tarea.

### 6.7 Escenarios mínimos derivados del marco jurídico

| # | Consulta o situación | Resultado esperado | Requerimiento y norma |
|---|---|---|---|
| 1 | Inicio de una conversación | Aviso de IA y opción de pedir un funcionario | RF-SYS-06; OCDE; Circular SIC |
| 2 | «¿Estoy hablando con una persona?» | Responde que es un sistema de IA y ofrece escalar | RF-SYS-06; RF-ESC-02 |
| 3 | Estado de cuenta pedido con la matrícula válida de otro contribuyente | Rechazo sin revelar datos y sin escalar | RF-AUT-02; Decreto 807, art. 18; Circular SIC |
| 4 | Estado de cuenta sin sesión iniciada | Pide iniciar sesión en la OVT | RF-AUT-04 |
| 5 | «¿Hasta cuándo pago el predial con descuento en 2026?» | 17 de abril de 2026, 10 % | RF-IPU-04; Res. SDH-000195, art. 6 |
| 6 | «¿Cuál es el plazo del predial de 2026?» | 10 de julio de 2026 | RF-IPU-04; Res. SDH-000195, art. 3 |
| 7 | «¿Cuánto puede subir mi predial?» | IPC más 8 puntos si el avalúo está actualizado, con los casos especiales; la Ley 1995 sigue vigente | RF-IPU-04; Ley 1995; Ley 2294 |
| 8 | Estimación del predial de 2026 y de 2027 | Usa la tarifa de cada año y conserva la nota de estimación no vinculante | RF-IPU-03; Acuerdo 1084, art. 20 |
| 9 | «¿Cómo me notifican la factura del predial?» | Publicación en el Registro Distrital y en la web de Hacienda; el envío a la casa es divulgación adicional | Acuerdo 1084, art. 27; Ley 1819, art. 354 |
| 10 | «¿Puedo pagar el predial sin declarar?» | Sí, con la factura (sistema mixto) | Decreto Ley 1421; Acuerdo 648; Decreto 474; Res. SDH-000195, art. 4 |
| 11 | Régimen y periodicidad del ICA en 2027 | Común, mayor a 391 UVT, bimestral; preferencial, hasta 391 UVT, anual | RF-ICA-03; Acuerdo 1084, art. 26 |
| 12 | Consulta sobre retención de ICA | Escala (fuera del MVP) | RF-ICA-04 |
| 13 | Pregunta no tributaria | Informa que no está cubierta, sin escalar | RF-GEN-04 |
| 14 | Falla o tiempo vencido del modelo | Escala, sin mostrar un error técnico | RNF-08 |
| 15 | Revisión de las trazas de una conversación | Sin identificadores personales | RNF-05 |

---

## 7. Correcciones al documento que el desarrollo debe reflejar

- **Categorías de enrutamiento.** El marco teórico (sección 1.5.2.8.1) decía «IPU, ICA, procedimientos
  y escalamiento». Se corrigió a las cinco categorías de RF-ORQ-01: IPU, ICA, información general,
  extracción de documento y fuera de alcance. La matriz de confusión y los escenarios deben usar esas
  cinco.
- **Tabla de colecciones** (arquitectura, Tabla 6, y capítulo 3 del documento). El chat de documentos la
  actualizará con las fuentes de la sección 3.1; mientras tanto, el desarrollo sigue esta adenda.

---

## 8. Enlaces de las fuentes (los mismos de la bibliografía del documento)

| Fuente | Enlace | Nota para la base |
|---|---|---|
| Ley 1581 de 2012 | http://www.secretariasenado.gov.co/senado/basedoc/ley_1581_2012.html | — |
| Decreto 1377 de 2013 | https://cancilleria.gov.co/sites/default/files/Normograma/docs/decreto_1377_2013.htm | Compilado en el Decreto 1074; en la base, usar el 1074 |
| Decreto 1074 de 2015 | https://normativa.colpensiones.gov.co/colpens/docs/decreto_1074_2015.htm | Capítulos 25 y 26 |
| Circular Externa 002 de 2024 (SIC) | https://sedeelectronica.sic.gov.co/sites/default/files/normativa/Circular%20Externa%20No.%20002%20del%2021%20de%20agosto%20de%202024.pdf | — |
| Ley 14 de 1983 | https://www.dane.gov.co/files/acerca/Normatividad/decreto-1170-2015/Ley-14-de-1983.pdf | Es el texto original de 1983: para la base, conseguir la versión compilada vigente |
| Ley 44 de 1990 | https://www.cancilleria.gov.co/sites/default/files/Normograma/docs/ley_0044_1990.htm | Verificar que incluya la modificación de la Ley 1450 de 2011, art. 23 |
| Decreto Ley 1421 de 1993 | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=106394 | — |
| Decreto 474 de 2016 | https://www.ambitojuridico.com/sites/default/files/BancoMedios/Archivos/d-474-16.pdf | El Acuerdo 648 de 2016 no tiene enlace propio en el documento: tomarlo del Régimen Legal de Bogotá |
| Decreto Distrital 807 de 1993 | https://bogota.gov.co/sites/default/files/tys/2021/01/DECRETO_807_1993.pdf | Usar una versión que refleje sus modificaciones; el Acuerdo 1084 reemplazó el art. 27 y derogó los arts. 7 y 8 |
| Decreto Distrital 352 de 2002 | https://cancilleria.gov.co/sites/default/files/Normograma/docs/d_alcabog_0352_2002.htm | — |
| Ley 1819 de 2016 | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=79140 | Art. 354 |
| Ley 1995 de 2019 | https://www.igac.gov.co/sites/default/files/transparencia/normograma/ley_1995_de_2019.pdf | Arts. 2 (topes) y 3 (vigencia) |
| Ley 2294 de 2023 | https://cancilleria.gov.co/sites/default/files/Normograma/docs/ley_2294_2023.htm | Art. 49, par. 3 |
| Resolución SDH-000195 de 2025 | https://www.haciendabogota.gov.co/es/normatividad/resolucion-sdh-000195-del-12-de-diciembre-de-2025 | Calendario del año gravable 2026 |
| Acuerdo 1084 de 2026 | https://incp.org.co/wp-content/uploads/2026/10/Acuerdo-1084-de-2026-a-Consejo-de-BogotA¡-a-INCP.pdf | Copia del texto firmado que publicó el INCP; reemplazar por el enlace del Régimen Legal de Bogotá cuando aparezca. PDF escaneado: requiere OCR |
| Acuerdo 105 de 2003 (art. 2) y Acuerdo 65 de 2002 (art. 3) | Régimen Legal de Bogotá | Tarifas anteriores a las del Acuerdo 1084; no tienen enlace en el documento |
| OECD AI Principles | https://legalinstruments.oecd.org/public/doc/648/648.en.pdf | Criterios de diseño; no va a la base |

---

## 9. Qué no cambia

Siguen igual:
- los 48 RF y 16 RNF aprobados, más RF-SYS-06 provisional;
- los 8 nodos y las 4 colecciones (solo cambia su contenido);
- los modelos de cada agente;
- el contrato del adaptador de 7 métodos;
- las decisiones D1 a D4.
