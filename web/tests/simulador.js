// API simulada en el navegador para las pruebas de la web (contrato de la sección 3.8).
// Los textos son los del sistema (Horario.aviso_fuera_de_horario para HOR-01, el aviso de
// transferencia, el de modo humano y la confirmación del recibo de OCR-01). Las consultas que
// llegan quedan en `solicitudes`, para revisar el token y los cuerpos.

export const TEXTOS = {
  avisoIa:
    "Te atiende un asistente de inteligencia artificial. Sus respuestas son orientativas y " +
    "puedes pedir que te atienda un funcionario en cualquier momento",
  predial:
    "El impuesto predial unificado es un tributo anual sobre los predios de Bogotá; se calcula " +
    "con el avalúo catastral y la tarifa que corresponde al predio (Acuerdo 105 de 2003, art. 2).",
  fueraDeHorario:
    "En este momento estoy fuera del horario de atención. Atiendo de lunes a viernes, de 8:00 a. m. " +
    "a 5:00 p. m. (hora de Colombia), sin contar festivos. Vuelvo a atender el lunes 5 de octubre de " +
    "2026 a las 8:00 a. m. Fuera de ese horario no puedo responder consultas ni transferirlas a un " +
    "funcionario: escríbeme de nuevo entonces.",
  transferencia:
    "Con gusto te comunico con un funcionario. Voy a transferir tu consulta a un funcionario, que te " +
    "atenderá a la brevedad. Ya le compartí un resumen para que no tengas que repetirlo.",
  confirmacion:
    "Estos son los datos que leí del recibo:\n- Matrícula catastral: 50C-9000301\n- Vigencia fiscal: " +
    "2026\n- Avalúo catastral: $350.000.000\n- Valor liquidado: $2.135.000\n- Descuento por pronto " +
    "pago: $213.500\n- Fecha límite de pago: 10/07/2026\n\n¿Es correcto?",
  funcionario: "Hola, soy el funcionario que revisa tu caso. Ya vi el resumen; te ayudo con el pago.",
};

const USUARIOS = [
  { usuario: "U01", nombre: "Usuario de Prueba 01", tipo_persona: "natural" },
  { usuario: "U03", nombre: "Usuario de Prueba 03", tipo_persona: "natural" },
  { usuario: "U04", nombre: "Empresa de Prueba 04 S.A.S.", tipo_persona: "juridica" },
];

function meta(extra = {}) {
  return {
    categoria: null, agentes_invocados: [], nivel_confianza: null, motivo_escalamiento: null,
    caso_id: null, fuentes: [], contextos: null, datos_extraidos: null, tiempos_ms: { total: 5 },
    tokens: {}, modelo_por_nodo: {}, version: "0.5.0", ...extra,
  };
}

