// B11: OVT simulada, widget y consola (RF-UI-01 a RF-UI-04, RF-SYS-06, RF-ESC-05 y RNF-07),
// con la API simulada en el navegador. Los 6 flujos corren en 1280 px y en 390 px; con
// CAPTURAS=1, cada uno guarda su captura en docs/capturas/ y cuatro de ellos, también la del modo
// oscuro. Al final, las pruebas del tema claro u oscuro y del ancho mínimo (360 px). Cada flujo
// lleva sus requerimientos como anotación `req`, que lee scripts/trazabilidad.py.
import { readFileSync } from "node:fs";

import { expect, test } from "@playwright/test";

import { TEXTOS, simularApi } from "./simulador.js";

const CAPTURAS = process.env.CAPTURAS === "1";
const MARCAS_PROHIBIDAS = /bogot[aá]|secretar[ií]a|hacienda|alcald[ií]a|realtix|realsit/i;
const PNG = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+ip1sAAAAASUVORK5CYII=",
  "base64",
);
const ESCRITORIO = { width: 1280, height: 800 };
const CELULAR = { width: 390, height: 844 };
const MINIMO = { width: 360, height: 740 };
// Capturas que también se toman en modo oscuro (con el sufijo _oscuro).
const CAPTURAS_OSCURAS = [
  "ovt_simulada",
  "widget_inicio",
  "widget_respuesta",
  "widget_fuera_de_horario",
  "consola_metricas",
];

test.use({ testIdAttribute: "data-prueba" });

// Espera a que las dos fuentes estén cargadas en la página y en el iframe del widget.
async function fuentesListas(page) {
  for (const marco of page.frames()) {
    await marco
      .evaluate(async () => {
        await Promise.all([
          document.fonts.load('700 1em "Archivo Variable"'),
          document.fonts.load('400 1em "Atkinson Hyperlegible Next Variable"'),
          document.fonts.load('700 1em "Atkinson Hyperlegible Next Variable"'),
        ]);
        await document.fonts.ready;
      })
      .catch(() => {});
  }
}

async function capturar(page, nombre, { completa = false } = {}) {
  if (!CAPTURAS) return;
  if ((await page.locator("html").getAttribute("data-tema")) === "oscuro") {
    if (!CAPTURAS_OSCURAS.includes(nombre)) return;
    nombre = `${nombre}_oscuro`;
  }
  await fuentesListas(page);
  await page.waitForTimeout(100); // el widget recalcula su altura con el rótulo ya dibujado
  // Con las fuentes cargadas cambia el alto del texto: la conversación vuelve al final (si hay
  // mensajes), como la deja el widget.
  for (const marco of page.frames()) {
    await marco
      .evaluate(() => {
        const zona = document.querySelector("main[aria-live]");
        if (zona?.querySelector("[data-autor]")) zona.scrollTop = zona.scrollHeight;
      })
      .catch(() => {});
  }
  const { width } = page.viewportSize();
  const path = `../docs/capturas/${nombre}_${width}.png`;
  await page.screenshot({ path, animations: "disabled", fullPage: completa });
}

async function abrirOvt(page, tamano, opciones) {
  const solicitudes = await simularApi(page, opciones);
  await page.setViewportSize(tamano);
  await page.goto("/ovt/");
  if (tamano.width < 640) {
    // En el celular el asistente empieza cerrado, para no tapar la página.
    await page.getByRole("button", { name: "Asistente tributario" }).click();
  }
  const widget = page.frameLocator("iframe[data-realtix-widget]");
  await expect(widget.getByTestId("aviso-ia")).toBeVisible();
  return { solicitudes, widget };
}

async function iniciarSesion(page, tamano, usuario = "U03") {
  if (tamano.width < 640) await page.getByRole("button", { name: "Ocultar asistente" }).click();
  await page.getByTestId("usuario").selectOption(usuario);
  await page.getByRole("button", { name: "Iniciar sesión simulada" }).click();
  await expect(page.getByTestId("sesion")).toContainText(usuario);
  if (tamano.width < 640) await page.getByRole("button", { name: "Asistente tributario" }).click();
}

