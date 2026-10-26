// Widget del sistema multiagente de IA (RF-UI-01 a RF-UI-04 y RF-SYS-06).
//
// - Aviso de IA visible al abrir, antes de cualquier respuesta (RF-SYS-06).
// - Quién habla, con etiqueta y color: asistente de IA, funcionario o sistema (RF-UI-03).
// - «Hablar con un funcionario» siempre a la vista (RF-ESC-02).
// - Fuentes de cada respuesta como referencias discretas.
// - Fuera de horario destacado, con la hora en que vuelve a atender (RNF-07).
// - Carga de recibos (JPG, PNG o PDF de hasta 5 MB) validada en el navegador (RF-UI-04).
// - Con la conversación escalada, consulta cada 5 s los mensajes nuevos del funcionario.
import { useCallback, useEffect, useRef, useState } from "react";

import {
  AVISO_IA,
  TAMANO_MAXIMO_MB,
  TIPOS_ADMITIDOS,
  enviarDocumento,
  enviarMensaje,
  mensajeParaMostrar,
  mensajesNuevos,
  nuevaConversacion,
  pedirFuncionario,
} from "../api.js";

const CONSULTA_MS = 5000;
const ORIGENES_PERMITIDOS = [
  window.location.origin,
  ...(import.meta.env.VITE_ORIGENES_OVT ?? "").split(",").map((o) => o.trim()).filter(Boolean),
];
const SUGERENCIAS = [
  "¿Qué es el impuesto predial?",
  "¿Hasta cuándo pago el predial con descuento?",
  "¿Cuándo declaro el ICA este año?",
];
// Etiqueta y color de cada interlocutor: el color acompaña, la etiqueta informa.
const QUIEN = {
  agente: {
    etiqueta: "Asistente de IA",
    chip: "bg-acento-suave text-acento",
    burbuja: "border-l-acento",
  },
  funcionario: {
    etiqueta: "Funcionario",
    chip: "bg-exito-suave text-exito",
    burbuja: "border-l-exito",
  },
  sistema: {
    etiqueta: "Sistema",
    chip: "bg-superficie-2 text-tinta-suave",
    burbuja: "border-l-borde-control",
  },
};
const VUELVE = /Vuelvo a atender el (.+? [ap]\. m\.)/;

// La respuesta trae al final «Fuentes: A; B.»: se muestran como referencias aparte.
function separarFuentes(texto) {
  const corte = texto.lastIndexOf("\n\nFuentes: ");
  if (corte < 0) return { cuerpo: texto, fuentes: [] };
  const lista = texto.slice(corte + "\n\nFuentes: ".length).replace(/\.\s*$/, "");
  return { cuerpo: texto.slice(0, corte), fuentes: lista.split("; ").filter(Boolean) };
}

function IconoClip() {
  return (
    <svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 11.5 12.6 19.9a5.5 5.5 0 0 1-7.8-7.8l8.5-8.5a3.7 3.7 0 0 1 5.2 5.2l-8.5 8.5a1.8 1.8 0 0 1-2.6-2.6l7.8-7.8" />
    </svg>
  );
}

function IconoReloj() {
  return (
    <svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" className="shrink-0">
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v5l3 2" />
    </svg>
  );
}

