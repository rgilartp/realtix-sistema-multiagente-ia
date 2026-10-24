# Estado del código de la actividad 6.3.1 — octubre de 2026

> Proyecto: sistema multiagente de IA para el soporte del proceso de facturación de Realtix.
> Este archivo acompaña al código de esta carpeta. Dice qué hace, cómo se verificó, qué fallas
> conocidas tiene y qué se debe corregir al migrarlo en el Paso 2 del plan de desarrollo.

---

## 1. Qué es esta carpeta

Es la única pieza de código que existe hoy: la base de datos sintética (SQLite con Faker
`es_CO`) y el adaptador de datos (`RealSitAdapter` y su implementación `MockRealSitAdapter`).
No hay agentes, grafo, API ni interfaz todavía.

- Corresponde a la última versión del equipo, que incluye la corrección de idempotencia de
  `demo.py` (identificadores con sufijo único por ejecución).
- Implementa 6 de los 7 métodos del contrato (Tabla 7 de arquitectura v2). El séptimo,
  `get_predios_contribuyente` (decisión D1), se agrega en el Paso 2.
- No incluye el entorno virtual, la carpeta `__pycache__` ni la base `data/realtix_sintetico.db`:
  la base se regenera con la semilla.

## 2. Cómo ejecutarlo

```bash
python -m venv venv
venv\Scripts\activate            # Windows;  source venv/bin/activate en macOS/Linux
pip install -r requirements.txt
python generate_synthetic_data.py --contribuyentes 150 --seed 42
python demo.py
```

## 3. Verificación de octubre de 2026

Entorno: Python 3.12.3 y Faker 40.38.0 (la versión instalada en el entorno del equipo). Se
repitieron las verificaciones de la revisión técnica de septiembre de 2026 y los resultados
coincidieron uno a uno:

| # | Verificación | Resultado |
|---|---|---|
| V-01 | Generar con `--contribuyentes 150 --seed 42` | 150 contribuyentes, 170 predios, 434 obligaciones y 317 pagos |
| V-02 | Ejecutar `demo.py` dos veces seguidas | Pasa las dos veces, incluido el rechazo de RF-AUT-02 |
| V-03 | Comparar dos generaciones con la misma semilla | Contribuyentes 150/150 y predios 170/170 idénticos; obligaciones 0/434 y pagos 0/317 |
| V-04 | Distribución de estados de pago | ICA 2026: 54 al día y 40 vencidas. IPU 2025: 170 al día. IPU 2026: 93 al día y 77 vencidas. Ninguna pendiente |
| V-05 | Obligaciones de ICA por contribuyente y vigencia | 13 contribuyentes con dos obligaciones de ICA 2026 de valores distintos |
| V-06 | Predios por tramo de tarifa del IPU | 4,0 por mil: 12 · 6,5: 23 · 9,0: 56 · 12,0: 79 |
| V-07 | Usar el adaptador desde un hilo distinto | `sqlite3.ProgrammingError` |
| V-08 | Registrar un caso escalado sin conversación previa | `sqlite3.IntegrityError: FOREIGN KEY constraint failed` |

Los nombres y números de documento los genera Faker; con otra versión de Faker pueden cambiar.
Por eso el Paso 1 fija las versiones de las dependencias.

## 4. Cambios hechos en este paquete (solo documentación)

En los archivos de esta carpeta se corrigieron únicamente comentarios, docstrings y el README.
La lógica es idéntica a la versión del equipo: se comprobó comparando el árbol sintáctico de
cada módulo sin docstrings, y las verificaciones de la sección 3 se ejecutaron sobre esta copia.

