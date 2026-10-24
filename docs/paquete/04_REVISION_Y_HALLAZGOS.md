# Revisión técnica del sistema multiagente de IA — qué se hizo, qué se encontró y cómo se corrige

> Paquete de traspaso del chat de desarrollo (OE3) · septiembre de 2026.
> Proyecto: sistema multiagente de IA para el soporte del proceso de facturación de Realtix.
> Los identificadores CA-nn y CR-nn remiten a los cambios de `03_ARQUITECTURA_OE2_v2.md` y
> `04_REQUERIMIENTOS_OE1_v2.md`.

> **Vigencia a octubre de 2026 (nota del paquete de desarrollo).** El texto de abajo se
> conserva como se escribió en septiembre de 2026. Lo que cambió desde entonces:
>
> - **Cambios CA-nn y CR-nn:** ya están aplicados en `documentos/Arquitectura_OE2_Realtix_FINAL`
>   y `documentos/Requerimientos_OE1_Realtix_FINAL`. Los archivos de control de cambios
>   (`03_ARQUITECTURA_OE2_v2.md` y `04_REQUERIMIENTOS_OE1_v2.md`) no vienen en este paquete;
>   sus identificadores quedan solo como referencia histórica.
> - **Sección 3 (código):** sigue vigente y se corrige en el Paso 2. M-04, M-05 y M-06 ya se
>   resolvieron en la documentación del código. Las verificaciones V-01 a V-08 se repitieron en
>   octubre de 2026 con los mismos resultados, y hay observaciones nuevas (OC-01 a OC-08) en
>   `codigo_6.3.1/realtix-mvp/ESTADO_DEL_CODIGO.md`.
> - **Sección 4 (normativa y despliegue):** vigente, salvo un dato de N-03: la documentación de
>   AWS consultada en octubre de 2026 indica una vigencia de 198 días para los certificados
>   exportables, no de 395; el precio se consulta en la página de precios de ACM al desplegar.
> - **Secciones 5 y 6 (brechas y referencias cruzadas):** resueltas en los documentos FINAL.
> - **Sección 7 (observaciones):** O-01, O-03 y O-05 ya se decidieron (sección 8b del contexto);
>   las demás no dejan nada pendiente para el desarrollo.
> - **Nombres de archivo de entonces → en este paquete:** `CONTEXTO_PROYECTO_REALTIX.md` →
>   `02_CONTEXTO_PROYECTO_REALTIX.md`; `02_PLAN_DESARROLLO_OE3.md` → `03_PLAN_DESARROLLO_OE3.md`;
>   `COMPARACION_Y_MEJORAS.md` → `05_COMPARACION_Y_MEJORAS.md`; los `.docx` FINAL → carpeta
>   `documentos/`; el código de `Realsit.zip` → `codigo_6.3.1/realtix-mvp/` (sin el entorno
>   virtual); las figuras → carpeta `figuras/`. `Cronograma_REALTIX.xlsx` no viene en el paquete.

---

## 1. Alcance de la revisión

Antes de iniciar el desarrollo de los agentes (actividad 6.3.4 en adelante) se revisó todo el
material del proyecto y se ejecutó el código existente, con el fin de detectar lo que impediría
integrar el grafo de LangGraph, la API y los datos sintéticos.

| Material | Qué se revisó |
|---|---|
| `CONTEXTO_PROYECTO_REALTIX.md` | Completo; es la fuente de verdad del proyecto |
| `COMPARACION_Y_MEJORAS.md` | Completo |
| `Requerimientos_OE1_Realtix_FINAL.docx` | Texto completo; los 48 RF, 16 RNF y 18 HU leídos uno por uno; 24 tablas |
| `Arquitectura_OE2_Realtix_FINAL.docx` | Texto completo, 11 tablas y las 3 figuras (extraídas del .docx y revisadas visualmente) |
| `Realsit.zip` | Código de 6.3.1 (`models.py`, `database.py`, `adapter.py`, `generate_synthetic_data.py`, `demo.py`, `README.md`) y base SQLite. Se ejecutó con Python 3.12 y Faker 40.39 |
| `Cronograma_REALTIX.xlsx` | Actividades 14 a 23 de la Fase 3 y sus semanas |

---

## 2. Verificaciones ejecutadas

