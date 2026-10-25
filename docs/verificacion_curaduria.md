# Verificación de la curaduría (B2)

Consulta de todas las fuentes: octubre de 2026. Las vistas lado a lado están en
[`docs/verificacion/index.html`](verificacion/index.html). La marca de verificación de cada tabla
la pone Rodolfo con `scripts/curaduria/marcar_verificado.py` después de revisar las vistas.

## Tablas de `datos/`

- [ ] `datos/tarifas/ipu_2026.yaml` — predial 2026, 30 rangos y 6 tarifas no residenciales. Contraste automático con el PDF de la resolución de rangos: 0 diferencias. Vista: `ipu_2026.html`.
- [ ] `datos/tarifas/ipu_2027.yaml` — predial 2027, art. 20 del Acuerdo 1084. Doble lectura (OCR e imagen) y texto digital del Régimen Legal. Vista: `ipu_2027.html`.
- [ ] `datos/tarifas/sobretasa_alumbrado_2027.yaml` — sobretasa de alumbrado, arts. 14 y 15. Doble lectura (OCR e imagen). Vista: `sobretasa_alumbrado_2027.html`.
- [ ] `datos/tarifas/ica_2027.yaml` — ICA 2027, art. 21: 447 actividades y la tarifa progresiva financiera. Doble lectura (imagen) y texto digital del Régimen Legal: 447 de 447 coinciden. Vista: `ica_2027.html`.
- [ ] `datos/calendario/2026.yaml` — calendario 2026. Las fechas del ICA bimestral y del SPAC se leyeron de las tablas incrustadas como imagen. Vista: `calendario_2026.html`.
- [ ] `datos/regimenes_ica.yaml` — regímenes del ICA de 2026 y 2027. Vista: `regimenes_y_uvt.html`.
- [ ] `datos/uvt_smmlv.yaml` — UVT y SMMLV. Salen de fuentes secundarias; contrastar con la DIAN y el decreto. Vista: `regimenes_y_uvt.html`.
- [ ] `datos/tarifas/ica_2026.yaml` — **pendiente**, sin tarifas (ver «Pendientes y decisiones»). No se marca.

## Lecturas del Acuerdo 1084 (OCR contra imagen)

| Dónde | El OCR leyó | La imagen dice | Se usa |
|---|---|---|---|
| Art. 15, límite de los residenciales (página 20) | 500 UVT | 600 UVT | la imagen |
| Art. 20, exclusión de estratos 1 y 2 (página 22) | inferior a 186 SMMLV | inferior a 16 SMMLV | la imagen |
| Art. 21, 6 filas (CIIU 2513, 6399, 9603, 35202, 47241, 47924) | otro número | la tarifa transcrita | la imagen |

En la tabla del art. 21 el OCR no leyó la tarifa de 115 filas ni el código de 147; por eso la
segunda lectura es la imagen y el texto digital del Régimen Legal, que ya trae el art. 21 como art. 3
del Acuerdo 65 de 2002 y coincide en las 447 filas.

## Fuentes y de dónde salió cada archivo

