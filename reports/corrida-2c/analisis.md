# Corrida 2c: análisis (ensayo general antes de la corrida 3)

Un ensayo de los 60 escenarios, más R3 y R4, sin R1 ni RAGAS, contra el despliegue `b52b8a8` con el
modo de evaluación encendido solo durante la corrida (se apagó al terminar y se comprobó desde
afuera). Juez v3 con la misma huella de la calibración (`afecd5c1…`, `--exigir-huella`).

## Regla fijada antes de ver el resultado

Con 52 o más de 60 y ninguna falla nueva causada por los cambios de esta ronda, el despliegue queda
como está; si no, PARADA con el análisis de cada falla, sin corregir nada y sin tocar ninguna
referencia. **Resultado: 50 de 60, por debajo de 52: PARADA.**

## Cifras

| Medida | Valor |
|---|---|
| Principal, tasa de la meta | 83,3 % (50 de 60; Wilson de 72,0 % a 90,7 %) |
| Principal, tasa estricta | 75,0 % (45 de 60) |
| Veredictos del juez (principal) | 45 correctas, 12 parcialmente correctas, 3 incorrectas |
| Respuestas con alucinación | 6 de 60 en el principal; 1 de 3 en R3 |
| R3 y R4 | 2 de 3 y 2 de 2 |
| Errores técnicos | 0 |
| Latencia del servidor, sin fragmentos (18 turnos) | p50 de 2.576 ms y p95 de 4.585 ms; 18 de 18 bajo 8 s |
| Latencia del servidor, con RAG (40 turnos) | p50 de 6.475 ms y p95 de 12.197 ms; 40 de 40 bajo 15 s |
| Trazas (RNF-05) | 1.284 ejecuciones revisadas, 0 con identificadores |
| Costo | US$2,63 (sistema 0,59; juez 2,04) |

## Cada no superado

