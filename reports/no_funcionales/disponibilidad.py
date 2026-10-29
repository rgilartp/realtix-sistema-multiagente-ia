"""Disponibilidad (RNF-06 · Horario de atención) con el registro del monitor del servidor.

El monitor (crontab del servidor, cada 5 minutos) escribe en `~/monitor_salud/salud.log` una línea
por chequeo: hora UTC, código HTTP de `/health`, tiempo en ms y commit desplegado. Este script lo
convierte a `salud.log` sin fechas (sección 0.4): día relativo al primer chequeo, hora de
Colombia, si el chequeo cae en horario hábil (lunes a viernes no festivos, de 8:00 a 17:00),
código, ms y commit.
También acepta ese archivo ya convertido, para repetir el cálculo desde el repositorio.

La cifra oficial es la del horario hábil sobre todo el registro. Como contexto: sin las ventanas de
despliegue (los chequeos a menos de 10 minutos de un cambio de commit) y desde el primer commit que
incluye la corrección del PR #54. Escribe `disponibilidad.json` y `disponibilidad.md`.

    uv run python reports/no_funcionales/disponibilidad.py <salud.log del servidor o el convertido>
"""

import json
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import holidays

BOGOTA = ZoneInfo("America/Bogota")
CORRECCION_54 = "297c215"  # fusión del PR #54 (fuga de conexiones en /health)
VENTANA = timedelta(minutes=10)
META = 99.0
CARPETA = Path(__file__).resolve().parent


def habil(momento: datetime) -> bool:
    """Lunes a viernes no festivos en Colombia, de 8:00 a 17:00 (hora de Colombia)."""
    local = momento.astimezone(BOGOTA)
    festivos = holidays.Colombia(years=local.year)
    return local.weekday() < 5 and local.date() not in festivos and 8 <= local.hour < 17


def incluye_54(commit: str) -> bool:
    r = subprocess.run(["git", "merge-base", "--is-ancestor", CORRECCION_54, commit], check=False)
    return r.returncode == 0


def leer(ruta: Path) -> list[dict]:
    """Lee el registro del servidor o el convertido; `t` queda como tiempo relativo al inicio."""
    filas = []
    inicio = None
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        if not linea.strip() or linea.startswith("#"):
            continue
        partes = linea.split()
        if partes[0].startswith("dia"):
            dia, hora, es_habil, codigo, ms, commit = partes
            h, m = hora.split(":")
            t = timedelta(days=int(dia[3:]), hours=int(h), minutes=int(m))
            filas.append({"t": t, "habil": es_habil == "1", "codigo": int(codigo), "ms": int(ms),
                          "commit": commit})  # fmt: skip
            continue
        hora_utc, codigo, ms, commit = partes
        momento = datetime.fromisoformat(hora_utc.replace("Z", "+00:00")).astimezone(UTC)
        local = momento.astimezone(BOGOTA)
        if inicio is None:
            inicio = local.date()
        t = timedelta(days=(local.date() - inicio).days, hours=local.hour, minutes=local.minute)
        filas.append({"t": t, "habil": habil(momento), "codigo": int(codigo), "ms": int(ms),
                      "commit": commit})  # fmt: skip
    return filas


