# Verificación de la curaduría (B2)

Consulta de todas las fuentes: octubre de 2026. Las vistas lado a lado están en
[`docs/verificacion/index.html`](verificacion/index.html). La marca de verificación de cada tabla
la pone Rodolfo con `scripts/curaduria/marcar_verificado.py` después de revisar las vistas.

## Tablas de `datos/`

- [ ] `datos/tarifas/ipu_2026.yaml` — predial 2026: 30 rangos residenciales (art. 1), 6 tarifas no residenciales (art. 2) y 10 rangos de clubes, destino 66 (art. 3) de la Resolución SDH-000194 de 2025. Contraste con el PDF fila por fila: 0 diferencias. Trae también las tarifas preferenciales de 2026 (Acuerdo 648, art. 1; Acuerdo 780, art. 3, parágrafo 2; Decreto 639, art. 207), contrastadas con la tabla del Acuerdo 648. Las demás categorías de 2026 no se transcriben (ver abajo). Vista: `ipu_2026.html`.
- [ ] `datos/tarifas/ipu_2027.yaml` — predial 2027, art. 20 del Acuerdo 1084, con sus reglas. Las preferenciales traen el texto literal de los límites y campos numéricos con la unidad de cada límite. Contraste con el texto digital del Régimen Legal, fila por fila: 5 tablas, 0 diferencias. Vista: `ipu_2027.html`.
- [ ] `datos/tarifas/sobretasa_alumbrado_2027.yaml` — sobretasa de alumbrado, arts. 11 y 13 a 15, con el texto literal de cada categoría y sus reglas. Contraste con el texto digital: 2 tablas, 0 diferencias. Vista: `sobretasa_alumbrado_2027.html`.
- [ ] `datos/tarifas/ica_2026.yaml` — ICA 2026: 486 actividades con tarifa, 10 de ellas por decisión de Rodolfo, más las demás actividades y el SIMPLE de 2026 (verificado con el art. 44 del Acuerdo 1019 de 2025). Armada con el texto original del art. 3 del Acuerdo 65, los Acuerdos 780 (arts. 6 y 7), 816 (art. 4) y 98 y la Resolución SDH-000265 de 2021. Segunda lectura de la resolución con el Registro Distrital 7103: 481 de 486 coinciden y 5 no se pudieron leer. Vista: `ica_2026.html`.
- [ ] `datos/tarifas/ica_2027.yaml` — ICA 2027, art. 21: 447 actividades de tarifa fija y 28 de tarifa progresiva (475 en total), las demás actividades y el ICA consolidado del SIMPLE (art. 24). Texto digital del Régimen Legal: 475 de 475 coinciden en los dos sentidos; el SIMPLE coincide con el texto digital y con la imagen. Vista: `ica_2027.html`.
- [ ] `datos/calendario/2026.yaml` — calendario 2026. Las fechas del ICA bimestral y del SPAC se leyeron de las tablas incrustadas como imagen. Vista: `calendario_2026.html`.
- [ ] `datos/regimenes_ica.yaml` — regímenes del ICA de 2026 y 2027. Vista: `regimenes_y_uvt.html`.
- [ ] `datos/uvt_smmlv.yaml` — UVT y SMMLV de 2025 y 2026, con la resolución de la DIAN y el decreto de cada año; los de 2027 siguen pendientes. Vista: `regimenes_y_uvt.html`.

## El Acuerdo 1084: texto digital y OCR

El Régimen Legal de Bogotá tiene el Acuerdo 1084 en texto (`i=194513`, en vigor desde el 9 de octubre de
2026, Registro Distrital 8679), con sus tablas. `knowledge_base/` sale de ese texto digital, no del OCR.
El PDF escaneado del INCP queda como contraste y como imagen de las vistas. El OCR traía errores que el
agente habría citado (el art. 15 decía «500 UVT» y «1200 UT», los encabezados de cada página quedaban
dentro de los artículos, el símbolo ° salía como `%`, `”` o `?` y las tablas salían revueltas).