function Etiqueta({ autor }) {
  const quien = QUIEN[autor] ?? QUIEN.sistema;
  return (
    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold ${quien.chip}`}>
      {quien.etiqueta}
    </span>
  );
}

function Burbuja({ mensaje }) {
  if (mensaje.autor === "contribuyente") {
    return (
      <div className="flex animate-entrada justify-end">
        <p className="max-w-[85%] rounded-burbuja rounded-br-md bg-acento-fuerte px-4 py-2.5 text-sm whitespace-pre-line text-white">
          {mensaje.archivo ? (
            <span className="inline-flex items-center gap-1.5">
              <IconoClip />
              <span className="sr-only">Archivo adjunto: </span>
              {mensaje.archivo}
            </span>
          ) : (
            mensaje.texto
          )}
        </p>
      </div>
    );
  }
  if (mensaje.estado === "fuera_de_horario") {
    const vuelve = VUELVE.exec(mensaje.texto)?.[1];
    return (
      <article className="animate-entrada space-y-2 rounded-2xl border border-advertencia-borde bg-advertencia-suave p-4" data-autor={mensaje.autor}>
        <div className="flex items-center gap-2">
          <Etiqueta autor={mensaje.autor} />
          <span className="text-xs font-semibold text-advertencia">Fuera del horario de atención</span>
        </div>
        {vuelve && (
          <p className="flex items-center gap-2 font-titulo text-base font-semibold text-advertencia">
            <IconoReloj />
            Vuelve a atender el {vuelve}
          </p>
        )}
        <p className="text-sm text-tinta">{mensaje.texto}</p>
      </article>
    );
  }
  const quien = QUIEN[mensaje.autor] ?? QUIEN.sistema;
  const problema = mensaje.estado === "error" || mensaje.estado === "rechazo_acceso";
  const { cuerpo, fuentes } = separarFuentes(mensaje.texto);
  return (
    <article className="flex animate-entrada flex-col items-start gap-1.5" data-autor={mensaje.autor}>
      <Etiqueta autor={mensaje.autor} />
      <div
        className={`max-w-[92%] rounded-burbuja rounded-tl-md border border-l-4 px-4 py-3 ${
          problema ? "border-error/40 border-l-error bg-error-suave" : `border-borde bg-superficie ${quien.burbuja}`
        }`}
      >
        <p className="text-sm whitespace-pre-line text-tinta">{cuerpo}</p>
        {fuentes.length > 0 && (
          <div className="mt-3 border-t border-borde pt-2">
            <p className="text-xs font-semibold tracking-wide text-tinta-suave uppercase">Fuentes</p>
            <ul className="mt-1 space-y-0.5 text-xs text-tinta-suave">
              {fuentes.map((f) => (
                <li key={f} className="flex gap-1.5">
                  <span aria-hidden="true">·</span>
                  {f}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </article>
  );
}

function Escribiendo() {
  return (
    <div className="flex animate-entrada items-center gap-2">
      <Etiqueta autor="agente" />
      <span className="flex gap-1 rounded-full bg-superficie px-3 py-2" aria-hidden="true">
        {[0, 150, 300].map((retraso) => (
          <span key={retraso} className="h-1.5 w-1.5 animate-punto rounded-full bg-acento" style={{ animationDelay: `${retraso}ms` }} />
        ))}
      </span>
      <span className="sr-only">El asistente está escribiendo</span>
    </div>
  );
}

export default function Widget() {
  const [token, setToken] = useState(null);
  // Una conversación nueva por carga y por sesión: los mensajes no se guardan en el navegador.
  const [conversacion, setConversacion] = useState(nuevaConversacion);
  const tokenActual = useRef(null);
  // La conversación vigente: una respuesta que llega después de cambiar de sesión se descarta.
  const conversacionActual = useRef(conversacion);
  conversacionActual.current = conversacion;
  const [mensajes, setMensajes] = useState([]);
  const [texto, setTexto] = useState("");
  const [ocupado, setOcupado] = useState(false);
  const [escalada, setEscalada] = useState(false);
  const [interlocutor, setInterlocutor] = useState("agente");
  const desde = useRef(null);
  const archivo = useRef(null);
  const final = useRef(null);

  const reiniciar = useCallback(() => {
    const nueva = nuevaConversacion();
    conversacionActual.current = nueva;
    setConversacion(nueva);
    setMensajes([]);
    setEscalada(false);
    setInterlocutor("agente");
    desde.current = null;
  }, []);

  // El token de la OVT llega por postMessage desde la página que inserta el widget.
  useEffect(() => {
    function recibir(evento) {
      if (evento.source !== window.parent || !ORIGENES_PERMITIDOS.includes(evento.origin)) return;
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
        try {
          window.parent.postMessage({ tipo: "realtix-widget-listo" }, origen);
        } catch {
          /* un origen mal configurado no rompe el widget */
        }
      }
    }
    return () => window.removeEventListener("message", recibir);
  }, [reiniciar]);

  useEffect(() => {
    final.current?.scrollIntoView?.({ block: "end" });
  }, [mensajes, ocupado]);

  const agregar = (...nuevos) => setMensajes((lista) => [...lista, ...nuevos]);

  const recibir = (respuesta) => {
    agregar({ autor: respuesta.interlocutor, texto: respuesta.respuesta, estado: respuesta.estado });
    setInterlocutor(respuesta.interlocutor);
    if (respuesta.estado === "escalada") setEscalada(true);
  };

  const conEspera = async (accion) => {
    const enCurso = conversacionActual.current;
    setOcupado(true);
    try {
      const respuesta = await accion();
      if (enCurso === conversacionActual.current) recibir(respuesta);
    } catch (error) {
      if (enCurso === conversacionActual.current) {
        agregar({ autor: "sistema", texto: mensajeParaMostrar(error), estado: "error" });
      }
    } finally {
      setOcupado(false);
    }
  };

  const preguntar = async (consulta) => {
    const limpio = consulta.trim();
    if (!limpio || ocupado) return;
    agregar({ autor: "contribuyente", texto: limpio });
    await conEspera(() => enviarMensaje(conversacion, limpio, token));
  };

  const enviar = async (evento) => {
    evento.preventDefault();
    const consulta = texto;
    setTexto("");
    await preguntar(consulta);
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
    agregar({ autor: "contribuyente", texto: elegido.name, archivo: elegido.name });
    const nota = texto.trim();
    setTexto("");
    await conEspera(() => enviarDocumento(conversacion, elegido, nota, token));
  };

  const funcionario = async () => {
    if (ocupado || escalada) return;
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
      } catch (error) {
        // Un 4xx no se arregla reintentando (conversación ajena o inexistente): se deja de
        // consultar; una falla de red se reintenta en la siguiente consulta.
        if (error?.estado >= 400 && error?.estado < 500) clearInterval(temporizador);
      }
    }
    const temporizador = setInterval(consultar, CONSULTA_MS);
    consultar();
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
  const punto = escalada ? "bg-exito-suave" : "bg-acento-suave";

  return (
    <div className="flex h-dvh flex-col bg-papel font-texto text-tinta">
      <header className="bg-acento px-4 pt-3 pb-3 text-white">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <h1 className="font-titulo text-lg leading-tight font-semibold">Asistente tributario</h1>
            <p className="mt-1 flex items-center gap-1.5 text-xs text-white" data-prueba="interlocutor" aria-live="polite">
              <span className={`inline-block h-2 w-2 rounded-full ${punto}`} aria-hidden="true" />
              {estadoActual}
            </p>
          </div>
          <span className="shrink-0 rounded-full border border-white/40 px-2.5 py-0.5 text-xs">
            {token ? "Sesión iniciada" : "Sin sesión"}
          </span>
        </div>
        <button
          type="button"
          onClick={funcionario}
          disabled={ocupado || escalada}
          className="mt-3 w-full rounded-lg bg-white px-3 py-2 text-sm font-semibold text-acento-fuerte transition-colors duration-150 ease-out hover:bg-acento-suave focus-visible:outline-white disabled:cursor-default disabled:bg-white/15 disabled:text-white disabled:hover:bg-white/15"
        >
          {escalada ? "Ya pediste un funcionario" : "Hablar con un funcionario"}
        </button>
      </header>

      <main className="flex-1 space-y-4 overflow-y-auto px-4 py-4" aria-live="polite" aria-relevant="additions">
        <section
          className="rounded-2xl border border-acento/25 bg-acento-suave p-4 text-sm text-tinta"
          data-prueba="aviso-ia"
          aria-label="Aviso de inteligencia artificial"
        >
          <p className="mb-1 font-titulo text-base font-semibold text-acento-fuerte">Antes de empezar</p>
          <p>{AVISO_IA}.</p>
        </section>

        {mensajes.length === 0 && !ocupado && (
          <section className="space-y-3 rounded-2xl border border-dashed border-borde-control/50 p-4" aria-label="Sugerencias">
            <p className="font-titulo text-base font-semibold">¿En qué te ayudo?</p>
            <p className="text-sm text-tinta-suave">
              Pregunta por el predial o el ICA, o adjunta tu recibo para revisarlo.
            </p>
            <div className="flex flex-wrap gap-2">
              {SUGERENCIAS.map((s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => preguntar(s)}
                  className="rounded-full border border-borde-control bg-superficie px-3 py-1.5 text-left text-xs text-tinta transition-colors duration-150 ease-out hover:border-acento hover:text-acento"
                >
                  {s}
                </button>
              ))}
            </div>
          </section>
        )}

        {mensajes.map((mensaje, i) => (
          <Burbuja key={i} mensaje={mensaje} />
        ))}
        {ocupado && <Escribiendo />}
        <div ref={final} />
      </main>

      <form onSubmit={enviar} className="border-t border-borde bg-superficie px-3 pt-3 pb-2">
        <div className="flex items-center gap-2">
          <input
            ref={archivo}
            id="recibo"
            type="file"
            accept=".jpg,.jpeg,.png,.pdf,image/jpeg,image/png,application/pdf"
            className="sr-only"
            onChange={adjuntar}
            data-prueba="archivo"
            tabIndex={-1}
          />
          <button
            type="button"
            onClick={() => archivo.current?.click()}
            disabled={ocupado}
            aria-label="Adjuntar recibo (JPG, PNG o PDF, hasta 5 MB)"
            className="grid h-11 w-11 shrink-0 place-items-center rounded-xl border border-borde-control text-tinta-suave transition-colors duration-150 ease-out hover:border-acento hover:text-acento disabled:opacity-50"
          >
            <IconoClip />
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
            autoComplete="off"
            className="h-11 min-w-0 flex-1 rounded-xl border border-borde-control bg-superficie px-3 text-sm text-tinta placeholder:text-tinta-suave focus:border-acento"
          />
          <button
            type="submit"
            disabled={ocupado || !texto.trim()}
            className="h-11 shrink-0 rounded-xl bg-acento px-4 text-sm font-semibold text-white transition-colors duration-150 ease-out hover:bg-acento-fuerte disabled:bg-superficie-2 disabled:text-tinta-suave"
          >
            Enviar
          </button>
        </div>
        <p className="mt-1.5 text-xs text-tinta-suave">
          Recibos en JPG, PNG o PDF, de hasta {TAMANO_MAXIMO_MB} MB · Entorno de pruebas con datos sintéticos
        </p>
      </form>
    </div>
  );
}
