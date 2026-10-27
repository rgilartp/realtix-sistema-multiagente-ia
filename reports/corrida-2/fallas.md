# Fallas de la corrida 2

Análisis de la sección 6.6 y de ADR-24, con el mismo formato de `reports/corrida-1/fallas.md`. Se
revisaron los 7 escenarios no superados de los 60 (R3 y R4 se superaron completos). El detalle de
cada ensayo (verificaciones y veredicto del juez v3, con sus afirmaciones sin fuente) está en
`calificados.jsonl` y `juez.jsonl`. La versión evaluada es `4e94e7a` (el `main` con las
correcciones de la corrida 1), con el juez v3 (huella `afecd5c1…`).

- **Causa técnica:** enrutamiento, recuperación, prompt, datos, umbral o infraestructura; se agrega
  «instrumento» cuando la falla está en la evaluación.
- **Familia de MAST** (Cemri y colaboradores): diseño del sistema, desalineación entre agentes o
  verificación de la tarea.
- **Origen según RAGAS:** recuperación (precisión o exhaustividad del contexto bajas), generación
  (fidelidad baja con un contexto suficiente) o sin RAG.
- **Regla A8:** ninguna corrección copia textos, preguntas ni cifras de los escenarios.

Las fallas se numeran G1 a G7 para no confundirlas con F1 a F13 de la corrida 1.

## Resumen

**Tasa de la meta: 88,3 %** (53 de 60; Wilson de 77,8 % a 94,2 %; bootstrap de 80,0 % a 95,0 %).
**Tasa estricta: 75,0 %** (45 de 60; Wilson de 62,8 % a 84,2 %). R3: 3 de 3. R4: 2 de 2. La meta del
85 % (51 de 60) se cumple en esta corrida de un ensayo; la corrida 3 (3 ensayos) es la que se
reporta.

| # | Falla | Dónde está | Escenarios (de los 60) | Corrección |
|---|---|---|---|---|
| G1 | Escala por confianza: la similitud de la parte general queda al borde del umbral | Umbral (y generación) | 1 (GEN-02) | Propuesta (el umbral y los pesos no se tocan en la ronda 2) |
| G2 | El fragmento del alivio de intereses no se recupera y la parte escala por confianza | Recuperación | 1 (IPU-14) | Mejora de la búsqueda (ronda 2) |
| G3 | Generalización sin fuente y rango de tarifas que no se recupera | Recuperación y generación | 1 (IPU-04) | Mejora de la búsqueda (ronda 2) |
| G4 | Fecha relativa calculada por el modelo («mañana») que contradice la fecha de hoy | Generación (datos) | 1 (ICA-07) | Días que faltan calculados por código (ronda 2) |
| G5 | Omite el periodo bimestral que nombra la norma recuperada | Generación | 1 (ICA-02) | Ninguna nueva (variación; la regla ya está) |
| G6 | Una pregunta general con «mi» se clasifica como personal y pide sesión | Enrutamiento | 1 (IPU-09) | Propuesta (el prompt del orquestador no se toca en la ronda 2) |
| G7 | Omite un plazo del calendario sin llamar la herramienta de fechas | Generación | 1 (IPU-13) | Ninguna nueva (variación) |

**Lectura para el documento.**

- De los 31 escenarios no superados en la corrida 1, se recuperaron 26 de los 60 (más 5 de R3 y
  R4). 12 los recuperó el **instrumento** (F1 y F3) y 14 el **sistema** (F2, F4, F5, F6, F7 y F8).
- 2 escenarios que se superaron en la corrida 1 no se superaron aquí (G6 y G7). Fallan igual con el
  código anterior a las correcciones (`reports/regresion-correcciones-corrida-1/variacion_sin_juez*.json`):
  son debilidades previas, no regresiones.
- Las 7 fallas son del sistema; ninguna es del instrumento. En dos (G5 y G7) el juez dio
  «correcta» y falló una verificación de código por un dato omitido.

## Atribución de lo recuperado

Cada escenario recuperado se atribuye a la corrección de la corrida 1 que lo cubría
(`reports/corrida-1/fallas.md`).