| Dónde | El OCR leyó | La imagen y el texto digital dicen | Se usa |
|---|---|---|---|
| Art. 15, límite de los residenciales (página 20) | 500 UVT | 600 UVT | el texto digital |
| Art. 20, exclusión de estratos 1 y 2 (página 22) | inferior a 186 SMMLV | inferior a 16 SMMLV | el texto digital |
| Art. 21, 6 filas (CIIU 2513, 6399, 9603, 35202, 47241, 47924) | otro número | la tarifa transcrita | el texto digital |
| Art. 24, SIMPLE (página 47) | faltaban los numerales 2 y 3 | 10, 14, 29, 30 (sic) y 14 | el texto digital |

En la tabla del art. 21 el OCR no leyó la tarifa de 115 filas ni el código de 147. El texto digital
coincide con las transcripciones de las imágenes en las 475 actividades.

## Predial 2026: lo que no se transcribe

Las demás categorías de 2026 (industrial, financiero, dotacional, rural y otras) tienen tarifa fija del
art. 2 del Acuerdo 105 de 2003 en su texto anterior al Acuerdo 1084 (Acuerdo 648 de 2016, art. 1, y
Acuerdo 897 de 2023, según la nota del Régimen Legal). No se transcriben porque el MVP usa residencial,
comercial y lote.

## ICA de 2026: cómo se armó y las decisiones de Rodolfo

El texto vigente en 2026 sale de estas fuentes, que Rodolfo aprobó en la parada de B2:

1. La tarifa de cada CIIU, de la columna de 2024 de la Resolución SDH-000265 de 2021 (compilación de la
   Secretaría de Hacienda; el PDF de `bogota.gov.co` y el Registro Distrital 7103 traen el mismo texto).
2. Los cambios del art. 6 del Acuerdo 780 de 2020 (columna «2024 y siguientes»).
3. El art. 4 del Acuerdo 816 de 2021: 14 por mil para las actividades financieras (28 filas).
4. El art. 7 del Acuerdo 780 (domicilios por plataformas, 11,04 por mil) y el Acuerdo 98 de 2003
   (edición y publicación de libros: 4,14 por mil si se cumplen las condiciones y 8 si no), derogados por
   el art. 52 del Acuerdo 1084.
5. El art. 44 del Acuerdo 1019 de 2025, también derogado por el art. 52, fijaba el ICA consolidado del
   régimen SIMPLE en 2026 (12, 16, 30 y 16 por mil); queda en una sección aparte del YAML.

**Criterio de la resolución.** La Resolución SDH-000265 de 2021 asigna cada CIIU a un grupo del art. 3 y,
en el grupo 302, a una fila del art. 6 del Acuerdo 780; la tarifa es la que fija el acuerdo vigente para
ese grupo o esa fila. Por eso las 10 actividades de construcción quedan en 6,9 o 7,6 por mil, y 6515 y
6523 van a 14 por mil, como todo el grupo de actividades financieras desde el Acuerdo 816: la resolución
las clasifica en el grupo 401 (literal d, actividades financieras) y trae 11,04 en su columna de 2024, y
el art. 4 del Acuerdo 816, posterior a la resolución, fija 14 por mil para todo ese literal.

Cada tarifa se contrastó con el texto de los acuerdos: las de grupo con el texto original del art. 3
del Acuerdo 65, y las que cambian con el art. 6 del Acuerdo 780. La página del ICA de Hacienda no se
descarga como texto. Diez filas chocaban entre la resolución y el Acuerdo 780, y Rodolfo decidió en la
parada de B2 cuál prevalece:

| CIIU | Choque | Tarifa que se aplica |
|---|---|---|
| 4111, 4112, 4311, 4312, 4321, 4322, 4329, 39002 | El art. 6 del Acuerdo 780 sube a 8,66 a los «servicios prestados por contratistas de construcción, constructores y urbanizadores», y la resolución los deja en 6,9. | 6,9 por mil |
| 4330, 4390 | La resolución da 7,6, pero el art. 6 solo nombra carreteras, proyectos de servicio público y otras obras de ingeniería civil. | 7,6 por mil |

