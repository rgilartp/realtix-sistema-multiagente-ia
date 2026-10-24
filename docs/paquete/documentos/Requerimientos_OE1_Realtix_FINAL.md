> **Conversión a Markdown de `Requerimientos_OE1_Realtix_FINAL.docx`** (octubre de 2026), para lectura en el chat de desarrollo. El contenido es el del documento oficial; el índice general se reemplazó por la lista de tablas, sin números de página. Si hubiera alguna diferencia, rige el `.docx`.

**DOCUMENTO DE METAS Y REQUERIMIENTOS**

**Sistema Multiagente de Inteligencia Artificial para el Soporte del Proceso de Facturación de Realtix**

*Fase 1 — Objetivo Específico 1 · Entregable: Documento de requerimientos*

Gilart Pulido Rodolfo Angel · Varón Puerto Dayanna Liceth

Director: MsC. Juan Carlos Barrero Calixto

Universidad Católica de Colombia · Bogotá D.C. · 2026

**Lista de tablas**

- Tabla 1. Definiciones, siglas y abreviaturas
- Tabla 2. Actores del sistema
- Tabla 3. Historias de usuario — Consulta de información tributaria general
- Tabla 4. Historias de usuario — Consulta de estado de cuenta y liquidación estimada
- Tabla 5. Historias de usuario — Extracción de datos de factura (OCR)
- Tabla 6. Historias de usuario — Escalamiento a funcionario humano
- Tabla 7. Historias de usuario — Conversación y alcance
- Tabla 8. Historias de usuario — Administración y observabilidad
- Tabla 9. Requerimientos generales del sistema multiagente de IA
- Tabla 10. Requerimientos de autenticación y control de acceso
- Tabla 11. Requerimientos del agente orquestador
- Tabla 12. Requerimientos del agente especializado en IPU
- Tabla 13. Requerimientos del agente especializado en ICA
- Tabla 14. Requerimientos del agente de información general y normativa
- Tabla 15. Requerimientos del agente de extracción OCR
- Tabla 16. Requerimientos del mecanismo de escalamiento
- Tabla 17. Requerimientos de la interfaz conversacional
- Tabla 18. Requerimientos de observabilidad y administración
- Tabla 19. Requerimientos no funcionales — Desempeño y escalabilidad
- Tabla 20. Requerimientos no funcionales — Seguridad y protección de datos
- Tabla 21. Requerimientos no funcionales — Disponibilidad y fiabilidad
- Tabla 22. Requerimientos no funcionales — Usabilidad
- Tabla 23. Requerimientos no funcionales — Mantenibilidad, portabilidad y despliegue
- Tabla 24. Requerimientos no funcionales — Calidad funcional

---

## 1. Introducción

Esta sección presenta el propósito del documento, los documentos de referencia y las definiciones, siglas y abreviaturas utilizadas.

### 1.1. Propósito

Este documento especifica los requerimientos del sistema multiagente de inteligencia artificial para el soporte del proceso de facturación tributaria municipal de Realtix, en cumplimiento del Objetivo Específico 1 del trabajo de grado. Los requerimientos se redactan siguiendo los criterios de la norma ISO/IEC/IEEE 29148:2018 (Systems and software engineering — Requirements engineering): cada requerimiento es atómico, verificable, no ambiguo y está identificado de forma única, agrupado por componente del sistema multiagente de IA al que corresponde.

El documento se elabora a partir de: (a) la documentación pública disponible del producto RealSit y de la Oficina Virtual Tributaria, (b) la normatividad tributaria municipal colombiana aplicable, (c) historias de usuario derivadas del planteamiento del problema, y (d) las decisiones de alcance adoptadas por el equipo de trabajo de grado, documentadas en la sección 3.3.

### 1.2. Documentos de referencia

- Ley 14 de 1983 — Fortalecimiento de los fiscos municipales.

- Ley 44 de 1990 — Impuesto Predial Unificado.

- Ley 1450 de 2011, artículo 23 — Modifica el artículo 4 de la Ley 44 de 1990: rango de tarifas del Impuesto Predial Unificado.

- Decreto Ley 1421 de 1993 — Estatuto Orgánico de Bogotá D.C.

- Decreto Distrital 352 de 2002 y Decreto Distrital 807 de 1993 — Estatuto tributario de Bogotá D.C.: normas sustanciales y procedimiento de los tributos distritales.

- Ley 1819 de 2016, artículo 354 — Sistema de facturación tributaria.

- Ley 1995 de 2019 — Límites al incremento anual del Impuesto Predial Unificado.

- Ley 1581 de 2012, Decreto 1377 de 2013 y Decreto 1074 de 2015 — Protección de datos personales.

- ISO/IEC/IEEE 29148:2018 — Requirements engineering.

- ISO/IEC 25010:2011 — Systems and software Quality Requirements and Evaluation (SQuaRE).

- Propuesta de trabajo de grado aprobada — Sistema Multiagente de IA para el Soporte del Proceso de Facturación de Realtix.

### 1.3. Definiciones, siglas y abreviaturas

**Tabla 1. Definiciones, siglas y abreviaturas**

