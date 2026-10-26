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
    "align-items:flex-end;gap:10px;font-family:inherit;pointer-events:none";

  var iframe = document.createElement("iframe");
  iframe.id = "realtix-widget";
  iframe.src = origen + "/widget/";
  iframe.title = "Asistente tributario (sistema multiagente de IA)";
  iframe.setAttribute("data-realtix-widget", "");

  var boton = document.createElement("button");
  boton.type = "button";
  boton.setAttribute("aria-controls", "realtix-widget");
  boton.style.cssText =
    "border:0;border-radius:6px;padding:12px 18px;background:#4b2c85;color:#fff;font:inherit;" +
    "font-size:17px;font-weight:700;box-shadow:0 4px 14px rgba(29,36,51,.28);cursor:pointer;" +
    "pointer-events:auto";
  boton.addEventListener("focus", function () {
    boton.style.outline = "3px solid #1d2433";
    boton.style.outlineOffset = "2px";
  });
  boton.addEventListener("blur", function () {
    boton.style.outline = "none";
  });

  // Margen superior: el panel no tapa el elemento marcado con data-realtix-respetar (en la OVT
  // simulada, el rótulo de entorno de pruebas).
  function margenSuperior() {
    var respetar = document.querySelector("[data-realtix-respetar]");
    var abajo = respetar ? respetar.getBoundingClientRect().bottom : 0;
    // En el celular el panel empieza justo debajo del rótulo, sin hueco.
    return Math.max(ancho.matches ? 16 : 8, Math.round(abajo) + (ancho.matches ? 12 : 0));
  }

  function medidas() {
    // Abre en 200 ms y cierra más rápido (140 ms); nace del botón, abajo a la derecha.
    var duracion = sinMovimiento.matches ? "0ms" : abierto ? "200ms" : "140ms";
    var curva = "cubic-bezier(.23,1,.32,1)";
    var borde = ancho.matches ? 16 : 8;
    var alto = window.innerHeight - margenSuperior() - borde - 48 - 10; // botón y separación
    var tamano = ancho.matches
      ? "width:400px;height:" + Math.min(680, alto) + "px;"
      : "width:calc(100vw - 16px);height:" + alto + "px;";
    // visibility (y no display) para que la transición de abrir y cerrar se vea; al cerrar, el
    // panel se oculta al terminar la transición.
    var transicion =
      "opacity " + duracion + " " + curva + ",transform " + duracion + " " + curva +
      ",visibility 0s linear " + (abierto ? "0s" : duracion);
    iframe.style.cssText =
      tamano +
      "border:0;border-radius:6px;background:#ecf1ee;pointer-events:auto;transform-origin:100% 100%;" +
      "box-shadow:0 1px 2px rgba(29,36,51,.08),0 12px 32px rgba(29,36,51,.2);" +
      "transition:" + transicion + ";" +
      (abierto
        ? "visibility:visible;opacity:1;transform:none;"
        : "visibility:hidden;opacity:0;transform:translateY(8px) scale(0.98);");
    // En el celular, con el panel abierto, el contenedor cubre lo que queda bajo el rótulo con el
    // color del papel, de borde a borde: no asoma la página detrás ni el botón tapa su texto.
    var hojaCompleta = !ancho.matches && abierto;
    contenedor.style.right = hojaCompleta ? "0" : borde + "px";
    contenedor.style.bottom = hojaCompleta ? "0" : borde + "px";
    contenedor.style.left = hojaCompleta ? "0" : "auto";
    contenedor.style.top = hojaCompleta ? margenSuperior() + "px" : "auto";
    contenedor.style.padding = hojaCompleta ? "0 8px 8px 8px" : "0";
    contenedor.style.background = hojaCompleta ? "#ecf1ee" : "transparent";
    contenedor.style.pointerEvents = hojaCompleta ? "auto" : "none";
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
  window.addEventListener("resize", medidas);

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

  function montar() {
    document.body.appendChild(contenedor);
    medidas();
    // Si el rótulo cambia de alto (otra anchura de ventana, fuentes cargadas), se recalcula.
    var respetar = document.querySelector("[data-realtix-respetar]");
    if (respetar && window.ResizeObserver) new ResizeObserver(medidas).observe(respetar);
  }
  // Con las fuentes cargadas cambia la altura del rótulo: se recalcula.
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(medidas);
  if (document.body) montar();
  else document.addEventListener("DOMContentLoaded", montar);
})();