**Decisión de Rodolfo:** prevalece la Resolución SDH-000265 de 2021, art. 1 («clasificación oficial por
CIIU de la Secretaría de Hacienda»). Motivo: es la clasificación con la que Hacienda aplica el art. 6 del
Acuerdo 780, se expidió después de ese acuerdo y no tiene modificaciones ni nulidades; además, el art. 21
del Acuerdo 1084 conserva la misma agrupación para 2027 (7 por mil para edificios, demolición,
preparación del terreno e instalaciones, y 8 para obras civiles, terminación y acabados). Cada una de
las 10 filas lleva la nota para el agente: «El art. 6 del Acuerdo 780 de 2020 nombra a los contratistas
de construcción, constructores y urbanizadores en el grupo que sube a 8,66 por mil; la Secretaría de
Hacienda clasificó esta actividad en la tarifa indicada, que es la que aplica».

El CIIU 4930 trae el grupo «01» truncado en la compilación de Hacienda; por decisión de Rodolfo es el
301, cuya tarifa (4,14 por mil) es la de la fila. Dos CIIU vienen mal escritos en la compilación de
Hacienda y en el Registro Distrital 7103 y se dejaron como 8523 («/ 8523», educación media técnica) y
85232 («85232/8551», educación de formación laboral; corresponde a la clase 8551, que ya está con la
misma tarifa), con una nota sobre cómo aparecen en la fuente. Las «demás actividades» de 2026 son las del
texto original del art. 3: industriales y comerciales 11,04 y servicios 9,66 por mil.

**Periodos.** Esta tabla cubre el año gravable 2026 de los declarantes anuales y los bimestres 1 a 5 de
2026 de los bimestrales. El Acuerdo 1084 se aprobó en plenaria el 28 de septiembre de 2026, se firmó el
8 de octubre de 2026 y entró en vigor el 9 de octubre de 2026, fechas dentro del bimestre 5
(septiembre-octubre). Por eso la tabla del art. 21 (`ica_2027.yaml`) aplica a los bimestrales desde el
bimestre 6 de 2026 (noviembre-diciembre, que se declara a más tardar el 12 de febrero de 2027) y a los
anuales desde el 1 de enero de 2027. Las normas derogadas que fijaban tarifas (Acuerdo 98 de 2003, art. 7
del Acuerdo 780 y art. 44 del Acuerdo 1019) rigen para los periodos de esta tabla; el art. 52 del Acuerdo
1084 las deroga y el art. 21 las reemplaza según su parágrafo. El SIMPLE de 2026 rige todo el año y desde
2027 aplica el art. 24.

Normas derogadas por el art. 52 del Acuerdo 1084 revisadas: solo el Acuerdo 98 de 2003, el art. 7 del
Acuerdo 780 y el art. 44 del Acuerdo 1019 fijaban tarifas del ICA. Las demás tratan de exenciones,
notificaciones, regímenes, predial, publicidad exterior o azar y espectáculos.

## Predial: tarifas preferenciales (RF-IPU-03)

En 2026 siguen vigentes las tarifas preferenciales de los residenciales de estratos 1, 2 y 3 con avalúo de
hasta 135 SMMLV; sin ellas la liquidación de 2026 cobraría de más. Fuentes: Acuerdo 648 de 2016, art. 1
(1 por mil de 16 a 107 SMMLV y 3 por mil de más de 107 a 135 SMMLV en los estratos 1 y 2, y 3 por mil hasta
135 SMMLV en el estrato 3), Acuerdo 780 de 2020, art. 3, parágrafo 2 («Se mantienen las tarifas
preferenciales del 1 y 3 por mil…») y Decreto 639 de 2025, art. 207. Con el SMMLV de 2026 ($1.750.905), 16,
107 y 135 SMMLV son $28.014.480, $187.346.835 y $236.372.175. El límite de 16 SMMLV cambia de un año a
otro: en 2026, «igual o menor» a 16 SMMLV no declara ni paga (Decreto 639, art. 207); en 2027 solo queda
excluido lo «inferior a 16 SMMLV» (Acuerdo 1084, art. 20) y 16 SMMLV exactos pagan 1 por mil. La vista
`ipu_2026.html` muestra la tabla junto al texto de las tres normas.