| Norma | Colección | Estado | Origen del archivo | Enlace |
|---|---|---|---|---|
| Ley 1581 de 2012 | `normativa_datos` | 34 artículos | Secretaría del Senado | http://www.secretariasenado.gov.co/senado/basedoc/ley_1581_2012.html |
| Decreto 1074 de 2015, caps. 25 y 26 | `normativa_datos` | 42 artículos | Colpensiones (normograma) | https://normativa.colpensiones.gov.co/colpens/docs/decreto_1074_2015.htm |
| Ley 44 de 1990 | `normativa_ipu` | 30 artículos | Colpensiones (normograma) | https://normativa.colpensiones.gov.co/colpens/docs/ley_0044_1990.htm |
| Ley 1995 de 2019 | `normativa_ipu` | 7 artículos | IGAC | https://www.igac.gov.co/sites/default/files/transparencia/normograma/ley_1995_de_2019.pdf |
| Ley 2294 de 2023, art. 49 | `normativa_ipu` | 1 artículos | Cancillería (normograma) | https://cancilleria.gov.co/sites/default/files/Normograma/docs/ley_2294_2023.htm |
| Ley 1819 de 2016, art. 354 | `normativa_ipu` | 1 artículos | Secretaría del Senado (parte 7 de la ley) | http://www.secretariasenado.gov.co/senado/basedoc/ley_1819_2016_pr007.html |
| Decreto Ley 1421 de 1993 | `normativa_ipu` | 3 artículos | Secretaría del Senado (cuatro partes) | http://www.secretariasenado.gov.co/senado/basedoc/decreto_1421_1993.html |
| Decreto 474 de 2016 | `normativa_ipu` | 21 artículos | Ámbito Jurídico (PDF) | https://www.ambitojuridico.com/sites/default/files/BancoMedios/Archivos/d-474-16.pdf |
| Acuerdo 648 de 2016 | `normativa_ipu` | 14 artículos | Régimen Legal de Bogotá | https://www.alcaldiabogota.gov.co/sisjur/normas/Norma1.jsp?i=67557&dt=S |
| Decreto Distrital 352 de 2002, cap. I | `normativa_ipu` | 18 artículos | Cancillería (normograma) | https://cancilleria.gov.co/sites/default/files/Normograma/docs/d_alcabog_0352_2002.htm |
| Decreto Distrital 807 de 1993 | `normativa_ipu` | 169 artículos | bogota.gov.co (PDF) | https://bogota.gov.co/sites/default/files/tys/2021/01/DECRETO_807_1993.pdf |
| Acuerdo 105 de 2003, art. 2 | `normativa_ipu` | 1 artículos | Régimen Legal de Bogotá (ya con el art. 20 del Acuerdo 1084) | https://www.alcaldiabogota.gov.co/sisjur/normas/Norma1.jsp?i=11030 |
| Acuerdo 780 de 2020, art. 3 | `normativa_ipu` | 1 artículos | Régimen Legal de Bogotá | https://www.alcaldiabogota.gov.co/sisjur/normas/Norma1.jsp?i=100965 |
| Resolución SDH-000194 de 2025 (rangos del predial de 2026) | `normativa_ipu` | 4 artículos | INCP (PDF, descargado por Rodolfo) | https://incp.org.co/wp-content/uploads/2025/12/Resolucion-000194-de-2025-SDH.pdf |
| Resolución SDH-000195 de 2025 | `normativa_ipu` | 4 artículos | Régimen Legal de Bogotá (guardado por Rodolfo) | https://www.alcaldiabogota.gov.co/sisjur/normas/Norma1.jsp?i=191813&dt=S |
| Resolución SDH-000195 de 2025 | `normativa_ica` | 2 artículos | Régimen Legal de Bogotá (mismo archivo) | https://www.alcaldiabogota.gov.co/sisjur/normas/Norma1.jsp?i=191813&dt=S |
| Acuerdo 1084 de 2026 | `normativa_ipu` | 19 artículos | INCP (PDF escaneado, descargado por Rodolfo; OCR propio) | https://incp.org.co/?p=136894 |
| Acuerdo 1084 de 2026 | `normativa_ica` | 10 artículos | INCP (mismo PDF y OCR) | https://incp.org.co/?p=136894 |
| Ley 14 de 1983 | `normativa_ica` | pendiente | — | https://www.funcionpublica.gov.co/eva/gestornormativo/norma_pdf.php?i=3645 |
| Decreto Distrital 352 de 2002, cap. II | `normativa_ica` | 29 artículos | Cancillería (normograma) | https://cancilleria.gov.co/sites/default/files/Normograma/docs/d_alcabog_0352_2002.htm |
| Decreto Distrital 807 de 1993 | `normativa_ica` | 169 artículos | bogota.gov.co (PDF) | https://bogota.gov.co/sites/default/files/tys/2021/01/DECRETO_807_1993.pdf |
| Acuerdo 65 de 2002, art. 3 | `normativa_ica` | 1 artículos | Régimen Legal de Bogotá (ya con el art. 21 del Acuerdo 1084) | https://www.alcaldiabogota.gov.co/sisjur/normas/Norma1.jsp?i=5156 |

Los archivos descargados quedan en `scripts/curaduria/descargas/`, que git ignora. La conversión a
Markdown y el corte por artículo los hace `scripts/curaduria/convertir.py`.

## Pendientes y decisiones

1. **ICA 2026 (`ica_2026.yaml`).** El Régimen Legal solo muestra el texto original del art. 3 del
   Acuerdo 65 (2002) y el nuevo del art. 21 del Acuerdo 1084 (desde 2027). El texto vigente en 2026 lo
   modifican el art. 6 del Acuerdo 780 de 2020 y el art. 4 del Acuerdo 816 de 2021, y el Acuerdo 816 no
   está entre las fuentes de la sección 5.1 de la especificación. No se completa con valores supuestos.
2. **Ley 14 de 1983.** La copia que enlaza la adenda es el texto original; el enlace de la Función
   Pública con el texto compilado no se pudo descargar. La colección `normativa_ica` queda sin ella.
3. **Ley 1581 de 2012.** El corte por artículo da 34 artículos y la ley tiene 28: sobran encabezados
   de las notas de jurisprudencia. Se limpia antes de la ingesta (B8).
4. **UVT y SMMLV.** Las cifras de 2025 y 2026 salen del INCP y de prensa económica, y el decreto del
   SMMLV de 2026 estuvo suspendido de forma provisional por el Consejo de Estado. Las de 2027 no existen aún.
5. **Fecha de aprobación del Acuerdo 1084** para el bimestre exacto de las tarifas nuevas del ICA:
   sigue sin confirmarse.
6. **Resolución de rangos.** El PDF lleva el número SDH-000194 de 2025; la adenda y la especificación la
   llaman «resolución de rangos de 2026».

## Verificado en el PDF del Acuerdo 1084

El art. 7 permite descontar el 60 % de los intereses y las sanciones causados si se paga el 100 % del
capital y el 40 % de los intereses y sanciones hasta el 21 de diciembre de 2026. Eso confirma el dato que
la especificación dejaba «por verificar».
