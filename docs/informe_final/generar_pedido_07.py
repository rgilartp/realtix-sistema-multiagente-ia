"""Genera los CSV del pedido 07 desde los archivos versionados, sin llamar a ninguna API.

Uso: uv run python docs/informe_final/generar_pedido_07.py

Lee `reports/corrida-3/` (calificados, resultados y RAGAS), `reports/calibracion/` y
`reports/corrida-2b/juez.jsonl`, `docs/usabilidad/` y `knowledge_base/`, y escribe los CSV en
`pedido_07/`. Queda fuera de esa carpeta porque lee las carpetas de usabilidad por el nombre de cada
autor, y los CSV los llaman A y B. Al final compara los totales con las cifras publicadas y falla
si alguno no coincide.
"""

import csv
import gzip
import json
import re
import sys
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path
from typing import Any

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

import yaml  # noqa: E402

from src.evaluacion.escenarios import cargar_conjunto  # noqa: E402
from src.integrations.costos import costo_usd  # noqa: E402
from src.integrations.segmentacion import segmentar_base  # noqa: E402

DESTINO = Path(__file__).resolve().parent / "pedido_07"
CORRIDA = RAIZ / "reports" / "corrida-3"
CONJUNTOS = ["principal", "R1", "R3", "R4"]
SONNET, HAIKU = "claude-sonnet-5-5", "claude-haiku-5-5"
METRICAS_RAGAS = ("context_precision", "context_recall", "faithfulness", "answer_relevancy")
# A y B son los mismos dos autores en calibracion.csv, heuristica.csv y usuarios.csv.
EVALUADORES = {"A": "rodolfo", "B": "dayanna"}
# Cómo se atendió cada problema (docs/reporte_de_pruebas.md, sección 8), por un patrón del texto.
CORRECCION = {
    r"modo oscuro": "PR #57",
    r"5 ?mb": "PR #60 (el widget y el backend reducen la imagen)",
    r"recortada": "PR #59 (el modelo decide primero si es un recibo)",
    r"ciiu": "En parte: PR #64 (entrada del glosario con su fuente); la indicación en el agente "
    "se revirtió en el PR #66 y queda como trabajo futuro",
}


def leer_jsonl(ruta: Path) -> list[dict[str, Any]]:
    abrir = gzip.open if ruta.suffix == ".gz" else open
    with abrir(ruta, "rt", encoding="utf-8") as f:
        return [json.loads(linea) for linea in f if linea.strip()]


def escribir(nombre: str, columnas: list[str], filas: list[dict[str, Any]]) -> None:
    with (DESTINO / nombre).open("w", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=columnas, lineterminator="\n")
        escritor.writeheader()
        escritor.writerows(filas)
    print(f"{nombre}: {len(filas)} filas")


def si_no(valor: bool) -> str:
    return "sí" if valor else "no"


def costo(tokens: dict[str, dict[str, int]]) -> Decimal:
    return sum(
        (costo_usd(m, t.get("entrada", 0), t.get("salida", 0)) for m, t in tokens.items()),
        Decimal(0),
    )


