// Ayudas compartidas por las capturas de B11 (`web.spec.js`) y las definitivas de B16
// (`capturas_reales.spec.js`).

// Espera a que las dos fuentes estén cargadas en la página y en el iframe del widget.
export async function fuentesListas(page) {
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

// Con las fuentes cargadas cambia el alto del texto: la conversación vuelve al final (si hay
// mensajes), como la deja el widget.
export async function conversacionAlFinal(page) {
  for (const marco of page.frames()) {
    await marco
      .evaluate(() => {
        const zona = document.querySelector("main[aria-live]");
        if (zona?.querySelector("[data-autor]")) zona.scrollTop = zona.scrollHeight;
      })
      .catch(() => {});
  }
}
