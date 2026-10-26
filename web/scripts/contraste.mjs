// Contraste WCAG 2.2 de la paleta de la web en sus dos modos (web/DESIGN.md). Lee los colores de
// src/estilos.css: el modo claro de @theme y el oscuro del bloque `:root[data-tema="oscuro"]`, que
// reemplaza a los claros. Revisa cada par de texto (4,5:1), de control y de foco (3:1), las celdas
// más intensas de la matriz de la consola (texto en tinta, 4,5:1) y los colores fijos de
// public/widget/embed.js. Uso: `npm run contraste`; sale con 1 si algo falla.
import { readFileSync } from "node:fs";

const leer = (ruta) => readFileSync(new URL(ruta, import.meta.url), "utf8");
const colores = (texto) =>
  Object.fromEntries([...texto.matchAll(/--color-([\w-]+):\s*(#[0-9a-f]{6})/gi)].map((m) => [m[1], m[2].toLowerCase()]));

const css = leer("../src/estilos.css");
const tema = /@theme\s*{([\s\S]*?)\n}/.exec(css)?.[1] ?? "";
const oscuro = /:root\[data-tema="oscuro"\]\s*{([\s\S]*?)}/.exec(css)?.[1] ?? "";
const claro = colores(tema);
const MODOS = { claro, oscuro: { ...claro, ...colores(oscuro) } };

const consola = leer("../src/consola/Consola.jsx");
const tope = {
  acierto: Number(/const TOPE_ACIERTO = (\d+);/.exec(consola)?.[1]),
  error: Number(/const TOPE_ERROR = (\d+);/.exec(consola)?.[1]),
};
const embed = leer("../public/widget/embed.js");
const colorEmbed = (modo, clave) =>
  new RegExp(`${modo}: {[^}]*${clave}: "(#[0-9a-f]{6})"`, "i").exec(embed)?.[1]?.toLowerCase();

const canal = (v) => (v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4);
const rgb = (hex) => [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255);
const luminancia = (hex) => {
  const [r, g, b] = rgb(hex).map(canal);
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
};
const contraste = (a, b) => {
  const [x, y] = [luminancia(a), luminancia(b)].sort((m, n) => n - m);
  return (x + 0.05) / (y + 0.05);
};
// color-mix(in srgb, c p%, base), como la usa fondoCelda en Consola.jsx (base: la hoja del modo).
const mezcla = (hex, p, base) => {
  const [c, h] = [rgb(hex), rgb(base)];
  return "#" + c.map((v, i) => Math.round(((v * p + h[i] * (100 - p)) / 100) * 255).toString(16).padStart(2, "0")).join("");
};

const PARES = [
  // [qué, primer plano, fondo, mínimo]
  ["texto en papel", "tinta", "papel", 4.5],
  ["texto en hoja", "tinta", "hoja", 4.5],
  ["texto suave en papel", "tinta-suave", "papel", 4.5],
  ["texto suave en hoja", "tinta-suave", "hoja", 4.5],
  ["texto suave en zona secundaria", "tinta-suave", "papel-2", 4.5],
  ["azul de texto en hoja (enlaces)", "sello-texto", "hoja", 4.5],
  ["azul de texto en papel", "sello-texto", "papel", 4.5],
  ["azul de texto en zona secundaria (pestañas)", "sello-texto", "papel-2", 4.5],
  ["azul de texto en azul suave", "sello-texto", "sello-suave", 4.5],
  ["blanco en azul (bandas, botones, cabecera)", "blanco", "sello", 4.5],
  ["blanco en azul fuerte (hover)", "blanco", "sello-fuerte", 4.5],
  ["azul en blanco (hover del botón de la cabecera)", "sello", "blanco", 4.5],
  ["blanco en la burbuja del contribuyente", "blanco", "burbuja", 4.5],
  ["tinta oscura en resaltador (rótulo)", "tinta-oscura", "resaltador", 4.5],
  ["blanco en verde (pestaña del funcionario)", "blanco", "funcionario", 4.5],
  ["verde de texto en hoja", "funcionario-texto", "hoja", 4.5],
  ["verde de texto en papel", "funcionario-texto", "papel", 4.5],
  ["verde de texto en zona secundaria", "funcionario-texto", "papel-2", 4.5],
  ["verde de texto en su fondo", "funcionario-texto", "funcionario-suave", 4.5],
  ["ámbar en su fondo (fuera de horario)", "advertencia", "advertencia-suave", 4.5],
  ["error en su fondo", "error", "error-suave", 4.5],
  ["error en hoja", "error", "hoja", 4.5],
  ["borde de control en hoja", "borde-control", "hoja", 3],
  ["borde de control en papel", "borde-control", "papel", 3],
  // Foco: anillo frente a lo que lo rodea
  ["foco azul sobre papel", "sello-texto", "papel", 3],
  ["foco azul sobre hoja", "sello-texto", "hoja", 3],
  ["anillo azul del caso elegido sobre azul suave", "sello-texto", "sello-suave", 3],
  ["foco resaltador sobre azul (cabecera, bandas, pestañas)", "resaltador", "sello", 3],
  ["foco tinta sobre el caso elegido", "tinta", "sello-suave", 3],
  ["puntos de «escribiendo» y barras del F1 sobre hoja", "sello-texto", "hoja", 3],
];

let fallas = 0;
const linea = (que, valor, minimo) => {
  const ok = valor >= minimo;
  if (!ok) fallas += 1;
  console.log(`${ok ? "ok  " : "FALLA"} ${valor.toFixed(2).padStart(6)}:1  (mín. ${minimo})  ${que}`);
};

for (const [modo, color] of Object.entries(MODOS)) {
  console.log(`\nModo ${modo}`);
  for (const [que, a, b, minimo] of PARES) {
    if (!color[a] || !color[b]) {
      console.log(`FALLA falta el color ${color[a] ? b : a} (${que})`);
      fallas += 1;
      continue;
    }
    linea(que, contraste(color[a], color[b]), minimo);
  }
  // Matriz: la celda más intensa de cada tipo, mezclada con la hoja, con texto en tinta.
  const acierto = mezcla(color["celda-acierto"], tope.acierto, color.hoja);
  const error = mezcla(color["celda-error"], tope.error, color.hoja);
  linea(`celda de acierto más intensa (${tope.acierto} %) con tinta`, contraste(color.tinta, acierto), 4.5);
  linea(`celda de error más intensa (${tope.error} %) con tinta`, contraste(color.tinta, error), 4.5);
  // embed.js: su fondo es el papel del modo y el foco del botón se ve sobre él.
  const [papel, foco] = [colorEmbed(modo, "papel"), colorEmbed(modo, "foco")];
  if (papel !== color.papel) {
    console.log(`FALLA embed.js usa ${papel} como papel y estilos.css, ${color.papel}`);
    fallas += 1;
  } else {
    linea("foco del botón del widget sobre el papel (embed.js)", contraste(foco, papel), 3);
  }
}

console.log(fallas ? `\n${fallas} pares por debajo del mínimo` : "\nTodos los pares cumplen WCAG 2.2 AA en los dos modos");
process.exit(fallas ? 1 : 0);