// El rótulo de entorno simulado sigue arriba y el widget no lo tapa (revisión externa de B11).
async function rotuloVisible(page) {
  const rotulo = await page.getByTestId("rotulo").boundingBox();
  const panel = await page.locator("iframe[data-realtix-widget]").boundingBox();
  expect(rotulo.y).toBe(0);
  expect(panel.y).toBeGreaterThanOrEqual(rotulo.y + rotulo.height);
}

// Con el teclado: escribir y Enter (sin el ratón).
const preguntar = async (widget, texto) => {
  const campo = widget.getByLabel("Escribe tu consulta");
  await campo.fill(texto);
  await campo.press("Enter");
};

// -- Flujos (cada uno es una prueba en 1280 px y, con CAPTURAS=1, también en 390 px) -----------

async function flujoOvt(page, tamano) {
  await simularApi(page);
  await page.setViewportSize(tamano);
  await page.goto("/ovt/");
  await expect(page.getByTestId("rotulo")).toHaveText(
    "Entorno simulado de pruebas — no es la Oficina Virtual Tributaria real",
  );
  // Sin logos ni imágenes: solo íconos de trazo decorativos, junto al texto que dicen.
  await expect(page.locator("img")).toHaveCount(0);
  await expect(page.locator('svg:not([aria-hidden="true"])')).toHaveCount(0);
  // El rótulo es una franja delgada de aviso: una línea de unos 38 px en escritorio.
  const { height } = await page.getByTestId("rotulo").boundingBox();
  expect(height).toBeLessThanOrEqual(tamano.width >= 1024 ? 40 : 64);
  await expect(page.getByTestId("que-probar").getByRole("listitem")).toHaveCount(4);
  expect(await page.locator("body").innerText()).not.toMatch(MARCAS_PROHIBIDAS);
  await expect(page.locator("iframe[data-realtix-widget]")).toHaveAttribute("src", /\/widget\/$/);
  // La captura de la OVT muestra la página con el asistente cerrado (en el celular ya lo está).
  if (tamano.width >= 640) await page.getByRole("button", { name: "Ocultar asistente" }).click();
  await page.evaluate(() => document.activeElement?.blur()); // sin el anillo de foco del clic
  await expect(page.getByRole("button", { name: "Asistente tributario" })).toBeVisible();
  await capturar(page, "ovt_simulada");
}

