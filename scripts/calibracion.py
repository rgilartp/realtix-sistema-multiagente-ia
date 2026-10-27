"""Muestra de calibración del juez y su kappa (sección 6.4; ADR-24: R2, A5 y A6). Sin red.

  # B15, después de la corrida 2: exporta 30 respuestas estratificadas, sin el veredicto del juez,
  # con el HTML de lectura y la hoja .xlsx de cada evaluador, y guarda la huella del juez (desde
  # aquí queda congelado):
  uv run python scripts/calibracion.py exportar --corrida corrida-2
  # Cuando los dos evaluadores y el consenso llenaron sus hojas, se pasan a muestra.csv:
  uv run python scripts/calibracion.py importar
  # B16, con la muestra ya calificada por Rodolfo y Dayanna:
  uv run python scripts/calibracion.py kappa --corrida corrida-2

Todo queda en `reports/calibracion/`: `muestra.csv`, `clave.json`, `huella_juez.txt` y `kappa.json`.
"""

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import cargar_configuracion  # noqa: E402
from src.evaluacion.calibracion import (  # noqa: E402
    COLUMNAS_EVALUADORES,
    TAMANO,
    calcular_kappa,
    elegir,
    exportar,
    exportar_para_evaluadores,
    importar_calificaciones,
)
from src.evaluacion.corrida import vigentes  # noqa: E402
from src.evaluacion.ejecutor import leer_resultados  # noqa: E402
from src.evaluacion.escenarios import RAIZ, cargar_conjunto  # noqa: E402
from src.evaluacion.juez import huella_del_juez  # noqa: E402

DESTINO = RAIZ / "reports" / "calibracion"


def ya_calificada(ruta: Path) -> bool:
    if not ruta.exists():
        return False
    with ruta.open(encoding="utf-8") as archivo:
        return any(any(f[c].strip() for c in COLUMNAS_EVALUADORES) for f in csv.DictReader(archivo))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("accion", choices=("exportar", "importar", "kappa"))
    parser.add_argument("--corrida", default="corrida-2")
    parser.add_argument("--tamano", type=int, default=TAMANO)
    parser.add_argument("--forzar", action="store_true", help="reemplaza una muestra calificada")
    args = parser.parse_args()
    corrida = RAIZ / "reports" / args.corrida

    if args.accion == "exportar":
        if ya_calificada(DESTINO / "muestra.csv") and not args.forzar:
            raise SystemExit("La muestra ya tiene calificaciones; no se reemplaza sin --forzar.")
        calificados = leer_resultados(corrida / "calificados.jsonl")
        ensayos = {
            e["id_conversacion"]: e for e in vigentes(leer_resultados(corrida / "resultados.jsonl"))
        }
        escenarios = {e["id"]: e for e in cargar_conjunto(["principal", "R1", "R3", "R4"])}
        muestra = elegir(calificados, args.tamano)
        # La huella es la del juez que calificó la corrida (sus registros); debe ser la actual.
        huellas = {j.get("huella") for j in leer_resultados(corrida / "juez.jsonl")}
        if huellas != {huella_del_juez(cargar_configuracion())}:
            raise SystemExit("La corrida no la calificó, entera, el juez actual (A5).")
        ruta = exportar(muestra, ensayos, escenarios, DESTINO, huellas.pop())
        material = exportar_para_evaluadores(muestra, ensayos, escenarios, DESTINO)
        print(f"{len(muestra)} respuestas en {ruta} (sin el veredicto del juez).")
        print("Material de cada evaluador:", ", ".join(str(m.relative_to(RAIZ)) for m in material))
        return 0
    if args.accion == "importar":
        completas = importar_calificaciones(DESTINO)
        print(f"{completas} filas completas en {DESTINO / 'muestra.csv'}.")
        return 0

    resultado = calcular_kappa(DESTINO, corrida / "juez.jsonl")
    (DESTINO / "kappa.json").write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    for comparacion in ("juez_frente_al_consenso", "entre_evaluadores"):
        for tipo, k in resultado[comparacion].items():
            bajo, alto = k["ic95"]
            print(f"{comparacion}, {tipo}: {k['kappa']:.3f} (IC 95 %: {bajo:.3f} a {alto:.3f})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
