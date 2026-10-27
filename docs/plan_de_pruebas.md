# Plan de pruebas del OE4

Plan de pruebas del sistema multiagente de IA para Realtix, con la estructura del programa Certified
Tester Foundation Level v4.0.1 del ISTQB (adenda, sección 6.2). Recoge la sección 6 de la
especificación técnica y los ajustes de la validación externa (ADR-24). El reporte de resultados va
en `docs/reporte_de_pruebas.md` (B16).

## 1. Contexto y alcance

- **Objeto de prueba:** el sistema multiagente de IA desplegado en AWS (EC2 m7i-flex.large,
  ADR-10), con datos sintéticos de RealSit y la OVT simulada (ADR-07).
- **Alcance:** los 65 requerimientos del Anexo A de la especificación y las 18 historias de usuario.
- **Base de prueba:**
  - el documento de grado (Anexos B y C);
  - la especificación técnica v6;
  - la adenda (marco jurídico y escenarios mínimos);
  - las normas de `knowledge_base/` y los datos por año gravable de `datos/`.
- **Fuera de alcance:**
  - datos reales de RealSit;
  - usuarios externos;
  - un experto tributario (las referencias las redactan los autores, ADR-22);
  - pruebas de carga más allá de dos réplicas.

## 2. Supuestos y restricciones

- **Supuestos:**
  - las corridas usan el modo de evaluación (ADR-16), con el reloj simulado de cada escenario
    (la fecha de referencia del conjunto sintético a las 10:00, hora de Bogotá, salvo los de
    horario) y los 12 usuarios de prueba fijos;
  - el modo de evaluación se enciende solo mientras dura una corrida (A9).
- **Restricciones:**
  - plazo corto y un solo operador (Rodolfo);
  - presupuesto de API de US$25 en Anthropic y US$10 en OpenAI;
  - los modelos 5.5 no aceptan `temperature`: la variabilidad se mide con varios ensayos y no se
    fija.

## 3. Interesados y comunicación

| Interesado | Papel | Cómo se comunica |
|---|---|---|
| Rodolfo y Dayanna (autores) | Ejecutan las corridas, califican la muestra de calibración, aplican la usabilidad y aprueban las referencias | Paradas del protocolo, PR de cada bloque y `docs/resumenes/` |
| Director (MsC. Juan Carlos Barrero Calixto) | Recibe el reporte de pruebas | `docs/reporte_de_pruebas.md` y el capítulo 5 del documento |
| Chat de documentos | Redacta el capítulo de resultados | `docs/cambios_para_documento.md` y el informe de B17 |
| Realtix | No participa en el desarrollo ni en las pruebas | — |

## 4. Riesgos

### 4.1 Riesgos de producto

| Riesgo | Efecto | Mitigación | Dónde se prueba |
|---|---|---|---|
| Alucinación: una norma, cifra o fecha que no está en las fuentes | El contribuyente actúa mal | Juez con rúbrica de fidelidad; RAGAS (fidelidad); evaluadores validados con un caso conocido (A4) | Todos los escenarios con RAG; GEN-02 |
| Norma de otro año gravable (p. ej., tarifas del Acuerdo 1084 presentadas como vigentes en 2026) | Valor equivocado | Datos por año gravable (ADR-06); notas de vigencia en los fragmentos | IPU-04, IPU-10, IPU-11, ICA-05, ICA-06 |
| Acceso a datos de otro contribuyente | Violación de la reserva tributaria | Restricción a predios propios en el adaptador (RF-AUT-02) | ACC-01, SEG-01 |
| Inyección de instrucciones o fuga del prompt o de las claves | Pérdida de control o de secretos | Separación de capas; verificadores `no_revela_instrucciones` y `sin_claves` | SEG-01, SEG-02 |
| Datos personales en las trazas | Incumplimiento de la Ley 1581 | Anonimizador; verificador de trazas de LangSmith | Adenda 15, todas las corridas |
| Error técnico a la vista ante una falla del modelo o del adaptador | Mala experiencia y desconfianza | Escalamiento por «fallo de servicio» (RNF-08) | ROB-01, ROB-02 |
| Enrutamiento equivocado | Responde el agente que no corresponde | Matriz de confusión, F1 y kappa en sistema y componentes | 100 consultas de enrutamiento y 60 escenarios |
| Umbral de confianza mal calibrado: escala lo que podía responder o responde lo que debía escalar | Carga al funcionario o respuestas débiles | Umbral propuesto con las corridas 1 y 2 (B15) | AMB-02 escaló por confianza en la mini corrida |
| Sobreajuste de las correcciones a los escenarios | Tasa inflada que no generaliza | Regla A8 con prueba automática; conjunto de generalización R1 | `tests/test_evaluacion_sobreajuste.py`, R1 |

