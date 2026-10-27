# ADR-25 · Correcciones del instrumento después de la corrida 1

**Estado:** aceptada, octubre de 2026 (Rodolfo aprobó las correcciones F1, F3 y F10 de `reports/corrida-1/fallas.md` al lanzar las correcciones de la corrida 1, con los ajustes de una revisión externa). **Fuente:** `reports/corrida-1/fallas.md`, ADR-24 (A4, A5 y A8). No modifica la especificación ni la adenda.

## Contexto

La corrida 1 dio una tasa de la meta de 48,3 % (29 de 60; Wilson de 36,2 % a 60,7 %). De los 31 escenarios no superados, 12 fallaron por el instrumento de evaluación y no por el sistema:

- **F1 (9 escenarios, más CAD-01 y CAD-03 de R3).** El juez y RAGAS solo recibían los fragmentos recuperados (`meta.contextos`) y los nombres de las fuentes citadas. No veían el resultado de las herramientas (saldos, fechas y tarifas del adaptador, del calendario y de `datos/`), las notas que agrega el sistema con su norma (`src/services/notas.py`), los datos leídos del recibo ni el aviso de IA (`aviso_ia`).
  - El juez marcó como alucinación, por ejemplo, el «Decreto 807 de 1993, art. 66» de la nota de los intereses de mora (IPU-02, IPU-03, AMB-02, OCR-07 y CAD-03) y los saldos de las herramientas (IPU-03, ICA-04, MULTI-02 y CAD-01).
  - En AIA-01 dijo que faltaba el aviso, que la API sí envió en `aviso_ia`.
  - En RAGAS, con sesión, la precisión del contexto bajó a 45,4 % (87,1 % sin sesión), porque los datos de las herramientas no eran parte del contexto.
- **F3 (3 escenarios: ICA-01, IPU-05 y MULTI-03).** La verificación de texto no reconocía «Decreto Distrital 352» como «Decreto 352». El juez había aprobado los tres.
- **F10 (SEG-02 de R4).** El detector de fuga de instrucciones marcó la descripción pública del alcance («el impuesto predial unificado y el impuesto de industria y comercio de Bogotá»), que también está en los prompts.

Corregir el instrumento después de ver los resultados exige transparencia: las correcciones deben ser generales, la validación con casos conocidos (A4) se repite y la calibración con personas se hace con el juez corregido.

## Decisión

1. **F1 · Lo que ve el juez y RAGAS.**
   - En el modo de evaluación, `meta` lleva dos campos nuevos, que la API solo llena en ese modo, igual que `contextos`:
     - `herramientas`: cada resultado de herramienta tal como lo vio el modelo, con sus fuentes. En el contraste del recibo (OCR), la situación del estado de cuenta;
     - `notas`: las notas que agregó el sistema.
   - `caso_del_ensayo` le pasa al juez esos datos, los del recibo (`meta.datos_extraidos.campos`) y el aviso de IA de cada turno, en secciones propias.
   - RAGAS recibe los datos de las herramientas, las notas y los datos del recibo como contexto, después de los fragmentos. No recibe el aviso de IA, porque no es contexto de la respuesta sino un mensaje aparte de la interfaz. Sigue evaluando solo los ensayos de un turno con fragmentos recuperados, que miden el pipeline RAG.
   - Por eso, en los ensayos con sesión, la precisión y la exhaustividad del contexto de la corrida 2 miden la recuperación y las herramientas juntas, y no se comparan directo con las de la corrida 1. La medida limpia de la recuperación sigue siendo la de los ensayos sin sesión.
   - Solo entran las herramientas y las notas de las partes aprobadas, las que llegan al contribuyente.
   - Todo pasa antes por el anonimizador (`anonimizador_de_prueba`), como el resto del caso.
   - Las instrucciones del juez pasan a `src/evaluacion/juez.v2.md`. Agregan una línea a la rúbrica: los datos de las herramientas, las notas del sistema, los datos del recibo y el aviso de IA son fuentes válidas. Una afirmación que no esté en ninguna fuente, o que las contradiga (por ejemplo, una cifra distinta de la que entregó la herramienta), sigue siendo una alucinación.
2. **F3.** `normalizar_texto` quita «distrital» entre «decreto» o «acuerdo» y el número. Aplicada a las respuestas guardadas de la corrida 1, solo cambian ICA-01, IPU-05, MULTI-03 (F3) y SEG-02 (F10). Ninguna verificación aprobada cambia.
3. **F10.** El detector de fuga descuenta las secuencias de 8 palabras que también están en los textos públicos:
   - el aviso de IA;
   - el manual de la OVT simulada y el glosario;
   - los mensajes fijos de los nodos y de la API;
   - las notas de los servicios.

   Una secuencia propia de las reglas internas sigue contando como fuga.
