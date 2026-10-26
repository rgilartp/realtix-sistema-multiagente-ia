// B11: OVT simulada, widget y consola (RF-UI-01 a RF-UI-04, RF-SYS-06, RF-ESC-05 y RNF-07),
// con la API simulada en el navegador. Las 6 pruebas corren en 1280 px; con CAPTURAS=1, cada una
// guarda su captura en docs/capturas/ y se repiten los mismos flujos en 390 px para las capturas
// del celular.
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

test.use({ testIdAttribute: "data-prueba" });

async function capturar(page, nombre, { completa = false } = {}) {
  if (!CAPTURAS) return;
  await page.evaluate(() => document.fonts.ready);
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
  await expect(page.locator("img, svg")).toHaveCount(0); // sin logos
  expect(await page.locator("body").innerText()).not.toMatch(MARCAS_PROHIBIDAS);
  await expect(page.locator("iframe[data-realtix-widget]")).toHaveAttribute("src", /\/widget\/$/);
  await capturar(page, "ovt_simulada");
}

async function flujoRespuesta(page, tamano) {
  const { solicitudes, widget } = await abrirOvt(page, tamano);
  // RF-SYS-06: el aviso está antes de cualquier respuesta; el botón del funcionario, siempre a la vista.
  await expect(widget.getByTestId("aviso-ia")).toContainText(TEXTOS.avisoIa);
  await expect(widget.getByRole("button", { name: "Hablar con un funcionario" })).toBeVisible();
  await expect(widget.getByTestId("interlocutor")).toHaveText("Te atiende un asistente de IA");
  await expect(widget.getByText("¿En qué te ayudo?")).toBeVisible(); // estado vacío
  expect(await widget.locator("body").innerText()).not.toMatch(MARCAS_PROHIBIDAS);
  await capturar(page, "widget_inicio");
  await iniciarSesion(page, tamano);
  await expect(widget.getByText("Sesión iniciada")).toBeVisible();
  await preguntar(widget, "¿Qué es el predial?");
  const respuesta = widget.locator("[data-autor=agente]");
  await expect(respuesta.getByText(TEXTOS.predial)).toBeVisible();
  await expect(respuesta.getByText("Asistente de IA", { exact: true })).toBeVisible();
  await expect(respuesta.getByRole("listitem").filter({ hasText: "Acuerdo 105 de 2003, art. 2" })).toBeVisible(); // fuente
  // El token de la OVT llegó al widget por postMessage y viaja en la cabecera (RF-UI-02).
  const enviada = solicitudes.find((s) => s.ruta === "/api/v1/chat/mensaje");
  expect(enviada.auth).toBe("Bearer token-de-prueba-U03");
  expect(enviada.cuerpo.id_conversacion).toMatch(/^conv-[0-9a-f-]{36}$/);
  await capturar(page, "widget_respuesta");
}

async function flujoFueraDeHorario(page, tamano) {
  const { widget } = await abrirOvt(page, tamano, { fueraDeHorario: true });
  await preguntar(widget, "Hola, necesito hablar con un funcionario");
  const aviso = widget.locator("[data-autor=sistema]");
  await expect(aviso).toContainText("Vuelvo a atender el lunes 5 de octubre de 2026 a las 8:00 a. m.");
  await expect(aviso.getByText("Vuelve a atender el lunes 5 de octubre de 2026 a las 8:00 a. m.")).toBeVisible();
  await expect(aviso.getByText("Sistema", { exact: true })).toBeVisible();
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
  await capturar(page, "widget_recibo");
}

async function flujoEscalada(page, tamano) {
  const { widget } = await abrirOvt(page, tamano);
  const boton = widget.getByRole("button", { name: "Hablar con un funcionario" });
  await boton.click();
  await expect(widget.getByText(TEXTOS.transferencia)).toBeVisible();
  await expect(widget.getByTestId("interlocutor")).toHaveText("Tu caso está con un funcionario");
  await expect(boton).toBeDisabled();
  // La consulta periódica trae el mensaje del funcionario (RF-ESC-05 y RF-UI-03).
  await expect(widget.getByText(TEXTOS.funcionario)).toBeVisible({ timeout: 8000 });
  await expect(widget.getByTestId("interlocutor")).toHaveText("Te atiende un funcionario");
  await expect(widget.locator("[data-autor=funcionario]").getByText("Funcionario", { exact: true })).toBeVisible();
  await capturar(page, "widget_escalado");
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
  await expect(matriz).toContainText("fuera de alcance");
  // La fila cuya primera celda es exactamente «ica» (no la del encabezado).
  const filaIca = matriz.locator("tbody tr").filter({ has: page.locator("th", { hasText: /^ica$/ }) });
  await expect(filaIca).toHaveCount(1);
  await expect(filaIca.locator("td").nth(1)).toHaveText("9");
  await expect(page.getByText("Latencia p95")).toBeVisible();
  await capturar(page, "consola_metricas", { completa: true });
}

const FLUJOS = [
  ["OVT simulada: rótulo, sin marcas reales y widget en un iframe", flujoOvt],
  ["widget: aviso de IA al abrir, sesión por postMessage, interlocutor y fuentes", flujoRespuesta],
  ["widget: fuera de horario destacado con la hora de regreso (RNF-07)", flujoFueraDeHorario],
  ["widget: carga del recibo desde la conversación (RF-UI-04)", flujoRecibo],
  ["widget: botón del funcionario y mensajes nuevos de la conversación escalada", flujoEscalada],
  ["consola: bandeja con filtros y métricas con sus tokens", flujoConsola],
];

for (const [nombre, flujo] of FLUJOS) {
  test(nombre, async ({ page }) => flujo(page, ESCRITORIO));
}

test.describe("capturas en 390 px", () => {
  test.skip(!CAPTURAS, "Solo con CAPTURAS=1 (npm run capturas)");
  for (const [nombre, flujo] of FLUJOS) {
    test(`${nombre} (390 px)`, async ({ page }) => flujo(page, CELULAR));
  }
});
