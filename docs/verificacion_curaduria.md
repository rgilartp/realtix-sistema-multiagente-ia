# Verificación de la curaduría (B2)

Consulta de todas las fuentes: octubre de 2026. Las vistas lado a lado están en
[`docs/verificacion/index.html`](verificacion/index.html). La marca de verificación de cada tabla
la pone Rodolfo con `scripts/curaduria/marcar_verificado.py` después de revisar las vistas.

## Tablas de `datos/`

- [ ] `datos/tarifas/ipu_2026.yaml` — predial 2026, 30 rangos y 6 tarifas no residenciales. Contraste automático con el PDF de la resolución SDH-000194 de 2025: 0 diferencias. Vista: `ipu_2026.html`.
- [ ] `datos/tarifas/ipu_2027.yaml` — predial 2027, art. 20 del Acuerdo 1084. Doble lectura (OCR e imagen) y texto digital del Régimen Legal. Vista: `ipu_2027.html`.
- [ ] `datos/tarifas/sobretasa_alumbrado_2027.yaml` — sobretasa de alumbrado, arts. 14 y 15. Doble lectura (OCR e imagen). Vista: `sobretasa_alumbrado_2027.html`.
- [ ] `datos/tarifas/ica_2026.yaml` — ICA 2026: 486 actividades con tarifa, 10 de ellas por decisión de Rodolfo. Armada con el texto original del art. 3 del Acuerdo 65, los Acuerdos 780 (arts. 6 y 7), 816 (art. 4) y 98 y la Resolución SDH-000265 de 2021. Segunda lectura de la resolución con el Registro Distrital 7103: 481 de 486 coinciden y 5 no se pudieron leer. Vista: `ica_2026.html`.
- [ ] `datos/tarifas/ica_2027.yaml` — ICA 2027, art. 21: 447 actividades de tarifa fija y 28 de tarifa progresiva (475 en total). Doble lectura (imagen) y texto digital del Régimen Legal: 475 de 475 coinciden, en los dos sentidos. Vista: `ica_2027.html`.
- [ ] `datos/calendario/2026.yaml` — calendario 2026. Las fechas del ICA bimestral y del SPAC se leyeron de las tablas incrustadas como imagen. Vista: `calendario_2026.html`.
- [ ] `datos/regimenes_ica.yaml` — regímenes del ICA de 2026 y 2027. Vista: `regimenes_y_uvt.html`.
- [ ] `datos/uvt_smmlv.yaml` — UVT y SMMLV de 2025 y 2026, con la resolución de la DIAN y el decreto de cada año; los de 2027 siguen pendientes. Vista: `regimenes_y_uvt.html`.

## Lecturas del Acuerdo 1084 (OCR contra imagen)

| Dónde | El OCR leyó | La imagen dice | Se usa |
|---|---|---|---|
| Art. 15, límite de los residenciales (página 20) | 500 UVT | 600 UVT | la imagen |
| Art. 20, exclusión de estratos 1 y 2 (página 22) | inferior a 186 SMMLV | inferior a 16 SMMLV | la imagen |
| Art. 21, 6 filas (CIIU 2513, 6399, 9603, 35202, 47241, 47924) | otro número | la tarifa transcrita | la imagen |

En la tabla del art. 21 el OCR no leyó la tarifa de 115 filas ni el código de 147; por eso la
segunda lectura es la imagen y el texto digital del Régimen Legal, que ya trae el art. 21 como art. 3
del Acuerdo 65 de 2002 y coincide en las 475 actividades (447 fijas y 28 progresivas).

## ICA de 2026: cómo se armó y la decisión de Rodolfo

El texto vigente en 2026 sale de estas fuentes, que Rodolfo aprobó en la parada de B2:

1. La tarifa de cada CIIU, de la columna de 2024 de la Resolución SDH-000265 de 2021 (compilación de la
   Secretaría de Hacienda; el PDF de `bogota.gov.co` y el Registro Distrital 7103 traen el mismo texto).
2. Los cambios del art. 6 del Acuerdo 780 de 2020 (columna «2024 y siguientes»).
3. El art. 4 del Acuerdo 816 de 2021: 14 por mil para las actividades financieras (28 filas).
4. El art. 7 del Acuerdo 780 (domicilios por plataformas, 11,04 por mil) y el Acuerdo 98 de 2003
   (edición y publicación de libros: 4,14 por mil si se cumplen las condiciones y 8 si no), derogados por
   el art. 52 del Acuerdo 1084: rigen hasta su publicación.
