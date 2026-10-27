# ADR-24 · Ajustes al plan de pruebas (validación externa) y mejoras R1 a R4

**Estado:** aceptada, octubre de 2026 (Rodolfo aprobó los ajustes A1 a A9 al lanzar B12, después de una validación externa del plan, y las mejoras R1 a R4 porque caben en el presupuesto). **Fuente:** sección 6 de la especificación técnica v6 y secciones 6.1 a 6.6 de la adenda. No modifica la especificación ni la adenda; los cambios que les tocan se proponen en el PR de B12.

## Contexto

Una revisión externa del plan de pruebas del OE4 encontró huecos de método. La estructura del ISTQB estaba incompleta: faltaban los riesgos, las técnicas, el presupuesto y el cronograma. El intervalo de confianza trataba como independientes los ensayos de un mismo escenario. El juez no tenía una prueba con casos conocidos ni quedaba congelado antes de calibrarlo. Las referencias no tenían una verificación automática, y las correcciones podían sobreajustarse a los escenarios. Además, propuso cuatro conjuntos que miden lo que los 60 escenarios no miden: la generalización, las conversaciones largas y la seguridad.

## Decisión

Ajustes al plan:

- **A1 · Estructura del ISTQB completa.** `docs/plan_de_pruebas.md` incluye:
  - los riesgos de producto y de proyecto, con su mitigación;
  - las técnicas de prueba con ejemplos de los escenarios: particiones de equivalencia, valores límite, tablas de decisión, transición de estados del modo humano, adivinación de errores y CA-01 a CA-06;
  - el presupuesto por corrida y el cronograma;
  - una tabla con cada compromiso de la sección 6 de la adenda y dónde se mide.
- **A2 · Intervalo con n = escenarios.** El intervalo de Wilson se calcula con n = 60 escenarios, no con los 180 ensayos, porque los ensayos de un mismo escenario no son independientes. Además, se calcula un bootstrap por escenario del promedio de sus 3 ensayos (10.000 remuestreos, semilla 42).
- **A3 · Dos tasas.** La de la meta: código y juez «correcta» o «parcialmente correcta», sin alucinación. Y una estricta: solo «correcta».
- **A4 · Evaluadores validados con casos conocidos.** Antes de la mini corrida se usa la respuesta guardada de GEN-02, con las tres secciones del manual que cita como contexto.
  - Con la frase «Para pagar o presentar, debes hacerlo directamente en la Oficina Virtual Tributaria», debe salir mal: en el juez, con alucinación o un veredicto distinto de «correcta»; en RAGAS, con menor fidelidad que la versión fiel.
  - La versión fiel debe salir «correcta» o «parcialmente correcta» sin alucinación, y con fidelidad de 0,9 o más.
  - Si no, es una parada.
- **A5 · Juez congelado.** El modelo, las instrucciones (`src/evaluacion/juez.v1.md`), la rúbrica, el esquema y los parámetros tienen una huella SHA-256. La calibración la guarda, y la corrida 3 (`--exigir-huella`) exige la misma; si cambia, se repite la calibración.
- **A6 · Kappa completo.** Se calcula entre el juez y el consenso humano, binario y ponderado lineal de 3 niveles, y entre los dos evaluadores antes del consenso, con intervalos por bootstrap.
- **A7 · Verificador de referencias** (`scripts/verificar_referencias.py`), que corre antes de la corrida 1.
  - Cada fuente esperada existe en la base.
  - Cada cifra de cada referencia coincide con `datos/`, con el adaptador, con el texto de la norma citada o con una operación de cifras verificadas.
  - Una discrepancia sin resolver es una parada: la decide Rodolfo.
- **A8 · Regla contra el sobreajuste.** Ningún texto, pregunta ni cifra de los escenarios va en prompts ni en código. Cada corrección es general y trae su caso de regresión. La regla está en `CLAUDE.md` y una prueba automática la vigila.
- **A9 · Detalles de medición.** RAGAS se prueba en español con sus 2 casos iniciales. Se reportan dos latencias: la del servidor (`meta.tiempos_ms.total`, la de la meta de RNF-01) y la que observa el cliente. El modo de evaluación solo se activa durante las corridas.

Mejoras, que se reportan aparte de los 60:

- **R1 · Generalización.** 10 variantes parafraseadas de escenarios aprobados de un turno con RAG, con la misma referencia (`tests/escenarios_adicionales/generalizacion.yaml`). Dayanna escribe las variantes y solo corren en la corrida 3.
- **R2 · Muestra de calibración de 30.** Pasa de 20 respuestas al azar a 30, estratificadas por el veredicto del juez: la mitad aprobadas y la mitad no. Los evaluadores no ven el veredicto.
- **R3 · Tres encadenados** (CAD-01 a CAD-03). Unen los turnos, las verificaciones y las referencias de escenarios aprobados en una conversación.
- **R4 · Dos de seguridad:**
  - SEG-01: inyección de instrucciones para ver otro predio;
  - SEG-02: pedido de revelar las instrucciones o las claves.

  Las referencias de R3 y R4 las aprueba Rodolfo antes de la corrida 1.

Detalles de implementación decididos en B12:

- **Evaluador de RAGAS:** `gpt-4.1-mini`. Con `gpt-4o-mini`, la validación A4 falló porque dio por sustentada la frase inventada.
- **`meta.contextos`** lleva cada fragmento con su cita, como lo ve el modelo.
- **`meta.tokens_por_modelo`** (solo en el modo de evaluación) permite costear una corrida contra el servidor.

## Alternativas

- Wilson con n = 180 ensayos: se descartó, porque subestima la incertidumbre (A2).
- Muestra de calibración al azar: con un juez que aprueba la mayoría, casi no tendría casos negativos y el kappa sería inestable (R2).
- Mantener `gpt-4o-mini` en RAGAS por precio: se descartó, porque no detecta una alucinación conocida (A4).

## Consecuencias

- El plan de pruebas cumple la estructura que el documento promete (adenda, sección 6.2).
- El intervalo de la meta es más ancho, pero honesto.
- La calibración tiene una muestra más grande y equilibrada, aunque estratificada. El reporte lo advierte, porque la prevalencia de la muestra no es la de la corrida.
- Una referencia mal transcrita se detecta antes de pagar una corrida.
- Las correcciones de la corrida 1 no pueden copiar los escenarios.
- Costo previsto con R1 a R4: unos US$16,70 de 25 en Anthropic y US$3,06 de 10 en OpenAI (`reports/presupuesto.md`).

## Cambio en el documento de grado

- En las secciones 1.5.2.7 y 1.5.2.8 (plan y métricas):
  - el intervalo con n = escenarios y el bootstrap;
  - las dos tasas;
  - la validación de los evaluadores y el juez congelado;
  - el kappa entre evaluadores;
  - la muestra de 30 estratificada.
- En el capítulo de resultados:
  - los conjuntos R1, R3 y R4, aparte;
  - la latencia del servidor y la del cliente.

Quedan en `docs/cambios_para_documento.md`.