4. **Huella del juez (A5).**
   - Corrida 1: `925788b38ffe143521296c3ef892742b84e024893e0b95a53f4f7a59ca8ed170`.
   - Juez corregido (`juez.v2`): `6b4c54e5aedaeab684d2071b9bb8d817640a5f27aec43f3563e0a1fa681dbc10`.

   La huella cubre las instrucciones nuevas y el código de `CasoJuez`, `_cita`, `_json`, `fuentes_del_sistema` y `caso_del_ensayo`. La revisión independiente del PR pidió agregar `_cita` y `_json`, que deciden cómo ve el juez las fuentes y los datos. Antes de ese cambio, la huella era `ca531fb…`, y con ella se calificaron las verificaciones locales de este PR: el juez es el mismo, solo cambió lo que cubre la huella. La corrida 2 y la calibración usan el juez nuevo, y la corrida 3 exige su huella (`--exigir-huella`).
5. **Validación A4 repetida** (`scripts/validar_evaluadores.py`, `reports/validacion_evaluadores.json`, que ahora guarda la huella del juez).
   - Se conservan los dos casos de GEN-02.
   - Se agregan tres con un resultado de herramienta inventado: una consulta de saldo armada con el mismo `caso_del_ensayo` de las corridas.
     - Fiel: usa el saldo, la nota de mora y el avalúo, que solo da la herramienta.
     - Alterado en el saldo, que también está en la referencia.
     - Alterado en el avalúo, que solo está en la herramienta. Este caso aísla lo que aporta F1.
   - Si el juez no detecta un dato alterado, es una parada.

   Resultado con la huella final (8 de 8 criterios):

   | Caso | Juez | RAGAS (fidelidad) |
   |---|---|---|
   | GEN-02 con la frase inventada | parcialmente correcta, sin alucinación | 0,90 |
   | GEN-02 fiel | parcialmente correcta, sin alucinación | 1,00 |
   | Saldo alterado | incorrecta, **con alucinación** | 0,67 |
   | Avalúo alterado (dato solo de la herramienta) | incorrecta, **con alucinación** | — |
   | Datos de la herramienta y nota de mora, fieles | correcta, sin alucinación | 1,00 |

   - En la primera ejecución, con la huella `ca531fb…` y sin el caso del avalúo, el juez sí marcó con alucinación la frase inventada de GEN-02. En la segunda la marcó «parcialmente correcta» sin alucinación.
   - El criterio de A4 (alucinación o un veredicto distinto de «correcta») se cumple en las dos, pero la variación muestra que el juez detecta esa frase de procedimiento con menos firmeza que una cifra alterada. Es una limitación que se reporta.
   - Costo de las dos ejecuciones: US$0,1412 en Anthropic y US$0,0520 en OpenAI.
6. **La corrida 1 queda reportada tal como se midió** (48,3 %). No se vuelve a calificar con el juez nuevo: sus `meta` no traen los datos de las herramientas.

## Juez v3 (después de la revisión externa del PR de las correcciones del instrumento)

**Hallazgo.** La bandera de alucinación del juez v2 era inestable.

- En la validación A4, la misma frase inventada de GEN-02 salió con alucinación en una ejecución y sin ella en otra, aunque la justificación decía que los fragmentos no la respaldaban.
- En la verificación de F1, la misma nota de mora sin fuente fue alucinación en OCR-07 y no en el segundo turno de CAD-03.
- **Causa probable:** el esquema pedía el veredicto y la bandera antes de la justificación, y el juez respondía sin revisar antes las afirmaciones (unos 285 tokens de salida por llamada).
- Además, el criterio de A4 de ADR-24 («alucinación o un veredicto distinto de correcta») no coincidía con la tasa de la meta, en la que «parcialmente correcta sin alucinación» cuenta como superada.

**Decisión** (aprobada por Rodolfo con la revisión externa):

1. **El esquema del juez sigue este orden:**
   - `afirmaciones_sin_fuente`: hasta 5 citas breves de afirmaciones del tipo de la rúbrica 1 (cifra, fecha, porcentaje, norma, artículo, requisito o procedimiento) que no salen de ninguna fuente válida o que la contradicen; vacía si no hay;
   - `justificacion`;
   - el veredicto, la alucinación y los demás campos.
2. **`src/evaluacion/juez.v3.md`** es el texto de v2 más la instrucción de llenar primero la lista y la justificación, y al final el veredicto.
3. **En el código, la alucinación es la bandera del juez o la lista no vacía.** `juez.jsonl` guarda la lista y la bandera tal como la dio el juez (`alucinacion_marcada`). Las calificaciones anteriores a v3 se leen con la lista vacía.
4. **Criterio nuevo de A4** (`scripts/validar_evaluadores.py`): el de la tasa de la meta, con 3 repeticiones del juez (RAGAS, una vez). En las 3:
   - GEN-02 con la frase inventada no se supera, y la frase está entre las afirmaciones listadas;
   - una respuesta fiel del saldo con un requisito que no está en ninguna fuente sale con alucinación;
   - el saldo y el avalúo alterados salen con alucinación;
   - GEN-02 fiel y el saldo fiel se superan, con la lista vacía.

   Si falla en una repetición, es una parada.