| **Sigla** | **Significado**                                                                     |
|-----------|-------------------------------------------------------------------------------------|
| IA        | Inteligencia artificial.                                                            |
| LLM       | Modelo de lenguaje de gran escala (Large Language Model).                           |
| VLM       | Modelo de lenguaje con capacidad de visión (Vision-Language Model).                 |
| RAG       | Generación aumentada por recuperación (Retrieval-Augmented Generation).             |
| OCR       | Reconocimiento óptico de caracteres (Optical Character Recognition).                |
| IPU       | Impuesto Predial Unificado.                                                         |
| ICA       | Impuesto de Industria y Comercio.                                                   |
| MVP       | Producto mínimo viable (Minimum Viable Product).                                    |
| SRS       | Especificación de requerimientos de software (Software Requirements Specification). |
| HU        | Historia de usuario.                                                                |
| RF        | Requerimiento funcional.                                                            |
| RNF       | Requerimiento no funcional.                                                         |

Fuente: Elaboración propia.

## 2. Alcance del sistema multiagente de IA

- El sistema multiagente de IA está dirigido al contribuyente como usuario final de la Oficina Virtual Tributaria.

- El sistema multiagente de IA realiza únicamente acciones de consulta y orientación de solo lectura (RF-SYS-02).

- El alcance normativo del MVP cubre el Impuesto Predial Unificado (IPU) y el Impuesto de Industria y Comercio (ICA) para el municipio de Bogotá D.C. (RF-SYS-03).

- Durante el desarrollo y la evaluación se emplean datos sintéticos; no se procesan datos reales de contribuyentes, en cumplimiento del acuerdo de confidencialidad suscrito con Realtix.

## 3. Descripción general del sistema

Esta sección describe la perspectiva y la arquitectura general del sistema multiagente de IA, sus actores y las decisiones de alcance y supuestos adoptados por el equipo.

### 3.1. Perspectiva y arquitectura

El sistema multiagente de IA se estructura bajo el patrón de orquestación Supervisor-Worker: un agente orquestador recibe cada consulta del contribuyente, la clasifica y la enruta hacia el agente especializado correspondiente, para luego consolidar la respuesta final. Los componentes del sistema multiagente de IA son: el agente orquestador, el agente especializado en IPU, el agente especializado en ICA, el agente de información general y normativa, el agente de extracción OCR, y el mecanismo de escalamiento a funcionario humano. La sección 5 detalla los requerimientos específicos de cada uno de estos componentes.

### 3.2. Actores del sistema

**Tabla 2. Actores del sistema**

| **Actor**                                 | **Descripción**                                                                                                                                               |
|-------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Contribuyente                             | Usuario final (persona natural o jurídica) que consulta información sobre sus obligaciones tributarias municipales a través de la Oficina Virtual Tributaria. |
| Agente orquestador                        | Componente que recibe la consulta del contribuyente, la clasifica y la enruta al agente especializado correspondiente, y consolida la respuesta final.        |
| Agente especializado en IPU               | Agente con RAG que atiende consultas, consultas de estado de cuenta y liquidaciones estimadas del Impuesto Predial Unificado.                                 |
| Agente especializado en ICA               | Agente con RAG que atiende consultas y estimaciones relacionadas con el Impuesto de Industria y Comercio.                                                     |
| Agente de información general y normativa | Agente con RAG que resuelve consultas transversales sobre el uso de la plataforma y conceptos tributarios generales.                                          |
| Agente de extracción OCR                  | Agente con capacidad de visión que procesa imágenes o PDF de facturas o recibos prediales cargados por el contribuyente y extrae los datos estructurados.     |
| Mecanismo de escalamiento                 | Componente que evalúa la confianza de cada respuesta y transfiere el caso a un funcionario humano cuando corresponde.                                         |
| Funcionario municipal                     | Persona que recibe los casos escalados por el sistema multiagente de IA cuando este no puede resolver la consulta con confianza suficiente.                   |
| Administrador del sistema                 | Persona técnica responsable de mantener la base de conocimiento, revisar métricas de observabilidad y aplicar correcciones al sistema multiagente de IA.      |

Fuente: Elaboración propia.

### 3.3. Decisiones de alcance y supuestos del proyecto

Las siguientes decisiones fueron adoptadas por el equipo de trabajo de grado para permitir el avance del proyecto de forma autónoma, y se documentan aquí como requerimientos de contexto del sistema multiagente de IA:

- Municipio piloto: Bogotá D.C., sede principal de operación de Realtix y jurisdicción del régimen de facturación-declaración establecido en el Decreto Ley 1421 de 1993.

- Tributos cubiertos por el MVP: Impuesto Predial Unificado (IPU) e Impuesto de Industria y Comercio (ICA). Las retenciones de ICA y otros tributos locales quedan fuera de este alcance (RF-ICA-04).

- Modelo de lenguaje: Claude Sonnet 4.6 para el agente orquestador y Claude Haiku 4.5 para los agentes especializados y el agente OCR, conforme al presupuesto aprobado del proyecto; la arquitectura se mantiene agnóstica al proveedor para permitir su sustitución futura (RF-SYS-04, RNF-10).

- Framework de orquestación: LangGraph.

- Base de conocimiento vectorial: ChromaDB, con generación de embeddings mediante el modelo text-embedding-3-large.

- Herramienta de observabilidad: LangSmith.

- Canal de despliegue: widget conversacional embebido en la Oficina Virtual Tributaria.

- Ambiente de datos: durante todo el desarrollo y la evaluación del MVP, el sistema multiagente de IA opera sobre un adaptador de datos sintéticos equivalente a RealSit; la integración con el sistema RealSit real queda fuera del alcance temporal del presente trabajo de grado, si bien la arquitectura se diseña para permitirla mediante la sustitución de dicho adaptador, sin rediseño de los agentes (RF-SYS-05).

- Validación de calidad de las respuestas: se realiza mediante el método LLM-as-judge y la revisión directa de los autores del proyecto durante la Fase 4, sin depender de la disponibilidad de un funcionario de Realtix.