| # | Verificación | Resultado |
|---|---|---|
| V-01 | Regenerar la base con `--contribuyentes 150 --seed 42` | 150 contribuyentes, 170 predios, 434 obligaciones y 317 pagos: coincide con el README |
| V-02 | Ejecutar `demo.py` dos veces seguidas | Pasa las dos veces, incluido el rechazo de RF-AUT-02; la corrección de idempotencia funciona |
| V-03 | Comparar identificadores entre dos generaciones con la misma semilla | Contribuyentes 150/150 y predios 170/170 idénticos, también contra la base incluida en el zip; obligaciones 0/434 y pagos 0/317 |
| V-04 | Distribución de estados de pago | ICA 2026: 54 al día y 40 vencidas. IPU 2025: 170 al día. IPU 2026: 93 al día y 77 vencidas. Ninguna obligación pendiente |
| V-05 | Obligaciones de ICA por contribuyente y vigencia | 13 contribuyentes con dos obligaciones de ICA 2026 de valores distintos |
| V-06 | Predios por tramo de tarifa del IPU en el generador | 4,0 por mil: 12 · 6,5 por mil: 23 · 9,0 por mil: 56 · 12,0 por mil: 79 |
| V-07 | Llamar al adaptador desde un hilo distinto al que lo creó | `sqlite3.ProgrammingError` |
| V-08 | Registrar un caso escalado sin conversación previa | `sqlite3.IntegrityError: FOREIGN KEY constraint failed` |
| V-09 | Conteo de requerimientos, tablas y líneas "Fuente" | 48 RF (SYS 5, AUT 4, ORQ 6, IPU 5, ICA 4, GEN 4, OCR 6, ESC 5, UI 4, OBS 5), 16 RNF, 18 HU. Requerimientos: 24 tablas y 24 líneas "Fuente". Arquitectura: 11 tablas y 11 líneas "Fuente", ninguna bajo las figuras |
| V-10 | Referencias cruzadas "Tabla N" contra los títulos reales | Arquitectura: 22 números de tabla citados, 14 erróneos en 11 ubicaciones. Requerimientos: 1 errónea |
| V-11 | Revisión visual de las figuras de arquitectura | Inconsistencias en las 3 (sección 5 de este archivo) |
| V-12 | Presencia de las cifras 150/170/434/317 en los documentos | No aparecen en los documentos entregados; solo en el README y en el contexto |
| V-13 | Regla del director de texto entre títulos | 5 casos de títulos consecutivos en arquitectura y 2 en requerimientos |
| V-14 | Convención "sistema multiagente de IA" | 26 apariciones de "sistema" sin el calificativo: 15 en requerimientos y 11 en arquitectura (sección 7) |
| V-15 | Normativa y despliegue en fuentes oficiales | Sección 4 |

Todas las versiones v2 se validaron automáticamente después de aplicar los cambios: conteos de
RF, RNF y HU, filas por tabla, líneas "Fuente", referencias cruzadas (cada número apunta a la
tabla correcta) y ausencia de títulos consecutivos.

---

## 3. Hallazgos en el código de 6.3.1

El código funciona como demostración, pero al usarlo como lo usarán el grafo y la API aparecen
tres fallas y tres problemas de datos. Todos se reprodujeron; ninguno es supuesto. Las
correcciones se aplican en el Paso 2 del plan (`02_PLAN_DESARROLLO_OE3.md`).

### H-01. El adaptador no se puede usar desde otro hilo

- **Qué pasa:** `MockRealSitAdapter` abre una conexión SQLite en su constructor y la reutiliza;
  SQLite rechaza por defecto su uso desde un hilo distinto.
- **Evidencia:** V-07.
- **Impacto:** FastAPI ejecuta los endpoints síncronos en un grupo de hilos y LangGraph puede
  ejecutar nodos en hilos distintos. El adaptador fallaría en la primera integración.
- **Corrección:** una conexión por operación, abierta y cerrada dentro de cada método.
- **Requerimientos:** RF-SYS-05, RNF-08.

### H-02. `registrar_caso_escalado` falla si la conversación no existe

- **Qué pasa:** la tabla `caso_escalado` tiene llave foránea hacia `conversacion` y ningún
  componente crea esa fila. `demo.py` funciona porque la inserta con SQL directo.
