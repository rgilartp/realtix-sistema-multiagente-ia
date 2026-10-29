# Verificación de las reglas por código, ronda 2 (repetición única): análisis

Con el código congelado de los PR #72 y #73 y la regla fijada antes de correr
(`../verif-fechas-por-codigo/regla_ronda3.md`). La ronda 1 está en `ronda1/`.

**Resultado: sin PARADA.**

## Escenarios con el juez (`../verif-reglas-por-codigo-2/`)

**6 de 6 superados**: ICA-03, ICA-07, ICA-08 y MULTI-02 correctas; IPU-04 y MULTI-03 parcialmente
correctas, sin alucinación. MULTI-03, que fallaba en la 2b, la 2c y la ronda 1, ahora pasa. Ninguna
falla nueva. Costo: US$0,32.

| Escenario | Latencia del servidor (ms) | Reescritura |
|---|---|---|
| ICA-03 | 8.734 | no |
| ICA-07 | 8.659 | sí |
| ICA-08 | 5.844 | no |
| IPU-04 | 8.155 | no |
| MULTI-02 | 9.522 | no |
| MULTI-03 | 16.720 | sí |

## Preguntas nuevas (`preguntas_resumen.md`; la verificación automática dio 4 de 6)

| Pregunta | Lectura |
|---|---|
| 2 (U12, anual) | Da la regla correcta con las palabras de la norma («no exceda de 391 UVT… presentan una única declaración anual; también… el régimen preferencial. Quienes superan ese monto declaran por bimestre»), no la de la herramienta; no la invierte. La verificación buscaba «hasta 391 UVT»: limitación |
| 6 («¿Influye el estrato…?») | No llamó `tarifas_predial`: describe las tarifas con los fragmentos y sus citas (Acuerdo 648 de 2016, art. 1; Acuerdo 780 de 2020, art. 3, par. 2; Ley 44 de 1990, art. 4). Tiene fuente: no es una descripción sin fuente |

- (d) Ninguna inversión de la regla de los 391 UVT; (e) ninguna descripción de tarifas sin fuente.
- Respuestas que no llamaron la herramienta esperada y acertaron: **1 de 6** (la 6).
- **Para Rodolfo (no es de este PR):** la pregunta 6 cita el Decreto 352 de 2002, cap. I, art. 26
  («sistema preferencial… en salarios mínimos diarios»), un texto de 2002 que la base trata como
  vigente porque `knowledge_base/vigencias.yaml` no tiene regla para él (sí la tiene el art. 25). Es
  un caso parecido al del art. 55 del capítulo II.
- Reescrituras: 3 de 6. Latencias del servidor: 12.649, 6.083, 9.531, 8.657, 8.330 y 10.926 ms.
- Costo: US$0,06.