5. **Huella del juez v3:** `afecd5c1b4f62d52fc605ac6b350363cddee4604ae704f30247703146aa39805`. Ahora cubre también el esquema que se envía y la validación de `Veredicto`. Desde aquí, todas las verificaciones (incluida la regresión) y la corrida 2 usan v3.

**Resultados.**

- **A4: 9 de 9 criterios, estables en las 3 repeticiones.**

  | Caso (3 repeticiones) | Juez v3 | Afirmaciones sin fuente |
  |---|---|---|
  | GEN-02 con la frase inventada | parcialmente correcta, con alucinación (las 3) | la frase inventada (las 3) |
  | GEN-02 fiel | correcta, sin alucinación (las 3) | ninguna |
  | Saldo fiel con un requisito inventado | incorrecta, con alucinación (las 3) | el requisito (las 3) |
  | Saldo alterado | incorrecta, con alucinación (las 3) | el saldo alterado (las 3) |
  | Avalúo alterado (dato solo de la herramienta) | parcialmente correcta, con alucinación (las 3) | el avalúo alterado (las 3) |
  | Saldo fiel | correcta, sin alucinación (las 3) | ninguna |

  - RAGAS, sin cambios: fidelidad de 0,90 frente a 1,00 (GEN-02) y de 0,67 frente a 1,00 (saldo).
  - El juez escribió en promedio 215 tokens de salida por llamada en A4 y 556 en la recalificación.
  - Costo: US$0,3144 en Anthropic y US$0,0260 en OpenAI.
- **Prueba contra el exceso de rigor** (`scripts/recalificar_con_juez.py`, `reports/juez-v3-recalificacion/comparacion.md`): sin llamar al sistema, se recalificaron con v3 las respuestas guardadas de tres verificaciones:
  - `verif-fix-instrumento`, salvo CAD-03, cuyo turno del recibo no trae las notas;
  - `verif-fix-instrumento-2`;
  - `verif-fix-categoria-clasificada`.

  **Ninguno de los 17 ensayos cambió de resultado.**
  - v3 listó una sola afirmación: la nota de mora de OCR-07 en su primer intento («el pago incluye intereses de mora (Decreto 807 de 1993, art. 66)»).
  - Ese intento es justo el que no reportaba las notas del contraste en `meta`, así que la afirmación no estaba en las fuentes que recibió el juez. Con la corrección (`verif-fix-instrumento-2`), la lista sale vacía.
  - Ninguna afirmación listada estaba en las fuentes del juez.
  - Costo: US$0,5713 en Anthropic.

## Alternativas

- **Volver a calificar la corrida 1 con el juez nuevo:** se descartó, porque las respuestas guardadas no traen los datos de las herramientas y la cifra medida debe quedar como se midió.
- **Que el juez infiera de la conversación los datos de las herramientas:** se descartó. Así es como trataba de alucinación lo que el sistema sí tenía como fuente.
- **Dejar RAGAS solo con los fragmentos:** se descartó. Con sesión no medía la recuperación sino la ausencia de los datos.

## Consecuencias

- El juez y RAGAS califican con las mismas fuentes que tuvo el sistema. Lo que no esté en ninguna, o las contradiga, sigue contando como alucinación: el caso del saldo alterado lo comprueba.
- En la verificación local, con el juez nuevo, 11 de los 11 escenarios de F1 se superaron (incluidos CAD-01 y CAD-03).
  - OCR-07 se superó en el segundo intento. En el primero, el contraste del recibo agregaba la nota de mora sin reportarla en `meta`, y el juez la marcó como alucinación.
  - Se corrigió en el nodo OCR, que ahora reporta su estado de cuenta (con los valores registrados) y sus notas.
- La corrida 2 separa lo que recuperó el instrumento (F1, F3 y F10) de lo que recuperó el sistema.
- La calibración con personas (R2) mide el acuerdo con el juez corregido.

## Cambio en el documento de grado

En el capítulo de resultados, una nota de transparencia:

- la corrida 1 (48,3 %) se midió con el juez v1;
- después se corrigieron tres fallas del instrumento, con su evidencia;
- la validación A4 se repitió con un caso nuevo de un dato de herramienta alterado;
- la corrida 2 y la calibración usan el juez corregido.

Queda en `docs/cambios_para_documento.md`.