- **Evidencia:** V-08.
- **Impacto:** el nodo de escalamiento fallaría justo en el caso que debe resolverse sin errores.
- **Corrección:** la implementación sintética registra la conversación si no existe antes de
  registrar el caso. El contrato no cambia. Queda documentado en la sección 5 de arquitectura
  v2 (CA-33).
- **Requerimientos:** RF-ESC-03, RNF-08.

### H-03. Identificadores de obligaciones y pagos no reproducibles

- **Qué pasa:** se generan con `uuid4`, que no depende de la semilla.
- **Evidencia:** V-03.
- **Impacto:** los escenarios de prueba que citen una obligación o un pago dejarían de ser
  válidos al regenerar la base; afecta la repetibilidad que exige RF-OBS-05.
- **Corrección:** derivar los identificadores del generador aleatorio con semilla. No cambia
  las cifras.

### H-04. ICA duplicado por predio

- **Qué pasa:** el generador crea una obligación de ICA por cada predio de un contribuyente con
  actividad económica.
- **Evidencia:** V-05.
- **Impacto:** el ICA grava la actividad, no la propiedad. El estado de cuenta muestra una
  liquidación de ICA distinta según el predio consultado.
- **Corrección (D4):** una sola obligación de ICA por contribuyente y vigencia, asociada al
  predio donde ejerce la actividad. Documentado en la sección 5 de arquitectura v2 (CA-33).
  Cambian las cifras de obligaciones y pagos.

### H-05. Datos sin variedad de estados

- **Evidencia:** V-04.
- **Impacto:** no hay datos para escenarios como "¿cuándo vence mi predial?" (obligación
  pendiente) o "¿debo años anteriores?" (mora de 2025), que el plan de pruebas del OE4 necesita.
- **Corrección (D4):** introducir obligaciones pendientes y en mora de vigencias anteriores.

### H-06. Tramo de IPU de 4 por mil

- **Evidencia:** V-06. El comentario del código cita el rango de 1 a 16 por mil de la Ley 44 de
  1990.
- **Impacto:** ese rango fue modificado (N-01). Los predios sintéticos no tienen estrato ni
  destino económico, así que el tramo no tiene justificación.
- **Corrección (D4):** tramo mínimo de 5 por mil. La tabla de tarifas se mueve a la capa de
  servicios, para que la liquidación estimada (RF-IPU-03) y los datos sintéticos usen la misma
  fuente; sus valores se alinean con la norma durante la curaduría (6.3.2).

### Hallazgos menores

| ID | Hallazgo | Corrección |
|---|---|---|
| M-01 | `get_obligaciones_vigentes` devuelve también las obligaciones pagadas y se solapa con `get_estado_cuenta` | "Vigentes" = pendientes de pago (pendiente o vencido) de cualquier vigencia; definido en arquitectura v2 (CA-31) |
| M-02 | `get_avaluo_catastral` fija la vigencia 2026 en el código | Tomarla de la configuración |
| M-03 | Una actividad de ICA inexistente lanza un `ValueError` genérico | Excepción propia del dominio |
| M-04 | Los docstrings, el README y el contexto llaman "Tabla 5" al contrato | En el documento entregado es la Tabla 7 |
| M-05 | El docstring de `PredioNoAutorizadoError` indica escalar | Se alinea con RF-AUT-02: rechazo explícito sin escalar (D3, CA-29) |
| M-06 | `EstadoCuenta.contribuyente` guarda el identificador y no el nombre | Se documenta el campo |
| M-07 | No hay forma de obtener los predios de un contribuyente | Se agrega `get_predios_contribuyente` (D1) |

### Higiene del repositorio

- El zip incluye el entorno virtual completo: 4.689 de sus 4.704 entradas. Va al `.gitignore`.
- El `__pycache__` es de Python 3.14, mientras el contenedor usa Python 3.12 (Tabla 9 de
  arquitectura). El desarrollo local se alinea a 3.12.
- La base generada (`.db`) no se versiona: se regenera con la semilla.

---

## 4. Verificación normativa y de despliegue

### N-01. Rango de tarifas del Impuesto Predial Unificado

