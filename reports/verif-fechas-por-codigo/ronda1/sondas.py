"""Sondas de fechas por código (plan de Rodolfo), contra la API local en modo de evaluación.

Corre cada combinación de `sondas.yaml` 2 veces con el reloj simulado a las 10:00 a. m. del día,
y verifica por código, sin juez, cada respuesta: la fecha exacta, ninguna expresión relativa a hoy,
«ya venció» en la oración de la fecha solo si el reloj está después, ninguna fecha igual o posterior
a hoy dada como vencida y, si se pregunta si ya venció, que la respuesta lo diga. Escribe
`resultados.jsonl` y `resumen.md` en esta carpeta. Se corre desde la raíz del repositorio (lee
`.env` por la configuración), con PostgreSQL y Chroma de Compose arriba:

    uv run python reports/verif-fechas-por-codigo/sondas.py
"""

import json
import re
import sys
import unicodedata
import uuid
from contextlib import ExitStack
from datetime import date
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
from src.services.expresiones_relativas import expresiones_relativas  # noqa: E402

REPETICIONES = 2
MESES = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre",
         "octubre", "noviembre", "diciembre")  # fmt: skip
FECHA = re.compile(rf"\b(\d{{1,2}})\s+de\s+({'|'.join(MESES)})(?:\s+de\s+(\d{{4}}))?")
_N = r"(?:\d+|un|una|uno|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|quince|veinte|treinta)"
# Además de las del verificador del sistema, las que prohíbe la regla del prompt.
OTRAS_RELATIVAS = re.compile(
    rf"\ben\s+{_N}\s+dias?\b(?!\s+habiles)|\b(?:la\s+)?proxima\s+semana\b|\bla\s+semana\s+pasada\b"
    r"|\bel\s+proximo\s+mes\b|\bel\s+mes\s+pasado\b"
)
VENCIO = re.compile(
    r"\bya\s+(?:se\s+)?(?:vencio|paso|expiro|termino|caduco)\b|\b(?:vencio|expiro)\b"
    r"|\bya\s+no\s+(?:esta|estan)\s+(?:disponibles?|vigentes?)\b"
    r"|\b(?:esta|estan|quedo|quedaron)\s+vencid[oa]s?\b|\bya\s+no\s+(?:alcanzas|puedes)\b"
)
NO_VENCIO = re.compile(
    r"\b(?:aun|todavia)\s+no\s+(?:vence|se\s+(?:te\s+)?vence|ha\s+vencido|ha\s+pasado)\b"
    r"|\bno\s+se\s+(?:te\s+|le\s+)?ha\s+vencido\b|\bno\s+ha\s+(?:vencido|pasado)\b"
    r"|\b(?:aun|todavia)\s+(?:estas\s+a\s+tiempo|puedes|alcanzas|esta\s+vigente|tienes\s+tiempo"
    r"|esta\s+disponible)\b|\b(?:sigue|esta)\s+(?:vigente|disponible)\b|\bvence\s+hoy\b"
    r"|\bno\s+esta\s+vencid[oa]\b|\bno\s+(?:esta|estas)\s+en\s+mora\b|\bal\s+dia\b|\ba\s+tiempo\b"
)
NEGACION = re.compile(r"\b(?:no|aun\s+no|todavia\s+no)\s+(?:\w+\s+)?$")


def normal(texto: str) -> str:
    sin_tildes = unicodedata.normalize("NFKD", texto.lower())
    return "".join(c for c in sin_tildes if not unicodedata.combining(c))


# Una oración que retoma la anterior («Ese plazo ya venció.») cuenta como parte de ella.
RETOMA = re.compile(r"^(?:ese|esa|esos|esas|este|esta|dicho|dicha|ya|el cual|la cual|pero)\b")


def oraciones(texto: str) -> list[str]:
    """Las oraciones del texto; la que retoma la anterior se une a ella."""
    salida: list[str] = []
    for o in (o.strip() for o in re.split(r"(?<=[.;!?])\s+|\n+", normal(texto))):
        if not o:
            continue
        if salida and RETOMA.match(o):
            salida[-1] += " " + o
        else:
            salida.append(o)
    return salida


def vencio_afirmativo(oracion: str) -> bool:
    """«ya venció» o equivalente, sin una negación justo antes («no está vencido»)."""
    return any(not NEGACION.search(oracion[: m.start()][-25:]) for m in VENCIO.finditer(oracion))


def fechas_de(oracion: str, anio_por_defecto: int) -> list[tuple[date, bool]]:
    salida = []
    for m in FECHA.finditer(oracion):
        anio = int(m.group(3)) if m.group(3) else anio_por_defecto
        salida.append((date(anio, MESES.index(m.group(2)) + 1, int(m.group(1))), bool(m.group(3))))
    return salida