async function flujoRespuesta(page, tamano) {
  const { solicitudes, widget } = await abrirOvt(page, tamano);
  // RF-SYS-06: el aviso está antes de cualquier respuesta; el botón del funcionario, siempre a la vista.
  await expect(widget.getByTestId("aviso-ia")).toContainText(TEXTOS.avisoIa);
  // Debajo, el aviso de datos personales (solo en la interfaz; el de la API no cambia).
  await expect(widget.getByTestId("aviso-datos")).toContainText("según la Ley 1581 de 2012");
  await expect(widget.getByTestId("aviso-datos")).toContainText("puedes no usar el asistente");
  const [ia, datos] = await Promise.all(["aviso-ia", "aviso-datos"].map((id) => widget.getByTestId(id).boundingBox()));
  expect(datos.y + datos.height).toBeLessThanOrEqual(ia.y + ia.height); // dentro del recuadro…
  expect(datos.y).toBeGreaterThan(ia.y + 40); // …y debajo de la franja y del aviso de IA
  await expect(widget.getByRole("button", { name: "Hablar con un funcionario" })).toBeVisible();
  await expect(widget.getByTestId("interlocutor")).toHaveText("Te atiende un asistente de IA");
  await expect(widget.getByText("¿En qué te ayudo?")).toBeVisible(); // estado vacío
  await expect(widget.getByTestId("aviso-ia")).toBeInViewport({ ratio: 1 }); // completo al abrir
  expect(await widget.locator("body").innerText()).not.toMatch(MARCAS_PROHIBIDAS);
  await capturar(page, "widget_inicio");
  // Sin sesión, una consulta personal recibe el aviso de sesión real (AVISO_SESION, ACC-02).
  await preguntar(widget, "¿Cuánto debo de mi predio?");
  const aviso = widget.locator("[data-autor=agente]");
  await expect(aviso.getByText(TEXTOS.avisoSesion)).toBeVisible();
  await expect(aviso.getByText("Asistente de IA", { exact: true })).toBeVisible();
  const sinSesion = solicitudes.find((s) => s.ruta === "/api/v1/chat/mensaje");
  expect(sinSesion.auth).toBeNull();
  expect(sinSesion.cuerpo.id_conversacion).toMatch(/^conv-[0-9a-f-]{36}$/);
  await rotuloVisible(page);
  await capturar(page, "widget_respuesta");
  // Con sesión, el token de la OVT llega al widget por postMessage y viaja en la cabecera
  // (RF-UI-02). El texto es neutro y solo sirve para revisar la lista de fuentes: sin captura.
  await iniciarSesion(page, tamano);
  await expect(widget.getByText("Sesión iniciada")).toBeVisible();
  await preguntar(widget, "Pregunta de prueba");
  const respuesta = widget.locator("[data-autor=agente]").filter({ hasText: TEXTOS.pruebaFuentes });
  await expect(respuesta.getByRole("listitem").filter({ hasText: "Fuente de prueba A" })).toBeVisible();
  await expect(respuesta.getByRole("listitem").filter({ hasText: "Fuente de prueba B" })).toBeVisible();
  const conSesion = solicitudes.filter((s) => s.ruta === "/api/v1/chat/mensaje").at(-1);
  expect(conSesion.auth).toBe("Bearer token-de-prueba-U03");
  await rotuloVisible(page);
}

async function flujoFueraDeHorario(page, tamano) {
  const { widget } = await abrirOvt(page, tamano, { fueraDeHorario: true });
  await preguntar(widget, "Hola, necesito hablar con un funcionario");
  const aviso = widget.locator("[data-autor=sistema]");
  await expect(aviso).toContainText("Vuelvo a atender el lunes 5 de octubre de 2026 a las 8:00 a. m.");
  await expect(aviso.getByText("Vuelve a atender el lunes 5 de octubre de 2026 a las 8:00 a. m.")).toBeVisible();
  await expect(aviso.getByText("Sistema", { exact: true })).toBeVisible();
  await rotuloVisible(page);
  await capturar(page, "widget_fuera_de_horario");
}

async function flujoRecibo(page, tamano) {
  const { solicitudes, widget } = await abrirOvt(page, tamano);
  await iniciarSesion(page, tamano);
  // Un tipo no admitido se rechaza en el navegador, sin llamar a la API.
  await widget.getByTestId("archivo").setInputFiles({ name: "nota.txt", mimeType: "text/plain", buffer: Buffer.from("hola") });
  await expect(widget.getByText("Solo puedo recibir el recibo en JPG, PNG o PDF.")).toBeVisible();
  expect(solicitudes.some((s) => s.ruta === "/api/v1/chat/documento")).toBe(false);
  await widget.getByTestId("archivo").setInputFiles({ name: "recibo.png", mimeType: "image/png", buffer: PNG });
  await expect(widget.getByText("recibo.png")).toBeVisible();
  await expect(widget.getByText("¿Es correcto?")).toBeVisible();
  const subida = solicitudes.find((s) => s.ruta === "/api/v1/chat/documento");
  expect(subida.auth).toBe("Bearer token-de-prueba-U03");
  await rotuloVisible(page);
  // Al cambiar el tamaño de la ventana, el widget tampoco tapa el rótulo.
  const otro = tamano.width < 640 ? ESCRITORIO : CELULAR;
  await page.setViewportSize(otro);
  await rotuloVisible(page);
  await page.setViewportSize(tamano);
  await rotuloVisible(page);
  await capturar(page, "widget_recibo");
}

