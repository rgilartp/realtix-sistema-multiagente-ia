"""Corre y califica una corrida de evaluación (B12; secciones 6.4, 6.5 y 6.10). Gasta tokens.

Ejemplos:
  # Mini corrida contra la API local (PostgreSQL y Chroma arriba con Compose):
  uv run python scripts/evaluar.py --corrida mini-corrida --local \\
      --escenarios AMB-02,OCR-01,ROB-01,IPU-04,GEN-02
  # Corrida 1 contra el despliegue, con los componentes y los conjuntos R3 y R4:
  uv run python scripts/evaluar.py --corrida corrida-1 --api https://<subdominio>.duckdns.org \\
      --conjuntos principal,R3,R4 --componentes
  # Corrida 3: 3 ensayos, R1, RAGAS, trazas y el juez congelado (A5):
  uv run python scripts/evaluar.py --corrida corrida-3 --api https://… --k 3 \\
      --conjuntos principal,R1,R3,R4 --componentes --ragas --trazas --exigir-huella
  # Solo recalcular los reportes con lo ya guardado (sin llamar a ningún modelo):
  uv run python scripts/evaluar.py --corrida corrida-1 --solo-reporte

Todo queda en `reports/<corrida>/`. Los ensayos y las calificaciones del juez se guardan a medida
que llegan; volver a correr el mismo comando reanuda sin pagar dos veces. `--tope-usd` detiene la
corrida si el gasto en Anthropic (sistema, juez y componentes, contando lo ya guardado) lo supera.
El modo de evaluación debe estar encendido en el servidor solo durante la corrida (A9); el script
se detiene si la API no lo tiene.
"""

import argparse
import json
import sys
from contextlib import ExitStack
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import cargar_configuracion  # noqa: E402
from src.evaluacion.corrida import (  # noqa: E402
    calificar,
    costo_de,
    metricas_por_conjunto,
)
from src.evaluacion.ejecutor import Ejecutor, leer_resultados  # noqa: E402
from src.evaluacion.escenarios import cargar_conjunto  # noqa: E402
from src.evaluacion.juez import Juez, huella_del_juez  # noqa: E402
from src.evaluacion.reportes import guardar_reportes  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
CONJUNTOS = ("principal", "R1", "R3", "R4")


class ModoEvaluacionApagado(SystemExit):
    pass


class Gasto:
    """Gasto en Anthropic de la corrida (sistema y juez), contado desde lo ya guardado: una corrida
    reanudada no reinicia la cuenta. `--tope-usd` la detiene al superarlo."""

    def __init__(self, destino: Path, tope: float | None) -> None:
        self.tope = Decimal(str(tope)) if tope else None
        self.usd = Decimal(0)
        for e in leer_resultados(destino / "resultados.jsonl"):
            self.usd += costo_de(
                (t.get("meta") or {}).get("tokens_por_modelo") or {} for t in e["turnos"]
            )
        for archivo in (
            "juez.jsonl",
            "componentes_juez.jsonl",
            "componentes_enrutamiento.jsonl",
            "componentes_agentes.jsonl",
        ):
            for fila in leer_resultados(destino / archivo):
                self.usd += costo_de([fila.get("tokens_por_modelo") or {}])

    def sumar(self, tokens_por_modelo: dict[str, dict[str, int]]) -> None:
        self.usd += costo_de([tokens_por_modelo])
        if self.tope and self.usd > self.tope:
            raise SystemExit(f"Se superó el tope de US${self.tope} (lleva US${self.usd:.4f}).")


def _jsonl(ruta: Path, filas: list[dict[str, Any]]) -> None:
    ruta.write_text(
        "".join(json.dumps(f, ensure_ascii=False) + "\n" for f in filas), encoding="utf-8"
    )


def _agregar(ruta: Path, fila: dict[str, Any]) -> None:
    with ruta.open("a", encoding="utf-8") as f:
        f.write(json.dumps(fila, ensure_ascii=False) + "\n")