## Base de conocimiento: limpieza de la segunda ronda

- **Texto ajeno y firmas.** El conversor corta cada artículo en su texto: la Ley 1581 traía unas 660
  líneas de firmas, la Sentencia C-748 de 2011 y el texto del proyecto de ley después del art. 30. En el
  último artículo de cada norma se conservan la fórmula de cierre y la fecha de expedición, pero no los
  nombres y cargos de quienes firman, y se quitan los títulos de la parte siguiente (TÍTULO, CAPÍTULO).
  Prueba: ningún archivo trae «TEXTO CONCILIADO» ni «SENTENCIA C-748», y ningún artículo sin tablas pasa
  de 15.000 caracteres.
- **Caracteres.** Se quitaron los 82 caracteres de formato Unicode (U+200B) y el pie de página de las
  resoluciones de la Secretaría de Hacienda.
- **Tablas.** El conversor expande `rowspan` y `colspan` repitiendo el valor, une las filas de encabezado
  («Base gravable desde», «Base gravable hasta»), parte las tablas por sus filas de subtítulo y quita las
  columnas vacías o repetidas por maquetación. Quedan como excepciones, con su razón, los subtítulos del
  texto original del art. 3 del Acuerdo 65 («b. Actividades Comerciales») y la fila de 5330, donde la
  fuente combina las columnas de 2021 y 2022 (la tarifa de 10,14 es de 2022).
- **Resolución SDH-000265.** Se corrigieron las celdas partidas «1 1,04» (2394, columna 2022, y 2816,
  columna 2024), «6 ,9» (4312, columna 2024) y «,9,66» (85591), se quitó el encabezado repetido en un
  corte de página y el espacio inicial de la fila de 5330.
- **Notas de vigencia.** Los archivos que mezclan años llevan al inicio una nota por año gravable:
  Acuerdos 105 de 2003, 648 de 2016, 780 de 2020, 65 de 2002 y 1084 (ICA) y 1019 de 2025, y una nota en el
  art. 45 del Decreto 639.
- **Erratas de la fuente.** La compilación de Hacienda trae «IGUALO MENOR» y «SMLMV N.» en el art. 207 del
  Decreto 639, «lijado» en los arts. 45 y 205 y «lije» en el art. 205; el Régimen Legal trae «igualo menor»
  en el art. 17 del Decreto 474. Como las fuentes los traen así, se dejan.
- **Artículos fuera de la tabla de la sección 5.** El art. 205 del Decreto 639 (declaración anual del ICA,
  menos de 391 UVT) se copia a `normativa_ica`, y el art. 44 del Acuerdo 1019 de 2025 se carga allí para
  verificar el SIMPLE de 2026.
- **SIMPLE de 2026.** Verificado con el texto del art. 44 del Acuerdo 1019 de 2025 en el Régimen Legal:
  12, 16, 30, 30 (sic) y 16 por mil, fila por fila (`contrastar_1084.py`); ya no depende de una fuente
  secundaria.

## Vistas

Las celdas de números, códigos y fechas no se parten (`white-space:nowrap`), las demás palabras se parten
solo en el límite de la celda (`overflow-wrap:break-word`), la columna se desplaza si la tabla es ancha,
las tarifas llevan coma decimal y las cifras grandes, puntos de miles, los enlaces muestran una etiqueta
corta y los extractos de la fuente salen como tablas HTML. El calendario muestra la imagen completa de la
Resolución SDH-000195 y, al lado, las tablas insertadas en la base de conocimiento.

## Fuentes y de dónde salió cada archivo