async function flujoEscalada(page, tamano) {
  const { widget } = await abrirOvt(page, tamano);
  const boton = widget.getByRole("button", { name: "Hablar con un funcionario" });
  await boton.click();
  await expect(widget.getByText(TEXTOS.transferencia)).toBeVisible();
  await expect(widget.getByTestId("interlocutor")).toHaveText("Tu caso está con un funcionario");
  await expect(widget.getByRole("button", { name: "Ya pediste un funcionario" })).toBeDisabled();
  await rotuloVisible(page);
  await capturar(page, "widget_escalado"); // antes del mensaje de prueba del funcionario
  // La consulta periódica trae el mensaje del funcionario (RF-ESC-05 y RF-UI-03).
  await expect(widget.getByText(TEXTOS.funcionario)).toBeVisible({ timeout: 8000 });
  await expect(widget.getByTestId("interlocutor")).toHaveText("Te atiende un funcionario");
  await expect(widget.locator("[data-autor=funcionario]").getByText("Funcionario", { exact: true })).toBeVisible();
}

async function flujoConsola(page, tamano) {
  await simularApi(page);
  await page.setViewportSize({ ...tamano, height: tamano.width < 640 ? 844 : 900 });
  await page.goto("/consola/");
  await expect(page.getByTestId("salud")).toContainText("ok");
  await expect(page.getByRole("link", { name: "Trazas en LangSmith" })).toHaveAttribute("href", /smith\.langchain\.com/);
  await page.getByRole("button", { name: "Cargar casos" }).click();
  await expect(page.getByText("Necesitas un token válido para esta consulta.")).toBeVisible();
  await page.getByLabel("Token de funcionario (bandeja)").fill("token-funcionario");
  await page.getByRole("button", { name: "Cargar casos" }).click();
  await page.getByRole("button", { name: /CASO-conv-91bc/ }).click();
  await expect(page.getByTestId("detalle")).toContainText("confianza insuficiente");
  await page.getByLabel("Motivo").selectOption("solicitud explícita"); // filtro de la bandeja
  await expect(page.getByRole("button", { name: /CASO-conv-91bc/ })).toHaveCount(0);
  await page.getByLabel("Motivo").selectOption("");
  await capturar(page, "consola_bandeja", { completa: true });
  await page.getByRole("button", { name: "Métricas" }).click();
  await page.getByLabel("Token de administrador (métricas)").fill("token-admin");
  await page.getByRole("button", { name: "Cargar métricas" }).click();
  const matriz = page.getByTestId("matriz");
  await expect(matriz).toContainText("Fuera de alcance");
  // La fila cuya primera celda es exactamente la del ICA (no la del encabezado).
  const filaIca = matriz.locator("tbody tr").filter({ has: page.locator("th", { hasText: /^ICA$/ }) });
  await expect(filaIca).toHaveCount(1);
  await expect(filaIca.locator("td").nth(1)).toHaveText("9");
  await expect(page.getByText("Latencia p95")).toBeVisible();
  await capturar(page, "consola_metricas", { completa: true });
}

const FLUJOS = [
  {
    nombre: "OVT simulada: rótulo, sin marcas reales y widget en un iframe",
    flujo: flujoOvt,
    req: ["RF-UI-01 · Widget embebible", "RNF-04 · Uso exclusivo de datos sintéticos"],
  },
  {
    nombre: "widget: aviso de IA al abrir, sesión por postMessage, interlocutor y fuentes",
    flujo: flujoRespuesta,
    req: ["RF-SYS-06 · Aviso de interacción con IA (provisional)", "RF-AUT-04 · Aviso de sesión requerida", "RF-UI-02 · Contexto de la sesión", "RF-UI-03 · Identificación del interlocutor", "RF-GEN-03 · Respuesta sustentada en fuentes"],
  },
  {
    nombre: "widget: fuera de horario destacado con la hora de regreso (RNF-07)",
    flujo: flujoFueraDeHorario,
    req: ["RNF-07 · Aviso fuera de horario"],
  },
  {
    nombre: "widget: carga del recibo desde la conversación (RF-UI-04)",
    flujo: flujoRecibo,
    req: ["RF-UI-04 · Carga desde la conversación", "RF-OCR-01 · Carga de archivos"],
  },
  {
    nombre: "widget: botón del funcionario y mensajes nuevos de la conversación escalada",
    flujo: flujoEscalada,
    req: ["RF-ESC-05 · Notificación al contribuyente", "RF-UI-03 · Identificación del interlocutor"],
  },
  {
    nombre: "consola: bandeja con filtros y métricas con sus tokens",
    flujo: flujoConsola,
    req: ["RF-OBS-02 · Matriz de confusión de enrutamiento", "RF-OBS-03 · Métricas de precisión y tiempo"],
  },
];