| Corrección | Instrumento o sistema | Escenarios recuperados (de los 60) | En R3 y R4 |
|---|---|---|---|
| F1 · El juez y RAGAS ven todas las fuentes | Instrumento | 9: AIA-01, AMB-02, ICA-04, IPU-02, IPU-03, IPU-10, MULTI-02, OCR-02, OCR-07 | CAD-01, CAD-03 |
| F3 · «Decreto Distrital» | Instrumento | 3: ICA-01, IPU-05, MULTI-03 | — |
| F10 · Detector de fuga | Instrumento | — | SEG-02 |
| F2 · Categoría clasificada | Sistema (registro) | 6: ESC-01, FA-01 a FA-05 | — |
| F4 y F8 · Periodicidad y estimación del ICA | Sistema | 3: ICA-05, ICA-06, ICA-08 | CAD-02 (también F1) |
| F5 · Anclaje y citas | Sistema | 1: IPU-01 | — |
| F6 · Aclaraciones | Sistema | 2: AMB-01, ICA-03 | — |
| F7 · Tarifas por año | Sistema | 2: ACC-04, IPU-06 | — |
| F9 · Rechazo previo | Sistema | — | SEG-01 |
| **Total** | | **26** (12 del instrumento y 14 del sistema) | 5 |

- Con 29 superados en la corrida 1, más 26 recuperados, menos 2 perdidos (G6 y G7), quedan 53.
- Sin las correcciones del instrumento, la tasa del sistema sería de 41 de 60 (68,3 %). Esta cifra es
  informativa: el juez también cambió a v3 (ADR-25).
- F2 corrige solo el registro de la categoría: el contribuyente ya recibía lo esperado.

## G1 · Escalamiento por confianza en la parte general (umbral)

- **Escenario:** GEN-02.
- **Evidencia:**
  - escaló por «confianza insuficiente» con 0,635. En las verificaciones locales había dado 0,686 y
    0,651, y en la corrida 1, 0,724;
  - el agente general, corrido solo, marca `completa`, así que la baja viene de la similitud de los
    fragmentos citados (`reports/verif-fix-anclaje-y-citas/consultas_directas.json`);
  - en esas ejecuciones directas sigue afirmando que los pagos se hacen en la Oficina Virtual
    Tributaria, sin fuente.
- **Evidencia (RAGAS):** precisión del contexto de 0,87 y exhaustividad de 1,0. El fragmento correcto
  llegó; la respuesta fue el aviso de transferencia (fidelidad de 0,25).
- **Origen:** umbral; la afirmación del canal, generación.
- **MAST:** diseño del sistema.
- **Corrección:**
  - **propuesta, sin aplicar en la ronda 2:** el umbral y los pesos de la confianza quedan fuera de
    la ronda 2 por instrucción de Rodolfo. El umbral propuesto (`reports/umbral/propuesta.md`)
    mantiene 0,70: con 0,625 o menos, GEN-02 respondería, pero su respuesta trae la afirmación sin
    fuente;
  - **la afirmación del canal** es la candidata conocida de la ronda 2: una regla en el prompt del
    agente general (no en `comun.v3`).

## G2 · El fragmento del alivio de intereses no se recupera (recuperación)

- **Escenario:** IPU-14.
- **Evidencia:**
  - escaló por «confianza insuficiente» con 0,64;
  - el alivio de intereses es el art. 7 del Acuerdo 1084, y no estuvo entre los fragmentos, como en
    la verificación de F6.
- **Evidencia (RAGAS):** exhaustividad de 0,33.
- **Origen:** recuperación.
- **MAST:** diseño del sistema.
- **Corrección:** la mejora de la búsqueda, por la regla de `reports/corrida-1/fallas.md` (sección
  «Recuperación»): IPU-04 e IPU-14 siguen sin superarse con una exhaustividad menor de 0,5. Entra
  como una corrección aparte en la ronda 2, con su caso de regresión en
  `tests/test_evaluacion_recuperacion.py`.

## G3 · Generalización sin fuente y rango que no se recupera (recuperación y generación)

- **Escenario:** IPU-04.
- **Evidencia (juez v3):** afirmación sin fuente: «se fija por destino del predio (residencial,
  comercial o lote)». Además omite el rango de tarifas del 5 al 16 por mil.
- **Evidencia (RAGAS):** precisión de 0,58, exhaustividad de 0,33 y fidelidad de 0,58.
- **Origen:** recuperación (exhaustividad baja) y generación (la generalización).
- **MAST:** verificación de la tarea. El verificador de citas no revisa las generalizaciones sin
  artículo.
- **Corrección:** la mejora de la búsqueda (G2). La generalización la vigila la regla de anclaje de
  `comun.v3`, que no se toca en la ronda 2.

## G4 · Fecha relativa que contradice la fecha de hoy (generación)

