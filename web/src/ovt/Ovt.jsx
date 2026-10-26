// OVT simulada (ADR-07 y sección 4.2): página de pruebas, sin logos ni marcas reales, con el
// selector de usuarios de prueba. Inserta el widget con una etiqueta de script que monta un
// iframe y le pasa el token de la sesión simulada.
import { useEffect, useState } from "react";

import { obtener, publicar } from "../api.js";

export const ROTULO = "Entorno simulado de pruebas — no es la Oficina Virtual Tributaria real";

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
      .then(setUsuarios)
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
    fijar(null);
  };

  return (
    <div className="min-h-screen bg-slate-100 text-slate-900">
      <div
        role="note"
        className="bg-amber-400 px-4 py-4 text-center text-xl font-bold text-amber-950 md:text-2xl"
        data-prueba="rotulo"
      >
        {ROTULO}
      </div>
      <div className="mx-auto max-w-3xl space-y-6 px-4 py-8">
        <header className="space-y-1">
          <h1 className="text-2xl font-semibold">OVT simulada</h1>
          <p className="text-sm text-slate-600">
            Página de pruebas del sistema multiagente de IA, con datos sintéticos. Elige un usuario
            de prueba para iniciar una sesión simulada; el asistente aparece abajo a la derecha.
          </p>
        </header>

        <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          {sesion ? (
            <div className="flex flex-wrap items-center justify-between gap-3">
              <p data-prueba="sesion">
                Sesión simulada de <strong>{sesion.nombre ?? sesion.usuario}</strong> ({sesion.usuario})
              </p>
              <button
                type="button"
                onClick={cerrar}
                className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm hover:bg-slate-100"
              >
                Cerrar sesión
              </button>
            </div>
          ) : (
            <form onSubmit={iniciar} className="flex flex-wrap items-end gap-3">
              <label className="flex flex-col gap-1 text-sm">
                Usuario de prueba
                <select
                  value={elegido}
                  onChange={(e) => setElegido(e.target.value)}
                  className="rounded-lg border border-slate-300 px-3 py-2"
                  data-prueba="usuario"
                >
                  <option value="">Elige un usuario</option>
                  {usuarios.map((u) => (
                    <option key={u.usuario} value={u.usuario}>
                      {u.usuario} · {u.nombre} ({u.tipo_persona})
                    </option>
                  ))}
                </select>
              </label>
              <button
                type="submit"
                disabled={!elegido}
                className="rounded-lg bg-slate-800 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
              >
                Iniciar sesión simulada
              </button>
            </form>
          )}
          {aviso && <p className="mt-3 text-sm text-rose-700">{aviso}</p>}
        </section>

        <section className="rounded-xl border border-dashed border-slate-300 p-5 text-sm text-slate-600">
          Sin sesión, el asistente responde consultas generales. Con sesión, también las de los
          predios del usuario de prueba elegido.
        </section>
      </div>
    </div>
  );
}
