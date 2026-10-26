/*
 * Inserta el widget del sistema multiagente de IA en una página (RF-UI-01 · Widget embebible).
 *
 *   <script src="https://<servidor>/widget/embed.js"></script>
 *   RealtixWidget.fijarSesion(token)   // token de la OVT simulada; null al cerrar la sesión
 *
 * Monta un iframe con /widget/ (ADR-08) y un botón para abrirlo u ocultarlo. En pantallas anchas
 * empieza abierto; en un celular, cerrado, para no tapar la página. El token pasa por postMessage,
 * solo al origen del widget, nunca en la URL; el widget avisa cuando está listo.
 */
(function () {
  var script = document.currentScript;
  var origen = new URL(script.src, window.location.href).origin;
  var ancho = window.matchMedia("(min-width: 640px)");
  var sinMovimiento = window.matchMedia("(prefers-reduced-motion: reduce)");
  var token = null;
  var listo = false;
  var abierto = ancho.matches;

  var contenedor = document.createElement("div");
  contenedor.setAttribute("data-realtix-contenedor", "");
  contenedor.style.cssText =
    "position:fixed;right:16px;bottom:16px;z-index:2147483000;display:flex;flex-direction:column;" +
    "align-items:flex-end;gap:10px;font-family:inherit";

  var iframe = document.createElement("iframe");
  iframe.id = "realtix-widget";
  iframe.src = origen + "/widget/";
  iframe.title = "Asistente tributario (sistema multiagente de IA)";
  iframe.setAttribute("data-realtix-widget", "");

  var boton = document.createElement("button");
  boton.type = "button";
  boton.setAttribute("aria-controls", "realtix-widget");
  boton.style.cssText =
    "border:0;border-radius:999px;padding:12px 18px;background:#0e5a64;color:#fff;font:inherit;" +
    "font-size:15px;font-weight:600;box-shadow:0 6px 18px rgba(28,34,38,.25);cursor:pointer";
  boton.addEventListener("focus", function () {
    boton.style.outline = "3px solid #1c2226";
    boton.style.outlineOffset = "2px";
  });
  boton.addEventListener("blur", function () {
    boton.style.outline = "none";
  });

  function medidas() {
    var transicion = sinMovimiento.matches
      ? "none"
      : "opacity 200ms cubic-bezier(.23,1,.32,1), transform 200ms cubic-bezier(.23,1,.32,1)";
    var tamano = ancho.matches
      ? "width:400px;height:min(680px, calc(100vh - 190px));" // el rótulo de la página queda visible
      : "width:calc(100vw - 16px);height:calc(100dvh - 190px);";
    iframe.style.cssText =
      tamano +
      "border:0;border-radius:18px;background:#fff;" +
      "box-shadow:0 1px 2px rgba(28,34,38,.06),0 12px 32px rgba(28,34,38,.18);" +
      "transition:" + transicion + ";" +
      (abierto ? "opacity:1;transform:none;" : "opacity:0;transform:translateY(8px);display:none;");
    contenedor.style.right = ancho.matches ? "16px" : "8px";
    contenedor.style.bottom = ancho.matches ? "16px" : "8px";
    boton.textContent = abierto ? "Ocultar asistente" : "Asistente tributario";
    boton.setAttribute("aria-expanded", String(abierto));
  }

  function enviar() {
    if (listo && iframe.contentWindow) {
      iframe.contentWindow.postMessage({ tipo: "realtix-sesion", token: token }, origen);
    }
  }

  boton.addEventListener("click", function () {
    abierto = !abierto;
    medidas();
    if (abierto) iframe.focus();
  });
  ancho.addEventListener("change", medidas);

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
    abrir: function () {
      abierto = true;
      medidas();
    },
  };

  contenedor.appendChild(iframe);
  contenedor.appendChild(boton);
  medidas();
  if (document.body) document.body.appendChild(contenedor);
  else document.addEventListener("DOMContentLoaded", function () { document.body.appendChild(contenedor); });
})();