- **Escenario:** ICA-07.
- **Evidencia (juez v3):** «vence el 9 de octubre de 2026 (mañana)», cuando la fecha de hoy que dio
  la herramienta es el 1 de octubre.
- **Evidencia (RAGAS):** exhaustividad de 1,0 y fidelidad de 0,95; las fechas son correctas, la
  falla es la relación con hoy.
- **Origen:** generación. El modelo calcula una fecha relativa.
- **Causa técnica:** datos. `fechas_ica` y `fechas_predial` dicen si cada fecha ya pasó, pero no
  cuántos días faltan.
- **MAST:** diseño del sistema.
- **Corrección (ronda 2):**
  - las herramientas de fechas agregan los días que faltan, calculados por código;
  - los prompts del IPU y del ICA dicen que una fecha relativa sale de ese dato y nunca de un cálculo
    del modelo.

## G5 · Omite el periodo de la norma (generación)

- **Escenario:** ICA-02.
- **Evidencia:** el juez dio «correcta» y la respuesta sigue el Decreto 352, art. 42, pero no dice
  que la liquidación es bimestral; falla la verificación «bimestre». RAGAS da 1,0, 1,0 y 0,95.
- **Origen:** generación, con un contexto suficiente.
- **MAST:** verificación de la tarea.
- **Corrección:** ninguna nueva. La regla «conserva el periodo que nombra la norma que citas»
  (`ica.v2`) lo superó en la verificación local después de la revisión del PR #41; aquí no. Es
  variación del modelo y la medirá la corrida 3 (3 ensayos).

## G6 · Una pregunta general con «mi» pide sesión (enrutamiento)

- **Escenario:** IPU-09.
- **Evidencia:**
  - el orquestador marcó la consulta como personal (`sesion_requerida`) y respondió con el aviso de
    sesión, con la categoría `general`;
  - con el código de la corrida 1 pasa lo mismo, en 3 de 3 intentos.
- **Origen:** sin RAG.
- **Causa técnica:** enrutamiento.
- **MAST:** diseño del sistema.
- **Corrección:** **propuesta, sin aplicar.** El prompt del orquestador queda fuera de la ronda 2.
  La regla general sería: una pregunta por cómo funciona el impuesto, aunque diga «mi», es general
  si no pide datos de la cuenta.

## G7 · Omite un plazo del calendario (generación)

- **Escenario:** IPU-13.
- **Evidencia:**
  - el juez dio «correcta», pero falla la verificación del plazo de expedición de las facturas;
  - el agente no llamó `fechas_predial` y respondió con los fragmentos;
  - con el código de la corrida 1 pasa lo mismo, en 3 de 3 intentos.
- **Evidencia (RAGAS):** exhaustividad de 0,67 y fidelidad de 1,0.
- **Origen:** generación.
- **MAST:** desalineación entre agentes: no pide la herramienta que trae el dato.
- **Corrección:** ninguna en la ronda 2. Una regla que obligue a dar los plazos en cualquier consulta
  sobre el pago se acercaría al escenario (A8).

## Otras observaciones

- **F11 (nota de mora repetida):** 1 de los 12 turnos con la advertencia de mora la repite.
- **Latencia (RNF-01):**
  - Con RAG, el p95 del servidor fue de 12.372 ms, con 39 de 39 turnos bajo 15 s.
  - Sin fragmentos, el p95 fue de 8.782 ms, con 18 de 19 bajo 8 s. El único que pasó la meta fue un
    escalamiento de fuera de alcance en el que el orquestador tardó 8.766 ms en clasificar: es la
    latencia del modelo del orquestador, que no cambió con las correcciones.
  - Desglose en `reporte.md`.
- **RAGAS:**
  - Sin sesión (21 casos): precisión de 82,7 %, exhaustividad de 82,5 % y fidelidad de 87,8 %.
  - Con sesión (16 casos), con los datos de las herramientas como contexto (F1), pasan de 45,4 %,
    33,1 % y 39,6 % en la corrida 1 a 47,5 %, 79,5 % y 80,3 %.
- **Trazas (RNF-05):** 1.277 ejecuciones de 63 conversaciones, ninguna con identificadores
  (`trazas.json`).

## Recuperación: ¿entra la mejora de la búsqueda?

**Sí.** La regla de `reports/corrida-1/fallas.md` se cumple: IPU-04 (G3) e IPU-14 (G2) siguen sin
superarse, las dos con una exhaustividad de 0,33. Entra en la ronda 2 como una corrección aparte, con
su caso de regresión en `tests/test_evaluacion_recuperacion.py`.
