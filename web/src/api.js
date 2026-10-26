// Cliente de la API del sistema multiagente de IA (contrato de la sección 3.8).
// Las rutas son relativas: en desarrollo las enruta Vite y en el servidor, el proxy.

export const AVISO_IA =
  "Te atiende un asistente de inteligencia artificial. Sus respuestas son orientativas y " +
  "puedes pedir que te atienda un funcionario en cualquier momento";
export const SIN_CONEXION =
  "No pude conectarme con el asistente. Revisa tu conexión e intenta de nuevo en unos minutos.";
export const TAMANO_MAXIMO_MB = 5;
export const TIPOS_ADMITIDOS = ["image/jpeg", "image/png", "application/pdf"];

function cabeceras(token, extra = {}) {
  return token ? { ...extra, Authorization: `Bearer ${token}` } : extra;
}

// Un error que se puede mostrar al contribuyente: el mensaje es de la API (en español) o el de
// «sin conexión». Cualquier otro error (red caída, respuesta que no es JSON) se convierte en este.
export class ErrorApi extends Error {
  constructor(mensaje, estado = 0) {
    super(mensaje);
    this.estado = estado;
  }
}

export function mensajeParaMostrar(error) {
  return error instanceof ErrorApi ? error.message : SIN_CONEXION;
}

async function pedir(ruta, opciones) {
  let respuesta;
  try {
    respuesta = await fetch(ruta, opciones);
  } catch {
    throw new ErrorApi(SIN_CONEXION); // la red falló: nunca «Failed to fetch»
  }
  return leer(respuesta);
}

// La API responde con el formato del chat también en los rechazos (413 y 415); en los demás
// errores, con {"detalle": …}. Ningún mensaje técnico llega al contribuyente.
async function leer(respuesta) {
  let cuerpo = null;
  try {
    cuerpo = await respuesta.json();
  } catch {
    cuerpo = null;
  }
  if (cuerpo && typeof cuerpo.respuesta === "string") return cuerpo;
  if (!respuesta.ok) throw new ErrorApi(cuerpo?.detalle ?? SIN_CONEXION, respuesta.status);
  if (cuerpo === null) throw new ErrorApi(SIN_CONEXION, respuesta.status);
  return cuerpo;
}

export async function enviarMensaje(idConversacion, mensaje, token) {
  return pedir("/api/v1/chat/mensaje", {
    method: "POST",
    headers: cabeceras(token, { "Content-Type": "application/json" }),
    body: JSON.stringify({ id_conversacion: idConversacion, mensaje }),
  });
}

export async function enviarDocumento(idConversacion, archivo, mensaje, token) {
  const datos = new FormData();
  datos.append("id_conversacion", idConversacion);
  datos.append("archivo", archivo);
  if (mensaje) datos.append("mensaje", mensaje);
  return pedir("/api/v1/chat/documento", { method: "POST", headers: cabeceras(token), body: datos });
}

export async function pedirFuncionario(idConversacion, token) {
  return pedir("/api/v1/escalamiento", {
    method: "POST",
    headers: cabeceras(token, { "Content-Type": "application/json" }),
    body: JSON.stringify({ id_conversacion: idConversacion }),
  });
}

export async function mensajesNuevos(idConversacion, desde, token) {
  return pedir(`/api/v1/chat/${encodeURIComponent(idConversacion)}/mensajes?desde=${desde}`, {
    headers: cabeceras(token),
  });
}

export async function obtener(ruta, token) {
  return pedir(ruta, { headers: cabeceras(token) });
}

export async function publicar(ruta, cuerpo) {
  return pedir(ruta, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(cuerpo),
  });
}

export function nuevaConversacion() {
  // Identificador aleatorio (uuid4): nadie puede adivinar la conversación de otro (B9).
  return `conv-${crypto.randomUUID()}`;
}