- Formato del documento procesado por el agente OCR: se define una plantilla sintética estándar del recibo de pago del Impuesto Predial Unificado, con la estructura típica de las administraciones tributarias municipales colombianas (identificación del predio, propietario, dirección, avalúo catastral, vigencia fiscal, tarifa, valor liquidado, descuentos por pronto pago y fecha límite de pago), documentada en el diseño del Objetivo Específico 2 (sección 5.2 del documento de arquitectura; RF-OCR-06).

- Atención posterior al escalamiento: el tiempo de respuesta del funcionario ante un caso escalado corresponde al proceso operativo interno de Realtix; el sistema multiagente de IA es responsable únicamente de generar y entregar el resumen del caso (RF-ESC-04).

- Autenticación: el sistema multiagente de IA delega la verificación de identidad en el mecanismo de autenticación ya existente en la Oficina Virtual Tributaria, y opera sobre la sesión autenticada del contribuyente. No se implementa un mecanismo de autenticación propio (RF-AUT-01 a RF-AUT-04).

- Horario de atención: el sistema multiagente de IA opera de 8:00 a. m. a 5:00 p. m. en días hábiles, en correspondencia con el horario de atención del canal humano al que escala los casos no resueltos (RNF-06, RNF-07).

- Empaquetado y despliegue: el sistema multiagente de IA se empaqueta en contenedores y se orquesta con Docker Compose. El despliegue del MVP se realiza sobre Amazon Web Services por ser la nube en la que opera RealSit, pero la contenerización evita la dependencia de ese proveedor y permite llevar el sistema multiagente de IA a otra nube o a un servidor propio sin cambios en el código (RNF-12 a RNF-15).

- No se contempla integración con pasarelas de pago ni ejecución de trámites; el sistema multiagente de IA es exclusivamente informativo y de orientación.

## 4. Historias de usuario

Las historias se agrupan por categoría funcional. Cada historia referencia los requerimientos funcionales de la sección 5 que la soportan.

### 4.1. Consulta de información tributaria general

**Tabla 3. Historias de usuario — Consulta de información tributaria general**

| **ID** | **Historia de usuario**                                                                                                                                                                            | **RF relacionados**  | **Prioridad** |
|--------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------|---------------|
| HU-01  | Como contribuyente, quiero preguntar en lenguaje natural qué es el Impuesto Predial Unificado y cómo se calcula, para entender mi obligación tributaria sin necesidad de leer la ley directamente. | RF-IPU-01            | Alta          |
| HU-02  | Como contribuyente, quiero consultar qué es el Impuesto de Industria y Comercio (ICA) y cuándo debo declararlo, para saber si me aplica.                                                           | RF-ICA-01            | Alta          |
| HU-03  | Como contribuyente, quiero preguntar sobre plazos, descuentos por pronto pago y beneficios tributarios vigentes, para planear mis pagos.                                                           | RF-IPU-04, RF-ICA-03 | Media         |
| HU-04  | Como contribuyente, quiero que el sistema multiagente de IA me explique términos tributarios (avalúo catastral, tarifa, sobretasa) en lenguaje sencillo, para comprender mi factura.               | RF-GEN-02            | Media         |

Fuente: Elaboración propia.

### 4.2. Consulta de estado de cuenta y liquidación estimada

**Tabla 4. Historias de usuario — Consulta de estado de cuenta y liquidación estimada**

| **ID** | **Historia de usuario**                                                                                                                                                          | **RF relacionados**  | **Prioridad** |
|--------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------|---------------|
| HU-05  | Como contribuyente, quiero consultar el estado de cuenta de mi predio ingresando mi número de identificación o de matrícula catastral, para saber si tengo saldos pendientes.    | RF-IPU-02            | Alta          |
| HU-06  | Como contribuyente, quiero consultar mi historial de pagos de los últimos periodos, para verificar que mis pagos fueron registrados correctamente.                               | RF-IPU-02            | Media         |
| HU-07  | Como contribuyente, quiero recibir una estimación del valor a pagar del IPU o del ICA a partir de los datos de mi predio o actividad económica, para presupuestar el pago.       | RF-IPU-03, RF-ICA-02 | Alta          |
| HU-18  | Como contribuyente, quiero que nadie más pueda consultar el estado de cuenta de mi predio conociendo únicamente mi matrícula catastral, para proteger mi información tributaria. | RF-AUT-01, RF-AUT-02 | Alta          |

Fuente: Elaboración propia.

### 4.3. Extracción de datos de factura (OCR)

**Tabla 5. Historias de usuario — Extracción de datos de factura (OCR)**

| **ID** | **Historia de usuario**                                                                                                                                                        | **RF relacionados**  | **Prioridad** |
|--------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------|---------------|
| HU-08  | Como contribuyente, quiero cargar una foto o PDF de mi factura predial, para que el sistema multiagente de IA extraiga automáticamente los datos relevantes y me los confirme. | RF-OCR-02, RF-OCR-03 | Alta          |
| HU-09  | Como contribuyente, quiero que el sistema multiagente de IA valide la calidad de la imagen cargada y me pida una nueva si no es legible, para evitar errores de extracción.    | RF-OCR-04            | Media         |

Fuente: Elaboración propia.

### 4.4. Escalamiento a funcionario humano

**Tabla 6. Historias de usuario — Escalamiento a funcionario humano**

