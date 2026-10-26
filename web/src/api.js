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
  if (!respuesta.ok) throw new Error(cuerpo?.detalle ?? SIN_CONEXION);
  return cuerpo;
}

export async function enviarMensaje(idConversacion, mensaje, token) {
  const r = await fetch("/api/v1/chat/mensaje", {
    method: "POST",
    headers: cabeceras(token, { "Content-Type": "application/json" }),
    body: JSON.stringify({ id_conversacion: idConversacion, mensaje }),
  });
  return leer(r);
}

export async function enviarDocumento(idConversacion, archivo, mensaje, token) {
  const datos = new FormData();
  datos.append("id_conversacion", idConversacion);
  datos.append("archivo", archivo);
  if (mensaje) datos.append("mensaje", mensaje);
  const r = await fetch("/api/v1/chat/documento", {
    method: "POST",
    headers: cabeceras(token),
    body: datos,
  });
  return leer(r);
}

export async function pedirFuncionario(idConversacion, token) {
  const r = await fetch("/api/v1/escalamiento", {
    method: "POST",
    headers: cabeceras(token, { "Content-Type": "application/json" }),
    body: JSON.stringify({ id_conversacion: idConversacion }),
  });
  return leer(r);
}

export async function mensajesNuevos(idConversacion, desde, token) {
  const r = await fetch(
    `/api/v1/chat/${encodeURIComponent(idConversacion)}/mensajes?desde=${desde}`,
    { headers: cabeceras(token) },
  );
  return leer(r);
}

export async function obtener(ruta, token) {
  const r = await fetch(ruta, { headers: cabeceras(token) });
  return leer(r);
}

export async function publicar(ruta, cuerpo) {
  const r = await fetch(ruta, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(cuerpo),
  });
  return leer(r);
}

export function nuevaConversacion() {
  // Identificador aleatorio (uuid4): nadie puede adivinar la conversación de otro (B9).
  return `conv-${crypto.randomUUID()}`;
}