El artículo 23 de la Ley 1450 de 2011 reescribió el artículo 4 de la Ley 44 de 1990: el rango
general de la tarifa quedó entre el 5 y el 16 por mil del avalúo. El rango de 1 a 16 por mil se
conservó solo para inmuebles urbanos de uso habitacional o rurales agropecuarios de estratos 1,
2 y 3 con valor inferior a 135 SMLMV, y los terrenos urbanizables no urbanizados y los
urbanizados no edificados pueden llegar hasta el 33 por mil.

- Fuentes: Secretaría General del Senado,
  <http://www.secretariasenado.gov.co/senado/basedoc/ley_1450_2011.html>; Función Pública,
  <https://www.funcionpublica.gov.co/eva/gestornormativo/norma_pdf.php?i=43101>.
- Consecuencias: el comentario del generador está desactualizado (H-06); las listas normativas
  de requerimientos no incluían la Ley 1450 de 2011 (CR-01, CR-03); la colección `normativa_ipu`
  debe incorporarla (CA-35); el corpus debe usar el texto compilado vigente de la Ley 44, o el
  nodo_ipu citaría un rango que ya no aplica.

### N-02. Estatuto tributario de Bogotá

El Decreto 352 de 2002 compila la normativa sustantiva de los tributos del Distrito Capital, y
la Secretaría Distrital de Hacienda lo presenta, junto con el Decreto 807 de 1993
(procedimiento), como las normas que componen el estatuto tributario de Bogotá.

- Fuentes: Secretaría Distrital de Hacienda, <https://www.haciendabogota.gov.co/es/sdh/tributarias>;
  normograma de la Cancillería, <https://cancilleria.gov.co/normograma/compilacion/docs/d_alcabog_0352_2002.htm>.
- Consecuencias: se agregan a las listas normativas (CR-02, CR-04) y a las colecciones
  `normativa_ipu` y `normativa_ica` (CA-35, CA-36). Los acuerdos del Concejo que fijan las
  tarifas vigentes quedan por identificar en la curaduría; no se verificaron en esta revisión.

### N-03. Certificados de AWS Certificate Manager en Nginx sobre EC2

Desde junio de 2025, ACM emite certificados públicos exportables que pueden instalarse
en instancias EC2, contenedores o servidores propios. Tienen vigencia de 395 días y costo por
emisión y renovación (el anuncio indicaba 15 USD por dominio y 149 USD por comodín; verificar
el precio vigente al desplegar). Antes, los certificados públicos de ACM solo podían asociarse a
servicios integrados como balanceadores de carga, CloudFront o API Gateway.

- Fuentes: AWS, <https://aws.amazon.com/about-aws/whats-new/2025/06/aws-certificate-manager-public-certificates-use-anywhere>;
  documentación de ACM, <https://docs.aws.amazon.com/acm/latest/userguide/acm-exportable-certificates.html>.
- Consecuencias: como la arquitectura termina TLS en el contenedor proxy, el certificado debe
  ser exportable (CA-37). Revisar el costo contra el rubro de AWS del presupuesto. Alternativas:
  un balanceador de carga con certificado no exportable, o Let's Encrypt en el proxy.

---

## 5. Brechas entre los documentos y los requerimientos

