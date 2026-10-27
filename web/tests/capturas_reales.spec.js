// B16: capturas definitivas contra el sistema multiagente de IA desplegado y congelado (no contra la
// API simulada). No corre en la CI ni con `npm test`: solo con CAPTURAS_REALES=1 y URL_REAL, por
// ejemplo, en horario hábil:
//   cd web && npm run build && \
//   CAPTURAS_REALES=1 URL_REAL=https://<subdominio>.duckdns.org TOKEN_ADMIN=<token> \
//   npx playwright test tests/capturas_reales.spec.js
// El token de administrador lo escribe Rodolfo en su terminal; no se guarda ni se imprime. Las
// consultas no son de ningún escenario (A8). Las capturas quedan en docs/capturas/definitivas/.
import { expect, test } from "@playwright/test";

const ACTIVO = process.env.CAPTURAS_REALES === "1" && Boolean(process.env.URL_REAL);
const ESCRITORIO = { width: 1280, height: 800 };
const CELULAR = { width: 390, height: 844 };
const ESPERA_RESPUESTA = 60_000; // una consulta con recuperación tarda hasta unos 15 s

test.skip(!ACTIVO, "Solo con CAPTURAS_REALES=1 y URL_REAL (B16).");
test.use({ baseURL: process.env.URL_REAL, testIdAttribute: "data-prueba" });

async function guardar(page, nombre, completa = false) {
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
  test(`respuesta sobre normas con sus fuentes (${tamano.width} px)`, async ({ page }) => {
    test.setTimeout(2 * ESPERA_RESPUESTA);
    const widget = await abrirWidget(page, tamano);
    const respuesta = await preguntar(widget, "¿Qué es el impuesto predial?");
    await expect(respuesta).toContainText("Fuentes", { timeout: ESPERA_RESPUESTA });
    await guardar(page, "widget_respuesta_normas");
  });

  test(`métricas reales de la consola (${tamano.width} px)`, async ({ page }) => {
    test.skip(!process.env.TOKEN_ADMIN, "Falta TOKEN_ADMIN en el entorno.");
    await page.setViewportSize(tamano);
    await page.goto("/consola/");
    await page.getByRole("button", { name: "Métricas" }).click();
    await page.getByLabel("Token de administrador (métricas)").fill(process.env.TOKEN_ADMIN);
    await page.getByRole("button", { name: "Cargar métricas" }).click();
    await expect(page.getByTestId("matriz")).toBeVisible({ timeout: ESPERA_RESPUESTA });
    await guardar(page, "consola_metricas_final", true);
  });
}