«Cambio de esta ronda» se refiere a lo fusionado antes de la corrida: las referencias corregidas
(#67), los textos del sistema y la vigencia del art. 55 (#68), las fechas relativas (#50) y la
auditoría de seguridad (#69). Ninguna falla se debe solo a una referencia más exigente: las que el
juez dio como parcialmente correctas sin alucinación fallaron por una verificación de código que no
cambió.

| Escenario | 2 | 2b | Causa | ¿Cambio de esta ronda? |
|---|---|---|---|---|
| AIA-01 | pasó | pasó | Generación: la respuesta del agente general menciona el botón «Hablar con un funcionario» y el glosario, y el juez no los encontró en los fragmentos (los mismos de la 2b) | No: el agente general y su prompt no cambiaron (la regla del botón es de la segunda ronda, #51) |
| GEN-02 | falló | falló | Enrutamiento y escalamiento: transfiere a un funcionario en lugar de responder que el asistente no presenta declaraciones ni hace pagos | No: falla desde la corrida 2 |
| ICA-02 | falló | pasó | Generación: no dice «bimestre» (verificación de código); el juez la da como parcialmente correcta, sin alucinación | No: los fragmentos son casi los mismos de la 2b y falló igual en la corrida 2 |
| IPU-04 | falló | falló | Recuperación y generación: no da el rango de tarifas y atribuye a los fragmentos una clasificación por destino | No: falla desde la corrida 2 |
| IPU-07 | pasó | pasó | Generación: afirma sin fuente que el saldo «está vencido y se pueden causar intereses de mora»; la respuesta se apoya en los plazos vencidos | Posible (#50): pasó en las corridas 2 y 2b y en la verificación de #50; la frase sobre los plazos vencidos es más insistente que en la 2b, pero no se puede atribuir con un solo ensayo |
| IPU-08 | pasó | falló | Generación: no advierte que el plazo general ya venció (lo que la respuesta no debe hacer) | No: ya falló en la 2b, antes de los cambios de esta ronda |
| IPU-13 | falló | pasó | Recuperación: no llegó el art. 4 de la Resolución SDH-000195 de 2025 y la respuesta no dice «30 de abril» (verificación de código); el juez la da como parcialmente correcta, sin alucinación | No: la colección del predial no cambió (la reingesta no tocó `normativa_ipu`) y falló igual en la corrida 2 |
| IPU-14 | falló | falló | Generación: niega el alivio de intereses del Acuerdo 1084 de 2026 y menciona un predio que no está en las fuentes | No: falla desde la corrida 2 |
| MULTI-02 | pasó | pasó | Generación: atribuye la fecha anual del ICA a quienes superan 391 UVT y afirma sin fuente que «no se puede pagar»; además da «hace 167 días» y «hace 83 días» sin que se los pidan | **Probable (#50):** el mismo error de los 391 UVT apareció en la verificación de #50 y no en las corridas 2 ni 2b |
| MULTI-03 | pasó | falló | Generación: afirma sin fuente que lo paga solo el propietario; la referencia corregida (#67) pide además la fusión de impuestos y el autoavalúo | No: ya falló en la 2b; la falla es por la alucinación, no por la referencia |
| CAD-02 (R3) | pasó | pasó | Generación y recuperación: atribuye la declaración anual del régimen preferencial al «parágrafo 2 del art. 3 del Acuerdo 1019 de 2025»; los fragmentos difieren de la 2b (sin el art. 1 de la Resolución SDH-000195 y con un segundo fragmento del art. 26 del Acuerdo 1084) | Posible (#68): la vigencia del art. 55 del Decreto 352 cambia los candidatos de la búsqueda del ICA, aunque el art. 55 no estaba entre los 5 fragmentos de la 2b; no se puede comprobar sin una prueba controlada |

Resumen: 11 no superados (10 del principal y 1 de R3). Frente a la corrida 2b, pasaron a fallar AIA-01,
ICA-02, IPU-07, IPU-13, MULTI-02 y CAD-02, y pasaron a superarse GEN-03, ICA-03 e ICA-08 (ICA-07 e
IPU-09, que fallaron en la corrida 2, también se superan). Con un solo ensayo, parte de esa diferencia
es variación (ICA-02 e IPU-13 ya fallaron en la corrida 2). Una falla es probablemente de un
cambio de esta ronda (MULTI-02, por #50) y dos son posibles (IPU-07, por #50; CAD-02, por #68).

## Trazas de los escenarios con recibo (imagen y nombres)

Revisión aparte de todas las trazas de OCR-01 a OCR-07 y CAD-03 en LangSmith, leyendo cada ejecución
completa (entradas, salidas, metadatos y adjuntos), dentro del backend desplegado y sin copiar
contenido:

| Escenario | Trazas | Ejecuciones | Adjuntos | «[IMAGEN]» | Base64 | `data:image` | Nombre declarado | Identificador de prueba |
|---|---|---|---|---|---|---|---|---|
| CAD-03 | 3 | 45 | 0 | 1 | 0 | 0 | 0 | 0 |
| OCR-01 | 1 | 18 | 0 | 1 | 0 | 0 | 0 | 0 |
| OCR-02 | 1 | 18 | 0 | 1 | 0 | 0 | 0 | 0 |
| OCR-03 | 1 | 18 | 0 | 1 | 0 | 0 | 0 | 0 |
| OCR-04 | 1 | 18 | 0 | 1 | 0 | 0 | 0 | 0 |
| OCR-05 | 1 | 18 | 0 | 1 | 0 | 0 | 0 | 0 |
| OCR-06 | 1 | 18 | 0 | 1 | 0 | 0 | 0 | 0 |
| OCR-07 | 2 | 25 | 0 | 1 | 0 | 0 | 0 | 0 |

En cada escenario, la imagen del recibo aparece como «[IMAGEN]» en la ejecución del modelo de visión,
y en ninguna de las 178 ejecuciones hay una imagen en base64 (tampoco las cabeceras de PNG, JPEG o
PDF en base64), una URL de datos de imagen ni un nombre declarado sin enmascarar.
