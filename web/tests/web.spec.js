// B11: OVT simulada, widget y consola (RF-UI-01 a RF-UI-04, RF-SYS-06, RF-ESC-05 y RNF-07),
// con la API simulada en el navegador. Con CAPTURAS=1 guarda las capturas en docs/capturas/.
import { expect, test } from "@playwright/test";

import { TEXTOS, simularApi } from "./simulador.js";

const CAPTURAS = "../docs/capturas";
const MARCAS_PROHIBIDAS = /bogot[aá]|secretar[ií]a|hacienda|alcald[ií]a|realtix|realsit/i;
const PNG = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+ip1sAAAAASUVORK5CYII=",
  "base64",
);

async function capturar(objetivo, nombre) {
  if (process.env.CAPTURAS === "1") await objetivo.screenshot({ path: `${CAPTURAS}/${nombre}.png` });
}

async function abrirOvt(page, opciones) {
  const solicitudes = await simularApi(page, opciones);
  await page.setViewportSize({ width: 1280, height: 800 });
  await page.goto("/ovt/");
  const widget = page.frameLocator("iframe[data-realtix-widget]");
  await expect(widget.getByTestId("aviso-ia")).toBeVisible();
  return { solicitudes, widget };
}

async function iniciarSesion(page, usuario = "U03") {
  await page.getByTestId("usuario").selectOption(usuario);
  await page.getByRole("button", { name: "Iniciar sesión simulada" }).click();
  await expect(page.getByTestId("sesion")).toContainText(usuario);
}

test.use({ testIdAttribute: "data-prueba" });

test("OVT simulada: rótulo, sin marcas reales y widget en un iframe @captura", async ({ page }) => {
  await abrirOvt(page);
  await expect(page.getByTestId("rotulo")).toHaveText(
    "Entorno simulado de pruebas — no es la Oficina Virtual Tributaria real",
  );
  await expect(page.locator("img, svg")).toHaveCount(0); // sin logos
  expect(await page.locator("body").innerText()).not.toMatch(MARCAS_PROHIBIDAS);
  await expect(page.locator("iframe[data-realtix-widget]")).toHaveAttribute("src", /\/widget\/$/);
  await capturar(page, "ovt_simulada");
});

test("widget: aviso de IA al abrir, sesión por postMessage e interlocutor @captura", async ({ page }) => {
  const { solicitudes, widget } = await abrirOvt(page);
  // RF-SYS-06: el aviso está antes de cualquier respuesta, con el botón del funcionario.
  await expect(widget.getByTestId("aviso-ia")).toContainText(TEXTOS.avisoIa);
  await expect(widget.getByTestId("aviso-ia").getByRole("button", { name: "Hablar con un funcionario" })).toBeVisible();
  await expect(widget.getByTestId("interlocutor")).toHaveText("Te atiende un asistente de IA");
  await iniciarSesion(page);
  await expect(widget.getByText("Sesión iniciada")).toBeVisible();
  await widget.getByLabel("Escribe tu consulta").fill("¿Qué es el predial?");
  await widget.getByRole("button", { name: "Enviar" }).click();
  await expect(widget.getByText(TEXTOS.predial)).toBeVisible();
  await expect(widget.locator("[data-autor=agente]").getByText("Asistente de IA")).toBeVisible();
  // El token de la OVT llegó al widget por postMessage y viaja en la cabecera (RF-UI-02).
  const enviada = solicitudes.find((s) => s.ruta === "/api/v1/chat/mensaje");
  expect(enviada.auth).toBe("Bearer token-de-prueba-U03");
  expect(enviada.cuerpo.id_conversacion).toMatch(/^conv-[0-9a-f-]{36}$/);
  await capturar(page, "widget_respuesta");
});

