# Tareas de usabilidad — Rodolfo Angel Gilart Pulido

Evaluación interna preliminar de usabilidad del sistema multiagente de IA (ADR-21; sección 6.8 de la
especificación técnica). La hace cada autor **por su lado**, sin hablar de los resultados con el otro
evaluador hasta que los dos terminen, y **sin ayuda de ninguna IA** para responder ni para redactar.

## Antes de empezar

1. **Horario.** El asistente atiende en días hábiles de 8:00 a. m. a 5:00 p. m., hora de Bogotá.
   Fuera de ese horario solo muestra el aviso de fuera de horario. Haz las tareas en ese horario.
2. **Dirección.** Abre https://tg2-multiagente.duckdns.org/ovt/ en Chrome, Edge o Firefox. Es la OVT simulada: una página de pruebas
   que dice «Entorno simulado de pruebas». No necesitas el repositorio ni ninguna clave: los
   archivos que usas (este formulario y el recibo de la tarea 3) te los entrega Rodolfo.
3. **Usuario de prueba.** En el selector «Usuario de prueba», elige el usuario que indica cada
   tarea y pulsa el botón para iniciar la sesión. Todos los usuarios son sintéticos.
4. **Conversación nueva.** Antes de cada tarea, recarga la página (F5) y vuelve a elegir el usuario,
   para empezar una conversación nueva. Esto importa sobre todo después de la tarea 5: una
   conversación transferida a un funcionario ya no la atiende el asistente.
5. **Qué anotar.** En la tabla de cada tarea: si la terminaste (sí, con ayuda o no), cuánto tardaste
   (minutos aproximados, con un reloj), cuántos errores o desvíos tuviste y tus comentarios. Los
   problemas de diseño que encuentres van, además, en `heuristica.md`.
6. **Al final**, llena `sus.md` (10 afirmaciones) pensando en toda la sesión.

## Tarea 1 · Consultar el estado de cuenta

- **Usuario:** U03 (persona natural con un predio residencial).
- **Qué haces:** pregunta, con tus palabras, cuánto debes del impuesto predial de tu predio.
- **Se logra si:** el asistente muestra el saldo de tu predio y dice si la obligación está vencida,
  con su fuente.

| Terminada (sí / con ayuda / no) | Minutos | Errores o desvíos | Comentarios |
|---|---|---|---|
|  |  |  |  |

## Tarea 2 · Estimar el impuesto de industria y comercio (ICA)

- **Usuario:** U12 (persona jurídica que declara el ICA cada año).
- **Qué haces:** pide una estimación del ICA de este año; cuando el asistente lo pida, inventa un
  código CIIU y unos ingresos plausibles (o usa los de tu actividad registrada, si el asistente la
  muestra).
- **Se logra si:** recibes una estimación con la tarifa, el valor y la nota de que no es vinculante.

| Terminada (sí / con ayuda / no) | Minutos | Errores o desvíos | Comentarios |
|---|---|---|---|
|  |  |  |  |

## Tarea 3 · Cargar un recibo y confirmar los datos

- **Usuario:** U03.
- **Archivo:** `recibo_de_prueba_U03.png`, que viene con este formulario (en el repositorio está en
  `docs/usabilidad/`). Es un recibo sintético con la leyenda «Documento sintético sin validez
  tributaria».
- **Qué haces:** adjunta el recibo con el control de carga de la ventana del asistente, revisa los
  datos que leyó y confírmalos.
- **Se logra si:** el asistente muestra los datos leídos, te pide confirmarlos y, al confirmar, los
  contrasta con el estado de cuenta del predio.

| Terminada (sí / con ayuda / no) | Minutos | Errores o desvíos | Comentarios |
|---|---|---|---|
|  |  |  |  |

## Tarea 4 · Hacer una pregunta fuera de alcance

- **Usuario:** cualquiera, o sin sesión.
- **Qué haces:** pregunta algo que no sea del predial ni del ICA de Bogotá (por ejemplo, un trámite
  de otro tributo o una pregunta que no sea tributaria).
- **Se logra si:** el asistente te dice con claridad que eso no lo atiende y qué sí atiende, o
  transfiere el caso si es un tema tributario que el sistema no cubre.

| Terminada (sí / con ayuda / no) | Minutos | Errores o desvíos | Comentarios |
|---|---|---|---|
|  |  |  |  |

## Tarea 5 · Pedir un funcionario

- **Usuario:** cualquiera.
- **Qué haces:** pide que te atienda una persona, con el botón «Hablar con un funcionario» o con tus
  palabras.
- **Se logra si:** el asistente confirma la transferencia, el caso queda registrado y la ventana
  avisa que la conversación está en manos de un funcionario.

| Terminada (sí / con ayuda / no) | Minutos | Errores o desvíos | Comentarios |
|---|---|---|---|
|  |  |  |  |

## Comentarios generales

(Escribe aquí lo que quieras agregar sobre toda la sesión.)
