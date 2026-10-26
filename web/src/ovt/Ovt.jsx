// OVT simulada (ADR-07 y sección 4.2): página de pruebas, sin logos ni marcas reales, con el
// selector de usuarios de prueba. Inserta el widget con una etiqueta de script que monta un
// iframe y le pasa el token de la sesión simulada.
import { useEffect, useState } from "react";

import { obtener, publicar } from "../api.js";

export const ROTULO = "Entorno simulado de pruebas — no es la Oficina Virtual Tributaria real";

const QUE_PROBAR = [
  ["Consultas generales", "Sin sesión: qué es el predial o el ICA, plazos y descuentos."],
  ["Tu cuenta", "Con sesión: lo que debes, tus pagos y una estimación del predial."],
  ["Tu recibo", "Adjunta el recibo sintético y confirma los datos que lee el asistente."],
  ["Un funcionario", "Pide que te atienda una persona en cualquier momento."],
];

function insertarWidget() {
  if (document.querySelector("script[data-realtix-embed]")) return;
  const script = document.createElement("script");
  script.src = "/widget/embed.js";
  script.dataset.realtixEmbed = "";
  document.body.appendChild(script);
}

export default function Ovt() {
  const [usuarios, setUsuarios] = useState([]);
  const [elegido, setElegido] = useState("");
  const [sesion, setSesion] = useState(null);
  const [aviso, setAviso] = useState("");

  useEffect(() => {
    insertarWidget();
    obtener("/api/v1/ovt-simulada/usuarios")
      .then((lista) => setUsuarios(Array.isArray(lista) ? lista : []))
      .catch(() => setAviso("No se pudo cargar la lista de usuarios de prueba."));
  }, []);

  const fijar = (token) => window.RealtixWidget?.fijarSesion(token);

  const iniciar = async (evento) => {
    evento.preventDefault();
    if (!elegido) return;
    try {
      const datos = await publicar("/api/v1/ovt-simulada/sesion", { usuario: elegido });
      setSesion(usuarios.find((u) => u.usuario === datos.usuario) ?? { usuario: datos.usuario });
      setAviso("");
      fijar(datos.token);
    } catch {
      setAviso("No se pudo iniciar la sesión simulada.");
    }
  };

  const cerrar = () => {
    setSesion(null);
    setElegido("");
    fijar(null);
  };

  return (
    <div className="min-h-dvh bg-papel font-texto text-tinta">
      <div
        role="note"
        data-realtix-respetar=""
        className="rotulo sticky top-0 z-10 px-4 py-3 text-center text-xl sm:text-2xl md:py-4 md:text-3xl"
        data-prueba="rotulo"
      >
        {ROTULO}
      </div>

      {/* En escritorio, la columna derecha queda libre para el widget (400 px y su margen). */}
      <div className="mx-auto max-w-4xl px-4 pt-8 pb-28 sm:px-6 md:pt-12 lg:mr-[448px] lg:ml-[max(1.5rem,calc(50vw-40rem))] lg:max-w-3xl">
        <header className="max-w-[65ch]">
          <h1 className="text-2xl font-bold md:text-3xl">OVT simulada</h1>
          <p className="mt-3 text-base text-tinta-suave">
            Esta página imita el portal donde vivirá el asistente. Elige un usuario de prueba para
            iniciar una sesión simulada: el asistente tributario la recibe sin que tengas que
            escribir nada. Todos los datos son sintéticos.
          </p>
        </header>

        <section className="mt-8 overflow-hidden rounded-casilla border border-sello bg-hoja" aria-labelledby="titulo-sesion">
          <h2 id="titulo-sesion" className="banda px-4 py-2 text-lg">
            Sesión simulada
          </h2>
          <div className="p-4 md:p-5">
            {sesion ? (
              <div className="flex flex-wrap items-center justify-between gap-3">
                <p data-prueba="sesion" className="text-base">
                  Sesión de <strong>{sesion.nombre ?? sesion.usuario}</strong>{" "}
                  <span className="text-tinta-suave">({sesion.usuario})</span>
                </p>
                <button
                  type="button"
                  onClick={cerrar}
                  className="min-h-11 rounded-control border border-borde-control bg-hoja px-4 text-sm font-semibold hover:border-sello hover:text-sello"
                >
                  Cerrar sesión
                </button>
              </div>
            ) : (
              <form onSubmit={iniciar} className="flex flex-col gap-3 sm:flex-row sm:items-stretch">
                <label className="casilla flex-1">
                  Usuario de prueba
                  <select value={elegido} onChange={(e) => setElegido(e.target.value)} data-prueba="usuario">
                    <option value="">Elige un usuario</option>
                    {usuarios.map((u) => (
                      <option key={u.usuario} value={u.usuario}>
                        {u.nombre} ({u.usuario}), {u.tipo_persona === "juridica" ? "persona jurídica" : "persona natural"}
                      </option>
                    ))}
                  </select>
                </label>
                <button
                  type="submit"
                  disabled={!elegido}
                  aria-describedby={elegido ? undefined : "ayuda-sesion"}
                  className="min-h-12 rounded-control bg-sello px-5 text-base font-semibold whitespace-nowrap text-hoja enabled:hover:bg-sello-fuerte disabled:bg-papel-2 disabled:text-tinta-suave"
                >
                  Iniciar sesión simulada
                </button>
              </form>
            )}
            {!sesion && !elegido && (
              <p id="ayuda-sesion" className="mt-2 text-sm text-tinta-suave">
                Elige un usuario para poder iniciar la sesión.
              </p>
            )}
            {aviso && (
              <p className="mt-3 rounded-casilla border border-error bg-error-suave px-3 py-2 text-sm text-error" role="alert">
                {aviso}
              </p>
            )}
          </div>
        </section>

        <section className="mt-10" aria-labelledby="titulo-probar">
          <h2 id="titulo-probar" className="text-xl font-bold">
            Qué puedes probar
          </h2>
          <dl className="mt-3 border-t border-renglon">
            {QUE_PROBAR.map(([titulo, texto]) => (
              <div key={titulo} className="grid gap-1 border-b border-renglon py-3 sm:grid-cols-[11rem_1fr] sm:gap-6">
                <dt className="font-semibold">{titulo}</dt>
                <dd className="text-tinta-suave">{texto}</dd>
              </div>
            ))}
          </dl>
        </section>
      </div>
    </div>
  );
}