5. El art. 44 del Acuerdo 1019 de 2025, también derogado por el art. 52, fijaba el ICA consolidado del
   régimen SIMPLE en 2026 (12, 16, 30 y 16 por mil); queda en una sección aparte del YAML.

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
301, cuya tarifa (4,14 por mil) es la de la fila.

Periodos: esta tabla cubre el año gravable 2026 de los declarantes anuales y los bimestres 1 a 5 de
2026 de los bimestrales. El Acuerdo 1084 se aprobó en plenaria el 28 de septiembre de 2026 y se firmó el
8 de octubre de 2026, ambas fechas dentro del bimestre 5 (septiembre-octubre). Por eso la tabla del
art. 21 (`ica_2027.yaml`) aplica a los bimestrales desde el bimestre 6 de 2026 (noviembre-diciembre, que
se declara a más tardar el 12 de febrero de 2027) y a los anuales desde el 1 de enero de 2027.

Normas derogadas por el art. 52 del Acuerdo 1084 revisadas: solo el Acuerdo 98 de 2003, el art. 7 del
Acuerdo 780 y el art. 44 del Acuerdo 1019 fijaban tarifas del ICA. Las demás tratan de exenciones,
notificaciones, regímenes, predial, publicidad exterior o azar y espectáculos.

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
| Decreto 474 de 2016 | `normativa_ipu` | 21 artículos | Régimen Legal de Bogotá; compilado por el Decreto 639 de 2025, que no se carga | https://www.alcaldiabogota.gov.co/sisjur/normas/Norma1.jsp?i=67262&dt=S |
| Acuerdo 648 de 2016 | `normativa_ipu` | 14 artículos | Régimen Legal de Bogotá | https://www.alcaldiabogota.gov.co/sisjur/normas/Norma1.jsp?i=67557&dt=S |
| Decreto Distrital 352 de 2002, cap. I | `normativa_ipu` | 18 artículos | Cancillería (normograma) | https://cancilleria.gov.co/sites/default/files/Normograma/docs/d_alcabog_0352_2002.htm |
| Decreto Distrital 807 de 1993 | `normativa_ipu` | 170 artículos | Régimen Legal de Bogotá, con modificaciones y notas de vigencia | https://www.alcaldiabogota.gov.co/sisjur/normas/Norma1.jsp?i=1637 |
| Acuerdo 105 de 2003, art. 2 | `normativa_ipu` | 1 artículos | Régimen Legal de Bogotá (ya con el art. 20 del Acuerdo 1084) | https://www.alcaldiabogota.gov.co/sisjur/normas/Norma1.jsp?i=11030 |
| Acuerdo 780 de 2020, art. 3 | `normativa_ipu` | 1 artículos | Régimen Legal de Bogotá | https://www.alcaldiabogota.gov.co/sisjur/normas/Norma1.jsp?i=100965 |
| Resolución SDH-000194 de 2025 (rangos del predial de 2026) | `normativa_ipu` | 4 artículos | INCP (PDF, descargado por Rodolfo) | https://incp.org.co/wp-content/uploads/2025/12/Resolucion-000194-de-2025-SDH.pdf |
| Resolución SDH-000195 de 2025 | `normativa_ipu` | 4 artículos | Régimen Legal de Bogotá (guardado por Rodolfo) | https://www.alcaldiabogota.gov.co/sisjur/normas/Norma1.jsp?i=191813&dt=S |
| Resolución SDH-000195 de 2025 | `normativa_ica` | 2 artículos | Régimen Legal de Bogotá (mismo archivo) | https://www.alcaldiabogota.gov.co/sisjur/normas/Norma1.jsp?i=191813&dt=S |
| Acuerdo 1084 de 2026 | `normativa_ipu` | 19 artículos | INCP (PDF escaneado, descargado por Rodolfo; OCR propio) | https://incp.org.co/?p=136894 |
| Acuerdo 1084 de 2026 | `normativa_ica` | 10 artículos | INCP (mismo PDF y OCR) | https://incp.org.co/?p=136894 |
| Ley 14 de 1983 | `normativa_ica` | 90 artículos | Régimen Legal de Bogotá, con notas de vigencia | https://www.alcaldiabogota.gov.co/sisjur/normas/Norma1.jsp?i=267 |
| Decreto Distrital 352 de 2002, cap. II | `normativa_ica` | 29 artículos | Cancillería (normograma) | https://cancilleria.gov.co/sites/default/files/Normograma/docs/d_alcabog_0352_2002.htm |
| Decreto Distrital 807 de 1993 | `normativa_ica` | 170 artículos | Régimen Legal de Bogotá, con modificaciones y notas de vigencia | https://www.alcaldiabogota.gov.co/sisjur/normas/Norma1.jsp?i=1637 |
| Acuerdo 65 de 2002, art. 3 | `normativa_ica` | 1 artículos | Régimen Legal de Bogotá (ya con el art. 21 del Acuerdo 1084) | https://www.alcaldiabogota.gov.co/sisjur/normas/Norma1.jsp?i=5156 |
| Acuerdo 780 de 2020, arts. 6 y 7 | `normativa_ica` | 2 artículos | Régimen Legal de Bogotá (mismo archivo); aprobada por Rodolfo en la parada de B2 | https://www.alcaldiabogota.gov.co/sisjur/normas/Norma1.jsp?i=100965 |
| Acuerdo 816 de 2021, art. 4 | `normativa_ica` | 1 artículos | Régimen Legal de Bogotá; aprobada por Rodolfo en la parada de B2 | https://www.alcaldiabogota.gov.co/sisjur/normas/Norma1.jsp?i=116160&dt=S |
| Acuerdo 98 de 2003 | `normativa_ica` | 3 artículos | Régimen Legal de Bogotá; aprobada por Rodolfo en la parada de B2 | https://www.alcaldiabogota.gov.co/sisjur/normas/Norma1.jsp?i=10597 |
| Resolución SDH-000265 de 2021, art. 1 | `normativa_ica` | 1 artículos | Compilación de la Secretaría de Hacienda; aprobada por Rodolfo en la parada de B2 | https://compilacionjuridica.shd.gov.co/compilacion/docs/resolucion_sdh_0265_2021.htm |
| Ley 1819 de 2016, arts. 342 y 345 | `normativa_ica` | 2 artículos | Secretaría del Senado (parte 7 de la ley, la misma del art. 354) | http://www.secretariasenado.gov.co/senado/basedoc/ley_1819_2016_pr007.html |