| Archivo | Cambio | Hallazgo |
|---|---|---|
| `adapter.py` | El contrato es la Tabla 7 de arquitectura v2, no la Tabla 5. Nota de estado: 6 de 7 métodos | M-04 |
| `adapter.py` | El docstring de `PredioNoAutorizadoError` pedía escalar; ahora indica la regla vigente: rechazo explícito, sin revelar datos y sin escalar | M-05 (D3) |
| `adapter.py` | `MockRealSitAdapter` se describía como «de solo lectura», pero registra los casos escalados; ahora lo dice | Nuevo |
| `models.py` | Tabla 7 en lugar de Tabla 5; se documenta que `EstadoCuenta.contribuyente` guarda el identificador y no el nombre | M-04, M-06 |
| `database.py` | La decisión de ambiente de datos está en la sección 3.3 de requerimientos y en la 6.3 de arquitectura (la 3.3 de arquitectura es AgentState) | Nuevo |
| `demo.py` | Tabla 7 en lugar de Tabla 5; el comentario sobre la conversación decía que la crea la interfaz, y ahora remite a H-02 | M-04, H-02 |
| `generate_synthetic_data.py` | Advertencia sobre el tramo de 4 por mil: el rango general vigente es de 5 a 16 por mil (art. 23 de la Ley 1450 de 2011) | H-06 (se corrige en el Paso 2) |
| `README.md` | Aviso de estado, Tabla 7, séptimo método pendiente, regla D3, orden de dependencia entre archivos, Python 3.12, causa real del `ModuleNotFoundError` y una errata | M-04 y nuevos |

## 5. Fallas conocidas que se corrigen en el Paso 2

El detalle y la evidencia están en `04_REVISION_Y_HALLAZGOS.md`, sección 3.

| ID | Falla | Corrección prevista |
|---|---|---|
| H-01 | El adaptador abre una conexión en el constructor y falla si se usa desde otro hilo (V-07); FastAPI y LangGraph usan varios hilos | Una conexión por operación |
| H-02 | `registrar_caso_escalado` falla si la conversación no existe (V-08) | Registrar la conversación si no existe, sin cambiar el contrato |
| H-03 | Identificadores de obligaciones y pagos con `uuid4`, no reproducibles (V-03) | Derivarlos del generador con semilla |
| H-04 | Una obligación de ICA por predio en lugar de una por contribuyente y vigencia (V-05) | Una sola, asociada al predio donde se ejerce la actividad (D4) |
| H-05 | Sin obligaciones pendientes ni mora de vigencias anteriores (V-04) | Introducir estados pendientes y en mora (D4) |
| H-06 | Tramo de IPU de 4 por mil, bajo el rango vigente (V-06) | Tramo mínimo de 5 por mil; tabla de tarifas en `src/services/tarifas.py` |
| M-01 | `get_obligaciones_vigentes` devuelve también las pagadas | "Vigentes" = pendiente o vencido, de cualquier vigencia (sección 8.1 de arquitectura v2) |
| M-02 | `get_avaluo_catastral` fija la vigencia 2026 en el código | Tomarla de la configuración |
| M-03 | Una actividad de ICA inexistente lanza un `ValueError` genérico | Excepción propia del dominio |
| M-07 | No hay forma de obtener los predios de un contribuyente | Agregar `get_predios_contribuyente` (D1) |

M-04, M-05 y M-06 quedaron resueltos en este paquete porque eran de documentación.

## 6. Observaciones nuevas (octubre de 2026)

Ninguna cambia una decisión; todas precisan cómo implementar las que ya existen. La mayoría se
resuelven en el Paso 2; OC-05 se aplica en los Pasos 4 y 7, y OC-06 en los Pasos 5 y 8. OC-08
requiere una decisión del equipo.

**OC-01. Volumen exacto de D4.** El equipo fijó el conjunto sintético en 500 predios con 4
vigencias de IPU (2023 a 2026), es decir, 2.000 obligaciones de IPU. El generador actual recibe
el número de contribuyentes y deriva los predios (1 o 2 por contribuyente), así que no garantiza
500: con 430 contribuyentes se obtuvieron entre 485 y 538 predios en 200 semillas. El generador
del Paso 2 debe recibir el número de predios. Las vigencias del ICA no están fijadas: se
proponen en el Paso 2 y se reportan con el resto de cifras.