def convertido(filas: list[dict]) -> str:
    lineas = ["# dia hora_colombia habil codigo ms commit"]
    for f in filas:
        minutos = int(f["t"].total_seconds() // 60)
        dia, resto = divmod(minutos, 24 * 60)
        hora = f"{resto // 60:02d}:{resto % 60:02d}"
        lineas.append(f"dia{dia} {hora} {int(f['habil'])} {f['codigo']} {f['ms']} {f['commit']}")
    return "\n".join(lineas) + "\n"


def tasa(filas: list[dict]) -> dict:
    total = len(filas)
    ok = sum(f["codigo"] == 200 for f in filas)
    valor = round(100 * ok / total, 2) if total else None
    return {"chequeos": total, "con_200": ok, "disponibilidad": valor}


def calcular(filas: list[dict]) -> dict:
    cambios = [b["t"] for a, b in zip(filas, filas[1:], strict=False) if a["commit"] != b["commit"]]
    for f in filas:
        f["despliegue"] = any(abs(f["t"] - c) <= VENTANA for c in cambios)
    con_54 = {c for c in {f["commit"] for f in filas} if incluye_54(c)}
    habiles = [f for f in filas if f["habil"]]
    caidas = [f for f in filas if f["codigo"] != 200]
    primera_con_54 = next((f["t"] for f in filas if f["commit"] in con_54), None)
    antes_54 = None
    if primera_con_54 is not None:
        antes_54 = round((primera_con_54 - filas[0]["t"]).total_seconds() / 3600, 1)
    resultado = {
        "periodo_horas": round((filas[-1]["t"] - filas[0]["t"]).total_seconds() / 3600, 1),
        "chequeos": len(filas),
        "oficial_horario_habil": tasa(habiles),
        "total_todas_las_horas": tasa(filas),
        "habil_sin_ventanas_de_despliegue": tasa([f for f in habiles if not f["despliegue"]]),
        "habil_desde_la_correccion_del_pr_54": tasa([f for f in habiles if f["commit"] in con_54]),
        "horas_antes_de_la_correccion_del_pr_54": antes_54,
        "fallas": {
            "total": len(caidas),
            "codigos": sorted({f["codigo"] for f in caidas}),
            "commits": sorted({f["commit"] for f in caidas}),
            "en_horario_habil": sum(f["habil"] for f in caidas),
            "antes_de_la_correccion_del_pr_54": sum(f["commit"] not in con_54 for f in caidas),
            "en_ventana_de_despliegue": sum(f["despliegue"] for f in caidas),
        },
        "despliegues_marcados": len(cambios),
        "meta": META,
    }
    resultado["cumple_meta"] = resultado["oficial_horario_habil"]["disponibilidad"] >= META
    return resultado


def como_md(r: dict) -> str:
    def fila(nombre: str, x: dict) -> str:
        valor = f"{x['disponibilidad']:.2f}".replace(".", ",")
        return f"| {nombre} | {x['con_200']} de {x['chequeos']} | {valor} % |"

    fallas = r["fallas"]
    veredicto = "cumple" if r["cumple_meta"] else "**no cumple**"
    codigos = ", ".join(map(str, fallas["codigos"]))
    commits = ", ".join(f"`{c}`" for c in fallas["commits"])
    return "\n".join(
        [
            "# Disponibilidad (RNF-06 · Horario de atención)",
            "",
            "Generado por `disponibilidad.py` desde `salud.log` (monitor del servidor cada 5"
            " minutos; días relativos al primer chequeo, hora de Colombia). No se edita a mano.",
            "",
            f"Periodo: {str(r['periodo_horas']).replace('.', ',')} horas, {r['chequeos']} chequeos."
            f" Meta: {r['meta']:.0f} % en horario hábil; resultado: {veredicto}.",
            "",
            "| Medida | Chequeos con 200 | Disponibilidad |",
            "|---|---|---|",
            fila("**Oficial: horario hábil, todo el registro**", r["oficial_horario_habil"]),
            fila("Todas las horas", r["total_todas_las_horas"]),
            fila(
                "Horario hábil sin las ventanas de despliegue",
                r["habil_sin_ventanas_de_despliegue"],
            ),  # fmt: skip
            fila(
                "Horario hábil desde la corrección del PR #54",
                r["habil_desde_la_correccion_del_pr_54"],
            ),  # fmt: skip
            "",
            f"Fallas: {fallas['total']} (códigos {codigos}; commits {commits});"
            f" {fallas['en_horario_habil']} en horario hábil,"
            f" {fallas['antes_de_la_correccion_del_pr_54']} antes de la corrección del PR #54 y"
            f" {fallas['en_ventana_de_despliegue']} en una ventana de despliegue."
            f" Despliegues marcados: {r['despliegues_marcados']}.",
            "",
        ]
    )


def main() -> int:
    filas = leer(Path(sys.argv[1]))
    (CARPETA / "salud.log").write_text(convertido(filas), encoding="utf-8")
    resultado = calcular(filas)
    (CARPETA / "disponibilidad.json").write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (CARPETA / "disponibilidad.md").write_text(como_md(resultado), encoding="utf-8")
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
