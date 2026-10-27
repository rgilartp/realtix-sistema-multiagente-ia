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