export async function simularApi(page, { fueraDeHorario = false } = {}) {
  const solicitudes = [];
  const conversaciones = new Set();
  let consultasDeMensajes = 0;

  const chat = (id, respuesta, interlocutor, estado, extra = {}) => {
    const primera = !conversaciones.has(id);
    conversaciones.add(id);
    return {
      id_conversacion: id, respuesta, aviso_ia: primera ? TEXTOS.avisoIa : null,
      interlocutor, estado, meta: meta(extra),
    };
  };

  await page.route("**/api/**", async (route) => {
    const peticion = route.request();
    const url = new URL(peticion.url());
    const ruta = url.pathname;
    const metodo = peticion.method();
    const auth = peticion.headers()["authorization"] ?? null;
    let cuerpo = null;
    if (metodo === "POST" && !ruta.endsWith("/documento")) cuerpo = peticion.postDataJSON();
    solicitudes.push({ ruta, metodo, auth, cuerpo });
    const json = (datos, status = 200) => route.fulfill({ status, json: datos });

    if (ruta === "/api/v1/ovt-simulada/usuarios") return json(USUARIOS);
    if (ruta === "/api/v1/ovt-simulada/sesion") {
      return json({ token: `token-de-prueba-${cuerpo.usuario}`, usuario: cuerpo.usuario, expira_en_s: 7200 });
    }
    if (ruta === "/api/v1/chat/mensaje") {
      if (fueraDeHorario) {
        return json(chat(cuerpo.id_conversacion, TEXTOS.fueraDeHorario, "sistema", "fuera_de_horario"));
      }
      return json(chat(cuerpo.id_conversacion, TEXTOS.predial, "agente", "respondida", {
        categoria: "ipu", agentes_invocados: ["nodo_orquestador", "nodo_ipu", "nodo_confianza", "nodo_respuesta"],
        nivel_confianza: 0.86,
      }));
    }
    if (ruta === "/api/v1/chat/documento") {
      const id = /name="id_conversacion"\r\n\r\n([^\r]+)/.exec(peticion.postData() ?? "")?.[1] ?? "conv";
      return json(chat(id, TEXTOS.confirmacion, "agente", "aclaracion", { categoria: "ocr" }));
    }
    if (ruta === "/api/v1/escalamiento" && metodo === "POST") {
      return json(chat(cuerpo.id_conversacion, TEXTOS.transferencia, "agente", "escalada", {
        motivo_escalamiento: "solicitud explícita", caso_id: `CASO-${cuerpo.id_conversacion}`,
        nivel_confianza: 0,
      }));
    }
    if (/^\/api\/v1\/chat\/[^/]+\/mensajes$/.test(ruta)) {
      consultasDeMensajes += 1;
      const base = [
        { indice: 0, autor: "contribuyente", texto: "Quiero hablar con un funcionario" },
        { indice: 1, autor: "agente", texto: TEXTOS.transferencia },
      ];
      const mensajes = consultasDeMensajes > 1
        ? [...base, { indice: 2, autor: "funcionario", texto: TEXTOS.funcionario }]
        : base;
      const desde = Number(url.searchParams.get("desde") ?? 0);
      return json({ id_conversacion: "conv", estado: "escalada", mensajes: mensajes.slice(desde), siguiente: mensajes.length });
    }
    if (ruta === "/api/v1/escalamiento/casos") {
      if (auth !== "Bearer token-funcionario") return json({ detalle: "Necesitas un token válido para esta consulta." }, 401);
      return json([
        { id_caso: "CASO-conv-7f3a", id_conversacion: "conv-7f3a", motivo: "solicitud explícita",
          categoria: null, nivel_confianza: 0, estado: "abierto", fecha_escalamiento: "2026-10-01T15:12:00Z" },
        { id_caso: "CASO-conv-91bc", id_conversacion: "conv-91bc", motivo: "confianza insuficiente",
          categoria: "ipu", nivel_confianza: 0.58, estado: "abierto", fecha_escalamiento: "2026-10-01T16:40:00Z" },
      ]);
    }
    if (ruta.startsWith("/api/v1/escalamiento/casos/")) {
      return json({
        id_caso: "CASO-conv-91bc", id_conversacion: "conv-91bc", motivo: "confianza insuficiente",
        categoria: "ipu", nivel_confianza: 0.58, estado: "abierto", fecha_escalamiento: "2026-10-01T16:40:00Z",
        resumen: "Motivo: confianza insuficiente. Categoría: ipu. Nivel de confianza: 0,58. Intentos de clasificación: 0.",
        resumen_estructurado: { motivo: "confianza insuficiente", categoria: "ipu", nivel_confianza: 0.58 },
        intentos: 0,
        mensajes: [
          { indice: 0, autor: "contribuyente", texto: "¿Cuánto puede subir mi predial de un año a otro?" },
          { indice: 1, autor: "agente", texto: TEXTOS.transferencia },
        ],
      });
    }
    if (ruta === "/api/v1/admin/metricas") {
      if (auth !== "Bearer token-admin") return json({ detalle: "Necesitas un token válido para esta consulta." }, 401);
      const fila = (valores) => ({ ipu: 0, ica: 0, general: 0, ocr: 0, fuera_de_alcance: 0, sin_categoria: 0, ...valores });
      return json({
        turnos: 64, turnos_etiquetados: 57, exactitud: 0.947,
        matriz_de_confusion: {
          ipu: fila({ ipu: 15 }), ica: fila({ ica: 9, general: 1 }), general: fila({ general: 7 }),
          ocr: fila({ ocr: 7 }), fuera_de_alcance: fila({ fuera_de_alcance: 3, general: 2 }), sin_categoria: fila({}),
        },
        por_categoria: {
          ipu: { soporte: 15, precision: 1, exhaustividad: 1, f1: 1 },
          ica: { soporte: 10, precision: 1, exhaustividad: 0.9, f1: 0.947 },
          general: { soporte: 7, precision: 0.7, exhaustividad: 1, f1: 0.824 },
          ocr: { soporte: 7, precision: 1, exhaustividad: 1, f1: 1 },
          fuera_de_alcance: { soporte: 5, precision: 1, exhaustividad: 0.6, f1: 0.75 },
        },
        promedio_macro: { precision: 0.94, exhaustividad: 0.9, f1: 0.904 },
        tiempos_ms: { mediana: 6868, p95: 14270, maximo: 14270 },
        por_estado: { respondida: 40 }, conversaciones: 57, conversaciones_escaladas: 9,
      });
    }
    return json({ detalle: "No encontré lo que buscas." }, 404);
  });
  await page.route("**/health", (route) =>
    route.fulfill({ json: { estado: "ok", version: "0.5.0", dependencias: { postgres: "ok", chroma: "ok", realsit: "ok" } } }),
  );
  return solicitudes;
}
