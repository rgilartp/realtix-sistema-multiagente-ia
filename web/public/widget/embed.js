/*
 * Inserta el widget del sistema multiagente de IA en una página (RF-UI-01 · Widget embebible).
 *
 *   <script src="https://<servidor>/widget/embed.js"></script>
 *   RealtixWidget.fijarSesion(token)   // token de la OVT simulada; null al cerrar la sesión
 *
 * Monta un iframe con /widget/ (ADR-08) y le pasa el token por postMessage, solo al origen del
 * widget; nunca en la URL. El widget avisa cuando está listo.
 */
(function () {
  var script = document.currentScript;
  var origen = new URL(script.src, window.location.href).origin;
  var iframe = document.createElement("iframe");
  var token = null;
  var listo = false;

  iframe.src = origen + "/widget/";
  iframe.title = "Asistente tributario (sistema multiagente de IA)";
  iframe.setAttribute("data-realtix-widget", "");
  iframe.style.cssText =
    "position:fixed;bottom:16px;right:16px;width:380px;height:620px;max-height:calc(100vh - 32px);" +
    "max-width:calc(100vw - 32px);border:0;border-radius:16px;" +
    "box-shadow:0 12px 32px rgba(0,0,0,.25);z-index:2147483000;background:#fff";

  function enviar() {
    if (listo && iframe.contentWindow) {
      iframe.contentWindow.postMessage({ tipo: "realtix-sesion", token: token }, origen);
    }
  }

  window.addEventListener("message", function (evento) {
    if (evento.source !== iframe.contentWindow || evento.origin !== origen) return;
    if (evento.data && evento.data.tipo === "realtix-widget-listo") {
      listo = true;
      enviar();
    }
  });

  window.RealtixWidget = {
    fijarSesion: function (nuevo) {
      token = nuevo || null;
      enviar();
    },
  };

  if (document.body) document.body.appendChild(iframe);
  else document.addEventListener("DOMContentLoaded", function () { document.body.appendChild(iframe); });
})();
