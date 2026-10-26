# Corrección de la recuperación (revisión externa sobre B8)

## Qué se hizo

Una revisión externa, comprobada sobre `main`, encontró cuatro problemas que afectaban a IPU-09 y a IPU-10. Se corrigieron así:

1. **Textos derogados indexados como vigentes** (`src/integrations/segmentacion.py`).
   - El reconocimiento de textos anteriores solo aceptaba «El texto original/anterior era el siguiente». Ahora reconoce cualquier variante de «El texto … era el siguiente:». En la base hay cinco: original (201), derogado (44 bloques del Decreto 807, en las dos colecciones), original del artículo (12), anterior (3) y «de los incisos derogados» (1).
   - También reconoce la marca dentro de un párrafo, «<El texto derogado era el siguiente>», que solo aparece en la Ley 14 de 1983, art. 4, derogado por la Ley 1955 de 2019. La nota de la derogatoria queda vigente y el artículo derogado pasa a texto anterior.
   - Acuerdo 648 de 2016, art. 1: los topes del 20 %, 15 %, 10 % y 18 %, el del IPC y el que remite al Decreto Ley 1421 son los incisos que derogó el Acuerdo 927 de 2024, art. 285, parágrafo. Se comprobó en la página del Régimen Legal, donde el texto vigente termina en el ajuste de los rangos con el IPVN. Ahora son texto anterior y no salen en ninguna búsqueda. La tabla de tarifas sigue vigente.
   - La base pasó de 1.117 a 1.148 fragmentos.
2. **Consulta de búsqueda en los términos de la norma.**
   - En la misma llamada, el orquestador devuelve para cada parte una `busqueda` escrita con el vocabulario de las normas (prompt `orquestador.v2.md`). El agente recupera con ella, anonimizada.
   - El año, el prompt («Parte que atiendes») y la respuesta siguen saliendo del texto del contribuyente.
   - Los parámetros de ADR-04 no cambian: 8 por canal, RRF k = 60 y 5 al prompt.
   - El prompt pide no escribir el significado de las siglas. En la calibración, el orquestador había inventado uno para SPAC.
3. **Prueba de la recuperación** (`scripts/probar_recuperacion.py` y `src/evaluacion/recuperacion.py`).
   - Toma cada escenario aprobado con `fuentes_esperadas` en `knowledge_base/`.
   - Pasa el primer turno por el orquestador real y recupera cada parte con las colecciones de su agente y el año del reloj del escenario.
   - Cuenta un acierto si entre los 5 primeros está la norma y el artículo esperados, con el texto de la parte y con la búsqueda.
   - Resultado en `reports/recuperacion.json`.
4. **Cada cifra con la fuente de la herramienta.**
   - El resultado de cada herramienta llega al modelo con sus `fuentes`. Antes el modelo no las veía, y por eso citaba la norma de un fragmento.
   - Cada tarifa del predial trae la fuente de su sección (`fuentes_por_seccion` en `datos/tarifas/ipu_2026.yaml`): el art. 1 de la Resolución SDH-000194 de 2025 para los residenciales urbanos, el art. 2 para los no residenciales y los lotes, el Acuerdo 648 de 2016, art. 1, y el Acuerdo 780 de 2020, art. 3, parágrafo 2, para las preferenciales, y el Decreto 639 de 2025, art. 207, para la exclusión.
   - Regla nueva del prompt común (`comun.v2.md`): cada cifra se cita con la fuente que entrega la herramienta, nunca con la norma de un fragmento.
5. **Reingesta y nueva escala de la similitud.** La calibración ahora pasa cada consulta por el orquestador, porque es la búsqueda lo que embebe el agente.

## Requerimientos

- RF-ORQ-01 · Clasificación de la consulta
- RF-IPU-04 · Plazos y descuentos
- RF-IPU-05 · Citación de la norma
- RF-GEN-03 · Respuesta sustentada en fuentes
- RF-ESC-01 · Cálculo del nivel de confianza
- RF-OBS-04 · Actualización de la base vectorial
- RF-OBS-05 · Ejecución repetible de pruebas

## Cómo se verificó

| Verificación | Resultado |
|---|---|
| `uv run pytest -q` | 501 superadas y 7 saltadas (las de modelos y embeddings reales) |
| Recorrido de toda la base | Ningún fragmento vigente contiene «… era el siguiente» (prueba `test_ningun_fragmento_vigente_trae_un_texto_anterior_o_derogado`) |
| Acuerdo 648, art. 1; Ley 14, art. 4; Decreto 807, art. 24 | Los textos derogados son anteriores, con vigencia `(0, 0)`; las tarifas y el ajuste con el IPVN siguen vigentes |
| Reingesta (`scripts/ingestar.py`) | 92 fragmentos embebidos (24.274 tokens, US$0,0032) y 1 borrado |
| Modelo falso | La búsqueda llega al recuperador y el texto, al prompt. En IPU-10, el modelo recibe la regla y «6,1 por mil» con la fuente «Resolución SDH-000194 de 2025, art. 1», sin el Acuerdo 648 |
| Embeddings reales (`REALTIX_PRUEBAS_REALES=1`) | «límite al aumento anual del impuesto predial» trae el art. 2 de la Ley 1995 entre los 5. Con «¿Cuánto puede subir el predial de un año a otro?» sigue sin traerlo (`xfail` estricto) |
| Lint | `ruff check` y `ruff format --check` sin observaciones |

### Aciertos de la recuperación (los 5 primeros, embeddings reales, una corrida)

50 escenarios aprobados con 69 fuentes de `knowledge_base/`. Una fuente acierta si su norma y uno de sus artículos están entre los 5 primeros fragmentos de alguna parte del escenario.

