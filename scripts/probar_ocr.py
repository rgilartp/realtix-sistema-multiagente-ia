"""Exactitud del agente OCR con el modelo de visión real (B10). Gasta tokens: se corre una vez.

Genera los recibos sintéticos en una carpeta temporal, los lee en PNG y en PDF con `MODELO_OCR` y
escribe `reports/b10_ocr.json` con la exactitud por campo, los rechazos, los tokens y el costo.

Uso: uv run python scripts/probar_ocr.py
"""

import json
import sys
import tempfile
from decimal import Decimal
from pathlib import Path

from langchain_core.callbacks import get_usage_metadata_callback

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.container import Contenedor  # noqa: E402
from src.data.generar.generate_synthetic_data import generar_datos  # noqa: E402
from src.data.generar.recibos import guardar, recibos_del_conjunto  # noqa: E402
from src.evaluacion.ocr import evaluar_ocr  # noqa: E402
from src.integrations.costos import usos_desde_metadatos  # noqa: E402

SALIDA = Path("reports/b10_ocr.json")


def main() -> None:
    contenedor = Contenedor()
    recibos = recibos_del_conjunto(generar_datos(42))
    with tempfile.TemporaryDirectory() as carpeta:
        archivos = {r.nombre: guardar(r, Path(carpeta)) for r in recibos}
        with get_usage_metadata_callback() as uso:
            reporte = evaluar_ocr(
                contenedor.modelo("ocr"), recibos, archivos, contenedor.settings.timeout_modelo_s
            )
    usos = usos_desde_metadatos(uso.usage_metadata)
    reporte["tokens"] = [
        {"modelo": u.modelo, "entrada": u.entrada, "salida": u.salida} for u in usos
    ]
    reporte["costo_usd"] = str(sum((u.costo_usd for u in usos), Decimal(0)))
    for fila in reporte["resultados"]:
        if "aciertos" in fila:
            fallos = [c for c, ok in fila["aciertos"].items() if not ok]
            print(f"{fila['documento']:<28} {fila['formato']}  {fallos or 'ok'}")
        else:
            estado = "rechazado bien" if fila["rechazo_correcto"] else "NO"
            print(f"{fila['documento']:<28} {fila['formato']}  {estado} {fila['problemas']}")
    print(json.dumps(reporte["resumen"], ensure_ascii=False, indent=1))
    print(f"Tokens: {reporte['tokens']}; costo: US${reporte['costo_usd']}")
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(json.dumps(reporte, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