| **ID** | **Historia de usuario**                                                                                                                                                                                       | **RF relacionados**  | **Prioridad** |
|--------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------|---------------|
| HU-10  | Como contribuyente, quiero que, si el sistema multiagente de IA no puede resolver mi consulta con suficiente confianza, se me ofrezca la opción de hablar con un funcionario, para no quedarme sin respuesta. | RF-ESC-01, RF-ESC-02 | Alta          |
| HU-11  | Como funcionario municipal, quiero recibir el caso escalado con el resumen de la conversación y los datos ya identificados, para no pedirle al contribuyente que repita la información.                       | RF-ESC-03            | Alta          |
| HU-12  | Como contribuyente, quiero saber en qué momento estoy hablando con un agente automático y en qué momento con una persona, para entender el estado de mi solicitud.                                            | RF-ESC-05, RF-UI-03  | Media         |

Fuente: Elaboración propia.

### 4.5. Conversación y alcance

**Tabla 7. Historias de usuario — Conversación y alcance**

| **ID** | **Historia de usuario**                                                                                                                                                    | **RF relacionados** | **Prioridad** |
|--------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------|---------------|
| HU-13  | Como contribuyente, quiero mantener el contexto de la conversación entre varias preguntas seguidas, para no repetir información que ya di.                                 | RF-UI-02            | Alta          |
| HU-14  | Como contribuyente, quiero que el sistema multiagente de IA me indique claramente cuando una consulta no está dentro de su alcance, para no generar expectativas erróneas. | RF-GEN-04           | Media         |

Fuente: Elaboración propia.

### 4.6. Administración y observabilidad

**Tabla 8. Historias de usuario — Administración y observabilidad**

| **ID** | **Historia de usuario**                                                                                                                                                    | **RF relacionados**  | **Prioridad** |
|--------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------|---------------|
| HU-15  | Como administrador del sistema, quiero visualizar el flujo de decisiones entre agentes de cada conversación, para depurar errores de enrutamiento.                         | RF-OBS-01            | Alta          |
| HU-16  | Como administrador del sistema, quiero actualizar los documentos de la base de conocimiento sin modificar el código de los agentes, para mantenerla vigente.               | RF-OBS-04            | Media         |
| HU-17  | Como administrador del sistema, quiero consultar métricas de enrutamiento y tiempo de respuesta por conversación, para evaluar el desempeño del sistema multiagente de IA. | RF-OBS-02, RF-OBS-03 | Alta          |

Fuente: Elaboración propia.

## 5. Requerimientos funcionales por componente

Los requerimientos funcionales se organizan por agente o componente del sistema multiagente de IA, conforme a la arquitectura descrita en la sección 3.1. Cada requerimiento se identifica con un prefijo asociado al componente correspondiente.

### 5.1. Requerimientos generales del sistema multiagente de IA

**Tabla 9. Requerimientos generales del sistema multiagente de IA**

| **ID**    | **Nombre**                      | **Descripción**                                                                                                                                                                                                                                                                              | **Prioridad** |
|-----------|---------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------|
| RF-SYS-01 | Patrón Supervisor-Worker        | El sistema multiagente de IA deberá estructurarse bajo el patrón de orquestación Supervisor-Worker, con un agente orquestador que enruta cada consulta hacia uno o más agentes especializados y consolida la respuesta final.                                                                | Alta          |
| RF-SYS-02 | Alcance de solo lectura         | El sistema multiagente de IA deberá limitarse a operaciones de consulta y orientación de solo lectura; no ejecutará operaciones de escritura, modificación de datos ni transacciones financieras sobre los sistemas de Realtix.                                                              | Alta          |
| RF-SYS-03 | Tributos y municipio cubiertos  | El sistema multiagente de IA deberá cubrir, en su versión de producto mínimo viable, el Impuesto Predial Unificado (IPU) y el Impuesto de Industria y Comercio (ICA) para el municipio de Bogotá D.C.; quedan excluidas de este alcance las retenciones de ICA y los demás tributos locales. | Alta          |
| RF-SYS-04 | Modelo sustituible              | El sistema multiagente de IA deberá permitir sustituir el modelo de lenguaje subyacente de cada agente mediante configuración, sin requerir cambios estructurales en el grafo de orquestación.                                                                                               | Media         |
| RF-SYS-05 | Adaptador equivalente a RealSit | El sistema multiagente de IA deberá operar sobre un adaptador de datos equivalente a RealSit, de manera que la lógica de los agentes sea independiente de la fuente de datos subyacente y pueda apuntar al sistema RealSit real sin rediseño.                                                | Alta          |

Fuente: Elaboración propia.

### 5.2. Autenticación y control de acceso a datos del contribuyente

**Tabla 10. Requerimientos de autenticación y control de acceso**

| **ID**    | **Nombre**                    | **Descripción**                                                                                                                                                                                                                                                                                   | **Prioridad** |
|-----------|-------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------|
| RF-AUT-01 | Verificación de identidad     | El sistema multiagente de IA deberá verificar la identidad del contribuyente, a través del mecanismo de autenticación de la Oficina Virtual Tributaria, antes de entregar cualquier información asociada a un predio, una obligación tributaria o un historial de pagos específico.               | Alta          |
| RF-AUT-02 | Restricción a predios propios | El sistema multiagente de IA deberá restringir las consultas de estado de cuenta, historial de pagos y obligaciones vigentes exclusivamente a los predios asociados al contribuyente autenticado, rechazando consultas sobre predios de terceros aunque se aporte una matrícula catastral válida. | Alta          |
| RF-AUT-03 | Consultas sin autenticación   | El sistema multiagente de IA deberá atender sin requerir autenticación únicamente las consultas de carácter general, conceptual o normativo que no involucren datos de un contribuyente identificable.                                                                                            | Alta          |
| RF-AUT-04 | Aviso de sesión requerida     | El sistema multiagente de IA deberá informar al contribuyente, cuando una consulta requiera autenticación y esta no exista en la sesión, que debe iniciar sesión en la Oficina Virtual Tributaria para continuar.                                                                                 | Media         |

