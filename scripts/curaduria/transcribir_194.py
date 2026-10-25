"""Genera las tablas de los arts. 2 y 3 de la Resolución SDH-000194 desde `ipu_2026.yaml`.

El PDF trae esas tablas como texto suelto. Los datos de `ipu_2026.yaml` ya se contrastaron con el
PDF (`contrastar_rangos.py`, 0 diferencias); aquí solo se les da forma de tabla Markdown.
"""

from decimal import Decimal

import yaml
from comun import RAIZ

INSERCIONES = RAIZ / "scripts" / "curaduria" / "inserciones"


def _pesos(valor: int | None) -> str:
    return "$ -" if valor is None else "$ " + f"{valor:,}".replace(",", ".")


def _tarifa(texto: str) -> str:
    return str(Decimal(texto).normalize()).replace(".", ",")


def _tabla(encabezado: list[str], filas: list[list[str]]) -> str:
    lineas = ["| " + " | ".join(encabezado) + " |", "|" + "---|" * len(encabezado)]
    return "\n".join(lineas + ["| " + " | ".join(f) + " |" for f in filas]) + "\n"


def main() -> None:
    datos = yaml.safe_load((RAIZ / "datos" / "tarifas" / "ipu_2026.yaml").read_text("utf-8"))
    no_residencial = [
        [f["destino"], _tarifa(f["tarifa_por_mil"]), _pesos(f["desde"]), _pesos(f["hasta"])]
        for f in datos["no_residencial"]
    ]
    clubes = [
        [_tarifa(f["tarifa_por_mil"]), _pesos(f["desde"]), _pesos(f["hasta"])]
        for f in datos["clubes_destino_66"]
    ]
    (INSERCIONES / "sdh_194_art_2.md").write_text(
        _tabla(
            ["Categoría y destino hacendario", "Tarifa por mil", "Desde", "Hasta"], no_residencial
        ),
        encoding="utf-8",
    )
    (INSERCIONES / "sdh_194_art_3.md").write_text(
        _tabla(["Tarifa por mil (destino 66)", "Desde", "Hasta"], clubes), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
