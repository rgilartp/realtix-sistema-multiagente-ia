// Íconos de trazo propios (sin librerías), decorativos: siempre van junto a un texto que dice lo
// mismo, así que llevan aria-hidden. Heredan el color del texto (currentColor).
function Icono({ tamano = 20, className = "", children }) {
  return (
    <svg
      viewBox="0 0 24 24"
      width={tamano}
      height={tamano}
      aria-hidden="true"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={`shrink-0 ${className}`}
    >
      {children}
    </svg>
  );
}

export const IconoAviso = (props) => (
  <Icono {...props}>
    <path d="M12 3.8 2.6 19.8h18.8L12 3.8Z" />
    <path d="M12 10v4.4" />
    <path d="M12 17.2h.01" strokeWidth="2.4" />
  </Icono>
);

export const IconoSol = (props) => (
  <Icono {...props}>
    <circle cx="12" cy="12" r="4" />
    <path d="M12 2.5v2M12 19.5v2M2.5 12h2M19.5 12h2M5.3 5.3l1.4 1.4M17.3 17.3l1.4 1.4M5.3 18.7l1.4-1.4M17.3 6.7l1.4-1.4" />
  </Icono>
);

export const IconoLuna = (props) => (
  <Icono {...props}>
    <path d="M20 14.6A8.2 8.2 0 0 1 9.4 4a8.2 8.2 0 1 0 10.6 10.6Z" />
  </Icono>
);

// Consultas generales: un libro abierto (las normas y el manual).
export const IconoLibro = (props) => (
  <Icono {...props}>
    <path d="M3 5.5c3-1 6-.8 9 1.2 3-2 6-2.2 9-1.2v13c-3-1-6-.8-9 1.2-3-2-6-2.2-9-1.2v-13Z" />
    <path d="M12 6.7v13" />
  </Icono>
);

// Tu cuenta: el predio.
export const IconoPredio = (props) => (
  <Icono {...props}>
    <path d="M3.5 11 12 4l8.5 7" />
    <path d="M6 9.5V20h12V9.5" />
    <path d="M10 20v-5h4v5" />
  </Icono>
);

// Tu recibo: un recibo con el borde inferior troquelado.
export const IconoRecibo = (props) => (
  <Icono {...props}>
    <path d="M6 3h12v18l-2-1.4-2 1.4-2-1.4-2 1.4-2-1.4L6 21V3Z" />
    <path d="M9 8h6M9 11.5h6M9 15h3.5" />
  </Icono>
);

// Un funcionario: una persona.
export const IconoPersona = (props) => (
  <Icono {...props}>
    <circle cx="12" cy="8" r="3.6" />
    <path d="M4.8 20.2c.9-3.9 3.8-6 7.2-6s6.3 2.1 7.2 6" />
  </Icono>
);

// Fechas y plazos.
export const IconoCalendario = (props) => (
  <Icono {...props}>
    <rect x="3.5" y="5" width="17" height="15.5" rx="1.5" />
    <path d="M3.5 9.5h17M8 3v4M16 3v4" />
  </Icono>
);
