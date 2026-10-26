// Widget del sistema multiagente de IA (RF-UI-01 a RF-UI-04 y RF-SYS-06).
//
// - Aviso de IA al abrir, antes de cualquier respuesta, con el botón «Hablar con un funcionario».
// - Indicador visible del interlocutor: asistente de IA, funcionario o mensaje del sistema.
// - Carga de recibos (JPG, PNG o PDF de hasta 5 MB) desde la conversación.
// - Mensaje de fuera de horario destacado (RNF-07).
// - Con la conversación escalada, consulta cada 5 s los mensajes nuevos del funcionario.
import { useCallback, useEffect, useRef, useState } from "react";

import {
  AVISO_IA,
  SIN_CONEXION,
  TAMANO_MAXIMO_MB,
  TIPOS_ADMITIDOS,
  enviarDocumento,
  enviarMensaje,
  mensajesNuevos,
  nuevaConversacion,
  pedirFuncionario,
} from "../api.js";

const CONSULTA_MS = 5000;
const ROTULOS = {
  agente: "Asistente de IA",
  funcionario: "Funcionario",
  sistema: "Mensaje del sistema",
};
const ESTILOS_ESTADO = {
  fuera_de_horario: "border-amber-300 bg-amber-50 text-amber-950",
  escalada: "border-sky-300 bg-sky-50 text-sky-950",
  aviso_sesion: "border-violet-300 bg-violet-50 text-violet-950",
  rechazo_acceso: "border-rose-300 bg-rose-50 text-rose-950",
};
const ORIGENES_PERMITIDOS = [
  window.location.origin,
  ...(import.meta.env.VITE_ORIGENES_OVT ?? "").split(",").map((o) => o.trim()).filter(Boolean),
];

function Burbuja({ mensaje }) {
  if (mensaje.autor === "contribuyente") {
    return (
      <div className="flex justify-end">
        <p className="max-w-[85%] rounded-2xl rounded-br-sm bg-emerald-700 px-3 py-2 text-sm whitespace-pre-line text-white">
          {mensaje.texto}
        </p>
      </div>
    );
  }
  const estilo = ESTILOS_ESTADO[mensaje.estado] ?? "border-slate-200 bg-white text-slate-900";
  return (
    <div className="flex flex-col items-start gap-1" data-autor={mensaje.autor}>
      <span className="text-xs font-semibold text-slate-500">{ROTULOS[mensaje.autor]}</span>
      <p className={`max-w-[90%] rounded-2xl rounded-bl-sm border px-3 py-2 text-sm whitespace-pre-line ${estilo}`}>
        {mensaje.texto}
      </p>
    </div>
  );
}

