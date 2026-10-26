"""Fija la escala de la similitud con 10 consultas de prueba (sección 3.3, pendiente de B5).

Cinco consultas pertinentes (de los escenarios aprobados, cada una contra su colección) y cinco sin
relación con la base (contra las cuatro colecciones). Cada consulta pasa primero por el orquestador
real, que escribe la búsqueda en los términos de la norma: es lo que embebe el agente (revisión
externa). De cada una toma el coseno más alto de sus fragmentos (el que usa la confianza) y propone
la escala: el coseno que vale 0 es el más alto de las consultas sin relación, y el que vale 1, la
mediana de las pertinentes. Guarda también el coseno con el texto del contribuyente, para comparar.
Escribe `reports/b08_calibracion.json`.

Gasta 10 llamadas a Sonnet 5.5 (unos US$0,06) y los embeddings de 20 consultas.
Uso: uv run python scripts/calibrar_similitud.py
"""

import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.agents.state import entrada_de_turno  # noqa: E402
from src.container import Contenedor  # noqa: E402
from src.integrations.recuperacion_hibrida import COLECCIONES  # noqa: E402
from src.integrations.trazas import Anonimizador  # noqa: E402

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
    contenedor = Contenedor()
    recuperador, clasificar = contenedor.recuperador, contenedor.deps.clasificador
    anonimizar = Anonimizador(para_modelos=True).texto

    def busqueda(id_: str, consulta: str) -> str:
        partes = clasificar(consulta, entrada_de_turno(consulta, f"calibracion-{id_}")).partes
        return anonimizar(partes[0].get("busqueda") or partes[0]["texto"])

    def mejor(consulta: str, colecciones: tuple[str, ...]):
        fragmentos = [
            f for c in colecciones for f in recuperador.recuperar(consulta, coleccion=c, anio=2026)
        ]
        return max(fragmentos, key=lambda f: f.similitud)

    filas = []
    consultas = [(i, c, (col,), "pertinente") for i, c, col in PERTINENTES] + [
        (i, c, COLECCIONES, "sin_relacion") for i, c in SIN_RELACION
    ]
    for id_, consulta, colecciones, tipo in consultas:
        buscada = busqueda(id_, consulta)
        con_busqueda, con_texto = mejor(buscada, colecciones), mejor(consulta, colecciones)
        filas.append({"consulta": id_, "tipo": tipo, "busqueda": buscada,
                      "coseno": round(con_busqueda.similitud, 4), "fragmento": con_busqueda.cita,
                      "coseno_con_texto": round(con_texto.similitud, 4),
                      "fragmento_con_texto": con_texto.cita})  # fmt: skip
    pertinentes = [f["coseno"] for f in filas if f["tipo"] == "pertinente"]
    ajenas = [f["coseno"] for f in filas if f["tipo"] == "sin_relacion"]
    escala = {"minimo": round(max(ajenas), 2), "maximo": round(statistics.median(pertinentes), 2)}
    for fila in filas:
        print(
            f"{fila['consulta']:<9}{fila['tipo']:<13}{fila['coseno']:.4f} "
            f"(texto {fila['coseno_con_texto']:.4f})  {fila['fragmento']}  «{fila['busqueda']}»"
        )
    print(f"Escala propuesta: {escala}")
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(
        json.dumps({"consultas": filas, "escala": escala}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
