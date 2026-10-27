"""Muestra de calibración del juez y su kappa (sección 6.4 y ADR-24: R2, A5 y A6).

- La muestra son 30 respuestas de la corrida 2, estratificadas por el veredicto del juez: la mitad
  aprobadas (correcta o parcial, sin alucinación) y la mitad no. Si un estrato tiene menos de 15, se
  toma completo y se completa con el otro. Ni el CSV ni la clave muestran el veredicto del juez: el
  kappa lo lee después de `juez.jsonl`.
- Cada evaluador califica por separado (veredicto de 3 niveles y si hubo alucinación); luego
  acuerdan el consenso. El kappa se calcula entre el juez y el consenso (binario y ponderado lineal
  de 3 niveles) y entre los dos evaluadores antes del consenso, con intervalos por bootstrap.
- Al exportar se guarda la huella del juez: desde la corrida 2 el juez queda congelado (A5).
"""

import csv
import json
import random
from pathlib import Path
from typing import Any

from src.evaluacion.ejecutor import leer_resultados
from src.evaluacion.juez import anonimizador_de_prueba
from src.evaluacion.metricas_eval import SEMILLA, VEREDICTOS, kappa_con_intervalo

TAMANO = 30
COLUMNAS_EVALUADORES = (
    "rodolfo_veredicto", "rodolfo_alucinacion",
    "dayanna_veredicto", "dayanna_alucinacion",
    "consenso_veredicto", "consenso_alucinacion",
)  # fmt: skip
SI = ("si", "sí", "s", "true", "1")


def aprobada(veredicto: str, alucinacion: bool) -> bool:
    return veredicto in ("correcta", "parcialmente correcta") and not alucinacion


def elegir(calificados: list[dict[str, Any]], tamano: int = TAMANO, semilla: int = SEMILLA):
    """Muestra estratificada por el veredicto del juez (de los 60 escenarios, con juez)."""
    candidatos = [c for c in calificados if c["conjunto"] == "principal" and c["juez"]]
    si = [c for c in candidatos if aprobada(c["juez"]["veredicto"], c["juez"]["alucinacion"])]
    no = [c for c in candidatos if c not in si]
    azar = random.Random(semilla)
    mitad = tamano // 2
    n_no = min(len(no), tamano - min(len(si), mitad))
    n_si = min(len(si), tamano - n_no)
    muestra = azar.sample(si, n_si) + azar.sample(no, n_no)
    azar.shuffle(muestra)  # el orden no delata el estrato
    return muestra


def exportar(
    muestra: list[dict[str, Any]],
    ensayos: dict[str, dict[str, Any]],
    escenarios: dict[str, dict[str, Any]],
    destino: Path,
    huella_juez: str,
) -> Path:
    """`muestra.csv` (sin el veredicto del juez), `clave.json` y `huella_juez.txt`."""
    destino.mkdir(parents=True, exist_ok=True)
    anonimizar = anonimizador_de_prueba()
    ruta = destino / "muestra.csv"
    clave = {}
    with ruta.open("w", newline="", encoding="utf-8") as archivo:
        escritor = csv.writer(archivo)
        escritor.writerow(
            ["muestra", "pregunta", "respuesta", "referencia", "fuentes", *COLUMNAS_EVALUADORES]
        )
        for i, c in enumerate(muestra, 1):
            ensayo = ensayos[c["id_conversacion"]]
            esc = escenarios[c["escenario"]]
            pregunta = " / ".join(t["usuario"] for t in ensayo["turnos"])
            respuesta = "\n---\n".join(t.get("respuesta") or "" for t in ensayo["turnos"])
            escritor.writerow(
                [
                    f"M{i:02d}",
                    anonimizar(pregunta),
                    anonimizar(respuesta),
                    str(esc["respuesta_referencia"]).strip(),
                    "; ".join(esc.get("fuentes_esperadas") or []),
                    *[""] * len(COLUMNAS_EVALUADORES),
                ]
            )
            clave[f"M{i:02d}"] = {
                "escenario": c["escenario"],
                "ensayo": c["ensayo"],
                "id_conversacion": c["id_conversacion"],
            }
    (destino / "clave.json").write_text(
        json.dumps(clave, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (destino / "huella_juez.txt").write_text(huella_juez + "\n", encoding="utf-8")
    return ruta


def huella_guardada(destino: Path) -> str | None:
    ruta = destino / "huella_juez.txt"
    return ruta.read_text(encoding="utf-8").strip() if ruta.exists() else None


def _veredicto(texto: str) -> str:
    v = " ".join(texto.strip().lower().split())
    if v in ("parcial", "parcialmente"):
        v = "parcialmente correcta"
    if v not in VEREDICTOS:
        raise ValueError(f"Veredicto desconocido en la muestra: «{texto}»")
    return v


def calcular_kappa(destino: Path, archivo_juez: Path) -> dict[str, Any]:
    """Kappa del juez frente al consenso y entre los evaluadores, con la muestra ya calificada."""
    clave = json.loads((destino / "clave.json").read_text(encoding="utf-8"))
    juez = {j["id_conversacion"]: j["veredicto"] for j in leer_resultados(archivo_juez)}
    with (destino / "muestra.csv").open(encoding="utf-8") as archivo:
        filas = list(csv.DictReader(archivo))
    pendientes = [
        f["muestra"] for f in filas if not all(f[c].strip() for c in COLUMNAS_EVALUADORES)
    ]
    if pendientes:
        raise ValueError(f"Faltan calificaciones en: {', '.join(pendientes)}")

    def de(persona: str, f: dict[str, str]) -> tuple[str, bool]:
        return _veredicto(f[f"{persona}_veredicto"]), f[
            f"{persona}_alucinacion"
        ].strip().lower() in SI

    calif = {p: [de(p, f) for f in filas] for p in ("rodolfo", "dayanna", "consenso")}
    del_juez = [juez[clave[f["muestra"]]["id_conversacion"]] for f in filas]
    calif["juez"] = [(j["veredicto"], j["alucinacion"]) for j in del_juez]

    def comparar(a: str, b: str) -> dict[str, Any]:
        binario_a = [aprobada(*x) for x in calif[a]]
        binario_b = [aprobada(*x) for x in calif[b]]
        return {
            "binario": kappa_con_intervalo(binario_a, binario_b),
            "ponderado_3_niveles": kappa_con_intervalo(
                [v for v, _ in calif[a]], [v for v, _ in calif[b]], VEREDICTOS
            ),
        }

    return {
        "muestra": len(filas),
        "juez_frente_al_consenso": comparar("juez", "consenso"),
        "entre_evaluadores": comparar("rodolfo", "dayanna"),
        "aprobadas_por_el_juez": sum(aprobada(*x) for x in calif["juez"]),
    }
