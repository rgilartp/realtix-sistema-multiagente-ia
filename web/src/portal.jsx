// Rótulo de entorno simulado y encabezado de portal, comunes a la OVT simulada y a la consola
// (web/DESIGN.md).
import { IconoAviso } from "./iconos.jsx";
import { BotonTema } from "./tema.jsx";

// Franja delgada de aviso, fija arriba y siempre visible (secciones 4.2 y 8 de la especificación;
// la franja baja en lugar de «en grande» la aprobó Rodolfo).
export function Rotulo({ children, ...props }) {
  return (
    <div role="note" className="rotulo sticky top-0 z-10" {...props}>
      <IconoAviso tamano={18} />
      <span>{children}</span>
    </div>
  );
}

// Barra superior del portal: el nombre de la página, un subtítulo corto, lo que cada página agregue
// y el interruptor del tema. `columna` alinea el contenido con el de la página.
export function Encabezado({ titulo, subtitulo, columna, children }) {
  return (
    <header className="sobre-oscuro bg-sello text-blanco">
      <div className={`flex flex-wrap items-center justify-between gap-x-6 gap-y-2 py-3 ${columna}`}>
        <div className="min-w-0">
          <h1 className="text-xl leading-tight font-bold md:text-2xl">{titulo}</h1>
          <p className="mt-0.5 text-sm">{subtitulo}</p>
        </div>
        <div className="flex flex-wrap items-center gap-x-5 gap-y-1">
          {children}
          <BotonTema />
        </div>
      </div>
    </header>
  );
}
