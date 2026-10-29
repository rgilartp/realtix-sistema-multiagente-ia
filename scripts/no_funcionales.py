"""Pruebas no funcionales contra la API desplegada (B15; sección 6.7). Gasta pocos tokens.

Las que dependen del modo de evaluación (cabeceras `X-Reloj-Simulado` y `X-Falla-Inyectada`) se
corren mientras está encendido, en la ventana de la corrida 2:

  # RNF-08 · Tiempos de espera y degradación: una falla de cada servicio, por tiempo y por error.
  uv run python scripts/no_funcionales.py fallas --api https://<subdominio>.duckdns.org
  # RNF-02 · Escalamiento horizontal: un turno, se apaga la réplica que lo atendió, otro turno.
  uv run python scripts/no_funcionales.py turno --api … --conversacion NF-replicas --paso 1
  uv run python scripts/no_funcionales.py turno --api … --conversacion NF-replicas --paso 2

Cada resultado queda en `reports/no_funcionales/` (JSON), sin datos personales: los usuarios son
sintéticos y no se guarda el texto de la respuesta, solo su estado y si delata un error técnico.
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.evaluacion.escenarios import DIR_ESCENARIOS, RAIZ  # noqa: E402
from src.evaluacion.evaluadores_codigo import ERROR_TECNICO  # noqa: E402

DESTINO = RAIZ / "reports" / "no_funcionales"
SERVICIOS = ("orquestador", "modelo", "recuperacion", "adaptador")
GENERAL = "¿Qué es el impuesto predial unificado y quién lo administra?"
PERSONAL = "¿Cuánto debo del predial de mi predio?"
SEGUIMIENTO = "¿Y qué pasa si lo pago tarde?"  # depende del turno anterior (contexto)


def reloj_habil() -> str:
    """El reloj de los escenarios (fecha de referencia del conjunto, día hábil a las 10:00)."""
    return str(
        yaml.safe_load((DIR_ESCENARIOS / "ROB-01.yaml").read_text(encoding="utf-8"))["reloj"]
    )


def _cliente(api: str) -> Any:
    import httpx

    return httpx.Client(base_url=api, timeout=90)


def _sesion(cliente: Any, usuario: str) -> dict[str, str]:
    r = cliente.post("/api/v1/ovt-simulada/sesion", json={"usuario": usuario})
    r.raise_for_status()
    return {"Authorization": f"Bearer {r.json()['token']}"}


def _turno(cliente: Any, conversacion: str, mensaje: str, cabeceras: dict[str, str]) -> dict:
    inicio = time.perf_counter()
    r = cliente.post(
        "/api/v1/chat/mensaje",
        headers=cabeceras,
        json={"id_conversacion": conversacion, "mensaje": mensaje},
    )
    try:
        datos = r.json() if r.status_code < 500 else {}
    except ValueError:  # una respuesta que no es JSON cuenta como fallida, sin romper el guion
        datos = {}
    meta = datos.get("meta") or {}
    return {
        "codigo_http": r.status_code,
        "estado": datos.get("estado"),
        "motivo_escalamiento": meta.get("motivo_escalamiento"),
        "error_tecnico_visible": bool(ERROR_TECNICO.search(datos.get("respuesta") or "")),
        "agentes_invocados": meta.get("agentes_invocados"),
        "latencia_cliente_ms": round((time.perf_counter() - inicio) * 1000),
    }


def _guardar(nombre: str, datos: Any) -> Path:
    DESTINO.mkdir(parents=True, exist_ok=True)
    ruta = DESTINO / nombre
    ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return ruta


def fallas(api: str) -> int:
    """RNF-08: cada falla inyectada escala por «fallo de servicio» y nunca muestra un error
    técnico. El adaptador se prueba con una consulta personal (sesión de U03)."""
    resultados = []
    with _cliente(api) as cliente:
        sesion = _sesion(cliente, "U03")
        for servicio in SERVICIOS:
            for modo in ("tiempo", "error"):
                cabeceras = {
                    "X-Reloj-Simulado": reloj_habil(),
                    "X-Escenario-Id": "NF-01",
                    "X-Falla-Inyectada": f"{servicio}:{modo}",
                    **(sesion if servicio == "adaptador" else {}),
                }
                mensaje = PERSONAL if servicio == "adaptador" else GENERAL
                conversacion = f"nf-fallas-{servicio}-{modo}-{time.monotonic_ns()}"
                fila = _turno(cliente, conversacion, mensaje, cabeceras)
                fila |= {
                    "falla": f"{servicio}:{modo}",
                    "pasa": fila["codigo_http"] == 200
                    and fila["estado"] == "escalada"
                    and fila["motivo_escalamiento"] == "fallo de servicio"
                    and not fila["error_tecnico_visible"],
                }
                resultados.append(fila)
                print(json.dumps(fila, ensure_ascii=False))
    ruta = _guardar(
        "fallas_inyectadas.json",
        {"pasan": sum(f["pasa"] for f in resultados), "de": len(resultados), "fallas": resultados},
    )
    print(f"{sum(f['pasa'] for f in resultados)} de {len(resultados)} en {ruta}")
    return 0 if all(f["pasa"] for f in resultados) else 1


def turno(api: str, conversacion: str, paso: int) -> int:
    """RNF-02: el paso 1 abre la conversación y el 2 la continúa (con otra réplica)."""
    mensaje = GENERAL if paso == 1 else SEGUIMIENTO
    cabeceras = {"X-Reloj-Simulado": reloj_habil(), "X-Escenario-Id": "NF-02"}
    with _cliente(api) as cliente:
        fila = _turno(cliente, conversacion, mensaje, cabeceras) | {"paso": paso}
    ruta = DESTINO / "replicas.json"
    anterior = json.loads(ruta.read_text(encoding="utf-8")) if ruta.exists() else {}
    previos = anterior.get("turnos", []) if anterior.get("conversacion") == conversacion else []
    _guardar("replicas.json", {"conversacion": conversacion, "turnos": [*previos, fila]})
    print(json.dumps(fila, ensure_ascii=False))
    return 0 if fila["codigo_http"] == 200 and fila["estado"] == "respondida" else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("accion", choices=("fallas", "turno"))
    parser.add_argument("--api", required=True)
    parser.add_argument("--conversacion", default="NF-replicas")
    parser.add_argument("--paso", type=int, choices=(1, 2), default=1)
    args = parser.parse_args()
    if args.accion == "fallas":
        return fallas(args.api)
    return turno(args.api, args.conversacion, args.paso)


if __name__ == "__main__":
    sys.exit(main())