def correr_ensayos(
    args: argparse.Namespace, escenarios: list[dict[str, Any]], destino: Path, gasto: Gasto
) -> None:
    settings = cargar_configuracion()
    por_id = {e["id"]: e for e in escenarios}

    def avance(ensayo: dict[str, Any]) -> None:
        turnos = ensayo["turnos"]
        con_grafo = [t for t in turnos if sum(((t.get("meta") or {}).get("tokens") or {}).values())]
        if con_grafo and not any(t["meta"].get("tokens_por_modelo") for t in con_grafo):
            raise ModoEvaluacionApagado(
                "La API no está en el modo de evaluación (MODO_EVALUACION=true); corrida detenida."
            )
        estados = ", ".join(str(t.get("estado")) for t in turnos)
        error = ensayo["error"] or ""
        print(f"{ensayo['escenario']:<8} ensayo {ensayo['ensayo']}  {estados}  {error}")
        motivos = {(t.get("meta") or {}).get("motivo_escalamiento") for t in turnos}
        if (
            por_id[ensayo["escenario"]].get("falla_inyectada")
            and "fallo de servicio" not in motivos
        ):
            print("  Aviso: no hubo «fallo de servicio»; ¿FALLAS_INYECTABLES está encendida?")
        for t in turnos:
            gasto.sumar((t.get("meta") or {}).get("tokens_por_modelo") or {})

    with ExitStack() as pila:
        if args.local:
            from fastapi.testclient import TestClient

            from src.agents.graph import checkpointer_postgres, construir_grafo
            from src.api.app import crear_app, servicios_desde_contenedor
            from src.container import Contenedor

            settings = settings.model_copy(
                update={
                    "modo_evaluacion": True,
                    "fallas_inyectables": True,
                    "ovt_simulada_activa": True,
                }
            )
            contenedor = Contenedor(settings)
            saver = pila.enter_context(
                checkpointer_postgres(settings.database_url.get_secret_value())
            )
            servicios = servicios_desde_contenedor(
                contenedor, construir_grafo(contenedor.deps, saver)
            )
            cliente = pila.enter_context(TestClient(crear_app(servicios)))
        else:
            import httpx

            cliente = pila.enter_context(httpx.Client(base_url=args.api, timeout=90))
        Ejecutor(cliente, args.corrida).correr(
            escenarios, args.k, destino / "resultados.jsonl", avance
        )


def correr_componentes(
    destino: Path,
    escenarios: list[dict[str, Any]],
    juez: Juez | None,
    huella: str,
    gasto: Gasto,
    evaluar: bool,
) -> dict[str, Any]:
    """Enrutamiento y agentes; cada resultado se guarda al llegar y se reanuda por id. Sin
    `evaluar` (`--solo-reporte`) no llama a ningún modelo: usa lo guardado."""
    from src.evaluacion.componentes import (
        clasificar_consultas,
        como_ensayo,
        correr_agente,
        escenarios_de_agente,
        metricas_de_enrutamiento,
    )
    from src.evaluacion.escenarios import cargar_enrutamiento

    ruta = destino / "componentes_enrutamiento.jsonl"
    ruta_agentes = destino / "componentes_agentes.jsonl"
    hechas = {f["id"] for f in leer_resultados(ruta)}
    propios = escenarios_de_agente([e for e in escenarios if e["grupo"] in _GRUPOS_PRINCIPALES])
    corridos = {a["escenario"] for a in leer_resultados(ruta_agentes)}
    if evaluar:
        from src.container import Contenedor

        deps = Contenedor().deps

        def guardar_consulta(fila: dict[str, Any]) -> None:
            _agregar(ruta, fila)
            gasto.sumar(fila["tokens_por_modelo"])
            print(f"{fila['id']:<11} {fila['esperada']:<17} {fila['predicha']}")

        pendientes = [c for c in cargar_enrutamiento() if c["id"] not in hechas]
        clasificar_consultas(deps, pendientes, guardar_consulta)
        for esc in (e for e in propios if e["id"] not in corridos):
            resultado = correr_agente(deps, esc)
            _agregar(ruta_agentes, resultado)
            gasto.sumar(resultado["tokens_por_modelo"])
    enrutamiento = leer_resultados(ruta)
    agentes = leer_resultados(ruta_agentes)
    por_id = {e["id"]: e for e in propios}
    ensayos = [
        como_ensayo(a, por_id[a["escenario"]])
        | {"id_conversacion": f"componentes-{a['escenario']}"}
        for a in agentes
    ]
    calificados = calificar(
        por_id,
        ensayos,
        juez,
        destino / "componentes_juez.jsonl",
        huella=huella,
        al_juzgar=lambda r: gasto.sumar(r["tokens_por_modelo"]),
    )
    superados = [
        c
        for c in calificados
        if c["juez"] and c["juez"]["veredicto"] != "incorrecta" and not c["juez"]["alucinacion"]
    ]
    return {
        "enrutamiento": metricas_de_enrutamiento(enrutamiento) if enrutamiento else None,
        "agentes": {
            "escenarios": len(calificados),
            "superados": len(superados),
            "tasa": len(superados) / len(calificados) if calificados else None,
        },
        "costo_usd": {
            "enrutamiento": str(costo_de(f["tokens_por_modelo"] for f in enrutamiento)),
            "agentes": str(costo_de(a["tokens_por_modelo"] for a in agentes)),
            "juez": str(costo_de(c["tokens_juez"] for c in calificados)),
        },
    }