for (const { nombre, flujo, req } of FLUJOS) {
  const anotaciones = { annotation: req.map((r) => ({ type: "req", description: r })) };
  test(nombre, anotaciones, async ({ page }) => flujo(page, ESCRITORIO));
  test(`${nombre} (390 px)`, anotaciones, async ({ page }) => flujo(page, CELULAR));
  // Las capturas del modo oscuro salen de los mismos flujos, con el sistema en modo oscuro: la
  // página arranca oscura y le pasa el tema al widget.
  if (CAPTURAS && CAPTURAS_OSCURAS.some((c) => flujo.toString().includes(`"${c}"`))) {
    for (const tamano of [ESCRITORIO, CELULAR]) {
      test(`${nombre} (modo oscuro, ${tamano.width} px)`, anotaciones, async ({ page }) => {
        await page.emulateMedia({ colorScheme: "dark" });
        await flujo(page, tamano);
      });
    }
  }
}

// -- Tema claro u oscuro --------------------------------------------------------------------------

// El interruptor del tema cambia también el del widget insertado: RF-UI-01.
const TEMA_REQ = { annotation: [{ type: "req", description: "RF-UI-01 · Widget embebible" }] };
const temaDe = (pagina) => pagina.locator("html");
const widgetHtml = (page) => page.frameLocator("iframe[data-realtix-widget]").locator("html");

for (const ruta of ["/ovt/", "/consola/"]) {
  test(`tema en ${ruta}: el interruptor «Modo oscuro» cambia el tema y lo recuerda al recargar`, TEMA_REQ, async ({ page }) => {
    await simularApi(page);
    await page.emulateMedia({ colorScheme: "light" });
    await page.goto(ruta);
    const boton = page.getByRole("switch", { name: "Modo oscuro" });
    await expect(temaDe(page)).toHaveAttribute("data-tema", "claro"); // arranca con el del sistema
    await expect(boton).toHaveAttribute("aria-checked", "false");
    await boton.click();
    await expect(temaDe(page)).toHaveAttribute("data-tema", "oscuro");
    await expect(boton).toHaveAttribute("aria-checked", "true");
    await page.reload();
    await expect(temaDe(page)).toHaveAttribute("data-tema", "oscuro"); // la elección se recuerda
    await expect(boton).toHaveAttribute("aria-checked", "true");
    await boton.click();
    await page.reload();
    await expect(temaDe(page)).toHaveAttribute("data-tema", "claro");
    await expect(boton).toHaveAttribute("aria-checked", "false");
  });

  test(`tema en ${ruta}: arranca oscuro con el sistema y funciona sin localStorage`, TEMA_REQ, async ({ page }) => {
    const errores = [];
    page.on("pageerror", (error) => errores.push(error.message));
    await simularApi(page);
    await page.addInitScript(() => {
      Object.defineProperty(window, "localStorage", {
        get() {
          throw new Error("almacenamiento bloqueado");
        },
      });
    });
    await page.emulateMedia({ colorScheme: "dark" });
    await page.goto(ruta);
    const boton = page.getByRole("switch", { name: "Modo oscuro" });
    await expect(temaDe(page)).toHaveAttribute("data-tema", "oscuro");
    await expect(boton).toHaveAttribute("aria-checked", "true");
    await boton.click();
    await expect(temaDe(page)).toHaveAttribute("data-tema", "claro");
    await expect(boton).toHaveAttribute("aria-checked", "false");
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    expect(errores).toEqual([]);
  });
}

