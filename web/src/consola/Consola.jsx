// Consola (sección 3.6 y RF-OBS-02 y RF-OBS-03): bandeja de solo lectura para el funcionario y
// métricas para el administrador, cada una con su token, y un enlace a LangSmith.
import { useEffect, useMemo, useRef, useState } from "react";

import { mensajeParaMostrar, obtener } from "../api.js";

const LANGSMITH = import.meta.env.VITE_LANGSMITH_URL ?? "https://smith.langchain.com/";
const CATEGORIAS = ["ipu", "ica", "general", "ocr", "fuera_de_alcance", "sin_categoria"];
const NOMBRES = {
  ipu: "Predial",
  ica: "ICA",
  general: "General",
  ocr: "Recibo (OCR)",
  fuera_de_alcance: "Fuera de alcance",
  sin_categoria: "Sin categoría",
};
const nombre = (categoria) => NOMBRES[categoria] ?? categoria.replaceAll("_", " ");
const CLAVES_RESUMEN = {
  motivo: "Motivo",
  motivo_original: "Motivo original",
  categoria: "Categoría",
  nivel_confianza: "Nivel de confianza",
  intentos: "Reclasificaciones",
  partes_resueltas: "Partes resueltas",
  partes_rechazadas: "Partes rechazadas",
  duracion_resumen_ms: "Tiempo del resumen (ms)",
};
const AUTORES = { contribuyente: "Contribuyente", agente: "Asistente de IA", funcionario: "Funcionario", sistema: "Sistema" };

function guardar(clave, valor) {
  try {
    sessionStorage.setItem(clave, valor);
  } catch {
    /* sin almacenamiento: el token vive mientras la página esté abierta */
  }
}

function leerGuardado(clave) {
  try {
    return sessionStorage.getItem(clave) ?? "";
  } catch {
    return "";
  }
}

function fecha(valor) {
  return valor
    ? new Date(valor).toLocaleString("es-CO", { timeZone: "America/Bogota", dateStyle: "medium", timeStyle: "short" })
    : "";
}

function numero(valor, decimales = 3, fijos = false) {
  if (valor === null || valor === undefined) return "—";
  return typeof valor === "number"
    ? valor.toLocaleString("es-CO", {
        maximumFractionDigits: decimales,
        minimumFractionDigits: fijos ? decimales : 0,
      })
    : String(valor);
}

function valorDelResumen(valor) {
  if (Array.isArray(valor)) {
    if (!valor.length) return "ninguna";
    return valor.map((p) => (typeof p === "string" ? p : (p.categoria ?? JSON.stringify(p)))).join(", ");
  }
  if (valor && typeof valor === "object") return JSON.stringify(valor);
  return numero(valor);
}

function Vacio({ titulo, texto }) {
  return (
    <div className="rounded-casilla border border-dashed border-borde-control px-6 py-10 text-center">
      <p className="font-titulo text-lg font-bold [font-stretch:87.5%]">{titulo}</p>
      <p className="mt-1 text-sm text-tinta-suave">{texto}</p>
    </div>
  );
}

function AvisoDeError({ texto }) {
  return texto ? (
    <p className="rounded-casilla border border-error bg-error-suave px-4 py-2 text-sm text-error" role="alert">
      {texto}
    </p>
  ) : null;
}

// Casilla de un token: el rótulo arriba, el campo y la ayuda ligada a él.
function Token({ etiqueta, ayuda, valor, alCambiar, id }) {
  return (
    <div className="casilla-unida">
      <label htmlFor={id}>{etiqueta}</label>
      <input
        id={id}
        type="password"
        value={valor}
        onChange={(e) => alCambiar(e.target.value)}
        aria-describedby={`${id}-ayuda`}
        autoComplete="off"
      />
      <span id={`${id}-ayuda`} className="text-xs font-normal text-tinta-suave">
        {ayuda}
      </span>
    </div>
  );
}

function Boton({ children, ...props }) {
  return (
    <button
      type="button"
      className="min-h-11 rounded-control bg-sello px-4 text-sm font-semibold text-hoja enabled:hover:bg-sello-fuerte disabled:cursor-wait disabled:bg-papel-2 disabled:text-tinta-suave"
      {...props}
    >
      {children}
    </button>
  );
}