Fuente: Elaboración propia.

### 5.3. Agente orquestador (supervisor)

**Tabla 11. Requerimientos del agente orquestador**

| **ID**    | **Nombre**                   | **Descripción**                                                                                                                                                                                                   | **Prioridad** |
|-----------|------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------|
| RF-ORQ-01 | Clasificación de la consulta | El agente orquestador deberá clasificar cada mensaje entrante del contribuyente en una de las categorías definidas (IPU, ICA, información general, extracción de documento, fuera de alcance) antes de enrutarlo. | Alta          |
| RF-ORQ-02 | Enrutamiento y consolidación | El agente orquestador deberá invocar al agente especializado correspondiente a la categoría identificada y esperar su respuesta antes de consolidar la respuesta final al contribuyente.                          | Alta          |
| RF-ORQ-03 | Consultas multiagente        | El agente orquestador deberá resolver consultas que requieran la intervención de más de un agente especializado mediante invocaciones secuenciales y una respuesta consolidada única.                             | Media         |
| RF-ORQ-04 | Implementación en LangGraph  | El agente orquestador deberá implementarse con LangGraph, modelando el flujo de agentes como un grafo de estados con capacidad de ciclos y puntos de verificación (checkpoints).                                  | Alta          |
| RF-ORQ-05 | Modelo de razonamiento       | El agente orquestador deberá utilizar el modelo Claude Sonnet 4.6 para las decisiones de enrutamiento y consolidación, dado el mayor costo relativo de esta tarea frente a los agentes de ejecución.              | Media         |
| RF-ORQ-06 | Prevención de bucles         | El agente orquestador deberá prevenir bucles de enrutamiento infinito mediante un número máximo de reintentos de clasificación por conversación.                                                                  | Alta          |

Fuente: Elaboración propia.

### 5.4. Agente especializado en Impuesto Predial Unificado (IPU)

**Tabla 12. Requerimientos del agente especializado en IPU**

| **ID**    | **Nombre**                    | **Descripción**                                                                                                                                                                                                                                                                            | **Prioridad** |
|-----------|-------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------|
| RF-IPU-01 | Consultas conceptuales de IPU | El agente especializado en IPU deberá responder consultas conceptuales sobre el Impuesto Predial Unificado (base gravable, tarifas, sujetos pasivos, periodicidad) mediante el pipeline RAG sobre la base de conocimiento curada con la Ley 44 de 1990 y la normativa municipal aplicable. | Alta          |
| RF-IPU-02 | Estado de cuenta e historial  | El agente especializado en IPU deberá consultar el estado de cuenta y el historial de pagos de un predio a partir de un identificador (cédula, NIT o matrícula catastral) mediante el adaptador de datos de solo lectura.                                                                  | Alta          |
| RF-IPU-03 | Liquidación estimada          | El agente especializado en IPU deberá calcular una liquidación estimada a partir del avalúo catastral y la tarifa vigente, presentando el desglose del cálculo (base gravable, tarifa aplicada, descuentos) y una nota explícita de que se trata de una estimación no vinculante.          | Alta          |
| RF-IPU-04 | Plazos y descuentos           | El agente especializado en IPU deberá informar los plazos de pago, descuentos por pronto pago y límites al incremento anual vigentes conforme a la Ley 1995 de 2019.                                                                                                                       | Media         |
| RF-IPU-05 | Citación de la norma          | El agente especializado en IPU deberá citar el artículo o norma específica que sustenta cada respuesta de contenido normativo.                                                                                                                                                             | Alta          |

Fuente: Elaboración propia.

### 5.5. Agente especializado en Industria y Comercio (ICA)

**Tabla 13. Requerimientos del agente especializado en ICA**

| **ID**    | **Nombre**                    | **Descripción**                                                                                                                                                                                                                                                                                        | **Prioridad** |
|-----------|-------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------|
| RF-ICA-01 | Consultas conceptuales de ICA | El agente especializado en ICA deberá responder consultas conceptuales sobre el Impuesto de Industria y Comercio (hecho generador, base gravable, periodicidad de declaración) mediante el pipeline RAG sobre la base de conocimiento curada con la Ley 14 de 1983 y la normativa municipal aplicable. | Alta          |
| RF-ICA-02 | Estimación por actividad      | El agente especializado en ICA deberá estimar el valor a declarar a partir de los ingresos brutos y la actividad económica indicados por el contribuyente, aplicando la tarifa correspondiente a la clasificación de la actividad.                                                                     | Alta          |
| RF-ICA-03 | Fechas de declaración         | El agente especializado en ICA deberá informar las fechas de declaración y pago vigentes para el régimen del contribuyente.                                                                                                                                                                            | Media         |
| RF-ICA-04 | Retenciones fuera de alcance  | El agente especializado en ICA deberá identificar de forma explícita las consultas relativas a retención de ICA, escenario excluido del alcance del MVP, y derivarlas al mecanismo de escalamiento.                                                                                                    | Media         |

Fuente: Elaboración propia.

### 5.6. Agente de información general y normativa

**Tabla 14. Requerimientos del agente de información general y normativa**

