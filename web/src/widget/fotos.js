// Fotos pesadas (hallazgo de la usabilidad): una foto del celular suele pesar más de 5 MB. Antes de
// subirla, el widget la reduce en el navegador a un lado largo de 2.000 px, en JPEG; el límite del
// servidor no cambia. Un PDF, o una imagen que ya cabe, se envía como está.
export const LADO_LARGO_MAXIMO = 2000;
const CALIDAD_JPEG = 0.85;

export async function reducirFoto(archivo, limiteBytes) {
  if (!archivo.type.startsWith("image/")) return archivo;
  let mapa;
  try {
    mapa = await createImageBitmap(archivo); // respeta la orientación de la foto
  } catch {
    return archivo; // si el navegador no la puede abrir, la revisa el servidor
  }
  const escala = Math.min(1, LADO_LARGO_MAXIMO / Math.max(mapa.width, mapa.height));
  if (escala === 1 && archivo.size <= limiteBytes) {
    mapa.close();
    return archivo;
  }
  const ancho = Math.round(mapa.width * escala);
  const alto = Math.round(mapa.height * escala);
  const lienzo = document.createElement("canvas");
  lienzo.width = ancho;
  lienzo.height = alto;
  const contexto = lienzo.getContext("2d");
  contexto.fillStyle = "#ffffff"; // un PNG con transparencia no queda con fondo negro en JPEG
  contexto.fillRect(0, 0, ancho, alto);
  contexto.drawImage(mapa, 0, 0, ancho, alto);
  mapa.close();
  const jpeg = await new Promise((listo) => lienzo.toBlob(listo, "image/jpeg", CALIDAD_JPEG));
  if (!jpeg) return archivo;
  return new File([jpeg], `${archivo.name.replace(/\.[^.]+$/, "")}.jpg`, { type: "image/jpeg" });
}
