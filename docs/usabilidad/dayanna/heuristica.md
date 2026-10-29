# Evaluación heurística — Dayanna Liceth Varón Puerto

Evaluación interna preliminar del sistema multiagente de IA con las 10 heurísticas de usabilidad de
Nielsen (ADR-21). Anota **cada problema** que encuentres al hacer las tareas de `tareas.md` (o al
explorar la ventana del asistente), **por tu lado** y **sin ayuda de ninguna IA**.

## Las 10 heurísticas

1. Visibilidad del estado del sistema: el sistema informa qué está pasando, a tiempo.
2. Correspondencia con el mundo real: habla con palabras del contribuyente, no técnicas.
3. Control y libertad del usuario: hay una salida clara cuando algo sale mal.
4. Consistencia y estándares: lo mismo se dice y se ve igual en todas partes.
5. Prevención de errores: el diseño evita que el usuario se equivoque.
6. Reconocer antes que recordar: lo necesario está a la vista; no hay que memorizarlo.
7. Flexibilidad y eficiencia de uso: sirve al novato y al experimentado.
8. Diseño estético y minimalista: no hay información irrelevante que distraiga.
9. Ayudar a reconocer, diagnosticar y recuperarse de errores: los mensajes de error dicen qué pasó y
qué hacer, en lenguaje claro.
10. Ayuda y documentación: si hace falta ayuda, es fácil de encontrar.

## Gravedad (escala de Nielsen)

0 = no es un problema de usabilidad · 1 = cosmético (se arregla si sobra tiempo) · 2 = menor (baja
prioridad) · 3 = mayor (alta prioridad) · 4 = catastrófico (hay que arreglarlo antes de entregar).

## Problemas encontrados

|N.º|Tarea (1 a 5) o «explorar»|Dónde (pantalla o mensaje)|Qué pasa|Heurística (1 a 10)|Gravedad (0 a 4)|
|-|-|-|-|-|-|
|1|3|mensaje|le cargué una foto que correspondía a una factura que no era una factura generada artificialmente, sino una de formato más realista y me dijo que estaba recortada lo que demuestra que no puede leer correctamente una factura real(el día que se use) y necesita decirme específicamente cuando no estoy cargando una factura o cuando estoy cargando una factura recortada para no confundir al usuario|9|4|
|2|3|mensaje|cuando probé tomando una foto desde mi celular para cargarla de una factura me dijo que pesaba más de 5 MB por lo que necesita más flexibilidad en los pesos de los archivos cargados|5|4|
|3|1|pantalla|al momento de iniciar sesión en modo oscuro no era muy legible el texto de los usuarios porque se combina con el fondo de la selección de usuario del menú desplegable de usuarios de prueba|8|2|
|4|2|mensaje|cuándo me respondió la pregunta de la estimación del ICA y el sistema me preguntó por el código CIIU no me dijo exactamente dónde encontrarlo y es posible que no todos los usuarios sepan dónde está por lo que hay que agregar a la respuesta dónde encontrar este código que es en el RUT de la DIAN o En el certificado de existencia y representación legal o de matrícula mercantil de la Cámara de Comercio, en la sección «Clasificación de actividades económicas - CIIU»|10|3|
|(Agrega las filas que necesites.)||||||

## Observaciones de contenido (aparte de la evaluación heurística)

Estas dos filas se escribieron con ayuda del chat del documento, así que no son parte de la
evaluación heurística y no cuentan en sus resultados. Se conservan tal cual como observaciones
sobre el contenido de las respuestas (fuentes y estimación del ICA).

|N.º|Tarea (1 a 5) o «explorar»|Dónde (pantalla o mensaje)|Qué pasa|Heurística (1 a 10)|Gravedad (0 a 4)|
|-|-|-|-|-|-|
|C1|2|mensaje|En la respuesta de la estimación del ICA, la lista «Fuentes» del final solo incluye el Acuerdo 65 de 2002 con sus modificaciones. Sin embargo, en el texto la respuesta también cita el Decreto 807 de 1993, art. 15, el Decreto 352 de 2002, art. 59, y la Resolución SDH-000195 de 2025, art. 2, que no aparecen en esa lista. Además, dos datos no tienen fuente. Uno es la periodicidad anual que supuso el asistente, que está en la Resolución SDH-000195 de 2025, art. 1. El otro es que el código 6201 tenga la tarifa de 9,66 por mil, que está en la clasificación de actividades de la Resolución SDH-000265 de 2021. Por eso, quien quiera verificar la respuesta no encuentra en un solo lugar todas las normas que se usaron.|4|2|
|C2|2|mensaje|En la respuesta de la estimación del ICA, el asistente aclaró que el valor de $8.694.000 no incluye el complementario de avisos y tableros, que es el 15 % del impuesto según el Decreto 352 de 2002, art. 59. Tampoco incluye la sobretasa bomberil, según la Resolución SDH-000195 de 2025, art. 2. Agregó que ambos «se suman cuando aplican», pero no dijo si alguno aplica en este caso. Para la sobretasa bomberil ya tenía los datos. En 2026 solo la declaran quienes tienen ingresos netos superiores a 43.498 UVT, es decir, más de 2.100 millones de pesos, y el usuario informó ingresos de 900 millones, así que no le aplica. Para avisos y tableros no preguntó si la persona tiene vallas, avisos o tableros visibles desde el espacio público o en sus vehículos, que es lo que hace que se cobre según el art. 57 del mismo decreto. Por eso el usuario queda sin saber si debe sumar esos valores a su estimación. El asistente debería decirle que la sobretasa bomberil no le aplica y preguntarle por los avisos antes de mencionar el 15 %.|8|2|