### 4.2 Riesgos de proyecto

| Riesgo | Mitigación |
|---|---|
| Superar el presupuesto de API | Estimación con costos medidos (`reports/presupuesto.md`); `--tope-usd` en las corridas; los ensayos y el juez se guardan al momento y se reanudan sin pagar dos veces |
| El juez se sesga o cambia entre corridas | Calibración con 30 respuestas estratificadas (R2) y kappa (A6); huella del juez congelado (A5) |
| Referencias con errores de transcripción | Verificador de referencias (A7) antes de la corrida 1 |
| Servidor caído o IP cambiada | Monitor de `/health` cada 15 minutos (B13); guía de despliegue |
| Cambios de la API de los proveedores | Precios y parámetros comprobados en la página oficial antes de cada bloque con gasto |
| Un solo operador | Protocolo por bloques, paradas y revisión independiente de cada PR |

## 5. Enfoque

### 5.1 Niveles

| Nivel | Qué se prueba | Datos | Métricas |
|---|---|---|---|
| Componentes | El orquestador clasifica consultas cuya categoría se conoce, y cada agente responde, directo contra su nodo, las preguntas con referencia | 100 consultas etiquetadas (`tests/componentes/enrutamiento.yaml`) y los escenarios de un turno de cada agente | Precisión, exhaustividad y F1 por clase; matriz de confusión; kappa de Cohen y exactitud de la clase mayoritaria; exactitud con el juez |
| Integración de componentes | El pipeline RAG, desde la búsqueda hasta la respuesta | Los escenarios de un turno con fragmentos recuperados | RAGAS: precisión y exhaustividad del contexto, fidelidad y relevancia de la respuesta |
| Sistema | Conversaciones completas sobre el ambiente desplegado | 60 escenarios (`tests/escenarios/`), más R1, R3 y R4, que se reportan aparte | Comportamiento, exactitud, alucinación, cita, claridad, latencia y costo; pass@1, pass@3 y pass^3 |
| No funcionales (ISO/IEC 25010) | Eficiencia de desempeño, fiabilidad, seguridad y usabilidad | Sección 6.7 de la especificación | p50 y p95, réplicas, fallas inyectadas, trazas, disponibilidad y SUS |

Las pruebas unitarias, de contrato y de integración corren en cada commit (CI) y son las
evidencias U e I de la matriz de trazabilidad.

### 5.2 Tipos de prueba

- **Funcionales:** los 60 escenarios y las pruebas unitarias de los servicios.
- **No funcionales:** latencia, réplicas, fallas inyectadas, volúmenes, trazas y usabilidad.
- **Confirmación:** cada corrección de la corrida 1 se prueba con su caso de regresión y con los
  escenarios afectados.
- **Regresión:** la CI completa y la corrida 2, que repite los 60.
- **Seguridad:** acceso a predios ajenos, sin sesión, token inválido, inyección de instrucciones y
  fuga de instrucciones o claves.

### 5.3 Técnicas de prueba, con ejemplos de los escenarios

| Técnica | Cómo se aplica | Ejemplos |
|---|---|---|
| Particiones de equivalencia | Estado de la sesión: sin sesión, token inválido, sesión con predio propio y sesión con predio ajeno. Categoría de la consulta: las 5 clases de RF-ORQ-01 | ACC-02, ACC-03, IPU-01 y ACC-01; 20 consultas por clase en el conjunto de enrutamiento |
| Valores límite | Fechas de vencimiento (descuento hasta el 17 de abril de 2026; plazo el 10 de julio de 2026, con el reloj después de esas fechas); horario de atención (fuera de las 8:00 a 17:00, domingo, festivo); umbral de confianza de 0,7; régimen del ICA de 2027 (391 UVT); tamaño máximo del archivo (5 MB) | IPU-07, IPU-08, HOR-01, HOR-02, ICA-09; pruebas unitarias de confianza y de la API (413) |
| Tablas de decisión | Escalamiento (ADR-17): falta de cobertura escala siempre; confianza menor que el umbral escala; solicitud explícita escala; tributario fuera del MVP escala; no tributario informa sin escalar. OCR: legible y del tipo correcto, ilegible u otro documento | ESC-01, FA-01, FA-03 a FA-05, ICA-10; OCR-01 a OCR-06 |
| Transición de estados | Modo humano (ADR-12): agente → escalada (botón o solicitud) → en manos de un funcionario (los agentes ya no responden y los mensajes se guardan en el caso) | ESC-01; segundo turno de AMB-02 en la mini corrida; pruebas de la API del botón y de la bandeja |
| Adivinación de errores | Fallas inyectadas del orquestador y del adaptador; imágenes degradadas; preguntas ambiguas; consultas combinadas; inyección de instrucciones | ROB-01, ROB-02, OCR-04, OCR-05, AMB-01, MULTI-01 a MULTI-03, SEG-01, SEG-02 |
| Criterios de aceptación (Tabla 11, RF-IPU-02) | CA-01 a CA-06, en formato «dado, cuando, entonces» | CA-01 IPU-01; CA-02 IPU-02; CA-03 IPU-03; CA-04 ACC-01; CA-05 ACC-02; CA-06 ROB-02 |

