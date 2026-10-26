"""Latencia y prueba de humo con modelos reales (RNF-01). Gasta tokens: una vez por bloque.

- Sin opciones: la prueba de humo de B7 por el grafo (`reports/b07_humo.json`).
- `--api`: de punta a punta por la API (B9), con el checkpointer de PostgreSQL, Chroma y el modo
  de evaluación encendido solo para esta corrida (`reports/b09_latencia.json`).

Uso: uv run python scripts/medir_latencia.py [--api] [--salida RUTA]
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.container import Contenedor  # noqa: E402
from src.evaluacion.humo import correr_humo  # noqa: E402


def humo(salida: Path) -> None:
    def avance(r: dict) -> None:
        estado = f"escaló ({r['motivo_escalamiento']})" if r["escalado"] else "respondió"
        print(f"{r['escenario']:<9} {r['tipo']:<17} {r['duracion_ms']:>9.1f} ms  {estado}")

    reporte = correr_humo(Contenedor().deps, salida, avance)
    resumen = reporte["resumen"]
    for tipo, datos in resumen["latencia"].items():
        print(f"{tipo}: mediana {datos['mediana_ms']} ms, máximo {datos['maximo_ms']} ms")
    for modelo, t in resumen["tokens"].items():
        print(f"{modelo}: {t['entrada']} tokens de entrada, {t['salida']} de salida")
    print(f"Costo total: US${resumen['costo_total_usd']}")


def por_api(salida: Path) -> None:
    from fastapi.testclient import TestClient

    from src.agents.graph import checkpointer_postgres, construir_grafo
    from src.api.app import crear_app, servicios_desde_contenedor
    from src.config import cargar_configuracion
    from src.evaluacion.latencia import correr_por_api, costo_de_interacciones, guardar

    settings = cargar_configuracion().model_copy(update={"modo_evaluacion": True})
    contenedor = Contenedor(settings)

    def avance(r: dict) -> None:
        marca = "cumple" if r["cumple_meta"] else "NO cumple"
        print(f"{r['escenario']:<9} {r['tipo']:<17} {r['duracion_ms']:>9.1f} ms  "
              f"{r['estado']:<16} {marca}")  # fmt: skip

    with checkpointer_postgres(settings.database_url.get_secret_value()) as saver:
        servicios = servicios_desde_contenedor(contenedor, construir_grafo(contenedor.deps, saver))
        with TestClient(crear_app(servicios)) as cliente:
            reporte = correr_por_api(cliente, settings.ovt_hmac_secret, avance)
        ids = {r["id_conversacion"] for r in reporte["resultados"]}
        costo = costo_de_interacciones(servicios.almacen.todas_las_interacciones(), ids)
    reporte["costo_total_usd"] = str(costo)
    guardar(reporte, salida)
    for tipo, datos in reporte["resumen"]["latencia"].items():
        print(f"{tipo}: mediana {datos['mediana_ms']} ms, máximo {datos['maximo_ms']} ms; "
              f"{datos['cumplen']}/{datos['consultas']} bajo {datos['meta_ms']} ms")  # fmt: skip
    print(f"Tokens: {reporte['resumen']['tokens']}; costo: US${costo}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--api", action="store_true", help="de punta a punta por la API (B9)")
    parser.add_argument("--salida", type=Path)
    args = parser.parse_args()
    if args.api:
        por_api(args.salida or Path("reports/b09_latencia.json"))
    else:
        humo(args.salida or Path("reports/b07_humo.json"))


if __name__ == "__main__":
    main()