export default function Widget() {
  const [token, setToken] = useState(null);
  // Una conversación nueva por carga y por sesión: los mensajes no se guardan en el navegador.
  const [conversacion, setConversacion] = useState(nuevaConversacion);
  const tokenActual = useRef(null);
  const [mensajes, setMensajes] = useState([]);
  const [texto, setTexto] = useState("");
  const [ocupado, setOcupado] = useState(false);
  const [escalada, setEscalada] = useState(false);
  const [interlocutor, setInterlocutor] = useState("agente");
  const desde = useRef(null);
  const archivo = useRef(null);
  const final = useRef(null);

  const reiniciar = useCallback(() => {
    setConversacion(nuevaConversacion());
    setMensajes([]);
    setEscalada(false);
    setInterlocutor("agente");
    desde.current = null;
  }, []);

  // El token de la OVT llega por postMessage desde la página que inserta el widget.
  useEffect(() => {
    function recibir(evento) {
      if (!ORIGENES_PERMITIDOS.includes(evento.origin)) return;
      if (evento.data?.tipo !== "realtix-sesion") return;
      const nuevo = evento.data.token ?? null;
      if (nuevo === tokenActual.current) return;
      tokenActual.current = nuevo;
      setToken(nuevo);
      reiniciar(); // otra sesión: otra conversación
    }
    window.addEventListener("message", recibir);
    if (window.parent !== window) {
      for (const origen of ORIGENES_PERMITIDOS) {
        window.parent.postMessage({ tipo: "realtix-widget-listo" }, origen);
      }
    }
    return () => window.removeEventListener("message", recibir);
  }, [reiniciar]);

  useEffect(() => {
    final.current?.scrollIntoView?.({ block: "end" });
  }, [mensajes]);

  const agregar = (...nuevos) => setMensajes((lista) => [...lista, ...nuevos]);

  const recibir = (respuesta) => {
    agregar({ autor: respuesta.interlocutor, texto: respuesta.respuesta, estado: respuesta.estado });
    setInterlocutor(respuesta.interlocutor);
    if (respuesta.estado === "escalada") setEscalada(true);
  };

  const conEspera = async (accion) => {
    setOcupado(true);
    try {
      recibir(await accion());
    } catch (error) {
      agregar({ autor: "sistema", texto: error?.message || SIN_CONEXION, estado: "error" });
    } finally {
      setOcupado(false);
    }
  };

  const enviar = async (evento) => {
    evento.preventDefault();
    const limpio = texto.trim();
    if (!limpio || ocupado) return;
    setTexto("");
    agregar({ autor: "contribuyente", texto: limpio });
    await conEspera(() => enviarMensaje(conversacion, limpio, token));
  };

  const adjuntar = async (evento) => {
    const elegido = evento.target.files?.[0];
    evento.target.value = "";
    if (!elegido) return;
    if (!TIPOS_ADMITIDOS.includes(elegido.type)) {
      agregar({ autor: "sistema", texto: "Solo puedo recibir el recibo en JPG, PNG o PDF.", estado: "error" });
      return;
    }
    if (elegido.size > TAMANO_MAXIMO_MB * 1024 * 1024) {
      agregar({
        autor: "sistema",
        texto: `El archivo pesa más de ${TAMANO_MAXIMO_MB} MB. Envía una foto o un PDF más liviano.`,
        estado: "error",
      });
      return;
    }
    agregar({ autor: "contribuyente", texto: `📎 ${elegido.name}` });
    await conEspera(() => enviarDocumento(conversacion, elegido, texto.trim(), token));
    setTexto("");
  };

  const funcionario = async () => {
    if (ocupado) return;
    agregar({ autor: "contribuyente", texto: "Quiero hablar con un funcionario" });
    await conEspera(() => pedirFuncionario(conversacion, token));
  };

  // Conversación escalada: mensajes nuevos del funcionario (RF-ESC-05 y RF-UI-03).
  useEffect(() => {
    if (!escalada) return undefined;
    let activo = true;
    async function consultar() {
      try {
        const datos = await mensajesNuevos(conversacion, desde.current ?? 0, token);
        if (!activo) return;
        if (desde.current !== null) {
          const nuevos = datos.mensajes.filter((m) => m.autor === "funcionario");
          if (nuevos.length) {
            agregar(...nuevos.map((m) => ({ autor: "funcionario", texto: m.texto })));
            setInterlocutor("funcionario");
          }
        }
        desde.current = datos.siguiente;
      } catch {
        /* se reintenta en la siguiente consulta */
      }
    }
    consultar();
    const temporizador = setInterval(consultar, CONSULTA_MS);
    return () => {
      activo = false;
      clearInterval(temporizador);
    };
  }, [escalada, conversacion, token]);

  const estadoActual = escalada
    ? interlocutor === "funcionario"
      ? "Te atiende un funcionario"
      : "Tu caso está con un funcionario"
    : "Te atiende un asistente de IA";

  return (
    <div className="flex h-screen flex-col bg-slate-50 text-slate-900">
      <header className="flex items-center justify-between gap-2 border-b border-slate-200 bg-emerald-800 px-4 py-3 text-white">
        <div>
          <h1 className="text-base font-semibold">Asistente tributario</h1>
          <p className="text-xs text-emerald-100" data-prueba="interlocutor" aria-live="polite">
            {estadoActual}
          </p>
        </div>
        <span className="rounded-full bg-white/15 px-2 py-0.5 text-[11px]">
          {token ? "Sesión iniciada" : "Sin sesión"}
        </span>
      </header>

      <main className="flex-1 space-y-3 overflow-y-auto px-4 py-4" aria-live="polite">
        <section
          className="rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-950"
          data-prueba="aviso-ia"
        >
          <p>{AVISO_IA}.</p>
          <button
            type="button"
            onClick={funcionario}
            disabled={ocupado || escalada}
            className="mt-2 rounded-lg border border-emerald-700 px-3 py-1 text-sm font-medium text-emerald-800 hover:bg-emerald-100 disabled:opacity-50"
          >
            Hablar con un funcionario
          </button>
        </section>
        {mensajes.map((mensaje, i) => (
          <Burbuja key={i} mensaje={mensaje} />
        ))}
        {ocupado && <p className="text-xs text-slate-500">El asistente está escribiendo…</p>}
        <div ref={final} />
      </main>

      <form onSubmit={enviar} className="flex items-center gap-2 border-t border-slate-200 bg-white p-3">
        <input
          ref={archivo}
          type="file"
          accept=".jpg,.jpeg,.png,.pdf,image/jpeg,image/png,application/pdf"
          className="hidden"
          onChange={adjuntar}
          data-prueba="archivo"
        />
        <button
          type="button"
          onClick={() => archivo.current?.click()}
          disabled={ocupado}
          title="Adjuntar recibo (JPG, PNG o PDF)"
          aria-label="Adjuntar recibo"
          className="rounded-lg border border-slate-300 px-2 py-2 text-sm hover:bg-slate-100 disabled:opacity-50"
        >
          📎
        </button>
        <label htmlFor="mensaje" className="sr-only">
          Escribe tu consulta
        </label>
        <input
          id="mensaje"
          value={texto}
          onChange={(e) => setTexto(e.target.value)}
          maxLength={2000}
          placeholder="Escribe tu consulta"
          className="min-w-0 flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-emerald-600 focus:outline-none"
        />
        <button
          type="submit"
          disabled={ocupado || !texto.trim()}
          className="rounded-lg bg-emerald-700 px-3 py-2 text-sm font-medium text-white hover:bg-emerald-800 disabled:opacity-50"
        >
          Enviar
        </button>
      </form>
    </div>
  );
}