_GRUPOS_PRINCIPALES = frozenset(
    {"aviso_ia", "acceso", "ipu", "ica", "general", "ocr", "fuera_de_alcance", "multiagente",
     "escalamiento", "ambiguas_varios_turnos", "horario", "robustez"}
)  # fmt: skip


def correr_ragas(
    destino: Path, escenarios: dict[str, dict[str, Any]], limite: int | None, evaluar: bool
) -> dict[str, Any]:
    """RAGAS de los ensayos de un turno con fragmentos; cada caso se guarda al llegar, con su
    `id_conversacion` (un ensayo repetido se vuelve a evaluar) y su costo."""
    from src.evaluacion.corrida import vigentes
    from src.evaluacion.ragas_eval import (
        METRICAS,
        MODELO_EVALUADOR,
        EvaluadorRagas,
        caso_del_ensayo,
    )

    ruta = destino / "ragas.jsonl"
    ruta_costo = destino / "ragas_costo.json"
    ensayos = [
        e
        for e in vigentes(leer_resultados(destino / "resultados.jsonl"))
        if escenarios[e["escenario"]]["grupo"] in _GRUPOS_PRINCIPALES
    ]
    vigentes_ids = {e["id_conversacion"] for e in ensayos}
    # Un caso con alguna métrica vacía (falló al calcularse) se vuelve a evaluar.
    hechos = {
        r["id_conversacion"]: r
        for r in leer_resultados(ruta)
        if r.get("id_conversacion") in vigentes_ids and all(r.get(m) is not None for m in METRICAS)
    }
    casos = [(e, c) for e in ensayos if (c := caso_del_ensayo(escenarios[e["escenario"]], e))]
    if limite:
        casos = casos[:limite]
    pendientes = [(e, c) for e, c in casos if e["id_conversacion"] not in hechos]
    if pendientes and evaluar:
        evaluador = EvaluadorRagas(cargar_configuracion())
        previo = (
            Decimal(json.loads(ruta_costo.read_text())["usd"])
            if ruta_costo.exists()
            else Decimal(0)
        )

        def guardar(i: int, puntajes: dict[str, float | None]) -> None:
            e = pendientes[i][0]
            fila = {
                "escenario": e["escenario"],
                "ensayo": e["ensayo"],
                "id_conversacion": e["id_conversacion"],
                **puntajes,
            }
            hechos[e["id_conversacion"]] = fila
            _agregar(ruta, fila)
            total = previo + evaluador.consumo.costo_usd()
            ruta_costo.write_text(json.dumps({"usd": str(total)}) + "\n", encoding="utf-8")

        evaluador.evaluar_varios([c for _, c in pendientes], guardar)
        print(f"RAGAS: {len(pendientes)} casos, US${evaluador.consumo.costo_usd():.4f}")
    filas = list(hechos.values())
    promedios = {}
    for m in METRICAS:
        valores = [f[m] for f in filas if f.get(m) is not None]
        promedios[m] = sum(valores) / len(valores) if valores else None
    costo = json.loads(ruta_costo.read_text())["usd"] if ruta_costo.exists() else "0"
    return {
        "casos": len(filas),
        "modelo": MODELO_EVALUADOR,
        "promedios": promedios,
        "costo_usd": costo,
    }


