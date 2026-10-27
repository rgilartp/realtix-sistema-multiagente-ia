// B16: capturas definitivas contra el sistema multiagente de IA desplegado y congelado (no contra la
// API simulada). No corre en la CI ni con `npm test`: solo con CAPTURAS_REALES=1 y URL_REAL. El
// comando, con el token leído sin eco y sin quedar en el historial, está en
// docs/capturas/definitivas/README.md.
// El token de administrador no se escribe en la página: se agrega como cabecera a la petición de
// las métricas, así no queda en las capturas ni en los informes de error de Playwright. Las
// consultas no son de ningún escenario (A8). Las capturas quedan en docs/capturas/definitivas/.
import { expect, test } from "@playwright/test";

import { conversacionAlFinal, fuentesListas } from "./capturas.js";

const ACTIVO = process.env.CAPTURAS_REALES === "1";
const ESCRITORIO = { width: 1280, height: 800 };
const CELULAR = { width: 390, height: 844 };
const ESPERA_RESPUESTA = 60_000; // una consulta con recuperación tarda hasta unos 15 s

if (ACTIVO && !process.env.URL_REAL) {
  throw new Error("Falta URL_REAL (la dirección del sistema desplegado).");
}

test.skip(!ACTIVO, "Solo con CAPTURAS_REALES=1 y URL_REAL (B16).");
test.use({ baseURL: process.env.URL_REAL, testIdAttribute: "data-prueba" });
// En orden: primero la consola, para que las dos consultas del widget no entren en sus métricas.
test.describe.configure({ mode: "serial" });

async function guardar(page, nombre, completa = false) {
  await fuentesListas(page);
  await page.waitForTimeout(100); // el widget recalcula su altura con el rótulo ya dibujado
  await conversacionAlFinal(page);
  const { width } = page.viewportSize();
  await page.screenshot({
    path: `../docs/capturas/definitivas/${nombre}_${width}.png`,
    animations: "disabled",
    fullPage: completa,
  });
}

async function abrirWidget(page, tamano) {
  await page.setViewportSize(tamano);
  await page.goto("/ovt/");
  if (tamano.width < 640) await page.getByRole("button", { name: "Asistente tributario" }).click();
  const widget = page.frameLocator("iframe[data-realtix-widget]");
  await expect(widget.getByTestId("aviso-ia")).toBeVisible();
  return widget;
}

async function preguntar(widget, texto) {
  const campo = widget.getByLabel("Escribe tu consulta");
  await campo.fill(texto);
  await campo.press("Enter");
  const respuesta = widget.locator("[data-autor=agente]").last();
  await expect(respuesta).toBeVisible({ timeout: ESPERA_RESPUESTA });
  return respuesta;
}

for (const tamano of [ESCRITORIO, CELULAR]) {
  test(`métricas reales de la consola (${tamano.width} px)`, async ({ page }) => {
    const token = process.env.TOKEN_ADMIN;
    expect(Boolean(token), "Falta TOKEN_ADMIN en el entorno.").toBe(true);
    await page.route("**/api/v1/admin/metricas**", (ruta) =>
      ruta.continue({
        headers: { ...ruta.request().headers(), authorization: `Bearer ${token}` },
      }),
    );
    await page.setViewportSize(tamano);
    await page.goto("/consola/");
    await page.getByRole("button", { name: "Métricas" }).click();
    // El campo lleva un texto de relleno; el token real va solo en la cabecera.
    await page.getByLabel("Token de administrador (métricas)").fill("token-en-cabecera");
    await page.getByRole("button", { name: "Cargar métricas" }).click();
    await expect(page.getByTestId("matriz")).toBeVisible({ timeout: ESPERA_RESPUESTA });
    await guardar(page, "consola_metricas_final", true);
  });
}

for (const tamano of [ESCRITORIO, CELULAR]) {
  test(`respuesta sobre normas con sus fuentes (${tamano.width} px)`, async ({ page }) => {
    test.setTimeout(2 * ESPERA_RESPUESTA);
    const widget = await abrirWidget(page, tamano);
    const respuesta = await preguntar(widget, "¿Qué es el impuesto predial?");
    await expect(respuesta).toContainText("Fuentes", { timeout: ESPERA_RESPUESTA });
    await guardar(page, "widget_respuesta_normas");
  });
}
