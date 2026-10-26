// Vite con React 19 y Tailwind 4 (ADR-08): tres páginas en una sola compilación.
//   /ovt/      OVT simulada con el widget insertado por una etiqueta de script
//   /widget/   el widget que monta el iframe
//   /consola/  bandeja del funcionario y métricas del administrador
// En desarrollo, /api y /health van a la API (uvicorn en el puerto 8001); en el servidor, el
// proxy sirve la compilación y enruta la API (B13).
import { resolve } from "node:path";

import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

const API = process.env.REALTIX_API ?? "http://localhost:8001";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  build: {
    rollupOptions: {
      input: {
        inicio: resolve(import.meta.dirname, "index.html"),
        ovt: resolve(import.meta.dirname, "ovt/index.html"),
        widget: resolve(import.meta.dirname, "widget/index.html"),
        consola: resolve(import.meta.dirname, "consola/index.html"),
      },
    },
  },
  server: {
    port: 5173,
    strictPort: true,
    proxy: { "/api": API, "/health": API },
  },
  preview: { port: 4173, strictPort: true, proxy: { "/api": API, "/health": API } },
});