| **ID**    | **Nombre**                       | **Descripción**                                                                                                                                                                                                                                                                                                                                             | **Prioridad** |
|-----------|----------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------|
| RF-GEN-01 | Consultas transversales          | El agente de información general deberá resolver consultas sobre el funcionamiento de la Oficina Virtual Tributaria y sobre conceptos tributarios transversales no específicos de un único tributo.                                                                                                                                                         | Media         |
| RF-GEN-02 | Explicación en lenguaje sencillo | El agente de información general deberá explicar en lenguaje sencillo términos técnicos presentes en la normativa o en los documentos cargados por el contribuyente.                                                                                                                                                                                        | Media         |
| RF-GEN-03 | Respuesta sustentada en fuentes  | El agente de información general deberá responder utilizando exclusivamente el contenido recuperado de la base de conocimiento vectorial, evitando afirmaciones no sustentadas en las fuentes indexadas.                                                                                                                                                    | Alta          |
| RF-GEN-04 | Detección de fuera de alcance    | El agente de información general deberá reconocer las consultas que no son de carácter tributario e informar al contribuyente que dicho tema no está cubierto por el sistema multiagente de IA, sin derivarlas al mecanismo de escalamiento; las consultas tributarias que exceden el alcance normativo definido (IPU, ICA) se tratan conforme a RF-ESC-02. | Alta          |

Fuente: Elaboración propia.

### 5.7. Agente de extracción de información (OCR)

**Tabla 15. Requerimientos del agente de extracción OCR**

| **ID**    | **Nombre**                      | **Descripción**                                                                                                                                                                                                                                                     | **Prioridad** |
|-----------|---------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------|
| RF-OCR-01 | Carga de archivos               | El agente OCR deberá aceptar como entrada archivos en formato JPG, PNG o PDF cargados por el contribuyente, con un tamaño máximo definido en la especificación técnica del sistema multiagente de IA.                                                               | Alta          |
| RF-OCR-02 | Extracción de campos            | El agente OCR deberá extraer, mediante un modelo de visión multimodal, los siguientes campos del recibo predial: identificación del predio o matrícula catastral, vigencia fiscal, avalúo catastral, valor liquidado, descuentos aplicables y fecha límite de pago. | Alta          |
| RF-OCR-03 | Confirmación de datos extraídos | El agente OCR deberá presentar al contribuyente los datos extraídos en formato estructurado y solicitar su confirmación antes de utilizarlos en otra consulta del sistema multiagente de IA.                                                                        | Alta          |
| RF-OCR-04 | Rechazo de documentos ilegibles | El agente OCR deberá detectar documentos ilegibles, incompletos o que no correspondan a un recibo predial, y solicitar al contribuyente un nuevo intento indicando el motivo específico del rechazo.                                                                | Media         |
| RF-OCR-05 | Modelo de visión                | El agente OCR deberá utilizar el modelo Claude Haiku 4.5 dado el volumen esperado de documentos y el criterio de eficiencia en costos definido para los agentes de ejecución.                                                                                       | Media         |
| RF-OCR-06 | Plantilla sintética de recibo   | El agente OCR deberá operar, durante el desarrollo y la evaluación, sobre la plantilla sintética de recibo predial descrita en la sección 3.3 y especificada en el documento de arquitectura (sección 5.2), en ausencia de acceso a documentos reales de Realtix.   | Alta          |

Fuente: Elaboración propia.

### 5.8. Mecanismo de escalamiento a funcionario humano

**Tabla 16. Requerimientos del mecanismo de escalamiento**

| **ID**    | **Nombre**                     | **Descripción**                                                                                                                                                                                                                                                                                                                                                                                                          | **Prioridad** |
|-----------|--------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------|
| RF-ESC-01 | Cálculo del nivel de confianza | El mecanismo de escalamiento deberá calcular un nivel de confianza compuesto, en el rango de 0.0 a 1.0, a partir de tres factores verificables: el puntaje de similitud de los fragmentos recuperados de la base de conocimiento, la autoevaluación de suficiencia declarada por el agente especializado, y la existencia de cobertura normativa para la consulta; dicho nivel se compara contra un umbral configurable. | Alta          |
| RF-ESC-02 | Activación del escalamiento    | El mecanismo de escalamiento deberá activarse automáticamente cuando el nivel de confianza sea inferior al umbral, cuando el contribuyente lo solicite explícitamente, o cuando la consulta, siendo de carácter tributario, esté fuera del alcance normativo definido (RF-SYS-03).                                                                                                                                       | Alta          |
| RF-ESC-03 | Resumen del caso               | El mecanismo de escalamiento deberá generar un resumen estructurado de la conversación (categoría de la consulta, datos ya identificados, intentos previos de resolución) antes de transferir el caso.                                                                                                                                                                                                                   | Alta          |
| RF-ESC-04 | Tiempo de entrega del resumen  | El mecanismo de escalamiento deberá entregar el resumen estructurado en un tiempo no mayor a 5 segundos desde el momento en que se activa la condición de escalamiento; el tiempo de atención posterior por parte del funcionario corresponde al proceso operativo interno de Realtix y no forma parte del alcance del sistema multiagente de IA.                                                                        | Media         |
| RF-ESC-05 | Notificación al contribuyente  | El mecanismo de escalamiento deberá notificar al contribuyente, dentro de la interfaz conversacional, que su caso fue transferido y que continuará su atención por un canal humano.                                                                                                                                                                                                                                      | Alta          |

Fuente: Elaboración propia.

### 5.9. Interfaz conversacional

