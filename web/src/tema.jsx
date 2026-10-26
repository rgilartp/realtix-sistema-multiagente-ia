// Tema claro u oscuro (web/DESIGN.md). public/tema.js fija data-tema en <html> antes de pintar;
// aquí están el botón de la OVT simulada y de la consola, y el cambio que también usa el widget.
import { useEffect, useState } from "react";

const CLAVE = "tema";
export const TEMAS = ["claro", "oscuro"];

const temaActual = () => (document.documentElement.getAttribute("data-tema") === "oscuro" ? "oscuro" : "claro");

function guardado() {
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

// Botón «Modo oscuro» (aria-pressed), con una casilla de formulario que se marca con una X.
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
      aria-pressed={oscuro}
      onClick={cambiar}
      data-prueba="boton-tema"
      className="inline-flex min-h-11 shrink-0 items-center gap-2 rounded-control border border-borde-control bg-hoja px-3 text-sm font-semibold text-tinta hover:border-sello-texto"
    >
      <span
        aria-hidden="true"
        className="grid h-5 w-5 place-items-center rounded-casilla border-2 border-tinta font-titulo text-sm leading-none font-bold"
      >
        {oscuro ? "X" : ""}
      </span>
      Modo oscuro
    </button>
  );
}