| ID | Brecha | Evidencia | Resolución |
|---|---|---|---|
| B-01 | No hay método para obtener los predios de un contribuyente | RF-IPU-02 (consulta por cédula o NIT) y la sección 6.1 (inyectar el conjunto de predios) no son implementables con los 6 métodos | D1: `get_predios_contribuyente` (CA-27, CA-30, CA-31, CA-40) |
| B-02 | El grafo documentado es lineal | La Tabla 2 v1 tiene 6 transiciones sin ciclos: RF-ORQ-03 (secuencia multiagente), RF-ORQ-04 (ciclos) y RF-ORQ-06 (reintentos) son inalcanzables; la solicitud explícita debía pasar por un worker; sin ruta al escalamiento si falla el orquestador (RNF-08) | D2: 2 transiciones nuevas (CA-13, CA-18, CA-26) |
| B-03 | AgentState incompleto | La sección 6.1 y la fila RF-AUT de la Tabla 10 exigen el contexto autorizado en el estado y la Tabla 3 no lo tenía; faltaban campos para RF-ORQ-03, RF-ORQ-06, RF-ESC-01, RF-ESC-03 y RF-OCR-01 | D2: 7 campos nuevos y ciclo de vida (CA-19, CA-20, CA-21) |
| B-04 | Conflicto sobre consultas fuera de alcance | RF-GEN-04 pide informar; RF-ESC-02 y la sección 3.4 piden escalar todo | D3 (CR-05, CR-06, CA-16, CA-24) |
| B-05 | Plantilla del recibo OCR no documentada | Requerimientos (sección 3.3 y RF-OCR-06) afirman que está en el diseño del OE2; el documento de arquitectura no la contenía | Nueva sección 5.2 (CA-33, CA-42, CR-07, CR-08) |
| B-06 | Reglas del nivel de confianza incompletas | Las respuestas basadas solo en datos del adaptador no tienen fragmentos (similitud indefinida); las preguntas de aclaración se escalarían; no se decía para qué usa Sonnet 4.6 el nodo de confianza | CA-22, CA-23, CA-25 |
| B-07 | Degradación ante fallos sin rutas definidas | La sección 3.5 no decía cómo llegar al escalamiento desde cada nodo | CA-26 |
| B-08 | Predio ajeno | El docstring del adaptador indica escalar; RF-AUT-02 indica rechazar | CA-29 y M-05 |
| B-09 | Figura 1 | Sin las transiciones de D2; las flechas condicionales hacia respuesta y escalamiento quedaban tapadas por sus etiquetas | `figura1_grafo_estados_v2.png` (CA-14) |
| B-10 | Figura 2 | Sin `actividad_economica` ni `fecha_limite_pago` (presentes en el código y necesarios para RF-ICA-02, RF-IPU-04 y RF-OCR-02); la nota decía que el OCR "alimenta" ObligacionTributaria, lo que contradice RF-SYS-02 | `figura2_modelo_datos_v2.png` (CA-32) |
| B-11 | Figura 3 | Los servicios externos aparecían dentro del host; el volumen `datos-sinteticos` no se conectaba al backend, su dueño según la Tabla 9 | `figura3_topologia_despliegue_v2.png` (CA-34) |
| B-12 | Figuras sin línea "Fuente" | 0 de 3 | CA-14, CA-32, CA-34 |
| B-13 | Sin ubicación para la configuración y el contenedor de dependencias | La Tabla 4 y RNF-14 los exigen; la Tabla 5 no los ubicaba | CA-39 |
| B-14 | Certificado TLS en AWS | La sección 9.3 no precisaba que el certificado de ACM debe ser exportable | CA-37 (N-03) |

---

## 6. Referencias cruzadas erróneas (lista exacta)

**Causa:** al insertar las Tablas 4 y 5 (secciones 3.6 y 3.7) no se actualizaron las referencias
posteriores. Todas las referencias a tablas con número 4 o mayor conservaron la numeración
anterior, con un desfase de +2.

| # | Ubicación | Dice | Debe decir | Cambio |
|---|---|---|---|---|
| 1 | Sección 1, primer párrafo | Tabla 8 y Tabla 9 | Tabla 10 y Tabla 11 | CA-01 |
| 2 | Sección 4, primera viñeta | Tabla 6 | Tabla 8 | CA-02 |
| 3 | Sección 5, primer párrafo | Tabla 5 | Tabla 7 | CA-03 |
| 4 | Tabla 10, fila RF-SYS | Tabla 5 | Tabla 7 | CA-04 |
| 5 | Tabla 10, fila RF-IPU | Tabla 1 y 4; Tabla 5 | Tabla 1 y 6; Tabla 7 | CA-05 |
| 6 | Tabla 10, fila RF-ICA | Tabla 1 y 4; Tabla 5 | Tabla 1 y 6; Tabla 7 | CA-06 |
| 7 | Tabla 10, fila RF-GEN | Tabla 1 y 4 | Tabla 1 y 6 | CA-07 |
| 8 | Tabla 10, fila RF-UI | Tabla 6 | Tabla 8 | CA-08 |
| 9 | Tabla 10, fila RF-OBS | Tabla 6 | Tabla 8 | CA-09 |
| 10 | Tabla 11, fila RNF-03, RNF-04 | Tabla 5 | Tabla 7 | CA-10 |
| 11 | Tabla 11, fila RNF-12, RNF-13 | Tabla 7 | Tabla 9 | CA-11 |