def revisar_trazas(corrida: str, horas: int) -> dict[str, Any]:
    from src.evaluacion.trazas_eval import ejecuciones_de_langsmith, revisar_ejecuciones

    ejecuciones = list(
        ejecuciones_de_langsmith(cargar_configuracion(), datetime.now(UTC) - timedelta(hours=horas))
    )
    trazas = {
        e.trace_id
        for e in ejecuciones
        if str(((e.extra or {}).get("metadata") or {}).get("id_conversacion", "")).startswith(
            f"{corrida}-"
        )
    }
    return revisar_ejecuciones([e for e in ejecuciones if e.trace_id in trazas])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--corrida", required=True, help="carpeta en reports/ (p. ej. corrida-1)")
    destino_api = parser.add_mutually_exclusive_group()
    destino_api.add_argument("--api", help="URL de la API desplegada")
    destino_api.add_argument("--local", action="store_true", help="API local con TestClient")
    parser.add_argument("--escenarios", help="ID separados por comas (por defecto, todos)")
    parser.add_argument("--conjuntos", default="principal", help=f"de {', '.join(CONJUNTOS)}")
    parser.add_argument("--k", type=int, default=1, help="ensayos por escenario")
    parser.add_argument("--componentes", action="store_true")
    parser.add_argument("--ragas", action="store_true")
    parser.add_argument("--ragas-limite", type=int, help="solo los primeros N casos (prueba)")
    parser.add_argument("--trazas", action="store_true", help="revisar LangSmith (RNF-05)")
    parser.add_argument("--trazas-horas", type=int, default=24)
    parser.add_argument("--exigir-huella", action="store_true", help="juez igual al calibrado (A5)")
    parser.add_argument("--solo-reporte", action="store_true", help="no llama a ningún modelo")
    parser.add_argument("--tope-usd", type=float)
    parser.add_argument(
        "--sin-aprobar", action="store_true", help="permite referencias sin aprobar"
    )
    args = parser.parse_args()

    destino = RAIZ / "reports" / args.corrida
    destino.mkdir(parents=True, exist_ok=True)
    settings = cargar_configuracion()
    huella = huella_del_juez(settings)
    if args.exigir_huella:
        from src.evaluacion.calibracion import huella_guardada

        calibrada = huella_guardada(RAIZ / "reports" / "calibracion")
        if calibrada != huella:
            raise SystemExit("El juez cambió desde la calibración (A5): hay que repetirla.")
    conjuntos = [c.strip() for c in args.conjuntos.split(",") if c.strip()]
    escenarios = cargar_conjunto(conjuntos)
    if args.escenarios:
        pedidos = {i.strip() for i in args.escenarios.split(",")}
        escenarios = [e for e in escenarios if e["id"] in pedidos]
        if faltan := pedidos - {e["id"] for e in escenarios}:
            raise SystemExit(f"Escenarios desconocidos: {sorted(faltan)}")
    por_id = {e["id"]: e for e in cargar_conjunto(list(CONJUNTOS))}
    sin_aprobar = sorted(e["id"] for e in escenarios if not e.get("aprobado_por"))
    if sin_aprobar and not args.solo_reporte and not args.sin_aprobar:
        raise SystemExit(
            f"Referencias sin aprobar: {', '.join(sin_aprobar)}. Rodolfo las aprueba antes de la "
            "corrida (criterio de entrada); --sin-aprobar solo para pruebas."
        )

    gasto = Gasto(destino, args.tope_usd)
    print(f"Gasto ya registrado en esta corrida: US${gasto.usd:.4f}")
    if not args.solo_reporte:
        if not (args.api or args.local):
            raise SystemExit("Falta --api URL o --local.")
        correr_ensayos(args, escenarios, destino, gasto)
    juez = None if args.solo_reporte else Juez(settings)
    ensayos = [e for e in leer_resultados(destino / "resultados.jsonl") if e["escenario"] in por_id]
    calificados = calificar(
        por_id,
        ensayos,
        juez,
        destino / "juez.jsonl",
        huella=huella,
        al_juzgar=lambda r: gasto.sumar(r["tokens_por_modelo"]),
    )
    _jsonl(destino / "calificados.jsonl", calificados)

    datos: dict[str, Any] = {"huella_juez": huella, "conjuntos": metricas_por_conjunto(calificados)}
    componentes_guardados = (destino / "componentes_enrutamiento.jsonl").exists()
    if (args.componentes and not args.solo_reporte) or componentes_guardados:
        datos["componentes"] = correr_componentes(
            destino, list(por_id.values()), juez, huella, gasto, evaluar=not args.solo_reporte
        )
    if (args.ragas and not args.solo_reporte) or (destino / "ragas.jsonl").exists():
        evaluar = args.ragas and not args.solo_reporte
        datos["ragas"] = correr_ragas(destino, por_id, args.ragas_limite, evaluar)
    if args.trazas:
        datos["trazas"] = revisar_trazas(args.corrida, args.trazas_horas)
    costos = {}
    for nombre, m in datos["conjuntos"].items():
        costos[f"Sistema ({nombre})"] = m["costo_usd"]["sistema"]
        costos[f"Juez ({nombre})"] = m["costo_usd"]["juez"]
    for nombre, valor in (datos.get("componentes") or {}).get("costo_usd", {}).items():
        costos[f"Componentes: {nombre}"] = valor
    if datos.get("ragas"):
        costos["RAGAS (OpenAI)"] = datos["ragas"]["costo_usd"]
    costos["Total"] = str(sum(Decimal(v) for v in costos.values()))
    datos["costos"] = costos
    guardar_reportes(destino, args.corrida, datos, calificados)
    principal = datos["conjuntos"].get("principal") or {}
    if principal.get("ensayos"):
        t = principal["tasa_meta"]
        bajo, alto = t["wilson95"]
        estricta = principal["tasa_estricta"]["tasa"]
        print(f"Tasa de la meta: {t['tasa']:.3f} (Wilson {bajo:.3f} a {alto:.3f})")
        print(f"Tasa estricta: {estricta:.3f}")
    print(f"Costo total registrado: US${costos['Total']}")
    print(f"Gasto en Anthropic de esta corrida: US${gasto.usd:.4f}")
    print(f"Reportes en {destino}")


if __name__ == "__main__":
    main()
