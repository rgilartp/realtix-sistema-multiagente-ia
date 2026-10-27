/*
 * Tema claro u oscuro de la web, antes de pintar la página (sin parpadeo). Va como archivo en el
 * <head> de la OVT simulada, la consola y el widget, no en línea: la CSP del despliegue bloquea los
 * scripts en línea.
 *
 * - En una página: la elección guardada por el interruptor «Modo oscuro»; si no hay, prefers-color-scheme.
 * - En el widget insertado (dentro de un iframe): prefers-color-scheme, y la página queda oculta
 *   hasta que llega el tema de la página que lo inserta (embed.js), con 400 ms como máximo.
 */
(function () {
  var raiz = document.documentElement;
  var oscuroDelSistema = window.matchMedia("(prefers-color-scheme: dark)").matches;
  var tema = oscuroDelSistema ? "oscuro" : "claro";
  var insertado = window.self !== window.top;
  if (!insertado) {
    try {
      var guardado = window.localStorage.getItem("tema");
      if (guardado === "claro" || guardado === "oscuro") tema = guardado;
    } catch (e) {
      /* sin almacenamiento: se usa el tema del sistema */
    }
  }
  raiz.setAttribute("data-tema", tema);
  if (insertado) {
    raiz.setAttribute("data-tema-pendiente", "");
    window.setTimeout(function () {
      raiz.removeAttribute("data-tema-pendiente");
    }, 400);
  }
})();