test(
  "tema: el widget recibe el de la página y solo acepta «claro» u «oscuro» de quien lo inserta",
  { annotation: [{ type: "req", description: "RF-UI-01 · Widget embebible" }] },
  async ({ page }) => {
    await simularApi(page);
    await page.emulateMedia({ colorScheme: "light" });
    await page.setViewportSize(ESCRITORIO);
    await page.goto("/ovt/");
    const widget = page.frameLocator("iframe[data-realtix-widget]");
    await expect(widget.getByTestId("aviso-ia")).toBeVisible();
    await expect(widgetHtml(page)).toHaveAttribute("data-tema", "claro");
    const boton = page.getByRole("switch", { name: "Modo oscuro" });
    await boton.click();
    await expect(widgetHtml(page)).toHaveAttribute("data-tema", "oscuro");
    await boton.click();
    await expect(widgetHtml(page)).toHaveAttribute("data-tema", "claro");

    // Valores no válidos desde la página: se ignoran.
    await page.evaluate(() => {
      const destino = document.querySelector("iframe[data-realtix-widget]").contentWindow;
      for (const tema of ["azul", "", null, 1, "oscuro ", "OSCURO", undefined]) {
        destino.postMessage({ tipo: "realtix-tema", tema }, window.location.origin);
      }
    });
    // Un tema válido enviado desde otro marco (no desde la página que lo inserta): se ignora.
    await page.evaluate(
      () =>
        new Promise((listo) => {
          const otro = document.createElement("iframe");
          otro.srcdoc =
            "<script>parent.document.querySelector('iframe[data-realtix-widget]').contentWindow" +
            ".postMessage({ tipo: 'realtix-tema', tema: 'oscuro' }, '*');</" + "script>";
          otro.onload = () => listo();
          document.body.appendChild(otro);
        }),
    );
    const marco = page.frames().find((f) => f.url().endsWith("/widget/"));
    await marco.evaluate(() => new Promise((listo) => setTimeout(listo, 200))); // ya los procesó
    await expect(widgetHtml(page)).toHaveAttribute("data-tema", "claro");
    await expect(widgetHtml(page)).not.toHaveAttribute("data-tema-pendiente", /.*/);
  },
);

test(
  "tema: sin página que lo inserte, el widget sigue el del sistema",
  { annotation: [{ type: "req", description: "RF-UI-01 · Widget embebible" }] },
  async ({ page }) => {
    await simularApi(page);
    await page.emulateMedia({ colorScheme: "dark" });
    await page.goto("/widget/");
    await expect(temaDe(page)).toHaveAttribute("data-tema", "oscuro");
    await expect(page.getByTestId("aviso-ia")).toBeVisible();
    await page.emulateMedia({ colorScheme: "light" });
    await expect(temaDe(page)).toHaveAttribute("data-tema", "claro");
  },
);

test("tema: el widget ignora el tema de una página de otro origen y no queda oculto", TEMA_REQ, async ({ page }) => {
  await simularApi(page);
  await page.emulateMedia({ colorScheme: "light" });
  // Una página en otro origen (127.0.0.1) inserta el widget de localhost: no está entre sus
  // orígenes permitidos, así que el widget no le avisa que está listo ni le acepta mensajes.
  await page.route("http://127.0.0.1:4173/otra-pagina/", (ruta) =>
    ruta.fulfill({
      contentType: "text/html",
      body:
        '<!doctype html><html lang="es" data-tema="oscuro"><body>' +
        '<script src="http://localhost:4173/widget/embed.js"></script></body></html>',
    }),
  );
  // Las dos direcciones son locales: Chromium pide permiso de red local para cargar el widget.
  await page.context().grantPermissions(["local-network-access"]);
  await page.goto("http://127.0.0.1:4173/otra-pagina/");
  const widget = page.frameLocator("iframe[data-realtix-widget]");
  // Sin tema de la página, el widget se muestra igual al vencer la espera (400 ms).
  await expect(widget.getByTestId("aviso-ia")).toBeVisible();
  await expect(widgetHtml(page)).not.toHaveAttribute("data-tema-pendiente", /.*/);
  await page.evaluate(() =>
    document
      .querySelector("iframe[data-realtix-widget]")
      .contentWindow.postMessage({ tipo: "realtix-tema", tema: "oscuro" }, "http://localhost:4173"),
  );
  const marco = page.frames().find((f) => f.url().endsWith("/widget/"));
  await marco.evaluate(() => new Promise((listo) => setTimeout(listo, 200)));
  await expect(widgetHtml(page)).toHaveAttribute("data-tema", "claro");
});