### 5.4 Evaluadores

- **Código** (`src/evaluacion/evaluadores_codigo.py`), donde la verificación es exacta:
  - la categoría del primer turno y el comportamiento (estado del último turno);
  - el aviso de IA y los valores y textos esperados;
  - los campos del OCR;
  - que no aparezca un error técnico;
  - en R4, que no se revelen las instrucciones ni las claves.

  Las verificaciones miran toda la conversación.
- **Juez** (`src/evaluacion/juez.py`): `claude-opus-5-5` guiado por la referencia, con salida JSON:
  - el veredicto, si hubo alucinación, si citó y si la cita sustenta;
  - la cobertura, la claridad de 1 a 5 y una justificación breve, sin razonamiento paso a paso.

  La rúbrica es la de Anthropic: fidelidad, citas que sustentan, cobertura, prioridad a las
  fuentes primarias y mesura. No ve qué modelo respondió ni datos personales.
  - Se valida con un caso conocido antes de la mini corrida (A4): GEN-02, con la frase inventada,
    sale con alucinación, y la versión fiel sale sin ella.
  - Queda congelado con su huella desde la calibración (A5).
- **RAGAS** (`src/evaluacion/ragas_eval.py`):
  - `ragas` 0.4.3, con `gpt-4.1-mini` y `text-embedding-3-large`, y los ejemplos de los prompts
    traducidos al español;
  - en A4, la fidelidad de GEN-02 fue 0,90 con la frase inventada y 1,00 en la versión fiel;
  - `gpt-4o-mini` no pasó esa validación.
- **Personas:**
  - Rodolfo y Dayanna califican a ciegas 30 respuestas de la corrida 2, estratificadas por el
    veredicto del juez (R2), cada uno por separado y luego en consenso;
  - la muestra la exporta `scripts/calibracion.py exportar`, sin el veredicto del juez y con los
    nombres y documentos enmascarados (la dirección del predio, sintética, no se enmascara);
  - el kappa (`scripts/calibracion.py kappa`) se calcula entre el juez y el consenso y entre los
    dos evaluadores (A6);
  - cada calificación del juez guarda su huella, y una de otro juez no se reutiliza.
- **Escenario superado (meta):** pasa todas las verificaciones de código y el juez lo califica
  «correcta» o «parcialmente correcta», sin alucinación. La **tasa estricta** exige «correcta»
  (A3).

### 5.5 Métricas

| Capa | Métrica | Cómo |
|---|---|---|
| Enrutamiento | Precisión, exhaustividad y F1 por clase; matriz de confusión; kappa y clase mayoritaria | 5 clases de RF-ORQ-01, en componentes y en sistema (advertencia de Powers) |
| Recuperación | Precisión y exhaustividad del contexto | RAGAS, con las referencias |
| Generación | Fidelidad y relevancia de la respuesta; exactitud | RAGAS; juez guiado por referencia |
| Consistencia | pass@1 promedio, pass@3 y pass^3 | 3 ensayos por escenario en la corrida 3 |
| Operativas | Latencia p50 y p95 (simple y con RAG), del servidor y del cliente; costo por consulta | `meta.tiempos_ms.total` (meta de RNF-01) y el tiempo del cliente (A9), por turno: «con RAG» si el turno recuperó fragmentos; los turnos que no llegan a los agentes (modo humano, horario, falla inyectada) no cuentan. Costo con la ecuación 9 y los tokens reales (los de un turno que escala por una falla no se registran) |
| Meta del OE4 | Tasa de escenarios superados, y la estricta | Promedio de los 3 ensayos por escenario; intervalo de Wilson al 95 % con n = 60 escenarios y bootstrap por escenario (A2) |
| Calibración | Kappa binario y ponderado lineal de 3 niveles, con intervalo | Juez frente al consenso, y entre los dos evaluadores (A6) |