def escenarios_csv(escenarios: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    calificados = leer_jsonl(CORRIDA / "calificados.jsonl")
    resultados = {r["id_conversacion"]: r for r in leer_jsonl(CORRIDA / "resultados.jsonl.gz")}
    filas = []
    for c in calificados:
        turnos = c["turnos"]
        primero, ultimo = turnos[0]["estado"], turnos[-1]["estado"]
        crudo = resultados[c["id_conversacion"]]["turnos"]
        escalo = any(t["estado"] == "escalada" for t in crudo)
        assert escalo == any((t.get("meta") or {}).get("caso_id") for t in crudo)
        ts = c["tokens_sistema"]
        filas.append(
            {
                "conjunto": c["conjunto"],
                "escenario": c["escenario"],
                "ensayo": c["ensayo"],
                "grupo": c["grupo"],
                "categoria_esperada": c["categoria_esperada"],
                "categoria_obtenida": c["categoria"],
                "comportamiento_esperado": escenarios[c["escenario"]]["comportamiento_esperado"],
                "estado_obtenido": primero if primero == ultimo else f"{primero} → {ultimo}",
                "veredicto_juez": c["juez"]["veredicto"],
                "alucinacion": si_no(c["juez"]["alucinacion"]),
                "superado": si_no(c["superado"]),
                "latencia_servidor_ms": turnos[0]["latencia_servidor_ms"],
                "latencia_cliente_ms": turnos[0]["latencia_cliente_ms"],
                "turnos": len(turnos),
                "tokens_entrada_sonnet": ts.get(SONNET, {}).get("entrada", 0),
                "tokens_salida_sonnet": ts.get(SONNET, {}).get("salida", 0),
                "tokens_entrada_haiku": ts.get(HAIKU, {}).get("entrada", 0),
                "tokens_salida_haiku": ts.get(HAIKU, {}).get("salida", 0),
                "costo_usd": f"{costo(ts):.7f}",
                "escalo": si_no(escalo),
                "superado_estricto": si_no(c["superado_estricto"]),
                "costo_juez_usd": f"{costo(c['tokens_juez']):.7f}",
            }
        )
    assert all(set(c["tokens_sistema"]) <= {SONNET, HAIKU} for c in calificados)
    return filas


def ragas_csv(escenarios: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    vigentes = {c["id_conversacion"] for c in leer_jsonl(CORRIDA / "calificados.jsonl")}
    filas = leer_jsonl(CORRIDA / "ragas.jsonl")
    assert len({r["id_conversacion"] for r in filas}) == len(filas)
    assert all(r["id_conversacion"] in vigentes for r in filas)
    # Como `scripts/evaluar.py`: los promedios solo usan los casos con las cuatro métricas.
    return [
        {
            "escenario": r["escenario"],
            "ensayo": r["ensayo"],
            **{m: "" if r[m] is None else f"{r[m]:.4f}" for m in METRICAS_RAGAS},
            "con_sesion": si_no(bool(escenarios[r["escenario"]].get("sesion"))),
            "en_promedio": si_no(all(r[m] is not None for m in METRICAS_RAGAS)),
        }
        for r in filas
    ]


def calibracion_csv() -> list[dict[str, Any]]:
    carpeta = RAIZ / "reports" / "calibracion"
    clave = json.loads((carpeta / "clave.json").read_text(encoding="utf-8"))
    juez = {
        j["id_conversacion"]: j["veredicto"]
        for j in leer_jsonl(RAIZ / "reports/corrida-2b/juez.jsonl")
    }
    with (carpeta / "muestra.csv").open(encoding="utf-8") as f:
        muestra = list(csv.DictReader(f))
    filas = []
    for m in muestra:
        k = clave[m["muestra"]]
        j = juez[k["id_conversacion"]]
        fila = {
            "muestra": m["muestra"],
            "escenario": k["escenario"],
            "ensayo": k["ensayo"],
            "juez_veredicto": j["veredicto"],
            "juez_alucinacion": si_no(j["alucinacion"]),
        }
        for letra, nombre in EVALUADORES.items():
            fila[f"evaluador_{letra}_veredicto"] = m[f"{nombre}_veredicto"]
            fila[f"evaluador_{letra}_alucinacion"] = m[f"{nombre}_alucinacion"]
        fila["consenso_veredicto"] = m["consenso_veredicto"]
        fila["consenso_alucinacion"] = m["consenso_alucinacion"]
        filas.append(fila)
    return filas


def _tabla_markdown(texto: str, titulo: str) -> list[list[str]]:
    """Filas de la primera tabla después de `titulo`, sin el encabezado ni las vacías."""
    bloque = texto.split(titulo, 1)[1].split("\n## ", 1)[0]
    filas = []
    for linea in bloque.splitlines():
        if not linea.startswith("|") or re.match(r"^\|[\s|:-]+\|$", linea):
            continue
        celdas = [c.strip() for c in linea.strip().strip("|").split("|")]
        if celdas[0].startswith("N.º") or not any(celdas[1:]) or celdas[0].startswith("(Agrega"):
            continue
        filas.append(celdas)
    return filas


def heuristica_csv() -> list[dict[str, Any]]:
    filas = []
    for letra, nombre in EVALUADORES.items():
        texto = (RAIZ / "docs/usabilidad" / nombre / "heuristica.md").read_text(encoding="utf-8")
        for numero, tarea, donde, que, heuristica, gravedad in _tabla_markdown(
            texto, "## Problemas encontrados"
        ):
            pr = [v for k, v in CORRECCION.items() if re.search(k, que, re.IGNORECASE)]
            assert len(pr) == 1, que
            filas.append(
                {
                    "evaluador": letra,
                    "anotacion": numero,
                    "tarea": tarea,
                    "donde": donde,
                    "que_pasa": que,
                    "heuristica": heuristica,
                    "gravedad": gravedad,
                    "correccion": pr[0],
                }
            )
    return filas


def usuarios_csv() -> list[dict[str, Any]]:
    filas = []
    for letra, nombre in EVALUADORES.items():
        texto = (RAIZ / "docs/usabilidad" / nombre / "sus.md").read_text(encoding="utf-8")
        respuestas = {
            int(n): int(r)
            for n, _, r in (
                [c.strip() for c in linea.strip().strip("|").split("|")]
                for linea in texto.splitlines()
                if re.match(r"^\|\s*\d+\s*\|", linea)
            )
        }
        assert sorted(respuestas) == list(range(1, 11))
        suma = sum(r - 1 if n % 2 else 5 - r for n, r in respuestas.items())
        filas.append(
            {
                "evaluador": letra,
                **{f"p{n}": respuestas[n] for n in range(1, 11)},
                "puntaje_sus": f"{Decimal(suma) * Decimal('2.5'):.1f}",
                "tipo": "evaluación interna de los autores (ADR-21), sin usuarios externos",
            }
        )
    return filas


def base_conocimiento_csv() -> list[dict[str, Any]]:
    raiz = RAIZ / "knowledge_base"
    por_archivo = Counter(
        f.metadatos["archivo"] for fragmentos in segmentar_base(raiz).values() for f in fragmentos
    )
    filas = []
    for indice in sorted(raiz.glob("*/fuentes.yaml")):
        coleccion = indice.parent.name
        for fuente in yaml.safe_load(indice.read_text(encoding="utf-8"))["fuentes"]:
            url = fuente.get("url") or ""
            filas.append(
                {
                    "archivo": fuente["archivo"],
                    "coleccion": coleccion,
                    "norma": fuente["norma"],
                    "url": " ; ".join(url) if isinstance(url, list) else url,
                    "mes_consulta": fuente.get("mes_consulta", ""),
                    "origen": " ".join(str(fuente.get("origen") or "").split()),
                    "fragmentos": por_archivo[f"{coleccion}/{fuente['archivo']}"],
                }
            )
    sin_fuente = set(por_archivo) - {f"{f['coleccion']}/{f['archivo']}" for f in filas}
    assert not sin_fuente, sin_fuente
    return filas


def verificar(esc, rag, cal, heu, usu, base) -> None:
    """Los totales deben coincidir con las cifras publicadas en `reports/` y en el reporte."""
    metricas = json.loads((CORRIDA / "metricas.json").read_text(encoding="utf-8"))
    principal = [f for f in esc if f["conjunto"] == "principal"]
    tasa = sum(f["superado"] == "sí" for f in principal) / len(principal)
    assert abs(tasa - metricas["conjuntos"]["principal"]["tasa_meta"]["tasa"]) < 1e-9, tasa
    por_conjunto: dict[str, Decimal] = defaultdict(Decimal)
    for f in esc:
        por_conjunto[f"Sistema ({f['conjunto']})"] += Decimal(f["costo_usd"])
        por_conjunto[f"Juez ({f['conjunto']})"] += Decimal(f["costo_juez_usd"])
    for clave, valor in por_conjunto.items():
        assert valor == Decimal(metricas["costos"][clave]), (clave, valor)
    completos = [f for f in rag if f["en_promedio"] == "sí"]
    assert len(completos) == metricas["ragas"]["casos"]
    for m in METRICAS_RAGAS:
        promedio = sum(float(f[m]) for f in completos) / len(completos)
        assert abs(promedio - metricas["ragas"]["promedios"][m]) < 1e-3, m
    kappa = json.loads((RAIZ / "reports/calibracion/kappa.json").read_text(encoding="utf-8"))
    aprobada = {"correcta", "parcialmente correcta"}  # como `calibracion.aprobada`
    juez_ok = sum(f["juez_veredicto"] in aprobada and f["juez_alucinacion"] == "no" for f in cal)
    assert len(cal) == kappa["muestra"] and juez_ok == kappa["aprobadas_por_el_juez"]
    assert len(heu) == 6 and [f["puntaje_sus"] for f in usu] == ["80.0", "97.5"]
    conteo = Counter()
    for f in base:
        conteo[f["coleccion"]] += f["fragmentos"]
    esperado = {"normativa_datos": 73, "normativa_ica": 562, "normativa_ipu": 491}
    assert conteo == esperado | {"plataforma_general": 23}, conteo
    print("Totales verificados contra metricas.json, kappa.json, el SUS y volumenes.json.")


def main() -> None:
    escenarios = {e["id"]: e for e in cargar_conjunto(CONJUNTOS)}
    esc = escenarios_csv(escenarios)
    escribir("escenarios.csv", list(esc[0]), esc)
    rag = ragas_csv(escenarios)
    escribir("ragas.csv", list(rag[0]), rag)
    cal = calibracion_csv()
    escribir("calibracion.csv", list(cal[0]), cal)
    heu = heuristica_csv()
    escribir("heuristica.csv", list(heu[0]), heu)
    usu = usuarios_csv()
    escribir("usuarios.csv", list(usu[0]), usu)
    base = base_conocimiento_csv()
    escribir("base_conocimiento.csv", list(base[0]), base)
    verificar(esc, rag, cal, heu, usu, base)


if __name__ == "__main__":
    main()