**OC-02. Unicidad de identificadores.** La matrícula se genera como `50C-` más 7 dígitos y los
documentos al azar, sin control de duplicados. Con unos 500 predios, 2 de 200 semillas repitieron
un identificador, y la inserción fallaría por llave primaria. El generador debe garantizar
unicidad.

**OC-03. Fecha de referencia fija.** `generar_obligaciones_y_pagos` fija `hoy = date(2026, 9, 12)`
dentro de la función. Conviene volverla parámetro del generador: define qué obligaciones quedan
pendientes o vencidas y es parte de la reproducibilidad. Con la fecha límite del 30 de junio,
toda obligación de IPU 2026 no pagada queda vencida a la fecha de referencia (12 de septiembre),
y por eso no hay pendientes (H-05).

**OC-04. Fechas límite alineadas con el calendario real.** El generador usa el 30 de junio para el
IPU y el 20 de enero para el ICA. Para 2026, la Alcaldía de Bogotá informó que el predial se pudo
pagar con 10 % de descuento hasta el 17 de abril y sin intereses hasta el 10 de julio:

- https://bogota.gov.co/mi-ciudad/hacienda/como-pagar-y-descargar-el-impuesto-predial-de-2026-en-bogota
- https://bogota.gov.co/mi-ciudad/hacienda/viernes-10-de-julio-vence-plazo-para-pagar-el-impuesto-predial-bogota

Como la base de conocimiento citará el calendario oficial, las fechas del conjunto sintético deben
coincidir con las del calendario que se cargue en `normativa_ipu`; si no, el adaptador y el RAG se
contradicen en la misma respuesta. Las fechas de 2023 a 2025 y las del ICA se toman del
calendario tributario oficial de cada año durante la curaduría (6.3.2). Mientras tanto, el Paso 2
usa valores provisionales y configurables (plan, Paso 2).

**OC-05. Descuento por pronto pago.** La plantilla del recibo (sección 5.2 de arquitectura v2),
RF-IPU-03 y RF-OCR-02 lo usan, pero el modelo de datos no lo guarda. Se recomienda calcularlo en
la capa de servicios a partir de la tarifa y el calendario, para la liquidación estimada y para los
recibos sintéticos del Paso 7, sin cambiar el modelo de la Figura 2 salvo decisión del equipo.

**OC-06. Mismo mensaje para predio inexistente y predio ajeno.** El adaptador distingue
`PredioNoEncontradoError` y `PredioNoAutorizadoError`, lo cual es correcto internamente. Lo que se
le responde al contribuyente debe ser igual en ambos casos, para no revelar si una matrícula
existe (sección 6.1: el rechazo no revela información del predio consultado).

**OC-07. Ruta de la base como texto.** `get_connection` espera un `Path`; si recibe la ruta como
texto, falla en `db_path.parent`. Al leer la ruta de la configuración (RNF-14) conviene aceptar
`str` o `Path`.

**OC-08. Casos que escalan antes de calcular la confianza.** La tabla `caso_escalado` exige
`nivel_confianza` (`REAL NOT NULL`) y el modelo `CasoEscalado` lo declara como `float`. Pero el
orquestador escala directamente, antes del nodo de confianza, cuando el contribuyente lo pide,
cuando la consulta tributaria está fuera de alcance, cuando se alcanza el tope de
reclasificaciones o cuando falla (Tabla 2 de arquitectura v2). En esos casos no hay un nivel que
guardar: registrar un caso con `nivel_confianza=None` falla con
`IntegrityError: NOT NULL constraint failed: caso_escalado.nivel_confianza` (comprobado). El equipo
decide entre un valor convenido, por ejemplo 0.0 junto con el motivo del escalamiento, o un campo
opcional; lo segundo cambia la Figura 2.