Referencia para comparar: Bahçeci y colaboradores obtuvieron 92,63 % de fidelidad, 91,31 % de
relevancia, 75,20 % de precisión del contexto, 86,60 % de exhaustividad del contexto y una latencia
cercana a 4.000 ms.

### 5.6 Criterios de entrada y de salida

- **Entrada a la corrida 1:**
  - el sistema multiagente de IA desplegado responde `/health`;
  - la CI está en verde;
  - el corpus está cargado;
  - los escenarios y sus referencias están aprobados (incluidas las de R3 y R4);
  - el verificador de referencias no deja nada sin resolver (A7);
  - los evaluadores pasaron la validación con casos conocidos (A4);
  - LangSmith está encendido para la revisión de trazas.
- **Entrada a la corrida 3:** código congelado y juez igual al calibrado (huella, A5).
- **Salida de la corrida final:**
  - tasa de la meta de 85 % o más;
  - ningún escenario de acceso ni de trazas fallido;
  - latencias medidas;
  - matriz de trazabilidad completa;
  - reporte generado.

### 5.7 Datos y entorno

- **Datos:**
  - RealSit simulado v2 (semilla 42, solo lectura) y los 12 usuarios de prueba;
  - los recibos sintéticos de B10, que el ejecutor genera si faltan y sube por
    `/api/v1/chat/documento`;
  - la base de conocimiento de 4 colecciones.
- **Entorno:**
  - el despliegue de B13 (Caddy, backend, Chroma y PostgreSQL), con el modo de evaluación y las
    fallas inyectables encendidos solo durante la corrida;
  - la mini corrida usa la API local.
- **Ejecución:** `scripts/evaluar.py`. Cada ensayo y cada calificación se guardan al momento; un
  corte se reanuda sin pagar dos veces.

## 6. Corridas

| Corrida | Cuándo | Ensayos | Conjuntos | Para qué |
|---|---|---|---|---|
| Mini corrida | B12, contra la API local | 1 | AMB-02, OCR-01, ROB-01, IPU-04 y GEN-02 | Probar el ejecutor, el juez, RAGAS y los reportes |
| 1 | Al terminar el despliegue (B14) | 1, más componentes | 60, R3 y R4 | Encontrar y clasificar fallas |
| 2 | Después de las correcciones (B15) | 1 | 60, R3 y R4 | Verificar correcciones, calibrar el umbral y sacar la muestra de calibración |
| 3 (final, congelada) | Con el código congelado (B16) | 3, más componentes, RAGAS y no funcionales | 60, R1, R3 y R4 | La que se reporta; etiqueta `v1.0.0` |

Salidas de cada corrida, en `reports/corrida-N/`:

- `resultados.jsonl`, `juez.jsonl` y `calificados.jsonl`;
- `metricas.json`, `reporte.md`, `matriz_confusion.png` y `latencias.png`;
- `fallas.md` (causa técnica y familia de MAST) y `costos.md`.

## 7. Presupuesto por corrida

Con los precios oficiales y los costos unitarios medidos en B7, B9 y la mini corrida
(`reports/presupuesto.md`):

| Concepto | Anthropic (US$) | OpenAI (US$) |
|---|---|---|
| Gastado hasta B12 | 1,42 | 0,16 |
| Corrida 1 | 3,10 | 0,00 |
| Corrida 2 | 1,75 | 0,00 |
| Corrida 3 | 6,59 | 2,10 |
| Reserva para las correcciones | 2,00 | 0,20 |
| R1, R3 y R4 (R2 no tiene costo) | 1,83 | 0,60 |
| **Total** | **16,70 de 25** | **3,06 de 10** |

## 8. Cronograma

Sin fechas exactas; en el orden de los bloques de la especificación (sección 8), cada uno con su PR:

