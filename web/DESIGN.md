---
version: alpha
name: Formulario y sello
description: Sistema visual de la OVT simulada, el widget del asistente tributario y la consola de funcionarios del sistema multiagente de IA.
colors:
  papel: "#F2F6FA"
  papel-2: "#E1E9F1"
  hoja: "#FFFFFF"
  renglon: "#C4D2E0"
  borde-control: "#66788C"
  tinta: "#13233A"
  tinta-suave: "#46566A"
  tinta-oscura: "#13233A"
  blanco: "#FFFFFF"
  sello: "#074C91"
  sello-fuerte: "#053A70"
  sello-texto: "#074C91"
  sello-suave: "#E3EDF8"
  burbuja: "#13233A"
  resaltador: "#FFD54F"
  funcionario: "#188034"
  funcionario-texto: "#16762F"
  advertencia: "#6E4600"
  advertencia-suave: "#FFF3CC"
  advertencia-borde: "#C9962B"
  error: "#A3271F"
  error-suave: "#FBE9E7"
  celda-acierto: "#074C91"
  celda-error: "#A3271F"
typography:
  titulo:
    fontFamily: Archivo Variable
    fontWeight: 700
  texto:
    fontFamily: Atkinson Hyperlegible Next Variable
    fontWeight: 400
  xs:
    fontSize: 0.875rem
    lineHeight: 1.4
  sm:
    fontSize: 0.9375rem
    lineHeight: 1.5
  base:
    fontSize: 1.0625rem
    lineHeight: 1.55
  lg:
    fontSize: 1.25rem
    lineHeight: 1.3
  xl:
    fontSize: 1.5rem
    lineHeight: 1.25
  2xl:
    fontSize: 1.875rem
    lineHeight: 1.15
  3xl:
    fontSize: 2.25rem
    lineHeight: 1.1
rounded:
  control: 6px
  casilla: 3px
  mensaje: 12px
components:
  rotulo:
    backgroundColor: "{colors.advertencia-suave}"
    textColor: "{colors.advertencia}"
    typography: "{typography.texto}"
  encabezado:
    backgroundColor: "{colors.sello}"
    textColor: "{colors.blanco}"
    typography: "{typography.titulo}"
  interruptor:
    backgroundColor: "{colors.sello}"
    textColor: "{colors.blanco}"
    rounded: "{rounded.control}"
  tarjeta:
    backgroundColor: "{colors.hoja}"
    textColor: "{colors.tinta}"
    rounded: "{rounded.casilla}"
  banda:
    backgroundColor: "{colors.sello}"
    textColor: "{colors.blanco}"
    typography: "{typography.titulo}"
    rounded: "{rounded.casilla}"
  casilla:
    backgroundColor: "{colors.hoja}"
    textColor: "{colors.tinta-suave}"
    rounded: "{rounded.casilla}"
  boton-principal:
    backgroundColor: "{colors.sello}"
    textColor: "{colors.blanco}"
    rounded: "{rounded.control}"
  boton-principal-hover:
    backgroundColor: "{colors.sello-fuerte}"
    textColor: "{colors.blanco}"
---

## Overview

La oficina virtual tributaria simulada de un municipio colombiano, su asistente de IA y la
consola de los funcionarios. La dirección sale de los materiales del trámite: el papel de
seguridad de los recibos, las casillas de los formularios con su rótulo dentro del borde, las
bandas que encabezan cada bloque y la tinta azul de los sellos de radicado. No imita ningún
formulario, sello ni marca real. Los colores son los del logo de Realtix (azul, verde y blanco),
sin el logo ni el nombre. El tono es institucional y sobrio; la cercanía la dan la letra legible y
el lenguaje claro. Hay modo claro y modo oscuro, con los mismos colores.

## Colors

- El fondo de las páginas es `papel`; lo que se lee o se llena va en `hoja`. Los neutros salen
  del azul.
- `sello` es el relleno del encabezado de portal, las bandas, los botones principales, la cabecera
  del widget y la pestaña del asistente de IA, siempre con texto `blanco`. Es tinta plana.
- `sello-texto` es el azul para texto, enlaces, el anillo de foco sobre `papel` y `hoja`, y el
  anillo del caso elegido. En el modo claro coincide con `sello`; en el oscuro es más claro.