| Norma | Colección | Estado | Origen del archivo | Enlace |
|---|---|---|---|---|
| Ley 1581 de 2012 | `normativa_datos` | 30 artículos | Secretaría del Senado (arts. 1 a 30) | http://www.secretariasenado.gov.co/senado/basedoc/ley_1581_2012.html |
| Decreto 1074 de 2015, caps. 25 y 26 | `normativa_datos` | 42 artículos | Colpensiones (normograma) | https://normativa.colpensiones.gov.co/colpens/docs/decreto_1074_2015.htm |
| Ley 44 de 1990 | `normativa_ipu` | 30 artículos | Colpensiones (normograma) | https://normativa.colpensiones.gov.co/colpens/docs/ley_0044_1990.htm |
| Ley 1995 de 2019 | `normativa_ipu` | 7 artículos | IGAC | https://www.igac.gov.co/sites/default/files/transparencia/normograma/ley_1995_de_2019.pdf |
| Ley 2294 de 2023, art. 49 | `normativa_ipu` | 1 artículos | Cancillería (normograma) | https://cancilleria.gov.co/sites/default/files/Normograma/docs/ley_2294_2023.htm |
| Ley 1819 de 2016, art. 354 | `normativa_ipu` | 1 artículos | Secretaría del Senado (parte 7 de la ley) | http://www.secretariasenado.gov.co/senado/basedoc/ley_1819_2016_pr007.html |
| Decreto Ley 1421 de 1993 | `normativa_ipu` | 3 artículos | Secretaría del Senado (cuatro partes) | http://www.secretariasenado.gov.co/senado/basedoc/decreto_1421_1993.html |
| Decreto 474 de 2016 | `normativa_ipu` | 21 artículos | Régimen Legal de Bogotá; texto anterior, no vigente: lo compiló y derogó el Decreto 639 de 2025 | https://www.alcaldiabogota.gov.co/sisjur/normas/Norma1.jsp?i=67262&dt=S |
| Decreto 639 de 2025 (Decreto Único Distrital Tributario), arts. que compilan el Decreto 474 de 2016 | `normativa_ipu` | 21 artículos | Compilación de la Secretaría de Hacienda (arts. que compilan el Decreto 474 y la derogatoria del art. 263) | https://compilacionjuridica.shd.gov.co/compilacion/docs/d_alcabog_0639_2025.htm |
| Acuerdo 648 de 2016 | `normativa_ipu` | 15 artículos | Régimen Legal de Bogotá | https://www.alcaldiabogota.gov.co/sisjur/normas/Norma1.jsp?i=67557&dt=S |
| Decreto Distrital 352 de 2002, cap. I | `normativa_ipu` | 18 artículos | Cancillería (normograma) | https://cancilleria.gov.co/sites/default/files/Normograma/docs/d_alcabog_0352_2002.htm |
| Decreto Distrital 807 de 1993 | `normativa_ipu` | 170 artículos | Régimen Legal de Bogotá, con modificaciones y notas de vigencia | https://www.alcaldiabogota.gov.co/sisjur/normas/Norma1.jsp?i=1637 |
| Acuerdo 105 de 2003, art. 2 | `normativa_ipu` | 1 artículos | Régimen Legal de Bogotá (ya con el art. 20 del Acuerdo 1084) | https://www.alcaldiabogota.gov.co/sisjur/normas/Norma1.jsp?i=11030 |
| Acuerdo 780 de 2020, art. 3 | `normativa_ipu` | 1 artículos | Régimen Legal de Bogotá | https://www.alcaldiabogota.gov.co/sisjur/normas/Norma1.jsp?i=100965 |
| Resolución SDH-000194 de 2025 (rangos del predial de 2026) | `normativa_ipu` | 4 artículos | INCP (PDF, descargado por Rodolfo) | https://incp.org.co/wp-content/uploads/2025/12/Resolucion-000194-de-2025-SDH.pdf |
| Resolución SDH-000195 de 2025 | `normativa_ipu` | 4 artículos | Régimen Legal de Bogotá (guardado por Rodolfo); las cuotas del SPAC, de la imagen | https://www.alcaldiabogota.gov.co/sisjur/normas/Norma1.jsp?i=191813&dt=S |
| Resolución SDH-000195 de 2025 | `normativa_ica` | 2 artículos | Régimen Legal de Bogotá (mismo archivo); las fechas bimestrales, de las imágenes | https://www.alcaldiabogota.gov.co/sisjur/normas/Norma1.jsp?i=191813&dt=S |
| Acuerdo 1084 de 2026 | `normativa_ipu` | 19 artículos | Régimen Legal de Bogotá (texto digital, en vigor desde el 9 de octubre de 2026); el PDF escaneado del INCP queda como contraste | https://www.alcaldiabogota.gov.co/sisjur/normas/Norma1.jsp?i=194513 |
| Acuerdo 1084 de 2026 | `normativa_ica` | 10 artículos | Régimen Legal de Bogotá (mismo texto digital) | https://www.alcaldiabogota.gov.co/sisjur/normas/Norma1.jsp?i=194513 |
| Ley 14 de 1983 | `normativa_ica` | 90 artículos | Régimen Legal de Bogotá, con notas de vigencia; arts. 33 y 36 marcados como texto anterior, no vigente | https://www.alcaldiabogota.gov.co/sisjur/normas/Norma1.jsp?i=267 |
| Decreto Distrital 352 de 2002, cap. II | `normativa_ica` | 29 artículos | Cancillería (normograma) | https://cancilleria.gov.co/sites/default/files/Normograma/docs/d_alcabog_0352_2002.htm |
| Decreto Distrital 807 de 1993 | `normativa_ica` | 170 artículos | Régimen Legal de Bogotá, con modificaciones y notas de vigencia | https://www.alcaldiabogota.gov.co/sisjur/normas/Norma1.jsp?i=1637 |
| Decreto 639 de 2025 (Decreto Único Distrital Tributario), art. 205 | `normativa_ica` | 1 artículos | Compilación de la Secretaría de Hacienda (mismo archivo); fuera de la tabla de la sección 5 | https://compilacionjuridica.shd.gov.co/compilacion/docs/d_alcabog_0639_2025.htm |
| Acuerdo 1019 de 2025, art. 44 | `normativa_ica` | 1 artículos | Régimen Legal de Bogotá; texto anterior, no vigente; fuera de la tabla de la sección 5 | https://www.alcaldiabogota.gov.co/sisjur/normas/Norma1.jsp?i=191818 |
| Acuerdo 65 de 2002, art. 3 | `normativa_ica` | 1 artículos | Régimen Legal de Bogotá (ya con el art. 21 del Acuerdo 1084) | https://www.alcaldiabogota.gov.co/sisjur/normas/Norma1.jsp?i=5156 |
| Acuerdo 780 de 2020, arts. 6 y 7 | `normativa_ica` | 2 artículos | Régimen Legal de Bogotá (mismo archivo); aprobada por Rodolfo en la parada de B2 | https://www.alcaldiabogota.gov.co/sisjur/normas/Norma1.jsp?i=100965 |
| Acuerdo 816 de 2021, art. 4 | `normativa_ica` | 1 artículos | Régimen Legal de Bogotá; aprobada por Rodolfo en la parada de B2 | https://www.alcaldiabogota.gov.co/sisjur/normas/Norma1.jsp?i=116160&dt=S |
| Acuerdo 98 de 2003 | `normativa_ica` | 3 artículos | Régimen Legal de Bogotá; aprobada por Rodolfo en la parada de B2 | https://www.alcaldiabogota.gov.co/sisjur/normas/Norma1.jsp?i=10597 |
| Resolución SDH-000265 de 2021, art. 1 | `normativa_ica` | 1 artículos | Compilación de la Secretaría de Hacienda; aprobada por Rodolfo en la parada de B2 | https://compilacionjuridica.shd.gov.co/compilacion/docs/resolucion_sdh_0265_2021.htm |
| Ley 1819 de 2016, arts. 342 y 345 | `normativa_ica` | 2 artículos | Secretaría del Senado (parte 7 de la ley, la misma del art. 354) | http://www.secretariasenado.gov.co/senado/basedoc/ley_1819_2016_pr007.html |