test("widget: fuera de horario destacado (RNF-07) @captura", async ({ page }) => {
  const { widget } = await abrirOvt(page, { fueraDeHorario: true });
  await widget.getByLabel("Escribe tu consulta").fill("Hola, necesito hablar con un funcionario");
  await widget.getByRole("button", { name: "Enviar" }).click();
  const aviso = widget.locator("[data-autor=sistema]");
  await expect(aviso).toContainText("Vuelvo a atender el lunes 5 de octubre de 2026 a las 8:00 a. m.");
  await expect(aviso.getByText("Mensaje del sistema")).toBeVisible();
  await capturar(page, "widget_fuera_de_horario");
});

test("widget: carga del recibo desde la conversación (RF-UI-04) @captura", async ({ page }) => {
  const { solicitudes, widget } = await abrirOvt(page);
  await iniciarSesion(page);
  // Un tipo no admitido se rechaza en el navegador, sin llamar a la API.
  await widget.getByTestId("archivo").setInputFiles({ name: "nota.txt", mimeType: "text/plain", buffer: Buffer.from("hola") });
  await expect(widget.getByText("Solo puedo recibir el recibo en JPG, PNG o PDF.")).toBeVisible();
  expect(solicitudes.some((s) => s.ruta === "/api/v1/chat/documento")).toBe(false);
  await widget.getByTestId("archivo").setInputFiles({ name: "recibo.png", mimeType: "image/png", buffer: PNG });
  await expect(widget.getByText("📎 recibo.png")).toBeVisible();
  await expect(widget.getByText("¿Es correcto?")).toBeVisible();
  const subida = solicitudes.find((s) => s.ruta === "/api/v1/chat/documento");
  expect(subida.auth).toBe("Bearer token-de-prueba-U03");
  await capturar(page, "widget_recibo");
});

test("widget: botón del funcionario y mensajes nuevos de la conversación escalada @captura", async ({ page }) => {
  const { widget } = await abrirOvt(page);
  await widget.getByTestId("aviso-ia").getByRole("button", { name: "Hablar con un funcionario" }).click();
  await expect(widget.getByText(TEXTOS.transferencia)).toBeVisible();
  await expect(widget.getByTestId("interlocutor")).toHaveText("Tu caso está con un funcionario");
  await expect(widget.getByRole("button", { name: "Hablar con un funcionario" })).toBeDisabled();
  // La consulta periódica trae el mensaje del funcionario (RF-ESC-05 y RF-UI-03).
  await expect(widget.getByText(TEXTOS.funcionario)).toBeVisible({ timeout: 8000 });
  await expect(widget.getByTestId("interlocutor")).toHaveText("Te atiende un funcionario");
  await expect(widget.locator("[data-autor=funcionario]").getByText("Funcionario", { exact: true })).toBeVisible();
  await capturar(page, "widget_escalado");
});

test("consola: bandeja con token de funcionario y métricas con el de administrador @captura", async ({ page }) => {
  await simularApi(page);
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.goto("/consola/");
  await expect(page.getByTestId("salud")).toContainText("ok");
  await expect(page.getByRole("link", { name: "Trazas en LangSmith" })).toHaveAttribute("href", /smith\.langchain\.com/);
  await page.getByRole("button", { name: "Cargar casos" }).click();
  await expect(page.getByText("Necesitas un token válido para esta consulta.")).toBeVisible();
  await page.getByLabel("Token de funcionario (bandeja)").fill("token-funcionario");
  await page.getByRole("button", { name: "Cargar casos" }).click();
  await page.getByRole("button", { name: "CASO-conv-91bc" }).click();
  await expect(page.getByTestId("detalle")).toContainText("confianza insuficiente");
  await capturar(page, "consola_bandeja");
  await page.getByRole("button", { name: "Métricas" }).click();
  await page.getByLabel("Token de administrador (métricas)").fill("token-admin");
  await page.getByRole("button", { name: "Cargar métricas" }).click();
  const matriz = page.getByTestId("matriz");
  await expect(matriz).toContainText("fuera_de_alcance");
  await expect(matriz.locator("tr", { hasText: "ica" }).first()).toContainText("9");
  await capturar(page, "consola_metricas");
});