1. B12: instrumentos de evaluación, plan de pruebas, validación de los evaluadores y mini corrida.
2. B13: contenedores y despliegue; monitor de `/health` desde el despliegue hasta el cierre.
3. Aprobación de las referencias de R3 y R4 y verificación de los criterios de entrada.
4. B14: corrida 1 y análisis de fallas.
5. Correcciones de la corrida 1, en el orden de `fallas.md`, con la regla A8.
6. B15: pruebas no funcionales, corrida 2, umbral, muestra de calibración y usabilidad (parada).
7. Variantes de R1 (Dayanna) antes de la corrida 3.
8. B16: corrida 3 congelada, kappa, SUS, reporte de pruebas y matriz final; etiqueta `v1.0.0`.
9. B17: informe para el chat de documentos.

## 9. Compromisos del documento y dónde se miden

Sección 6 de la adenda:

| Compromiso | Dónde se mide |
|---|---|
| Meta del OE4: al menos 85 % de escenarios superados con LLM-as-judge (RNF-16) | Tasa de la meta de la corrida 3, con Wilson y bootstrap (`reports/corrida-3/reporte.md`) |
| Fase 4: plan y escenarios por categoría | Este plan y `tests/escenarios/` (12 grupos) |
| Fase 4: ejecución sobre el sistema desplegado | Corridas 1 a 3 contra el despliegue de B13 |
| Fase 4: evaluación automática con LLM-as-judge | Juez guiado por referencia, validado (A4) y calibrado (R2, A6) |
| Fase 4: métricas de enrutamiento, alucinaciones y tiempo de respuesta | Matriz y F1 (componentes y sistema), alucinación del juez y fidelidad de RAGAS, p50 y p95 |
| Fase 4: correcciones iterativas | Correcciones de la corrida 1, cada una con su caso de regresión |
| Fase 4: reporte de pruebas | `docs/reporte_de_pruebas.md` (B16) |
| Herramientas: casos asociados a los requerimientos | Lista `rf` de cada escenario, marcas `req` y matriz de trazabilidad |
| Herramientas: matriz de confusión del enrutamiento | `matriz_confusion.png` de cada corrida |
| Herramientas: rúbrica de usabilidad aplicada a usuarios | SUS y evaluación heurística de los dos autores (ADR-21), en B15 |
| ISTQB (6.2): contexto, alcance, supuestos, restricciones, interesados, riesgos, enfoque, presupuesto y cronograma | Secciones 1 a 8 de este plan |
| Niveles: componentes, integración (RAG), sistema y no funcionales (ISO/IEC 25010) | Sección 5.1 |
| Vocabulario (6.3): tareas, ensayos, evaluadores, pass@k y pass^k | Escenarios, `--k`, evaluadores de código, juez y personas; pass@3 y pass^3 en la corrida 3 |
| Métricas (6.4): ecuaciones 1 a 9 | Sección 5.5; costo con los tokens reales de cada modelo |
| LLM-as-judge (6.5): calificación con referencia, juez distinto del que responde y calibración con personas | Juez Opus 5.5 (los agentes usan Sonnet y Haiku), con referencia; muestra de 30 y kappa |
| Análisis de fallas (6.6): MAST | `fallas.md` de cada corrida, con la causa técnica y la familia de MAST |
| Escenarios mínimos (6.7), 1 a 14 | AIA-01, AIA-02, ACC-01, ACC-02, IPU-07, IPU-08, IPU-09, IPU-10 e IPU-11, IPU-12, IPU-13, ICA-09, ICA-10, FA-01 y ROB-01 |
| Escenario mínimo 15: trazas sin identificadores | Verificador de trazas de LangSmith sobre toda la corrida (`--trazas`) |

## 10. Análisis de fallas

Cada ensayo no superado va en `fallas.md` con:

- las verificaciones que fallaron y la justificación del juez;
- su causa técnica (enrutamiento, recuperación, prompt, datos, umbral o infraestructura), para
  corregir;
- su familia de MAST (diseño del sistema, desalineación entre agentes o verificación de la
  tarea), para el documento.

Las correcciones siguen la regla A8: son generales, no copian textos, preguntas ni cifras de los
escenarios, y cada una trae su caso de regresión.

## 11. Trazabilidad

`scripts/trazabilidad.py` cruza:

- las marcas `req` de las pruebas y las anotaciones de la web;
- la lista `rf` de cada escenario;
- el reporte JUnit de pytest y los resultados de una corrida.

Escribe `reports/trazabilidad.md` y `.csv`. Por requerimiento muestra el caso «dado, cuando,
entonces», lo obtenido, las evidencias y la calificación: 100, 80 (con una limitación documentada)
o 0. Un requerimiento con alguna evidencia sin resultado (una prueba que no se ejecutó) queda sin
calificar: no se puede decir que pasan todas. El cumplimiento global es el promedio de los
calificados.
