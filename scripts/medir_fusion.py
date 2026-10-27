"""Mide, sin modelos, cuántas fuentes esperadas recupera la fusión de dos consultas (G2 y G3).

Con las partes guardadas en `reports/recuperacion.json` (texto del contribuyente y búsqueda del
orquestador), compara la búsqueda sola con `recuperar_con_dos_consultas` (la función real del
agente) y con la variante de texto y búsqueda concatenados. Solo gasta embeddings (OpenAI).
Escribe `reports/recuperacion_fusion.json`.

Uso: uv run python scripts/medir_fusion.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.agents.agente import ConfigAgente, recuperar, recuperar_con_dos_consultas  # noqa: E402
from src.agents.prompts import Prompt  # noqa: E402
from src.container import Contenedor  # noqa: E402
from src.evaluacion.escenarios import RAIZ, cargar_escenarios  # noqa: E402
from src.evaluacion.recuperacion import (  # noqa: E402
    COLECCIONES_POR_CATEGORIA,
    acierta,
    fuentes_de_la_base,
    normas_de_la_base,
)
from src.integrations.trazas import Anonimizador  # noqa: E402


def main() -> int:
    deps = Contenedor().deps
    anonimizar = Anonimizador(para_modelos=True).texto
    escenarios = {e["id"]: e for e in cargar_escenarios()}
    normas = normas_de_la_base()
    previo = json.loads((RAIZ / "reports" / "recuperacion.json").read_text(encoding="utf-8"))
    modos = ("busqueda", "fusion", "concatenada")
    aciertos = dict.fromkeys(modos, 0)
    total, cambios = 0, []
    for r in previo["resultados"]:
        recuperados: dict[str, list] = {m: [] for m in modos}
        for p in r["partes"]:
            colecciones = COLECCIONES_POR_CATEGORIA.get(p["categoria"], ())
            config = ConfigAgente(p["categoria"], Prompt("", "", ""), colecciones)
            b, t = anonimizar(p["busqueda"]), anonimizar(p["texto"])
            recuperados["busqueda"] += recuperar(deps, config, b, p["anio"])
            recuperados["fusion"] += recuperar_con_dos_consultas(deps, config, b, t, p["anio"])
            recuperados["concatenada"] += recuperar(deps, config, f"{t} {b}", p["anio"])
        for f in fuentes_de_la_base(escenarios[r["escenario"]], normas):
            total += 1
            fila = {m: acierta(f, recuperados[m]) for m in modos}
            for m in modos:
                aciertos[m] += fila[m]
            if fila["fusion"] != fila["busqueda"]:
                cambios.append({"escenario": r["escenario"], "fuente": f.texto, **fila})
    salida = {
        "que_es": "Sin modelos: fuentes esperadas entre los 5 fragmentos con la búsqueda sola, "
        "con la fusión de la búsqueda y el texto (recuperar_con_dos_consultas) y con los dos "
        "concatenados, con las partes guardadas en reports/recuperacion.json",
        "fuentes": total,
        "aciertos": aciertos,
        "cambios_de_la_fusion": cambios,
    }
    destino = RAIZ / "reports" / "recuperacion_fusion.json"
    destino.write_text(json.dumps(salida, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"fuentes": total, "aciertos": aciertos}, ensure_ascii=False))
    for c in cambios:
        print(c)
    return 0


if __name__ == "__main__":
    sys.exit(main())