Además, el Registro Distrital 7103 (`https://www.alcaldiabogota.gov.co/sisjur/normas/verNormaPDF?i=109475`)
sirve solo para contrastar la tabla de la Resolución SDH-000265 y no va a `knowledge_base/`.

Los archivos descargados quedan en `scripts/curaduria/descargas/`, que git ignora. La conversión a
Markdown y el corte por artículo los hace `scripts/curaduria/convertir.py`.

## Límites de las fuentes y pendientes

1. **Decreto 474 de 2016.** El Régimen Legal lo marca como derogado y compilado por el Decreto Único
   Sectorial 639 de 2025, que no se carga. El texto cargado es el del decreto con sus notas.
2. **Decreto 807 de 1993.** Es la versión del Régimen Legal, con las modificaciones y las notas de
   vigencia; los arts. 7 y 8 aparecen derogados por el Acuerdo 1084.
3. **Ley 1581 de 2012.** Se cargan los artículos 1 a 30; los «artículos» 31 a 34 del texto de la Secretaría
   del Senado son del proyecto que citan las notas de jurisprudencia.
4. **Ley 14 de 1983.** Texto del Régimen Legal de Bogotá (`i=267`) con sus notas de vigencia, cortado en
   90 artículos. Los arts. 33 (base gravable) y 36 (actividades de servicios) traen la nota «Modificado
   por el art. 342 (345), Ley 1819 de 2016» pero muestran el texto de 1983: en la base quedan marcados
   como «texto anterior, no vigente», con una remisión a los arts. 342 y 345 de la Ley 1819 de 2016, que
   se cargan en `normativa_ica`.
5. **UVT y SMMLV de 2027.** No existen aún.
6. **Resolución de rangos.** El PDF lleva el número SDH-000194 de 2025; la adenda y la especificación la
   llaman «resolución de rangos de 2026».
7. **Ruido de las fuentes.** Algunas páginas traen enlaces y notas de jurisprudencia dentro de los
   artículos; la limpieza se hace en B8.

## Verificado en el PDF del Acuerdo 1084

El art. 7 permite descontar el 60 % de los intereses y las sanciones causados si se paga el 100 % del
capital y el 40 % de los intereses y sanciones hasta el 21 de diciembre de 2026. Eso confirma el dato que
la especificación dejaba «por verificar».