En total, 14 números de tabla erróneos en 11 ubicaciones; los otros 8 números citados eran
correctos. Referencias adicionales corregidas:

- Tabla 11, fila RNF-09: remitía a la sección 3.2, que no trata los prompts; ahora remite a la
  Tabla 5 (CA-12, con CA-38).
- Requerimientos, RF-OCR-06: remitía a la "Tabla 2 (sección 3.3)"; la Tabla 2 es la de actores
  (CR-07).
- Fuera de los documentos: el código de 6.3.1, su README y el contexto llaman "Tabla 5" al
  contrato del adaptador (se corrige en el Paso 2 y en el contexto v2).

---

## 7. Otras observaciones

**O-01. Convención "sistema multiagente de IA".** De las 26 apariciones de "sistema" sin el
calificativo, la v2 corrige 12 que están en prosa (CA-44 a CA-50; CR-09 a CR-13). Se dejaron,
a propósito, 14 que no son redacción libre: 5 se refieren al sistema RealSit o a nombres de
fase del cronograma ("Diseño de la arquitectura del sistema", "Desarrollo del sistema"), y 9
son títulos, el título de la Tabla 2 de requerimientos o el nombre del actor "Administrador del
sistema". El chat de documentos decide si también ajusta títulos y el nombre del actor.

**O-02. Regla del director de texto entre títulos.** Los 7 casos de títulos consecutivos de los
documentos entregados se corrigen con una frase introductoria (CA-51 a CA-55; CR-14, CR-15).

**O-03. Redacción del KPI en la sección 10.1 de arquitectura.** Dice "(100% de componentes que
satisfacen los requerimientos aprobados)", mientras el KPI 2 aprobado en la propuesta es "igual
o superior al 95%". Sugerencia: "(meta: 95 % o más; resultado: 100 % de los grupos de
requerimientos cubiertos)". No se aplicó en la v2: verificar contra la propuesta aprobada.

**O-04. Cobertura total declarada en la sección 1 de arquitectura.** Con la topología v1 no era
cierta para RF-ORQ-03, RF-ORQ-04 y RF-ORQ-06; con la v2 sí. Conviene tenerlo presente para la
sustentación.

**O-05. Referencia de RNF-16 en la Tabla 11.** Remite a la sección 8.3 (integración con modelos
y LangSmith). El plan de pruebas se documenta en el OE4; al integrar el documento final conviene
remitir al capítulo de evaluación.

**O-06. Índice de requerimientos.** "4. Historias de usuario" figura en la página 8 y su
subsección 4.1 en la 7; se corrige al regenerar el índice en Word.

**O-07. Consolidación de la respuesta.** RF-ORQ-02 atribuye la consolidación al agente
orquestador y la arquitectura la asigna a nodo_respuesta. La Tabla 1 ya relaciona RF-ORQ-02 con
nodo_respuesta, así que es coherente como flujo de orquestación. No requiere cambio.

---

## 8. Dónde queda cada corrección

| Corrección | Documento v2 | Código (paso del plan) |
|---|---|---|
| Referencias cruzadas | CA-01 a CA-12; CR-07, CR-08 | Docstrings (Paso 2) |
| D1 — predios del contribuyente | CA-27, CA-30, CA-31, CA-40 | Paso 2 |
| D2 — grafo y estado | CA-13 a CA-26, CA-41, CA-43 | Pasos 3 a 5 |
| D3 — fuera de alcance y predio ajeno | CR-05, CR-06; CA-16, CA-24, CA-29 | Pasos 4 y 5 |
| D4 — datos sintéticos | CA-33 (precisión sobre el ICA) | Paso 2 |
| Plantilla del recibo OCR | CA-33, CA-42; CR-07, CR-08 | Paso 7 |
| Normativa | CR-01 a CR-04; CA-35, CA-36 | Curaduría 6.3.2 y Paso 6 |
| Figuras | CA-14, CA-32, CA-34 | — |
| Certificado TLS | CA-37 | Paso 11 |
| Estructura del repositorio | CA-38, CA-39 | Paso 1 |
| Fallas y menores del código (H-01 a H-06, M-01 a M-07) | — | Paso 2 |
| Convención y formato | CA-44 a CA-55; CR-09 a CR-15 | — |