| Conjunto | Con el texto de la parte | Con la búsqueda |
|---|---|---|
| Todos (50 escenarios, 69 fuentes): fuentes | 34 (49,3 %) | 40 (58,0 %) |
| Todos: escenarios con todas sus fuentes | 22 (44,0 %) | 28 (56,0 %) |
| Los que responden con fragmentos (31 de IPU, ICA, general y multiagente; 48 fuentes): fuentes | 25 (52,1 %) | 30 (62,5 %) |
| Los que responden con fragmentos: escenarios con todas | 14 (45,2 %) | 19 (61,3 %) |

- **IPU-09:** con la búsqueda («límite del incremento anual del impuesto predial unificado respecto del año anterior»), el art. 2 de la Ley 1995 llega primero; con el texto, no entra en los 5. El art. 49 de la Ley 2294 no llega por ninguna de las dos vías. Su vigencia la dice el prompt común y la nota de la Ley 1995 que agrega el código.
- **Fuentes que entran con la búsqueda y no con el texto (11):**
  - ICA-03, ICA-04, ICA-05 (Acuerdo 1084, art. 21), ICA-08 e ICA-09;
  - IPU-06 (Acuerdo 780), IPU-09, IPU-11 e IPU-12 (Ley 1819, art. 354);
  - la parte de ICA de MULTI-02 y de MULTI-03.
- **Fuentes que entran con el texto y no con la búsqueda (6):**
  - GEN-02 (manual de la OVT) e IPU-14 (Acuerdo 1084, art. 7);
  - IPU-10 (Resolución SDH-000195, arts. 3 y 6);
  - dos de IPU-12 (Acuerdo 648, art. 5, y Acuerdo 1084, art. 27);
  - la parte de IPU de MULTI-03 (Ley 44).
  - Se revisan en la corrida 1.
- **No dependen de la recuperación** los 19 escenarios restantes: acceso, horario, fuera de alcance, robustez, OCR y aviso de IA. Su respuesta es un texto fijo, sale del adaptador o escala. Lo mismo pasa con las cifras de IPU-10 y MULTI-02, que entrega la herramienta con su fuente (corrección 4).
- La salida del orquestador varía de una corrida a otra. Una primera corrida, con el prompt anterior a la regla de las siglas, dio 36 y 40 aciertos de 69.

### Escala de la similitud

Las mismas 10 consultas de B8, cada una con la búsqueda del orquestador (`reports/b08_calibracion.json`).

| Consulta | Tipo | Coseno con la búsqueda | Coseno con el texto | Fragmento |
|---|---|---|---|---|
| ICA-01 | pertinente | 0,722 | 0,683 | Decreto 352 de 2002, cap. II, art. 41 |
| IPU-09 | pertinente | 0,691 | 0,548 | Ley 1995 de 2019, art. 2 |
| IPU-04 | pertinente | 0,676 | 0,689 | Decreto 352 de 2002, cap. I, art. 14 |
| GEN-07 | pertinente | 0,616 | 0,572 | Ley 1581 de 2012, art. 8 |
| GEN-04 | pertinente | 0,527 | 0,517 | Glosario, SPAC |
| FA-02 (licencia) | sin relación | 0,401 | 0,357 | Ley 14 de 1983, art. 54 |
| FA-01 (clima) | sin relación | 0,393 | 0,407 | Ley 14 de 1983, art. 29 |
| Receta | sin relación | 0,318 | 0,320 | Decreto 807 de 1993, art. 39 |
| Película | sin relación | 0,227 | 0,226 | Manual de la OVT simulada |
| Fútbol | sin relación | 0,221 | 0,196 | Ley 14 de 1983, art. 14 |

Nueva escala: 0,40 vale 0 (el coseno más alto de las consultas sin relación) y 0,68 vale 1 (la mediana de las pertinentes). En B8 era de 0,41 a 0,57. Las corridas 1 y 2 la calibran de nuevo (ADR-17).

### Gasto

| Concepto | Costo |
|---|---|
| Reingesta (OpenAI) | US$0,0032 |
| Prueba de recuperación, dos corridas (Sonnet 5.5, 50 llamadas cada una; la segunda, 132.513 tokens de entrada y 7.875 de salida) | US$0,682 |
| Calibración, dos corridas (Sonnet 5.5, 10 llamadas cada una; estimado con el costo por llamada de la prueba) | unos US$0,14 |
| Embeddings de las consultas | menos de US$0,001 |
| **Total** | **unos US$0,82 en Anthropic y US$0,004 en OpenAI** |

Gasto acumulado del proyecto: unos US$0,96 de US$25 en Anthropic y unos US$0,08 de US$10 en OpenAI.

## Decisiones tomadas y pendientes

- **`fuentes_por_seccion` en `datos/tarifas/ipu_2026.yaml`.** Es un campo nuevo; los valores no cambian. Los artículos salen de los títulos de la resolución en `knowledge_base/`. Sin ese campo (2027), la fuente sigue siendo la del archivo.
- **La prueba de la recuperación cuenta a todos los escenarios con fuentes de la base**, como se pidió, y también, aparte, a los que responden con fragmentos.
- **La consulta de búsqueda no tiene prueba de calidad propia.** La miden la tasa de aciertos y las corridas.

## Cambios frente al documento de grado

Se actualizó `docs/cambios_para_documento.md`:

- la consulta de búsqueda, como extensión de la sección 3.3;
- los textos derogados de la segmentación (5.2);
- la nueva escala de la similitud;
- la fuente de cada cifra.