def verificar(texto: str, caso: dict[str, Any]) -> dict[str, bool]:
    hoy = date.fromisoformat(caso["dia"])
    esperada = date.fromisoformat(caso["fecha"])
    partes = oraciones(texto)
    con_la_fecha = [
        o
        for o in partes
        if any(
            f == esperada and (con_anio or not caso.get("exigir_anio"))
            for f, con_anio in fechas_de(o, hoy.year)
        )
    ]
    ya_paso = esperada < hoy
    if ya_paso and caso.get("vencida") is not False:
        oracion_ok = any(vencio_afirmativo(o) for o in con_la_fecha)
    elif not ya_paso:
        oracion_ok = not any(vencio_afirmativo(o) for o in con_la_fecha)
    else:
        oracion_ok = True
    futuras_ok = not any(
        vencio_afirmativo(o) for o in partes if any(f >= hoy for f, _ in fechas_de(o, hoy.year))
    )
    todo = normal(texto)
    if caso.get("vencida") is True:
        dice_si_vencio = vencio_afirmativo(todo)
    elif caso.get("vencida") is False:
        dice_si_vencio = bool(NO_VENCIO.search(todo))
    else:
        dice_si_vencio = True
    return {
        "fecha_exacta": bool(con_la_fecha),
        "sin_relativas": not expresiones_relativas(texto) and not OTRAS_RELATIVAS.search(todo),
        "vencio_en_la_oracion": oracion_ok,
        "ninguna_futura_vencida": futuras_ok,
        "dice_si_vencio": dice_si_vencio,
    }


def main() -> int:
    sondas = yaml.safe_load((CARPETA / "sondas.yaml").read_text(encoding="utf-8"))["sondas"]
    settings = cargar_configuracion().model_copy(
        update={"modo_evaluacion": True, "ovt_simulada_activa": True}
    )
    filas: list[dict[str, Any]] = []
    with ExitStack() as pila:
        contenedor = Contenedor(settings)
        saver = pila.enter_context(checkpointer_postgres(settings.database_url.get_secret_value()))
        servicios = servicios_desde_contenedor(contenedor, construir_grafo(contenedor.deps, saver))
        cliente = pila.enter_context(TestClient(crear_app(servicios)))
        n = 0
        for sonda in sondas:
            for caso in sonda["casos"]:
                n += 1
                sesion = caso.get("sesion", sonda.get("sesion"))
                for repeticion in range(1, REPETICIONES + 1):
                    cabeceras = {
                        "X-Escenario-Id": f"SONDA-{n:02d}",
                        "X-Reloj-Simulado": f"{caso['dia']}T10:00:00-05:00",
                    }
                    if sesion:
                        r = cliente.post("/api/v1/ovt-simulada/sesion", json={"usuario": sesion})
                        cabeceras["Authorization"] = f"Bearer {r.json()['token']}"
                    r = cliente.post(
                        "/api/v1/chat/mensaje",
                        json={
                            "id_conversacion": f"sonda-fechas-{uuid.uuid4().hex[:12]}",
                            "mensaje": sonda["pregunta"],
                        },
                        headers=cabeceras,
                    )
                    cuerpo = r.json()
                    meta = cuerpo.get("meta") or {}
                    texto = cuerpo.get("respuesta", "")
                    checks = verificar(texto, caso)
                    checks["http_200"] = r.status_code == 200
                    checks["en_horario"] = cuerpo.get("estado") != "fuera_de_horario"
                    fila = {
                        "sonda": n,
                        "repeticion": repeticion,
                        "pregunta": sonda["pregunta"],
                        "sesion": sesion,
                        **caso,
                        "estado": cuerpo.get("estado"),
                        "herramientas": [
                            h.get("herramienta") for h in meta.get("herramientas") or []
                        ],
                        "reescrituras": meta.get("reescrituras"),
                        "respuesta": texto,
                        "verificaciones": checks,
                        "pasa": all(checks.values()),
                        "costo_usd": str(costo_de([meta.get("tokens_por_modelo") or {}])),
                    }
                    filas.append(fila)
                    print(f"{n:02d}.{repeticion} {caso['dia']} {sesion or '-':4} "
                          f"{'pasa' if fila['pasa'] else 'FALLA ' + str(checks)}")  # fmt: skip
    (CARPETA / "resultados.jsonl").write_text(
        "".join(json.dumps(f, ensure_ascii=False) + "\n" for f in filas), encoding="utf-8"
    )
    costo = sum(Decimal(f["costo_usd"]) for f in filas)
    pasan = sum(f["pasa"] for f in filas)
    lineas = [
        "# Sondas de fechas por código",
        "",
        f"{pasan} de {len(filas)} respuestas pasan todas las verificaciones; costo US${costo:.4f}.",
        "",
        "| Sonda | Rep. | Día | Sesión | Fecha esperada | Pasa | Verificaciones que fallan |",
        "|---|---|---|---|---|---|---|",
    ]
    for f in filas:
        fallan = ", ".join(k for k, v in f["verificaciones"].items() if not v) or "—"
        lineas.append(
            f"| {f['sonda']:02d} | {f['repeticion']} | {f['dia']} | {f['sesion'] or '—'} | "
            f"{f['fecha']} | {'sí' if f['pasa'] else 'no'} | {fallan} |"
        )
    (CARPETA / "resumen.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print(f"{pasan} de {len(filas)} pasan; costo US${costo:.4f}")
    return 0 if pasan == len(filas) else 1


if __name__ == "__main__":
    sys.exit(main())
