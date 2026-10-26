---
version: alpha
name: Formulario y sello
description: Sistema visual de la OVT simulada, el widget del asistente tributario y la consola de funcionarios del sistema multiagente de IA.
colors:
  papel: "#ECF1EE"
  papel-2: "#DFE7E2"
  hoja: "#FFFFFF"
  renglon: "#C3D1CA"
  borde-control: "#6B7A75"
  tinta: "#1D2433"
  tinta-suave: "#4A5560"
  sello: "#4B2C85"
  sello-fuerte: "#3A1F6C"
  sello-suave: "#ECE6F5"
  resaltador: "#FFD54F"
  funcionario: "#24613F"
  funcionario-suave: "#E2F0E6"
  advertencia: "#6E4600"
  advertencia-suave: "#FFF3CC"
  advertencia-borde: "#C9962B"
  error: "#A3271F"
  error-suave: "#FBE9E7"
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
    backgroundColor: "{colors.resaltador}"
    textColor: "{colors.tinta}"
    typography: "{typography.titulo}"
  banda:
    backgroundColor: "{colors.sello}"
    textColor: "{colors.hoja}"
    typography: "{typography.titulo}"
    rounded: "{rounded.casilla}"
  casilla:
    backgroundColor: "{colors.hoja}"
    textColor: "{colors.tinta-suave}"
    rounded: "{rounded.casilla}"
  boton-principal:
    backgroundColor: "{colors.sello}"
    textColor: "{colors.hoja}"
    rounded: "{rounded.control}"
  boton-principal-hover:
    backgroundColor: "{colors.sello-fuerte}"
    textColor: "{colors.hoja}"
---

## Overview

La oficina virtual tributaria simulada de un municipio colombiano, su asistente de IA y la
consola de los funcionarios. La dirección sale de los materiales del trámite: el papel de
seguridad verde pálido de los recibos, las casillas de los formularios con su rótulo dentro del
borde, las bandas que encabezan cada bloque y la tinta morada de los sellos de radicado. No imita
ningún formulario, sello ni marca real. El tono es institucional y sobrio; la cercanía la dan la
letra legible y el lenguaje claro.

## Colors

- El fondo de las páginas es `papel`; lo que se lee o se llena va en `hoja`.
- `sello` es el único acento: el asistente de IA, las bandas, los botones principales y el foco.
  Es tinta plana.
- `resaltador` se reserva para el rótulo de entorno simulado y para el anillo de foco sobre
  `sello` o `tinta`.
- Quien habla tiene un color fijo y siempre su nombre escrito: `sello` para el asistente de IA,
  `funcionario` para el funcionario y `papel-2` con `tinta` para el sistema.
- `renglon` solo separa filas y bloques. El borde de cualquier control usa `borde-control`.
- Todo par de texto cumple 4,5:1 y todo control o anillo de foco, 3:1. `npm run contraste`
  lo mide, junto con las celdas más intensas de la matriz de la consola.

## Typography

- `titulo` (Archivo, semicondensada) se usa en el rótulo, los títulos, las
  bandas, los identificadores de caso y las cifras grandes.
- `texto` (Atkinson Hyperlegible Next) se usa en todo lo demás. Los mensajes del widget van en
  `base`, para lectores mayores o con baja visión.
- Los títulos se escriben en oración, nunca en mayúsculas espaciadas.
- Las tablas y los identificadores llevan cifras tabulares.
- Las fuentes son autoalojadas, con fontsource y sin CDN.

## Layout

- El texto va alineado a la izquierda, con líneas de 65 a 75 caracteres.
- En escritorio, la OVT deja libre la columna derecha para el panel del widget.
- Desde 360 px no hay desplazamiento horizontal. La matriz de la consola es la excepción: avisa
  que se desliza.
- Una lista de datos se escribe como renglones, no como tarjetas. Los campos relacionados van
  en casillas unidas: el filete entre ellas es el fondo `borde-control`.

## Elevation & Depth

Solo el panel flotante del widget y su botón llevan sombra. Las secciones se separan con bordes,
bandas y renglones.

## Shapes

- El radio depende del papel: `control` en botones y campos, `casilla` en casillas, folios y
  bandas, y `mensaje` en los mensajes del widget.
- La esquina de un mensaje que toca la pestaña de quien habla queda recta.
- Nada usa forma de píldora.

## Components

- **Rótulo:** franja fija arriba de la OVT con el texto exacto «Entorno simulado de pruebas — no
  es la Oficina Virtual Tributaria real», grande y con un filete inferior de `tinta`. La consola
  lleva una versión más baja.
- **Banda:** el título de un bloque (sesión simulada, caso, matriz, tabla por categoría) en un
  rectángulo de `sello` con texto `hoja`. Las bandas y el rótulo concentran la audacia de la
  página; lo demás queda en tinta sobre papel.
- **Casilla:** el campo con su rótulo pequeño arriba, dentro del borde. El foco rodea la casilla
  entera.
- **Pestaña de quien habla:** el nombre del interlocutor, como pestaña de carpeta pegada a su
  mensaje.
- **Movimiento:** solo responde a una acción.
  - Un mensaje que llega o el caso que se abre aparece con un fundido y un desplazamiento corto,
    con salida suave.
  - El panel se abre y se cierra con la misma curva.
  - Un botón pulsado cede un poco de escala.
  - Con `prefers-reduced-motion`, nada se desplaza ni cambia de escala, y los puntos de
    «escribiendo» quedan quietos.

## Do's and Don'ts

- Do: conservar el texto exacto del rótulo, grande y siempre visible.
- Don't: usar marcas, logos, colores ni nombres reales (Alcaldía de Bogotá, Secretaría de
  Hacienda, DIAN o bancos), ni copiar el estilo de un producto real.
- Don't: poner fotos ni imágenes en la OVT.
- Don't: dar al morado degradados, brillos ni íconos de magia o destellos.
- Don't: poner etiquetas en mayúsculas sobre los títulos ni unir datos con puntos medios.
- Don't: agregar librerías de interfaz o de animación. Las fuentes nuevas solo entran como
  paquetes de fontsource con versión exacta.