Además, el Registro Distrital 7103 (`https://www.alcaldiabogota.gov.co/sisjur/normas/verNormaPDF?i=109475`)
y el PDF escaneado del Acuerdo 1084 (`https://incp.org.co/?p=136894`) sirven solo para contrastar y no
van a `knowledge_base/`.

Los archivos descargados quedan en `scripts/curaduria/descargas/`, que git ignora. La conversión a
Markdown y el corte por artículo los hace `scripts/curaduria/convertir.py`: quita enlaces, imágenes y
anclas de javascript, pasa las tablas de datos a Markdown y conserva las notas de vigencia
(«Modificado por…»). Las tablas que la fuente trae como imagen se transcriben (fechas de la
Resolución SDH-000195, arts. 1 y 5) y se marcan «tabla en imagen en la fuente, transcrita».

## Límites de las fuentes y pendientes

1. **Decreto 474 de 2016.** El Régimen Legal lo marca derogado y compilado en el Decreto 639 de 2025
   (Decreto Único Distrital Tributario). Sus 21 artículos quedan como «texto anterior, no vigente» con
   remisión al artículo del 639 que los compila (arts. 217 a 227, 231 a 233, 205 a 207 y 43 a 45), y esos
   artículos y la derogatoria del art. 263 se cargan en `normativa_ipu`.
