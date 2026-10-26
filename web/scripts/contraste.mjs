// Contraste WCAG 2.2 de la paleta de la web (web/DESIGN.md). Lee los colores de src/estilos.css y
// revisa cada par de texto (4,5:1), de control y de foco (3:1), y las celdas más intensas de la
// matriz de la consola (texto en tinta, 4,5:1). Uso: `npm run contraste`; sale con 1 si algo falla.
import { readFileSync } from "node:fs";

const css = readFileSync(new URL("../src/estilos.css", import.meta.url), "utf8");
const color = Object.fromEntries([...css.matchAll(/--color-([\w-]+):\s*(#[0-9a-f]{6})/gi)].map((m) => [m[1], m[2]]));
const consola = readFileSync(new URL("../src/consola/Consola.jsx", import.meta.url), "utf8");
const tope = {
  acierto: Number(/const TOPE_ACIERTO = (\d+);/.exec(consola)?.[1]),
  error: Number(/const TOPE_ERROR = (\d+);/.exec(consola)?.[1]),
};

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
// color-mix(in srgb, c p%, white), como la usa fondoCelda en Consola.jsx.
const mezcla = (hex, p) =>
  "#" + rgb(hex).map((v) => Math.round((v * p + 1 * (100 - p)) / 100 * 255).toString(16).padStart(2, "0")).join("");

const PARES = [
  // [qué, primer plano, fondo, mínimo]
  ["texto en papel", "tinta", "papel", 4.5],
  ["texto en hoja", "tinta", "hoja", 4.5],
  ["texto suave en papel", "tinta-suave", "papel", 4.5],
  ["texto suave en hoja", "tinta-suave", "hoja", 4.5],
  ["texto suave en zona secundaria", "tinta-suave", "papel-2", 4.5],
  ["sello en hoja (enlaces, pestañas)", "sello", "hoja", 4.5],
  ["sello en papel", "sello", "papel", 4.5],
  ["blanco en sello (bandas, botones)", "hoja", "sello", 4.5],
  ["blanco en sello fuerte (hover)", "hoja", "sello-fuerte", 4.5],
  ["sello en sello suave", "sello", "sello-suave", 4.5],
  ["blanco en tinta (burbuja del contribuyente)", "hoja", "tinta", 4.5],
  ["tinta en resaltador (rótulo)", "tinta", "resaltador", 4.5],
  ["funcionario en hoja", "funcionario", "hoja", 4.5],
  ["funcionario en su fondo", "funcionario", "funcionario-suave", 4.5],
  ["ámbar en su fondo (fuera de horario)", "advertencia", "advertencia-suave", 4.5],
  ["error en su fondo", "error", "error-suave", 4.5],
  ["borde de control en hoja", "borde-control", "hoja", 3],
  ["borde de control en papel", "borde-control", "papel", 3],
  // Foco: anillo frente a lo que lo rodea
  ["foco sello sobre papel", "sello", "papel", 3],
  ["foco sello sobre hoja", "sello", "hoja", 3],
  ["foco resaltador sobre sello (cabecera, bandas, pestañas)", "resaltador", "sello", 3],
  ["foco blanco sobre sello", "hoja", "sello", 3],
  ["foco tinta del botón del panel sobre papel", "tinta", "papel", 3],
  ["foco tinta sobre el caso elegido", "tinta", "sello-suave", 3],
];

let fallas = 0;
const linea = (que, valor, minimo) => {
  const ok = valor >= minimo;
  if (!ok) fallas += 1;
  console.log(`${ok ? "ok  " : "FALLA"} ${valor.toFixed(2).padStart(6)}:1  (mín. ${minimo})  ${que}`);
};

for (const [que, a, b, minimo] of PARES) {
  if (!color[a] || !color[b]) {
    console.log(`FALLA falta el color ${color[a] ? b : a} (${que})`);
    fallas += 1;
    continue;
  }
  linea(que, contraste(color[a], color[b]), minimo);
}
// Matriz: la celda más intensa de cada tipo, con texto en tinta.
linea(`celda de acierto más intensa (sello al ${tope.acierto} %) con tinta`, contraste(color.tinta, mezcla(color.sello, tope.acierto)), 4.5);
linea(`celda de error más intensa (error al ${tope.error} %) con tinta`, contraste(color.tinta, mezcla(color.error, tope.error)), 4.5);

console.log(fallas ? `\n${fallas} pares por debajo del mínimo` : "\nTodos los pares cumplen WCAG 2.2 AA");
process.exit(fallas ? 1 : 0);
