// Consola (sección 3.6 y RF-OBS-02 y RF-OBS-03): bandeja de solo lectura para el funcionario y
// métricas para el administrador, cada una con su token, y un enlace a LangSmith.
import { useEffect, useState } from "react";

import { obtener } from "../api.js";

const LANGSMITH = import.meta.env.VITE_LANGSMITH_URL ?? "https://smith.langchain.com/";
const CATEGORIAS = ["ipu", "ica", "general", "ocr", "fuera_de_alcance", "sin_categoria"];

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
  return valor ? new Date(valor).toLocaleString("es-CO", { timeZone: "America/Bogota" }) : "";
}

function numero(valor) {
  return valor === null || valor === undefined ? "—" : String(valor).replace(".", ",");
}

function Token({ etiqueta, valor, alCambiar, id }) {
  return (
    <label className="flex flex-col gap-1 text-sm" htmlFor={id}>
      {etiqueta}
      <input
        id={id}
        type="password"
        value={valor}
        onChange={(e) => alCambiar(e.target.value)}
        className="rounded-lg border border-slate-300 px-3 py-2"
        autoComplete="off"
      />
    </label>
  );
}

function Bandeja({ token }) {
  const [casos, setCasos] = useState([]);
  const [detalle, setDetalle] = useState(null);
  const [error, setError] = useState("");

  const cargar = async () => {
    try {
      setCasos(await obtener("/api/v1/escalamiento/casos", token));
      setError("");
    } catch (e) {
      setError(e.message);
    }
  };

  const abrir = async (id) => {
    try {
      setDetalle(await obtener(`/api/v1/escalamiento/casos/${encodeURIComponent(id)}`, token));
    } catch (e) {
      setError(e.message);
    }
  };

  return (
    <section className="space-y-3" data-prueba="bandeja">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Bandeja de casos (solo lectura)</h2>
        <button type="button" onClick={cargar} className="rounded-lg bg-slate-800 px-3 py-1.5 text-sm text-white">
          Cargar casos
        </button>
      </div>
      {error && <p className="text-sm text-rose-700">{error}</p>}
      <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-100 text-xs text-slate-600 uppercase">
            <tr>
              <th className="px-3 py-2">Caso</th>
              <th className="px-3 py-2">Motivo</th>
              <th className="px-3 py-2">Categoría</th>
              <th className="px-3 py-2">Confianza</th>
              <th className="px-3 py-2">Fecha</th>
              <th className="px-3 py-2">Estado</th>
            </tr>
          </thead>
          <tbody>
            {casos.map((c) => (
              <tr key={c.id_caso} className="border-t border-slate-100 hover:bg-slate-50">
                <td className="px-3 py-2">
                  <button type="button" onClick={() => abrir(c.id_caso)} className="text-emerald-800 underline">
                    {c.id_caso}
                  </button>
                </td>
                <td className="px-3 py-2">{c.motivo}</td>
                <td className="px-3 py-2">{c.categoria ?? "sin clasificar"}</td>
                <td className="px-3 py-2">{numero(c.nivel_confianza)}</td>
                <td className="px-3 py-2">{fecha(c.fecha_escalamiento)}</td>
                <td className="px-3 py-2">{c.estado}</td>
              </tr>
            ))}
            {!casos.length && (
              <tr>
                <td colSpan={6} className="px-3 py-4 text-center text-slate-500">
                  Sin casos cargados
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      {detalle && (
        <article className="space-y-3 rounded-xl border border-slate-200 bg-white p-4" data-prueba="detalle">
          <h3 className="font-semibold">{detalle.id_caso}</h3>
          <p className="text-sm whitespace-pre-line">{detalle.resumen}</p>
          <details className="text-sm">
            <summary className="cursor-pointer text-slate-600">Resumen estructurado</summary>
            <pre className="mt-2 overflow-x-auto rounded bg-slate-100 p-2 text-xs">
              {JSON.stringify(detalle.resumen_estructurado, null, 2)}
            </pre>
          </details>
          <ol className="space-y-2 text-sm">
            {detalle.mensajes.map((m) => (
              <li key={m.indice} className="rounded-lg bg-slate-50 px-3 py-2">
                <span className="font-semibold">{m.autor}: </span>
                <span className="whitespace-pre-line">{m.texto}</span>
              </li>
            ))}
          </ol>
        </article>
      )}
    </section>
  );
}

function Metricas({ token }) {
  const [datos, setDatos] = useState(null);
  const [error, setError] = useState("");

  const cargar = async () => {
    try {
      setDatos(await obtener("/api/v1/admin/metricas", token));
      setError("");
    } catch (e) {
      setError(e.message);
    }
  };

  return (
    <section className="space-y-3" data-prueba="metricas">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Métricas de enrutamiento y tiempos</h2>
        <button type="button" onClick={cargar} className="rounded-lg bg-slate-800 px-3 py-1.5 text-sm text-white">
          Cargar métricas
        </button>
      </div>
      {error && <p className="text-sm text-rose-700">{error}</p>}
      {datos && (
        <div className="space-y-4">
          <dl className="grid grid-cols-2 gap-3 text-sm md:grid-cols-4">
            {[
              ["Turnos", datos.turnos],
              ["Conversaciones etiquetadas", datos.turnos_etiquetados],
              ["Exactitud", numero(datos.exactitud)],
              ["Conversaciones escaladas", datos.conversaciones_escaladas],
              ["Mediana (ms)", numero(datos.tiempos_ms.mediana)],
              ["p95 (ms)", numero(datos.tiempos_ms.p95)],
              ["Máximo (ms)", numero(datos.tiempos_ms.maximo)],
              ["F1 macro", numero(datos.promedio_macro.f1)],
            ].map(([nombre, valor]) => (
              <div key={nombre} className="rounded-xl border border-slate-200 bg-white p-3">
                <dt className="text-xs text-slate-500">{nombre}</dt>
                <dd className="text-lg font-semibold">{valor}</dd>
              </div>
            ))}
          </dl>
          <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
            <table className="w-full text-center text-sm" data-prueba="matriz">
              <caption className="p-2 text-left text-sm font-medium">
                Matriz de confusión (filas: categoría esperada; columnas: la del sistema)
              </caption>
              <thead className="bg-slate-100 text-xs">
                <tr>
                  <th className="px-2 py-1 text-left">Esperada</th>
                  {CATEGORIAS.map((c) => (
                    <th key={c} className="px-2 py-1">{c}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {CATEGORIAS.map((fila) => (
                  <tr key={fila} className="border-t border-slate-100">
                    <th className="px-2 py-1 text-left font-medium">{fila}</th>
                    {CATEGORIAS.map((col) => {
                      const valor = datos.matriz_de_confusion[fila]?.[col] ?? 0;
                      const tono = fila === col && valor ? "bg-emerald-100" : valor ? "bg-rose-50" : "";
                      return (
                        <td key={col} className={`px-2 py-1 ${tono}`}>
                          {valor}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
            <table className="w-full text-sm">
              <thead className="bg-slate-100 text-xs">
                <tr>
                  <th className="px-3 py-1 text-left">Categoría</th>
                  <th className="px-3 py-1">Soporte</th>
                  <th className="px-3 py-1">Precisión</th>
                  <th className="px-3 py-1">Exhaustividad</th>
                  <th className="px-3 py-1">F1</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(datos.por_categoria).map(([categoria, m]) => (
                  <tr key={categoria} className="border-t border-slate-100 text-center">
                    <td className="px-3 py-1 text-left">{categoria}</td>
                    <td>{m.soporte}</td>
                    <td>{numero(m.precision)}</td>
                    <td>{numero(m.exhaustividad)}</td>
                    <td>{numero(m.f1)}</td>
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

  return (
    <div className="min-h-screen bg-slate-100 text-slate-900">
      <header className="flex flex-wrap items-center justify-between gap-3 bg-slate-800 px-6 py-4 text-white">
        <div>
          <h1 className="text-xl font-semibold">Consola del sistema multiagente de IA</h1>
          <p className="text-xs text-slate-300">Entorno simulado de pruebas, con datos sintéticos</p>
        </div>
        <div className="flex items-center gap-4 text-sm">
          <span data-prueba="salud">
            Servicio: {salud?.estado ?? "…"}
            {salud?.version ? ` · versión ${salud.version}` : ""}
          </span>
          <a href={LANGSMITH} target="_blank" rel="noreferrer" className="underline">
            Trazas en LangSmith
          </a>
        </div>
      </header>
      <main className="mx-auto max-w-6xl space-y-6 px-4 py-6">
        <div className="grid gap-4 rounded-xl border border-slate-200 bg-white p-4 md:grid-cols-2">
          <Token
            id="token-funcionario"
            etiqueta="Token de funcionario (bandeja)"
            valor={tokenFuncionario}
            alCambiar={(v) => {
              setTokenFuncionario(v);
              guardar("realtix-funcionario", v);
            }}
          />
          <Token
            id="token-admin"
            etiqueta="Token de administrador (métricas)"
            valor={tokenAdmin}
            alCambiar={(v) => {
              setTokenAdmin(v);
              guardar("realtix-admin", v);
            }}
          />
        </div>
        <nav className="flex gap-2">
          {[
            ["bandeja", "Bandeja"],
            ["metricas", "Métricas"],
          ].map(([clave, nombre]) => (
            <button
              key={clave}
              type="button"
              onClick={() => setVista(clave)}
              aria-pressed={vista === clave}
              className={`rounded-lg px-4 py-2 text-sm ${vista === clave ? "bg-emerald-700 text-white" : "bg-white"}`}
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
