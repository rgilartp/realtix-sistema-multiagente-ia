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
        className="franja-simulada sticky top-0 z-10 border-b-2 border-advertencia-borde px-4 py-4 text-center text-xl leading-snug font-bold text-advertencia sm:text-2xl md:py-5 md:text-3xl"
        data-prueba="rotulo"
      >
        {ROTULO}
      </div>

      {/* En escritorio, la columna derecha queda libre para el widget (400 px y su margen). */}
      <div className="mx-auto max-w-4xl px-4 pt-8 pb-28 sm:px-6 md:pt-12 lg:mr-[448px] lg:ml-[max(1.5rem,calc(50vw-40rem))] lg:max-w-3xl">
        <header className="max-w-2xl space-y-3">
          <p className="text-xs font-semibold tracking-[0.14em] text-acento uppercase">
            Datos sintéticos · Solo para pruebas
          </p>
          <h1 className="font-titulo text-3xl leading-tight font-semibold md:text-4xl">OVT simulada</h1>
          <p className="text-base text-tinta-suave">
            Esta página imita el portal donde vivirá el asistente. Elige un usuario de prueba para
            iniciar una sesión simulada: el asistente tributario la recibe sin que tengas que
            escribir nada.
          </p>
        </header>

        <section className="mt-8 rounded-2xl border border-borde bg-superficie p-5 shadow-panel md:p-6" aria-labelledby="titulo-sesion">
          <h2 id="titulo-sesion" className="font-titulo text-xl font-semibold">
            Sesión simulada
          </h2>
          {sesion ? (
            <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
              <p data-prueba="sesion" className="text-base">
                Sesión de <strong>{sesion.nombre ?? sesion.usuario}</strong>{" "}
                <span className="text-tinta-suave">({sesion.usuario})</span>
              </p>
              <button
                type="button"
                onClick={cerrar}
                className="rounded-xl border border-borde-control px-4 py-2 text-sm font-semibold transition-colors duration-150 ease-out hover:border-acento hover:text-acento"
              >
                Cerrar sesión
              </button>
            </div>
          ) : (
            <form onSubmit={iniciar} className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-end">
              <label className="flex flex-1 flex-col gap-1.5 text-sm font-semibold">
                Usuario de prueba
                <select
                  value={elegido}
                  onChange={(e) => setElegido(e.target.value)}
                  className="h-11 rounded-xl border border-borde-control bg-superficie px-3 text-base font-normal"
                  data-prueba="usuario"
                >
                  <option value="">Elige un usuario</option>
                  {usuarios.map((u) => (
                    <option key={u.usuario} value={u.usuario}>
                      {u.usuario} · {u.nombre} ({u.tipo_persona === "juridica" ? "persona jurídica" : "persona natural"})
                    </option>
                  ))}
                </select>
              </label>
              <button
                type="submit"
                disabled={!elegido}
                className="h-11 rounded-xl bg-acento px-5 text-sm font-semibold whitespace-nowrap text-white transition-colors duration-150 ease-out hover:bg-acento-fuerte disabled:bg-superficie-2 disabled:text-tinta-suave"
              >
                Iniciar sesión simulada
              </button>
            </form>
          )}
          {aviso && (
            <p className="mt-3 rounded-lg bg-error-suave px-3 py-2 text-sm text-error" role="alert">
              {aviso}
            </p>
          )}
        </section>

        <section className="mt-8" aria-labelledby="titulo-probar">
          <h2 id="titulo-probar" className="font-titulo text-xl font-semibold">
            Qué puedes probar
          </h2>
          <ul className="mt-4 grid gap-3 sm:grid-cols-2">
            {QUE_PROBAR.map(([titulo, texto]) => (
              <li key={titulo} className="rounded-2xl border border-borde bg-superficie p-4">
                <p className="font-semibold text-acento-fuerte">{titulo}</p>
                <p className="mt-1 text-sm text-tinta-suave">{texto}</p>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </div>
  );
}