**Tabla 17. Requerimientos de la interfaz conversacional**

| **ID**   | **Nombre**                      | **Descripción**                                                                                                                                                                                  | **Prioridad** |
|----------|---------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------|
| RF-UI-01 | Widget embebible                | La interfaz conversacional deberá desplegarse como un widget embebible dentro de la Oficina Virtual Tributaria.                                                                                  | Alta          |
| RF-UI-02 | Contexto de la sesión           | La interfaz conversacional deberá mantener el contexto de una misma sesión para resolver referencias a mensajes anteriores del contribuyente.                                                    | Alta          |
| RF-UI-03 | Identificación del interlocutor | La interfaz conversacional deberá indicar de forma visible si el contribuyente está interactuando con un agente automático o con un funcionario humano, en cualquier momento de la conversación. | Media         |
| RF-UI-04 | Carga desde la conversación     | La interfaz conversacional deberá permitir al contribuyente cargar archivos (imágenes o PDF) directamente desde la conversación para su envío al agente OCR.                                     | Alta          |

Fuente: Elaboración propia.

### 5.10. Observabilidad y administración

**Tabla 18. Requerimientos de observabilidad y administración**

| **ID**    | **Nombre**                          | **Descripción**                                                                                                                                                                                                                        | **Prioridad** |
|-----------|-------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------|
| RF-OBS-01 | Traza del flujo entre agentes       | El sistema multiagente de IA deberá registrar la traza completa del flujo entre agentes (agente invocado, herramienta utilizada, tiempo de cada paso) para cada conversación, mediante la herramienta de observabilidad LangSmith.     | Alta          |
| RF-OBS-02 | Matriz de confusión de enrutamiento | El sistema multiagente de IA deberá exponer al administrador métricas de enrutamiento mediante matriz de confusión, comparando el agente al que se enrutó cada consulta contra el agente que debió atenderla según el plan de pruebas. | Alta          |
| RF-OBS-03 | Métricas de precisión y tiempo      | El sistema multiagente de IA deberá exponer métricas de precisión, exhaustividad y F1 calculadas sobre la matriz de confusión de enrutamiento, así como el tiempo de respuesta por conversación.                                       | Media         |
| RF-OBS-04 | Actualización de la base vectorial  | El sistema multiagente de IA deberá permitir actualizar los documentos de la base de conocimiento vectorial (ingesta y reindexación en ChromaDB) sin requerir cambios en el código de los agentes.                                     | Media         |
| RF-OBS-05 | Ejecución repetible de pruebas      | El sistema multiagente de IA deberá permitir la ejecución repetible del plan de pruebas definido para la Fase 4 sobre el ambiente desplegado.                                                                                          | Alta          |

Fuente: Elaboración propia.

## 6. Requerimientos no funcionales

Los requerimientos no funcionales se agrupan según las características de calidad definidas en la norma ISO/IEC 25010:2011.

### 6.1. Desempeño y escalabilidad

**Tabla 19. Requerimientos no funcionales — Desempeño y escalabilidad**

| **ID** | **Nombre**              | **Descripción**                                                                                                                                                                                | **Prioridad** |
|--------|-------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------|
| RNF-01 | Tiempo de respuesta     | El sistema multiagente de IA deberá responder consultas simples en un tiempo objetivo menor a 8 segundos y consultas con RAG en menor a 15 segundos, medidos en el plan de pruebas.            | Alta          |
| RNF-02 | Escalamiento horizontal | El sistema multiagente de IA deberá poder escalar horizontalmente ante picos de consulta, como los periodos de facturación predial, mediante la replicación de sus contenedores de aplicación. | Media         |

Fuente: Elaboración propia.

### 6.2. Seguridad y protección de datos

**Tabla 20. Requerimientos no funcionales — Seguridad y protección de datos**

| **ID** | **Nombre**                        | **Descripción**                                                                                                                                                                                   | **Prioridad** |
|--------|-----------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------|
| RNF-03 | Protección de datos personales    | El sistema multiagente de IA deberá tratar los datos personales de los contribuyentes conforme a la Ley 1581 de 2012 y sus decretos reglamentarios (finalidad, minimización, seguridad).          | Alta          |
| RNF-04 | Uso exclusivo de datos sintéticos | El sistema multiagente de IA no deberá procesar datos reales de contribuyentes durante el desarrollo y la evaluación; se utilizarán datos sintéticos generados para tal fin.                      | Alta          |
| RNF-05 | Registro auditable                | El sistema multiagente de IA deberá registrar cada interacción de forma auditable, sin almacenar información sensible en texto plano fuera de los mecanismos de almacenamiento seguros definidos. | Alta          |

Fuente: Elaboración propia.

### 6.3. Disponibilidad y fiabilidad

**Tabla 21. Requerimientos no funcionales — Disponibilidad y fiabilidad**

| **ID** | **Nombre**                      | **Descripción**                                                                                                                                                                                                                                                                                                                                                | **Prioridad** |
|--------|---------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------|
| RNF-06 | Horario de atención             | El sistema multiagente de IA deberá estar disponible en el horario de atención al contribuyente, de 8:00 a. m. a 5:00 p. m. (hora de Bogotá) en días hábiles, con un objetivo de disponibilidad del 99% dentro de dicho horario y ventanas de mantenimiento programadas fuera de él.                                                                           | Alta          |
| RNF-07 | Aviso fuera de horario          | El sistema multiagente de IA deberá informar de forma explícita al contribuyente, mediante un mensaje en la interfaz conversacional, cuando sea consultado fuera del horario de atención definido, indicando el horario en que estará nuevamente disponible.                                                                                                   | Media         |
| RNF-08 | Tiempos de espera y degradación | El sistema multiagente de IA deberá aplicar un tiempo máximo de espera por cada invocación a servicios externos (modelo de lenguaje, base de conocimiento vectorial y adaptador de datos) y, ante su vencimiento o ante un fallo del servicio, deberá derivar la consulta al mecanismo de escalamiento en lugar de retornar un error técnico al contribuyente. | Alta          |

