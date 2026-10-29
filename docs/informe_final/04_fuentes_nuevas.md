# Fuentes para la bibliografía (borrador)

Las fuentes que usa el sistema multiagente de IA se separan en dos grupos: las que el documento de
grado ya cita (con su número, según `docs/06_ADENDA_MARCO_JURIDICO_Y_PRUEBAS.md`) y las nuevas, que
hay que agregar a la bibliografía. Los enlaces salen de `knowledge_base/*/fuentes.yaml` y de
`datos/*.yaml`.

## Normas ya citadas en el documento de grado

| Norma | Cita | Enlace |
|---|---|---|
| Ley 1581 de 2012 | [104] | http://www.secretariasenado.gov.co/senado/basedoc/ley_1581_2012.html |
| Decreto 1074 de 2015, caps. 25 y 26 | [106] | https://normativa.colpensiones.gov.co/colpens/docs/decreto_1074_2015.htm |
| Resolución SDH-000195 de 2025 | [113] | https://www.alcaldiabogota.gov.co/sisjur/normas/Norma1.jsp?i=191813&dt=S |
| Acuerdo 1084 de 2026 | [114] | https://www.alcaldiabogota.gov.co/sisjur/normas/Norma1.jsp?i=194513 |
| Acuerdo 648 de 2016 y Decreto 474 de 2016 | [109] | https://www.alcaldiabogota.gov.co/sisjur/normas/Norma1.jsp?i=67557&dt=S y https://www.alcaldiabogota.gov.co/sisjur/normas/Norma1.jsp?i=67262&dt=S |
| Decreto Distrital 352 de 2002 | [111] | https://cancilleria.gov.co/sites/default/files/Normograma/docs/d_alcabog_0352_2002.htm |
| Decreto Distrital 807 de 1993 | [110] | https://www.alcaldiabogota.gov.co/sisjur/normas/Norma1.jsp?i=1637 |
| Decreto Ley 1421 de 1993 | [108] | http://www.secretariasenado.gov.co/senado/basedoc/decreto_1421_1993.html |
| Ley 2294 de 2023, art. 49 | [21] | https://cancilleria.gov.co/sites/default/files/Normograma/docs/ley_2294_2023.htm |
| Ley 1995 de 2019 | [112] | https://www.igac.gov.co/sites/default/files/transparencia/normograma/ley_1995_de_2019.pdf |
| Ley 1819 de 2016, arts. 342, 345 y 354 | [44] | http://www.secretariasenado.gov.co/senado/basedoc/ley_1819_2016_pr007.html |
| Ley 44 de 1990 | [14] | https://normativa.colpensiones.gov.co/colpens/docs/ley_0044_1990.htm |
| Ley 14 de 1983 | [45] | https://www.alcaldiabogota.gov.co/sisjur/normas/Norma1.jsp?i=267 |

## Normas nuevas

Cargadas en la base de conocimiento o usadas en `datos/` (tarifas, plazos, UVT y SMMLV, ADR-06).

| Norma | Uso | Enlace |
|---|---|---|
| Resolución SDH-000194 de 2025 (rangos del predial de 2026) | Base de conocimiento y `datos/tarifas/` | https://incp.org.co/wp-content/uploads/2025/12/Resolucion-000194-de-2025-SDH.pdf |
| Acuerdo 1019 de 2025, art. 44 | Base de conocimiento y `datos/` | https://www.alcaldiabogota.gov.co/sisjur/normas/Norma1.jsp?i=191818 |
| Acuerdo 816 de 2021, art. 4 | Base de conocimiento | https://www.alcaldiabogota.gov.co/sisjur/normas/Norma1.jsp?i=116160&dt=S |
| Acuerdo 780 de 2020, arts. 3, 6 y 7 | Base de conocimiento y `datos/tarifas/` (ADR-20) | https://www.alcaldiabogota.gov.co/sisjur/normas/Norma1.jsp?i=100965 |
| Acuerdo 105 de 2003, art. 2 | Base de conocimiento y `datos/tarifas/` | https://www.alcaldiabogota.gov.co/sisjur/normas/Norma1.jsp?i=11030 |
| Acuerdo 98 de 2003 | Base de conocimiento y `datos/tarifas/` | https://www.alcaldiabogota.gov.co/sisjur/normas/Norma1.jsp?i=10597 |
| Acuerdo 65 de 2002, art. 3 | Base de conocimiento y `datos/tarifas/` | https://www.alcaldiabogota.gov.co/sisjur/normas/Norma1.jsp?i=5156 |
| Resolución SDH-000265 de 2021, art. 1 | Base de conocimiento | https://compilacionjuridica.shd.gov.co/compilacion/docs/resolucion_sdh_0265_2021.htm |
| Decreto 639 de 2025 (Decreto Único Distrital Tributario) | Base de conocimiento | https://compilacionjuridica.shd.gov.co/compilacion/docs/d_alcabog_0639_2025.htm |
| Resolución DIAN 000193 de 2024 (UVT de 2025) | `datos/uvt_smmlv.yaml` | https://normograma.dian.gov.co/dian/compilacion/docs/resolucion_dian_0193_2024.htm |
| Resolución DIAN 000238 de 2025 (UVT de 2026) | `datos/uvt_smmlv.yaml` | https://normograma.dian.gov.co/dian/compilacion/docs/resolucion_dian_0238_2025.htm |
| Decreto 1572 de 2024 (SMMLV de 2025) | `datos/uvt_smmlv.yaml` | https://normativa.colpensiones.gov.co/compilacion/docs/decreto_1572_2024.htm |
| Decreto 1469 de 2025 (SMMLV de 2026) | `datos/uvt_smmlv.yaml` | https://normativa.colpensiones.gov.co/compilacion/docs/decreto_1469_2025.htm |

**PENDIENTE (verificar):** el chat de documentos confirma, contra la bibliografía completa, que
ninguna de las «nuevas» esté ya citada con otro número.

## Métodos y herramientas

Ya citados en el documento de grado (según la adenda):

- Cemri y colaboradores, taxonomía MAST de fallas de sistemas multiagente [99] (análisis de fallas,
  sección 6.6).
- Bahçeci y colaboradores [64] (referencia de comparación de RAGAS y latencia, sección 6.5).
- ISTQB, programa Certified Tester Foundation Level v4.0.1 [46] (estructura del plan de pruebas).
- La advertencia de Powers sobre la exactitud frente al azar [47] (métricas).
- RAGAS [103] (métricas de recuperación y generación; versión 0.4.3).
- ISO/IEC 25010 (atributos no funcionales; la adenda la nombra sin número: **PENDIENTE (verificar)**
  su número en la bibliografía).

Nuevos o sin número en la adenda. **PENDIENTE (verificar):** los datos bibliográficos completos
(autores, año, título y lugar de publicación) se toman de las fuentes originales; este borrador no
los inventa.

- Intervalo de Wilson y kappa de Cohen (métricas).
- System Usability Scale (SUS) y heurísticas de Nielsen (usabilidad, ADR-21).
- Fusión por rango recíproco (RRF) y BM25 (recuperación híbrida, ADR-04).
- PABAK (kappa ajustado por prevalencia y sesgo; calibración del juez, sección 5.9).
- Intervalo por bootstrap (tasa de la meta, sección 5.8).
- pass@k y pass^k (consistencia entre ensayos, sección 5.8).