function Bandeja({ token }) {
  const [casos, setCasos] = useState(null);
  const [detalle, setDetalle] = useState(null);
  const [error, setError] = useState("");
  const [cargando, setCargando] = useState(false);
  const tituloDetalle = useRef(null);

  useEffect(() => {
    // Otro token: lo cargado con el anterior no se sigue mostrando.
    setCasos(null);
    setDetalle(null);
  }, [token]);
  const [busqueda, setBusqueda] = useState("");
  const [motivo, setMotivo] = useState("");
  const [estado, setEstado] = useState("");

  const cargar = async () => {
    setCargando(true);
    try {
      setCasos(await obtener("/api/v1/escalamiento/casos", token));
      setError("");
    } catch (e) {
      setError(mensajeParaMostrar(e));
    } finally {
      setCargando(false);
    }
  };

  const abrir = async (id) => {
    try {
      setDetalle(await obtener(`/api/v1/escalamiento/casos/${encodeURIComponent(id)}`, token));
    } catch (e) {
      setError(mensajeParaMostrar(e));
    }
  };

  // Al abrir un caso, el foco pasa a su título: el lector de pantalla lo anuncia y, en el
  // celular, el detalle (que queda debajo de la lista) entra en la pantalla.
  const idDetalle = detalle?.id_caso;
  useEffect(() => {
    if (idDetalle) tituloDetalle.current?.focus();
  }, [idDetalle]);

  const motivos = useMemo(() => [...new Set((casos ?? []).map((c) => c.motivo))], [casos]);
  const estados = useMemo(() => [...new Set((casos ?? []).map((c) => c.estado))], [casos]);
  const visibles = (casos ?? []).filter(
    (c) =>
      (!motivo || c.motivo === motivo) &&
      (!estado || c.estado === estado) &&
      (!busqueda || `${c.id_caso} ${c.id_conversacion}`.toLowerCase().includes(busqueda.toLowerCase())),
  );
  const detalleVisible = detalle && visibles.some((c) => c.id_caso === detalle.id_caso) ? detalle : null;

  return (
    <section className="space-y-4" data-prueba="bandeja" aria-labelledby="titulo-bandeja" aria-busy={cargando}>
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 id="titulo-bandeja" className="text-xl font-bold md:text-2xl">
            Bandeja de casos
          </h2>
          <p className="text-sm text-tinta-suave">Solo lectura: los casos que escaló el sistema, con su resumen.</p>
        </div>
        <Boton onClick={cargar} disabled={cargando}>
          Cargar casos
        </Boton>
      </div>
      <AvisoDeError texto={error} />

      {casos && (
        <div className="casillas sm:grid-cols-3">
          <label className="casilla-unida">
            Buscar
            <input value={busqueda} onChange={(e) => setBusqueda(e.target.value)} placeholder="Caso o conversación" />
          </label>
          <label className="casilla-unida">
            Motivo
            <select value={motivo} onChange={(e) => setMotivo(e.target.value)}>
              <option value="">Todos</option>
              {motivos.map((m) => (
                <option key={m}>{m}</option>
              ))}
            </select>
          </label>
          <label className="casilla-unida">
            Estado
            <select value={estado} onChange={(e) => setEstado(e.target.value)}>
              <option value="">Todos</option>
              {estados.map((e) => (
                <option key={e}>{e}</option>
              ))}
            </select>
          </label>
        </div>
      )}

      {!casos ? (
        <Vacio titulo="Sin casos cargados" texto="Escribe el token de funcionario y carga la bandeja." />
      ) : !visibles.length ? (
        <Vacio titulo="No hay casos con esos filtros" texto="Cambia la búsqueda, el motivo o el estado." />
      ) : (
        <div className="grid items-start gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.1fr)]">
          <ul className="divide-y divide-renglon overflow-hidden rounded-casilla border border-borde-control bg-hoja" aria-label={`${visibles.length} casos`}>
            {visibles.map((c) => {
              const elegido = detalleVisible?.id_caso === c.id_caso;
              return (
                <li key={c.id_caso}>
                  <button
                    type="button"
                    onClick={() => abrir(c.id_caso)}
                    aria-pressed={elegido}
                    className={`w-full px-4 py-3 text-left focus-visible:-outline-offset-3 active:scale-100 ${
                      elegido ? "bg-sello-suave ring-2 ring-sello ring-inset" : "hover:bg-papel"
                    }`}
                  >
                    <span className="flex flex-wrap items-baseline justify-between gap-2">
                      <span className="font-titulo text-lg font-bold [font-stretch:87.5%]">{c.id_caso}</span>
                      <span className="rounded-casilla border border-borde-control px-2 text-xs font-semibold text-tinta-suave">{c.estado}</span>
                    </span>
                    <span className="mt-0.5 block text-sm text-tinta">{c.motivo}</span>
                    <span className="mt-0.5 block text-xs text-tinta-suave">
                      {NOMBRES[c.categoria] ?? "Sin clasificar"}, confianza {numero(c.nivel_confianza, 2)}. {fecha(c.fecha_escalamiento)}
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>
          {detalleVisible ? (
            <article
              className="animate-entrada overflow-hidden rounded-casilla border border-sello bg-hoja"
              data-prueba="detalle"
              aria-labelledby="titulo-detalle"
            >
              <h3 id="titulo-detalle" ref={tituloDetalle} tabIndex={-1} className="banda scroll-mt-4 px-4 py-2 text-lg">
                {detalleVisible.id_caso}
              </h3>
              <div className="space-y-5 p-4 md:p-5">
                <p className="rounded-casilla bg-papel p-3 text-sm whitespace-pre-line text-wrap">{detalleVisible.resumen}</p>
                <div>
                  <h4 className="text-base font-bold">Resumen estructurado</h4>
                  <dl className="mt-1 text-sm">
                    {Object.entries(detalleVisible.resumen_estructurado ?? {}).map(([clave, valor]) => (
                      <div key={clave} className="grid grid-cols-[10rem_1fr] gap-x-4 border-b border-renglon py-1.5">
                        <dt className="text-tinta-suave">{CLAVES_RESUMEN[clave] ?? clave}</dt>
                        <dd className="font-semibold tabular-nums">
                          {clave === "categoria" && valor ? nombre(valor) : valorDelResumen(valor)}
                        </dd>
                      </div>
                    ))}
                  </dl>
                </div>
                <div>
                  <h4 className="text-base font-bold">Conversación</h4>
                  <ol className="mt-1 text-sm">
                    {detalleVisible.mensajes.map((m) => (
                      <li key={m.indice} className="border-b border-renglon py-2 last:border-b-0">
                        <span className="text-xs font-semibold text-tinta-suave">{AUTORES[m.autor] ?? m.autor}</span>
                        <p className="whitespace-pre-line text-wrap">{m.texto}</p>
                      </li>
                    ))}
                  </ol>
                </div>
              </div>
            </article>
          ) : (
            <Vacio titulo="Elige un caso" texto="Verás su resumen estructurado y la conversación." />
          )}
        </div>
      )}
    </section>
  );
}

// Intensidad del color según el valor; el texto siempre es tinta. El tope de cada color deja el
// contraste en 4,5:1 o más (lo mide `npm run contraste`, que lee estos valores).
const TOPE_ACIERTO = 40;
const TOPE_ERROR = 35;
function fondoCelda(valor, maximo, diagonal) {
  if (!valor) return undefined;
  const proporcion = valor / maximo;
  const color = diagonal ? "var(--color-sello)" : "var(--color-error)";
  const tope = diagonal ? TOPE_ACIERTO : TOPE_ERROR;
  return `color-mix(in srgb, ${color} ${Math.round(10 + proporcion * (tope - 10))}%, white)`;
}

function Metricas({ token }) {
  const [datos, setDatos] = useState(null);
  const [error, setError] = useState("");
  const [cargando, setCargando] = useState(false);

  useEffect(() => setDatos(null), [token]);

  const cargar = async () => {
    setCargando(true);
    try {
      setDatos(await obtener("/api/v1/admin/metricas", token));
      setError("");
    } catch (e) {
      setError(mensajeParaMostrar(e));
    } finally {
      setCargando(false);
    }
  };

  // Las categorías salen de la respuesta, en el orden conocido y luego las nuevas.
  const categorias = datos
    ? [
        ...CATEGORIAS.filter((c) => c in datos.matriz_de_confusion),
        ...Object.keys(datos.matriz_de_confusion).filter((c) => !CATEGORIAS.includes(c)),
      ]
    : [];
  const maximo = datos
    ? Math.max(1, ...categorias.flatMap((f) => categorias.map((c) => datos.matriz_de_confusion[f]?.[c] ?? 0)))
    : 1;

  return (
    <section className="space-y-4" data-prueba="metricas" aria-labelledby="titulo-metricas" aria-busy={cargando}>
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 id="titulo-metricas" className="text-xl font-bold md:text-2xl">
            Métricas de enrutamiento y tiempos
          </h2>
          <p className="text-sm text-tinta-suave">Del registro de interacciones y las etiquetas de los escenarios.</p>
        </div>
        <Boton onClick={cargar} disabled={cargando}>
          Cargar métricas
        </Boton>
      </div>
      <AvisoDeError texto={error} />
      {!datos ? (
        <Vacio titulo="Sin métricas cargadas" texto="Escribe el token de administrador y carga las métricas." />
      ) : (
        <div className="animate-entrada space-y-5">
          <dl className="casillas grid-cols-2 md:grid-cols-4">
            {[
              ["Exactitud del enrutamiento", numero(datos.exactitud)],
              ["F1 macro", numero(datos.promedio_macro.f1)],
              ["Latencia p50", `${numero(datos.tiempos_ms.mediana, 0)} ms`],
              ["Latencia p95", `${numero(datos.tiempos_ms.p95, 0)} ms`],
              ["Turnos registrados", numero(datos.turnos)],
              ["Turnos etiquetados", numero(datos.turnos_etiquetados)],
              ["Conversaciones escaladas", numero(datos.conversaciones_escaladas)],
              ["Latencia máxima", `${numero(datos.tiempos_ms.maximo, 0)} ms`],
            ].map(([nombre, valor]) => (
              <div key={nombre} className="bg-hoja px-3 py-2.5">
                <dt className="text-xs font-semibold text-tinta-suave">{nombre}</dt>
                <dd className="mt-0.5 font-titulo text-2xl font-bold tabular-nums [font-stretch:87.5%]">{valor}</dd>
              </div>
            ))}
          </dl>

          <div className="overflow-hidden rounded-casilla border border-sello bg-hoja">
            <h3 id="titulo-matriz" className="banda px-4 py-2 text-lg">
              Matriz de confusión
            </h3>
            <div className="px-4 pt-3 pb-2">
              <p className="text-sm text-tinta-suave">
                Cada fila es la categoría esperada y cada columna, la que eligió el sistema; la
                diagonal son los aciertos.
              </p>
              <p className="text-sm text-tinta-suave sm:hidden">Desliza la tabla para ver todas las columnas.</p>
            </div>
            <div className="overflow-x-auto">
            <table
              className="w-full min-w-[640px] table-fixed text-sm tabular-nums"
              data-prueba="matriz"
              aria-labelledby="titulo-matriz"
            >
              <colgroup>
                <col className="w-40" />
                {categorias.map((c) => (
                  <col key={c} />
                ))}
              </colgroup>
              <thead>
                <tr className="text-xs text-tinta-suave">
                  <th scope="col" className="px-3 py-2 text-left font-semibold">Esperada</th>
                  {categorias.map((c) => (
                    <th key={c} scope="col" className="px-1 py-2 text-center font-semibold break-words">
                      {nombre(c)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {categorias.map((fila) => (
                  <tr key={fila} className="border-t border-renglon">
                    <th scope="row" className="px-3 py-2 text-left font-semibold">
                      {nombre(fila)}
                    </th>
                    {categorias.map((col) => {
                      const valor = datos.matriz_de_confusion[fila]?.[col] ?? 0;
                      return (
                        <td
                          key={col}
                          className={`px-2 py-2 text-center ${valor ? "font-semibold text-tinta" : "text-tinta-suave"}`}
                          style={{ background: fondoCelda(valor, maximo, fila === col) }}
                        >
                          {valor}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
            </div>
          </div>

          <div className="overflow-x-auto rounded-casilla border border-sello bg-hoja">
            <table className="w-full text-sm tabular-nums">
              <caption className="banda px-4 py-2 text-left text-lg">Por categoría</caption>
              <thead>
                <tr className="text-xs text-tinta-suave">
                  <th scope="col" className="px-4 py-2 text-left font-semibold">Categoría</th>
                  <th scope="col" className="px-2 py-2 text-right font-semibold sm:px-3">
                    <abbr title="Soporte" className="no-underline sm:hidden">Sop.</abbr>
                    <span className="hidden sm:inline">Soporte</span>
                  </th>
                  <th scope="col" className="px-2 py-2 text-right font-semibold sm:px-3">
                    <abbr title="Precisión" className="no-underline sm:hidden">Prec.</abbr>
                    <span className="hidden sm:inline">Precisión</span>
                  </th>
                  <th scope="col" className="px-2 py-2 text-right font-semibold sm:px-3">
                    <abbr title="Exhaustividad" className="no-underline sm:hidden">Exh.</abbr>
                    <span className="hidden sm:inline">Exhaustividad</span>
                  </th>
                  <th scope="col" className="px-2 py-2 text-left font-semibold sm:px-4">F1</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(datos.por_categoria).map(([categoria, m]) => (
                  <tr key={categoria} className="border-t border-renglon">
                    <th scope="row" className="px-3 py-2 text-left font-semibold sm:px-4">
                      {nombre(categoria)}
                    </th>
                    <td className="px-2 py-2 text-right sm:px-3">{m.soporte}</td>
                    <td className="px-2 py-2 text-right sm:px-3">{numero(m.precision, 3, true)}</td>
                    <td className="px-2 py-2 text-right sm:px-3">{numero(m.exhaustividad, 3, true)}</td>
                    <td className="px-2 py-2 sm:px-4">
                      <span className="flex items-center gap-2">
                        <span className="font-semibold sm:w-12 sm:text-right">{numero(m.f1, 3, true)}</span>
                        <span className="hidden h-2 w-24 overflow-hidden rounded-[2px] bg-papel-2 sm:block" aria-hidden="true">
                          <span className="block h-full bg-sello" style={{ width: `${(m.f1 ?? 0) * 100}%` }} />
                        </span>
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </section>
  );
}

export default function Consola() {
  const [tokenFuncionario, setTokenFuncionario] = useState(() => leerGuardado("realtix-funcionario"));
  const [tokenAdmin, setTokenAdmin] = useState(() => leerGuardado("realtix-admin"));
  const [salud, setSalud] = useState(null);
  const [vista, setVista] = useState("bandeja");

  useEffect(() => {
    obtener("/health").then(setSalud).catch(() => setSalud({ estado: "sin conexión" }));
  }, []);

  const sano = salud?.estado === "ok";

  return (
    <div className="min-h-dvh bg-papel font-texto text-tinta">
      <div className="rotulo px-4 py-2 text-center text-base md:text-lg">
        Entorno simulado de pruebas con datos sintéticos
      </div>
      <header className="border-b border-renglon bg-hoja">
        <div className="mx-auto flex max-w-6xl flex-wrap items-end justify-between gap-3 px-4 py-4 sm:px-6">
          <div>
            <h1 className="text-2xl font-bold md:text-3xl">Consola</h1>
            <p className="text-sm text-tinta-suave">Sistema multiagente de IA, para funcionarios y administradores</p>
          </div>
          <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm">
            <span
              data-prueba="salud"
              className={`inline-flex items-center gap-2 font-semibold ${sano ? "text-funcionario" : "text-tinta-suave"}`}
            >
              <span className={`h-2.5 w-2.5 rounded-full ${sano ? "bg-funcionario" : "bg-tinta-suave"}`} aria-hidden="true" />
              Servicio: {salud?.estado ?? "…"}
              {salud?.version ? ` (v${salud.version})` : ""}
            </span>
            <a href={LANGSMITH} target="_blank" rel="noreferrer" className="inline-block py-1 font-semibold text-sello underline">
              Trazas en LangSmith
              <span className="sr-only"> (se abre en otra pestaña)</span>
            </a>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-6xl space-y-6 px-4 py-6 sm:px-6">
        <div className="casillas md:grid-cols-2">
          <Token
            id="token-funcionario"
            etiqueta="Token de funcionario (bandeja)"
            ayuda="Permite leer los casos escalados."
            valor={tokenFuncionario}
            alCambiar={(v) => {
              setTokenFuncionario(v);
              guardar("realtix-funcionario", v);
            }}
          />
          <Token
            id="token-admin"
            etiqueta="Token de administrador (métricas)"
            ayuda="Permite ver las métricas de enrutamiento y de tiempo."
            valor={tokenAdmin}
            alCambiar={(v) => {
              setTokenAdmin(v);
              guardar("realtix-admin", v);
            }}
          />
        </div>
        <nav className="flex gap-1 border-b-2 border-sello" aria-label="Vistas de la consola">
          {[
            ["bandeja", "Bandeja"],
            ["metricas", "Métricas"],
          ].map(([clave, nombre]) => (
            <button
              key={clave}
              type="button"
              onClick={() => setVista(clave)}
              aria-pressed={vista === clave}
              className={`min-h-11 rounded-t-control px-5 text-sm font-semibold active:scale-100 ${
                vista === clave ? "bg-sello text-hoja" : "bg-papel-2 text-tinta hover:bg-sello-suave hover:text-sello"
              }`}
            >
              {nombre}
            </button>
          ))}
        </nav>
        {vista === "bandeja" ? <Bandeja token={tokenFuncionario} /> : <Metricas token={tokenAdmin} />}
      </main>
    </div>
  );
}