Fuente: Elaboración propia.

### 6.4. Usabilidad

**Tabla 22. Requerimientos no funcionales — Usabilidad**

| **ID** | **Nombre**         | **Descripción**                                                                                                                                                                    | **Prioridad** |
|--------|--------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------|
| RNF-09 | Lenguaje accesible | El sistema multiagente de IA deberá utilizar lenguaje claro y accesible, evitando tecnicismos jurídicos sin explicación, considerando perfiles con baja alfabetización tributaria. | Media         |

Fuente: Elaboración propia.

### 6.5. Mantenibilidad, portabilidad y despliegue

**Tabla 23. Requerimientos no funcionales — Mantenibilidad, portabilidad y despliegue**

| **ID** | **Nombre**                | **Descripción**                                                                                                                                                                                                                             | **Prioridad** |
|--------|---------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------|
| RNF-10 | Portabilidad del modelo   | El sistema multiagente de IA deberá permitir sustituir el LLM subyacente sin rediseñar la arquitectura de agentes (ver RF-SYS-04).                                                                                                          | Media         |
| RNF-11 | Código versionado         | El código fuente y la documentación técnica del sistema multiagente de IA deberán quedar versionados en un repositorio Git al cierre del proyecto.                                                                                          | Media         |
| RNF-12 | Imágenes de contenedor    | El sistema multiagente de IA deberá empaquetarse en imágenes de contenedor conforme al estándar OCI, de manera que pueda desplegarse sobre cualquier proveedor de nube o sobre un servidor propio sin modificar el código de la aplicación. | Alta          |
| RNF-13 | Orquestación con Compose  | El sistema multiagente de IA deberá poder levantarse completo, con todos sus servicios y dependencias, mediante un único archivo de orquestación de contenedores (docker-compose.yml).                                                      | Alta          |
| RNF-14 | Configuración por entorno | El sistema multiagente de IA deberá recibir toda su configuración dependiente del entorno (credenciales de las APIs, cadenas de conexión y umbrales) mediante variables de entorno, sin valores fijos en el código ni en las imágenes.      | Alta          |
| RNF-15 | Volúmenes persistentes    | El sistema multiagente de IA deberá persistir los datos de la base de conocimiento, la memoria de sesión y el conjunto sintético en volúmenes externos a los contenedores, de modo que sobrevivan a su reinicio o sustitución.              | Alta          |

Fuente: Elaboración propia.

### 6.6. Calidad funcional

**Tabla 24. Requerimientos no funcionales — Calidad funcional**

| **ID** | **Nombre**                   | **Descripción**                                                                                                                                                                                                   | **Prioridad** |
|--------|------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------|
| RNF-16 | Tasa de respuestas correctas | El sistema multiagente de IA deberá alcanzar una tasa de respuestas correctas o parcialmente correctas, evaluadas mediante el método LLM-as-judge, igual o superior al 85% de los escenarios de prueba definidos. | Alta          |

Fuente: Elaboración propia.

## 7. Normatividad tributaria y de datos aplicable

Base normativa que debe reflejarse en la base de conocimiento del sistema multiagente de IA y que enmarca el tratamiento de datos personales:

- Ley 14 de 1983 — Fortalecimiento de los fiscos municipales; regula el Impuesto de Industria y Comercio.

- Ley 44 de 1990 — Crea el Impuesto Predial Unificado; base gravable y tarifas.

- Ley 1450 de 2011, artículo 23 — Modifica el artículo 4 de la Ley 44 de 1990 y fija el rango general de tarifas del Impuesto Predial Unificado entre el 5 y el 16 por mil del avalúo; la base de conocimiento debe incorporar el texto vigente de la Ley 44 con esta modificación.

- Decreto Ley 1421 de 1993 — Estatuto Orgánico de Bogotá D.C.; sistema mixto de facturación-declaración.

- Decreto Distrital 352 de 2002 y Decreto Distrital 807 de 1993 — Estatuto tributario de Bogotá D.C. (normas sustanciales y procedimiento), junto con los acuerdos del Concejo de Bogotá que fijan las tarifas vigentes de IPU e ICA.

- Ley 1819 de 2016, artículo 354 — Sistema de facturación tributaria: notificación, plazos y título ejecutivo.

- Ley 1995 de 2019 — Límites al incremento anual del Impuesto Predial Unificado.

- Ley 1581 de 2012, Decreto 1377 de 2013 y Decreto 1074 de 2015 — Protección de datos personales; aplican al tratamiento de información del contribuyente por parte del sistema multiagente de IA.

## 8. Aprobación

Este documento constituye el entregable de la Fase 1 del proyecto (documento de metas y requerimientos) y da cumplimiento al Objetivo Específico 1 del trabajo de grado. Con su elaboración se da por completado el objetivo, quedando listo el proyecto para iniciar la Fase 2 (Diseño de la arquitectura del sistema).

Elaborado por: Rodolfo Angel Gilart Pulido, Dayanna Liceth Varón Puerto

Director: MsC. Juan Carlos Barrero Calixto