// La lista nativa de un select toma el fondo del select: en el modo oscuro, con fondo transparente,
// quedaba texto claro sobre el blanco del navegador (hallazgo de la usabilidad). El select y cada
// opción llevan fondo opaco y texto con 4,5:1 en los dos modos, en la OVT y en la consola (el
// widget no tiene listas).
const luminanciaCss = (css) => {
  const [r, g, b] = css.match(/[\d.]+/g).slice(0, 3).map((v) => {
    const c = Number(v) / 255;
    return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
};
async function listaLegible(select) {
  const colores = await select.evaluate((el) =>
    [el, ...el.options].map((n) => [getComputedStyle(n).backgroundColor, getComputedStyle(n).color]),
  );
  for (const [fondo, texto] of colores) {
    expect(fondo).toMatch(/^rgb\(/); // opaco: no «transparent» ni rgba con alfa
    const [a, b] = [luminanciaCss(texto), luminanciaCss(fondo)].sort((x, y) => y - x);
    expect((a + 0.05) / (b + 0.05)).toBeGreaterThanOrEqual(4.5);
  }
}

for (const esquema of ["light", "dark"]) {
  const modo = esquema === "dark" ? "oscuro" : "claro";
  test(`listas desplegables legibles en la OVT y la consola (modo ${modo})`, TEMA_REQ, async ({ page }) => {
    await simularApi(page);
    await page.emulateMedia({ colorScheme: esquema });
    await page.goto("/ovt/");
    await expect(temaDe(page)).toHaveAttribute("data-tema", modo);
    await expect(page.getByTestId("usuario").locator("option").nth(1)).toBeAttached(); // ya cargó
    await listaLegible(page.getByTestId("usuario"));
    await page.goto("/consola/");
    await page.getByLabel("Token de funcionario (bandeja)").fill("token-funcionario");
    await page.getByRole("button", { name: "Cargar casos" }).click();
    for (const filtro of ["Motivo", "Estado"]) await listaLegible(page.getByLabel(filtro));
  });
}

// Fotos pesadas (hallazgo de la usabilidad): el widget reduce la foto antes de subirla (lado largo
// de 2.000 px, en JPEG). Un PDF de más de 5 MB no se reduce: se rechaza con el mensaje de siempre.
test(
  "widget: reduce las fotos pesadas antes de subirlas y rechaza un PDF pesado",
  { annotation: [{ type: "req", description: "RF-UI-04 · Carga desde la conversación" }] },
  async ({ page }) => {
    const { solicitudes, widget } = await abrirOvt(page, ESCRITORIO);
    await iniciarSesion(page, ESCRITORIO);
    // Una «foto» de 2.600 × 1.950 px con grano, que en PNG pesa más de 5 MB.
    const foto = Buffer.from(
      await page.evaluate(() => {
        const [ancho, alto] = [2600, 1950];
        const lienzo = document.createElement("canvas");
        Object.assign(lienzo, { width: ancho, height: alto });
        const contexto = lienzo.getContext("2d");
        const datos = contexto.createImageData(ancho, alto);
        for (let i = 0; i < datos.data.length; i += 4) {
          const x = (i / 4) % ancho;
          const grano = Math.random() * 40;
          datos.data.set([60 + (x % 180) + grano, 120 + grano, 200 - grano, 255], i);
        }
        contexto.putImageData(datos, 0, 0);
        return lienzo.toDataURL("image/png").split(",")[1];
      }),
      "base64",
    );
    expect(foto.length).toBeGreaterThan(5 * 1024 * 1024);
    await widget.getByTestId("archivo").setInputFiles({ name: "foto.png", mimeType: "image/png", buffer: foto });
    await expect(widget.getByText("¿Es correcto?")).toBeVisible();
    const subida = solicitudes.find((s) => s.ruta === "/api/v1/chat/documento");
    expect(subida.cuerpo).toMatchObject({ nombre: "foto.jpg", tipo: "image/jpeg" });
    expect(subida.cuerpo.bytes).toBeLessThan(5 * 1024 * 1024);
    const antes = solicitudes.length;
    const pdf = { name: "recibo.pdf", mimeType: "application/pdf", buffer: Buffer.alloc(6 * 1024 * 1024) };
    await widget.getByTestId("archivo").setInputFiles(pdf);
    await expect(widget.getByText("El archivo pesa más de 5 MB. Envía una foto o un PDF más liviano.")).toBeVisible();
    expect(solicitudes.slice(antes).some((s) => s.ruta === "/api/v1/chat/documento")).toBe(false);
  },
);

// La CSP del despliegue (B13) bloquea los scripts en línea: ninguna página compilada los tiene.
test("las páginas compiladas no tienen scripts en línea", async () => {
  for (const pagina of ["index.html", "ovt/index.html", "widget/index.html", "consola/index.html"]) {
    const html = readFileSync(new URL(`../dist/${pagina}`, import.meta.url), "utf-8");
    const scripts = [...html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/g)];
    for (const [, atributos, cuerpo] of scripts) {
      expect(atributos, pagina).toMatch(/\bsrc=/);
      expect(cuerpo.trim(), pagina).toBe("");
    }
  }
});

// Sin desplazamiento horizontal desde 360 px, en los dos modos. La matriz de la consola se desliza
// dentro de su propio contenedor (y lo avisa), no la página.
const sinDesborde = async (marco) =>
  expect(await marco.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)).toBe(0);

for (const esquema of ["light", "dark"]) {
  const modo = esquema === "dark" ? "oscuro" : "claro";
  test(`ancho mínimo: sin desplazamiento horizontal desde 360 px (modo ${modo})`, TEMA_REQ, async ({ page }) => {
    await simularApi(page);
    await page.emulateMedia({ colorScheme: esquema });
    for (const ancho of [MINIMO, CELULAR]) {
      await page.setViewportSize(ancho);
      await page.goto("/ovt/");
      await expect(temaDe(page)).toHaveAttribute("data-tema", modo);
      await sinDesborde(page);
      await page.getByRole("button", { name: "Asistente tributario" }).click();
      const widget = page.frameLocator("iframe[data-realtix-widget]");
      await expect(widget.getByTestId("aviso-ia")).toBeVisible();
      await expect(widgetHtml(page)).toHaveAttribute("data-tema", modo);
      await sinDesborde(page);
      await sinDesborde(page.frames().find((f) => f.url().endsWith("/widget/")));

      await page.goto("/widget/");
      await sinDesborde(page);

      await page.goto("/consola/");
      await page.getByLabel("Token de funcionario (bandeja)").fill("token-funcionario");
      await page.getByRole("button", { name: "Cargar casos" }).click();
      await page.getByRole("button", { name: /CASO-conv-91bc/ }).click();
      await expect(page.getByTestId("detalle")).toBeVisible();
      await sinDesborde(page);
      await page.getByRole("button", { name: "Métricas" }).click();
      await page.getByLabel("Token de administrador (métricas)").fill("token-admin");
      await page.getByRole("button", { name: "Cargar métricas" }).click();
      await expect(page.getByTestId("matriz")).toBeVisible();
      await sinDesborde(page);
    }
  });
}
