// Pruebas de la web con Playwright (B11). La API se simula en el navegador con el contrato de la
// sección 3.8 (tests/simulador.js): no se gastan modelos ni hace falta el backend. Las capturas
// para docs/capturas/ se toman con `npm run capturas`.
import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "tests",
  fullyParallel: true,
  reporter: [["list"]],
  use: { baseURL: "http://localhost:4173", locale: "es-CO", timezoneId: "America/Bogota" },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: {
    command: "npx vite preview --port 4173 --strictPort",
    url: "http://localhost:4173/ovt/",
    reuseExistingServer: !process.env.CI,
  },
});
