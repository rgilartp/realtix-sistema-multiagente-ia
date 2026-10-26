"""Fija la escala de la similitud con 10 consultas de prueba (sección 3.3, pendiente de B5).

Cinco consultas pertinentes (de los escenarios aprobados, cada una contra su colección) y cinco sin
relación con la base (contra las cuatro colecciones). Toma el coseno del mejor fragmento de cada
una y propone la escala: el coseno que vale 0 es el más alto de las consultas sin relación, y el que
vale 1, la mediana de las pertinentes. Escribe `reports/b08_calibracion.json`.

Gasta solo los embeddings de las 10 consultas (unos 200 tokens).
Uso: uv run python scripts/calibrar_similitud.py
"""

import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.container import Contenedor  # noqa: E402
from src.integrations.recuperacion_hibrida import COLECCIONES  # noqa: E402

PERTINENTES = (
    ("IPU-04", "¿Qué es el impuesto predial unificado y cómo se calcula?", "normativa_ipu"),
    ("IPU-09", "¿Cuánto puede subir mi predial de un año a otro?", "normativa_ipu"),
    ("ICA-01", "¿Qué es el impuesto de industria y comercio y quién lo paga?", "normativa_ica"),
    ("GEN-04", "¿Qué es el SPAC?", "plataforma_general"),
    ("GEN-07", "¿Qué derechos tengo sobre mis datos personales?", "normativa_datos"),
)
SIN_RELACION = (
    ("FA-01", "¿Cómo va a estar el clima mañana en Bogotá?"),
    ("FA-02", "¿Cómo renuevo mi licencia de conducción?"),
    ("receta", "¿Cuál es la receta del ajiaco santafereño?"),
    ("futbol", "¿Quién ganó el último partido de la selección de fútbol?"),
    ("pelicula", "Recomiéndame una película de ciencia ficción"),
)
SALIDA = Path("reports/b08_calibracion.json")


def main() -> None:
    recuperador = Contenedor().recuperador
    filas = []
    for id_, consulta, coleccion in PERTINENTES:
        mejor = recuperador.recuperar(consulta, coleccion=coleccion, k=5, anio=2026)[0]
        filas.append({"consulta": id_, "tipo": "pertinente", "coseno": round(mejor.similitud, 4),
                      "fragmento": mejor.cita})  # fmt: skip
    for id_, consulta in SIN_RELACION:
        mejores = [
            recuperador.recuperar(consulta, coleccion=c, k=1, anio=2026)[0] for c in COLECCIONES
        ]
        mejor = max(mejores, key=lambda f: f.similitud)
        filas.append({"consulta": id_, "tipo": "sin_relacion", "coseno": round(mejor.similitud, 4),
                      "fragmento": mejor.cita})  # fmt: skip
    pertinentes = [f["coseno"] for f in filas if f["tipo"] == "pertinente"]
    ajenas = [f["coseno"] for f in filas if f["tipo"] == "sin_relacion"]
    escala = {"minimo": round(max(ajenas), 2), "maximo": round(statistics.median(pertinentes), 2)}
    for fila in filas:
        print(f"{fila['consulta']:<9}{fila['tipo']:<13}{fila['coseno']:.4f}  {fila['fragmento']}")
    print(f"Escala propuesta: {escala}")
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(
        json.dumps({"consultas": filas, "escala": escala}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
