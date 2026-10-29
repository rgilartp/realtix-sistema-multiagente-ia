"""Preguntas nuevas de la verificación de reglas por código, contra la API local en modo de
evaluación y sin juez (plan de Rodolfo). Escribe `preguntas_resultados.jsonl` y
`preguntas_resumen.md`. Se corre desde la raíz del repositorio (lee `.env` por la configuración),
con PostgreSQL y Chroma de Compose arriba:

    uv run python reports/verif-reglas-por-codigo/preguntas.py
"""

import json
import re
import sys
import unicodedata
import uuid
from contextlib import ExitStack
from decimal import Decimal
from pathlib import Path
from typing import Any

CARPETA = Path(__file__).resolve().parent
sys.path.insert(0, str(CARPETA.parents[1]))

import yaml  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from src.agents.graph import checkpointer_postgres, construir_grafo  # noqa: E402
from src.api.app import crear_app, servicios_desde_contenedor  # noqa: E402
from src.config import cargar_configuracion  # noqa: E402
from src.container import Contenedor  # noqa: E402
from src.evaluacion.corrida import costo_de  # noqa: E402
from src.evaluacion.escenarios import cargar_conjunto, normalizar_texto  # noqa: E402

MAYOR = re.compile(r"\b(?:mayor\s+a|supera|superior\s+a|mas\s+de)\s+391\s+uvt")
HASTA = re.compile(
    r"\b(?:hasta|no\s+supera|menor\s+o\s+igual\s+a|igual\s+o\s+menor\s+a)\s+391\s+uvt"
)
POR_ESTRATO = re.compile(
    r"\bpor\s+estratos?\b|\bsegun\s+(?:el|su)\s+estrato\b|\bdepende\s+del\s+estrato\b"
)


def normal(texto: str) -> str:
    sin = unicodedata.normalize("NFKD", texto.lower())
    return "".join(c for c in sin if not unicodedata.combining(c))


def verificar(p: dict[str, Any], texto: str, herramientas: list[dict[str, Any]]) -> dict[str, bool]:
    t = normal(texto)
    nombres = [h.get("herramienta") for h in herramientas]
    if p["tema"] == "periodicidad":
        reglas = [
            str((h.get("resultado") or {}).get("regla_de_la_periodicidad") or "")
            for h in herramientas
        ]
        regla = next((r for r in reglas if r), "")
        if p["periodicidad"] == "bimestral":
            copia = bool(MAYOR.search(t))
            invertida = bool(HASTA.search(t))
        else:
            copia = bool(HASTA.search(t)) or "declaracion anual unica" in t
            invertida = bool(MAYOR.search(t))
        return {
            "herramienta_trae_la_regla": bool(regla),
            "copia_la_regla": copia,
            "sin_inversion_391": not invertida,
        }
    oraciones = re.split(r"(?<=[.;!?])\s+|\n+", t)
    sin_estrato = not any(POR_ESTRATO.search(o) and "preferencial" not in o for o in oraciones)
    return {
        "llama_tarifas_predial": "tarifas_predial" in nombres,
        "sin_tarifa_por_estrato": sin_estrato,
    }


def main() -> int:
    plan = yaml.safe_load((CARPETA / "preguntas.yaml").read_text(encoding="utf-8"))
    escenarios = {
        normalizar_texto(t["usuario"])
        for e in cargar_conjunto(["principal", "R1", "R3", "R4"])
        for t in e["turnos"]
    }
    copiadas = [p["id"] for p in plan["preguntas"] if normalizar_texto(p["pregunta"]) in escenarios]
    if copiadas:
        raise SystemExit(f"Preguntas que copian un escenario: {copiadas}")
    settings = cargar_configuracion().model_copy(
        update={"modo_evaluacion": True, "ovt_simulada_activa": True}
    )
    filas = []
    with ExitStack() as pila:
        contenedor = Contenedor(settings)
        saver = pila.enter_context(checkpointer_postgres(settings.database_url.get_secret_value()))
        servicios = servicios_desde_contenedor(contenedor, construir_grafo(contenedor.deps, saver))
        cliente = pila.enter_context(TestClient(crear_app(servicios)))
        for p in plan["preguntas"]:
            cabeceras = {
                "X-Escenario-Id": f"REGLA-{p['id']:02d}",
                "X-Reloj-Simulado": f"{plan['dia']}T10:00:00-05:00",
            }
            if p.get("sesion"):
                r = cliente.post("/api/v1/ovt-simulada/sesion", json={"usuario": p["sesion"]})
                cabeceras["Authorization"] = f"Bearer {r.json()['token']}"
            r = cliente.post(
                "/api/v1/chat/mensaje",
                json={
                    "id_conversacion": f"regla-{uuid.uuid4().hex[:12]}",
                    "mensaje": p["pregunta"],
                },
                headers=cabeceras,
            )
            cuerpo = r.json()
            meta = cuerpo.get("meta") or {}
            herramientas = meta.get("herramientas") or []
            checks = verificar(p, cuerpo.get("respuesta", ""), herramientas)
            checks["en_horario"] = cuerpo.get("estado") != "fuera_de_horario"
            filas.append(
                {
                    **p,
                    "estado": cuerpo.get("estado"),
                    "herramientas": [h.get("herramienta") for h in herramientas],
                    "respuesta": cuerpo.get("respuesta", ""),
                    "verificaciones": checks,
                    "pasa": all(checks.values()),
                    "costo_usd": str(costo_de([meta.get("tokens_por_modelo") or {}])),
                }
            )
            print(p["id"], "pasa" if filas[-1]["pasa"] else f"FALLA {checks}")
    (CARPETA / "preguntas_resultados.jsonl").write_text(
        "".join(json.dumps(f, ensure_ascii=False) + "\n" for f in filas), encoding="utf-8"
    )
    pasan = sum(f["pasa"] for f in filas)
    costo = sum(Decimal(f["costo_usd"]) for f in filas)
    lineas = [
        "# Preguntas nuevas de la verificación de reglas por código",
        "",
        f"{pasan} de {len(filas)} pasan; costo US${costo:.4f}.",
        "",
        "| Pregunta | Tema | Sesión | Herramientas | Pasa | Verificaciones que fallan |",
        "|---|---|---|---|---|---|",
    ]
    for f in filas:
        fallan = ", ".join(k for k, v in f["verificaciones"].items() if not v) or "—"
        lineas.append(
            f"| {f['id']} | {f['tema']} | {f.get('sesion') or '—'} | "
            f"{', '.join(f['herramientas']) or '—'} | {'sí' if f['pasa'] else 'no'} | {fallan} |"
        )
    (CARPETA / "preguntas_resumen.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print(f"{pasan} de {len(filas)} pasan; costo US${costo:.4f}")
    return 0 if pasan == len(filas) else 1


if __name__ == "__main__":
    sys.exit(main())