2. **Otros decretos cargados.** Revisados: el Decreto 807 de 1993 solo trae una referencia «Ver Decreto
   Distrital 639 de 2025» y el Decreto 352 de 2002 no lo menciona; ninguno está derogado ni compilado por
   el 639.
3. **Decreto 807 de 1993.** Es la versión del Régimen Legal, con las modificaciones y las notas de
   vigencia; los arts. 7 y 8 aparecen derogados por el Acuerdo 1084.
4. **Ley 1581 de 2012.** Se cargan los artículos 1 a 30; los «artículos» 31 a 34 del texto de la Secretaría
   del Senado son del proyecto que citan las notas de jurisprudencia.
5. **Ley 14 de 1983.** Texto del Régimen Legal de Bogotá (`i=267`) con sus notas de vigencia, cortado en
   90 artículos. Los arts. 33 (base gravable) y 36 (actividades de servicios) traen la nota «Modificado
   por el art. 342 (345), Ley 1819 de 2016» pero muestran el texto de 1983: quedan marcados como «texto
   anterior, no vigente», con remisión a los arts. 342 y 345 de la Ley 1819 de 2016, que se cargan en
   `normativa_ica`.
6. **Acuerdo 648 de 2016.** Faltaba el art. 1 (tarifas del predial y ajuste anual de los rangos con el
   IPVN) porque la «A» de la letra capitular quedaba en otra línea del HTML; ya está cargado y hay una
   prueba: toda norma marcada «todos» empieza en el art. 1 y no tiene saltos.
7. **UVT y SMMLV de 2027.** No existen aún.
8. **Resolución de rangos.** El PDF lleva el número SDH-000194 de 2025; la adenda y la especificación la
   llaman «resolución de rangos de 2026».
9. **Para la ingesta (B8).** Los «textos originales» (Acuerdo 65, art. 3; Acuerdo 105, art. 2) y los
   marcados «texto anterior, no vigente» (Ley 14, arts. 33 y 36; Decreto 474) se ingieren con
   `vigencia_hasta`. Los textos que rigen desde 2027 (art. 3 del Acuerdo 65 y art. 2 del Acuerdo 105 en
   su texto nuevo, y el art. 27 del Decreto 807) se ingieren con `vigencia_desde` 2027 (bimestre 6 de
   2026 para el ICA de los bimestrales).

## Verificado en el texto del Acuerdo 1084

El art. 7 permite descontar el 60 % de los intereses y las sanciones causados si se paga el 100 % del
capital y el 40 % de los intereses y sanciones hasta el 21 de diciembre de 2026. Eso confirma el dato que
la especificación dejaba «por verificar».
