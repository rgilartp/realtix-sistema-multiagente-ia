// Tema claro u oscuro (web/DESIGN.md). public/tema.js fija data-tema en <html> antes de pintar;
// aquí están el interruptor de la OVT simulada y de la consola, y el cambio que también usa el widget.
import { useEffect, useState } from "react";

import { IconoLuna, IconoSol } from "./iconos.jsx";

const CLAVE = "tema";
export const TEMAS = ["claro", "oscuro"];
// La elección de esta visita, por si el almacenamiento falla: así un cambio del tema del sistema
// no la deshace.
let elegido = null;

const temaActual = () => (document.documentElement.getAttribute("data-tema") === "oscuro" ? "oscuro" : "claro");

function guardado() {
  if (elegido) return elegido;
  try {
    const valor = window.localStorage.getItem(CLAVE);
    return TEMAS.includes(valor) ? valor : null;
  } catch {
    return null; // sin almacenamiento, la página funciona igual
  }
}

// Cambia el tema de golpe: durante ese cuadro nada hace transición (los botones no se
// desvanecen a destiempo).
export function aplicarTema(tema) {
  const raiz = document.documentElement;
  raiz.classList.add("cambiando-tema");
  raiz.setAttribute("data-tema", tema);
  window.getComputedStyle(raiz).color; // aplica los colores nuevos sin transición
  requestAnimationFrame(() => raiz.classList.remove("cambiando-tema"));
}

// Interruptor «Modo oscuro» (role="switch"), con el sol o la luna en la perilla.
export function BotonTema() {
  const [tema, setTema] = useState(temaActual);

  // Sin una elección guardada, sigue al sistema mientras la página está abierta.
  useEffect(() => {
    const consulta = window.matchMedia("(prefers-color-scheme: dark)");
    const seguir = (evento) => {
      if (guardado()) return;
      const nuevo = evento.matches ? "oscuro" : "claro";
      aplicarTema(nuevo);
      setTema(nuevo);
    };
    consulta.addEventListener("change", seguir);
    return () => consulta.removeEventListener("change", seguir);
  }, []);

  const cambiar = () => {
    const nuevo = tema === "oscuro" ? "claro" : "oscuro";
    aplicarTema(nuevo);
    setTema(nuevo);
    elegido = nuevo;
    try {
      window.localStorage.setItem(CLAVE, nuevo);
    } catch {
      /* no se recuerda, pero el tema cambia */
    }
  };

  const oscuro = tema === "oscuro";
  return (
    <button
      type="button"
      role="switch"
      aria-checked={oscuro}
      onClick={cambiar}
      data-prueba="boton-tema"
      className="interruptor inline-flex min-h-11 shrink-0 items-center gap-2.5 text-sm font-semibold"
    >
      <span aria-hidden="true" className="interruptor-riel">
        <span className="interruptor-perilla">{oscuro ? <IconoLuna tamano={14} /> : <IconoSol tamano={14} />}</span>
      </span>
      Modo oscuro
    </button>
  );
}