- El verde es del funcionario y de los estados correctos: `funcionario` como relleno con texto
  `blanco` y `funcionario-texto` para texto.
- El verde y el azul nunca se juntan con texto.
- `resaltador` se reserva para la selección de texto, con `tinta-oscura`, y para el anillo de foco
  sobre `sello`.
- El ámbar es el de los avisos: el rótulo de entorno simulado y fuera de horario. El ámbar y el
  rojo de error conservan su papel en los dos modos.
- Quien habla tiene un color fijo y siempre su nombre escrito: azul para el asistente de IA, verde
  para el funcionario y `papel-2` con `tinta` para el sistema. El mensaje del contribuyente va en
  `burbuja` con texto `blanco`.
- `renglon` solo separa filas y bloques. El borde de cualquier control usa `borde-control`.
- La matriz de la consola mezcla `celda-acierto` o `celda-error` con la `hoja` del modo, hasta su
  tope, y el texto es `tinta`.
- En los dos modos, todo par de texto cumple 4,5:1, y todo control o anillo de foco, 3:1.
  `npm run contraste` lo mide, junto con las celdas más intensas de la matriz, y la CI lo corre.

## Themes

El modo claro son los valores del frontmatter. El modo oscuro reemplaza estos tokens; los demás
(`sello`, `blanco`, `resaltador`, `tinta-oscura` y `funcionario`) son iguales en los dos modos.

| Token | Oscuro |
|---|---|
| papel | `#0A1626` |
| papel-2 | `#182C47` |
| hoja | `#11223A` |
| renglon | `#2A4060` |
| borde-control | `#7088A6` |
| tinta | `#E6EDF5` |
| tinta-suave | `#A8B8CB` |
| sello-fuerte | `#0A5CAD` |
| sello-texto | `#8CC2F5` |
| sello-suave | `#163A60` |
| burbuja | `#24476E` |
| funcionario-texto | `#6FD08C` |
| advertencia | `#F2C56B` |
| advertencia-suave | `#2E2408` |
| advertencia-borde | `#8A6A1C` |
| error | `#FF9D91` |
| error-suave | `#3A1714` |
| celda-acierto | `#6AAEF0` |
| celda-error | `#FF7B6E` |

- El tema se marca con `data-tema="claro|oscuro"` en `<html>`.
- Un archivo pequeño en el `<head>` lo fija antes de pintar la página: usa la elección guardada o,
  si no hay ninguna, `prefers-color-scheme`.
- El widget sigue el tema de la página que lo inserta. Sin esa página, sigue `prefers-color-scheme`.

## Typography

- `titulo` (Archivo, semicondensada) se usa en los títulos, las bandas, los identificadores de
  caso y las cifras grandes.
- `texto` (Atkinson Hyperlegible Next) se usa en todo lo demás, incluido el rótulo. Los mensajes
  del widget van en `base`, para lectores mayores o con baja visión.
- Los títulos se escriben en oración, nunca en mayúsculas espaciadas.
- Las tablas y los identificadores llevan cifras tabulares.
- Las fuentes son autoalojadas, con fontsource y sin CDN.

## Layout

- El texto va alineado a la izquierda, con líneas de 65 a 75 caracteres.
- En escritorio, la OVT deja libre la columna derecha para el panel del widget. El encabezado y
  el contenido usan la misma columna, que llega hasta el borde del panel.
- Desde 360 px no hay desplazamiento horizontal. La matriz de la consola es la excepción: avisa
  que se desliza.
- Una lista de datos se escribe como renglones, no como tarjetas. Las excepciones son «Qué puedes
  probar» y las sugerencias del widget, que orientan en lugar de listar datos: tarjetas con ícono,
  sin sombra, en dos columnas en escritorio y en una en el celular. Los campos relacionados van
  en casillas unidas: el filete entre ellas es el fondo `borde-control`.

## Elevation & Depth

Solo el panel flotante del widget y su botón llevan sombra. El panel lleva además un filete de
1 px: muy tenue en el modo claro y de `renglon` en el oscuro, donde la sombra casi no se ve. Las
secciones se separan con bordes, bandas y renglones.

## Shapes

- El radio depende del papel: `control` en botones y campos, `casilla` en casillas, folios y
  bandas, y `mensaje` en los mensajes del widget.
- La esquina de un mensaje que toca la pestaña de quien habla queda recta.
- Nada usa forma de píldora.

## Components

- **Rótulo:** franja delgada (unos 38 px en una línea; en el celular ocupa dos), fija arriba y
  siempre visible, con el texto exacto «Entorno simulado de pruebas — no es la Oficina Virtual
  Tributaria real» en 14 a 15 px seminegrita, el ícono de aviso y el ámbar de los avisos
  (`advertencia` sobre `advertencia-suave`, con un filete de `advertencia-borde`). La consola lleva
  su versión: «Entorno simulado de pruebas con datos sintéticos». Antes era una franja grande de
  `resaltador`; la franja delgada la aprobó Rodolfo.
- **Encabezado de portal:** barra de `sello` con texto `blanco` bajo el rótulo, con el nombre de la
  página («OVT simulada» o «Consola»), un subtítulo corto y, a la derecha, el interruptor del tema.
  En la consola lleva también el estado del servicio (punto blanco lleno si está bien y vacío si no)
  y el enlace a las trazas.
- **Banda:** el título de un bloque (sesión simulada, caso, matriz, tabla por categoría) en un
  rectángulo de `sello` con texto `blanco`. Las bandas y el encabezado de portal concentran la
  audacia de la página; lo demás queda en tinta sobre papel.
- **Casilla:** el campo con su rótulo pequeño arriba, dentro del borde. El foco rodea la casilla
  entera.
- **Antes de empezar:** el recuadro del widget al abrir. Lleva una banda de `sello-suave` y el aviso
  de IA en `tinta`. Debajo, separado por un renglón, va el aviso de datos personales en `sm` y
  `tinta-suave`. Al abrir el widget, el recuadro se ve completo, también en el celular.
- **Pestaña de quien habla:** el nombre del interlocutor, como pestaña de carpeta pegada a su
  mensaje.
- **Pestañas de la consola:** la activa es un relleno de `sello` con una marca superior de
  `sello-texto`, que la distingue de las inactivas en los dos modos.
- **Interruptor «Modo oscuro»:** está en el encabezado de la OVT y de la consola. Es un botón con
  `role="switch"` y `aria-checked`: un riel con esquinas de `control` y una perilla cuadrada blanca
  con el sol (claro) o la luna (oscuro); encendido, el riel se llena de `tinta-oscura`. El cambio de
  tema es instantáneo y no hace transiciones.
- **Tarjeta:** `hoja` con un filete de `renglon`, radio de `casilla` y sin sombra; el ícono va en un
  cuadro de `sello-suave` con `sello-texto`.
- **Íconos:** de trazo, propios (`src/iconos.jsx`, sin librerías) y decorativos (`aria-hidden`),
  siempre junto a un texto que dice lo mismo.
- **Movimiento:** solo responde a una acción.
  - Un mensaje que llega o el caso que se abre aparece con un fundido y un desplazamiento corto,
    con salida suave.
  - El panel se abre y se cierra con la misma curva.
  - Un botón pulsado cede un poco de escala.
  - Con `prefers-reduced-motion`, nada se desplaza ni cambia de escala, y los puntos de
    «escribiendo» quedan quietos.

## Do's and Don'ts

- Do: conservar el texto exacto del rótulo, siempre visible, en su franja delgada de aviso.
- Don't: usar marcas, logos, colores ni nombres reales (Alcaldía de Bogotá, Secretaría de
  Hacienda, DIAN o bancos), ni copiar el estilo de un producto real. La única excepción son los
  colores del logo de Realtix (ver Colors).
- Don't: poner fotos ni imágenes en la OVT; solo los íconos de trazo decorativos.
- Don't: dar al azul degradados, brillos ni íconos de magia o destellos.
- Don't: juntar el verde y el azul con texto (1,7:1).
- Don't: poner el logo o los nombres de Realtix o RealSit en las páginas; solo se usan sus colores.
- Don't: poner etiquetas en mayúsculas sobre los títulos ni unir datos con puntos medios.
- Don't: agregar librerías de interfaz o de animación. Las fuentes nuevas solo entran como
  paquetes de fontsource con versión exacta.
