"""Contrasta los YAML de `datos/` con las tablas del texto digital del Acuerdo 1084.

El texto digital es el del Régimen Legal de Bogotá, ya cortado por artículo en `knowledge_base/`.
Compara, fila por fila, la sobretasa de alumbrado (arts. 14 y 15), el predial de 2027 (art. 20) y el
ICA consolidado del SIMPLE (art. 24), más el de 2026 (art. 44 del Acuerdo 1019 de 2025). Escribe
`docs/verificacion/acuerdo_1084_contraste.json` y termina con código 1 si hay diferencias.
Uso: uv run python scripts/curaduria/contrastar_1084.py
"""

import json
import re
import sys
from decimal import Decimal

import yaml
from comun import KNOWLEDGE_BASE, RAIZ

IPU = KNOWLEDGE_BASE / "normativa_ipu" / "acuerdo_1084_2026.md"
ICA_1019 = KNOWLEDGE_BASE / "normativa_ica" / "acuerdo_1019_2025_ica.md"
ICA = KNOWLEDGE_BASE / "normativa_ica" / "acuerdo_1084_2026_ica.md"
SALIDA = RAIZ / "docs" / "verificacion" / "acuerdo_1084_contraste.json"


def _yaml(ruta: str) -> dict:
    return yaml.safe_load((RAIZ / "datos" / ruta).read_text(encoding="utf-8"))


def _articulo(texto: str, numero: int) -> str:
    inicio = texto.index(f"\n## Artículo {numero}\n")
    fin = texto.find("\n## Artículo ", inicio + 1)
    return texto[inicio : fin if fin != -1 else len(texto)]


def tablas(texto: str) -> list[list[list[str]]]:
    """Tablas Markdown de un texto, como listas de filas de celdas (sin el encabezado)."""
    resultado: list[list[list[str]]] = []
    actual: list[list[str]] = []
    for linea in texto.splitlines() + [""]:
        if linea.startswith("|"):
            celdas = [c.strip() for c in linea.strip().strip("|").split("|")]
            if not all(re.fullmatch(r"-+", c) for c in celdas if c):
                actual.append(celdas)
        elif actual:
            resultado.append(actual[1:])
            actual = []
    return resultado


def _decimal(texto: str) -> Decimal:
    return Decimal(texto.replace(",", ".").strip()).normalize()


def _pesos(texto: str) -> int:
    return int(re.sub(r"[^\d]", "", texto))


def _rango(desde: str, hasta: str | None = None) -> tuple:
    """Pasa «$ 1», «Más de $ X», «Cualquier avalúo» o «135 SMMLV» a (desde, hasta) numéricos."""

    def punta(valor: str, es_desde: bool):
        v = valor.strip()
        if re.fullmatch(r"cualquier avalúo", v, re.IGNORECASE):
            return 1 if es_desde else None
        if v.lower().startswith("más de"):
            n = _pesos(v)
            return n if "smmlv" in v.lower() else n + 1
        return _pesos(v)

    if desde.lower().startswith("cualquier"):
        return (1, None)
    return (punta(desde, True), punta(hasta, False) if hasta and hasta != "—" else None)


def _comparar(nombre: str, del_texto: list, del_yaml: list) -> dict:
    diferencias = []
    if len(del_texto) != len(del_yaml):
        diferencias.append(f"el texto tiene {len(del_texto)} filas y el YAML {len(del_yaml)}")
    for i, (a, b) in enumerate(zip(del_texto, del_yaml, strict=False), 1):
        if a != b:
            diferencias.append(f"fila {i}: texto {a} contra YAML {b}")
    return {
        "tabla": nombre,
        "filas_en_el_texto": len(del_texto),
        "filas_en_el_yaml": len(del_yaml),
        "diferencias": diferencias,
    }


def contrastar() -> list[dict]:
    ipu, ica = IPU.read_text(encoding="utf-8"), ICA.read_text(encoding="utf-8")
    sobretasa, predial = (
        _yaml("tarifas/sobretasa_alumbrado_2027.yaml"),
        _yaml("tarifas/ipu_2027.yaml"),
    )
    simple = _yaml("tarifas/ica_2027.yaml")["regimen_simple_2027"]
    resultados = []

    art_14 = tablas(_articulo(ipu, 14))[0]
    resultados.append(
        _comparar(
            "sobretasa, art. 14 (categoría y tarifas)",
            [(re.sub(r"\s+", " ", f[0]), _decimal(f[1]), _decimal(f[2])) for f in art_14],
            [
                (t["descripcion"], _decimal(t["de_2027_a_2041"]), _decimal(t["desde_2042"]))
                for t in sobretasa["tarifas_por_mil"]
            ],
        )
    )
    art_15 = tablas(_articulo(ipu, 15))[0]
    resultados.append(
        _comparar(
            "sobretasa, art. 15 (topes en UVT)",
            [(f[0], int(re.sub(r"\D", "", f[1]))) for f in art_15],
            [(t["descripcion"], t["valor_limite_uvt"]) for t in sobretasa["topes_uvt"]],
        )
    )

    art_20 = tablas(_articulo(ipu, 20))
    urbanos, rurales, residencial, no_residencial, clubes = art_20[:5]
    pref = predial["preferenciales"]
    resultados.append(
        _comparar(
            "predial 2027, preferenciales urbanos y rurales con destino agropecuario",
            [(f[1].lower(), f[2].lower(), _decimal(f[3])) for f in urbanos],
            [
                (f["desde"].lower(), f["hasta"].lower(), _decimal(f["tarifa_por_mil"]))
                for f in pref["residencial_urbano_y_rural_agropecuario"]
            ],
        )
    )
    resultados.append(
        _comparar(
            "predial 2027, preferenciales residenciales rurales",
            [(f[0].lower(), f[1].lower(), _decimal(f[2])) for f in rurales],
            [
                (f["desde"].lower(), f["hasta"].lower(), _decimal(f["tarifa_por_mil"]))
                for f in pref["residencial_rural"][:2]
            ],
        )
    )

    def fila_residencial(f: list[str]) -> tuple:
        if f[0].lower().startswith("más de"):  # la fuente repite «Más de…» en Desde y en Hasta
            return (*_rango(f[0]), _decimal(f[-1]))
        return (*_rango(f[0], f[1]), _decimal(f[-1]))

    resultados.append(
        _comparar(
            "predial 2027, residenciales generales",
            [fila_residencial(f) for f in residencial],
            [
                (
                    f["desde"] if f["desde"] > 1 else 1,
                    f["hasta"],
                    _decimal(f["tarifa_por_mil"]),
                )
                for f in predial["generales"]["residencial"]
            ],
        )
    )

    def fila_no_residencial(f: list[str]) -> tuple:
        tarifa = _decimal(f[1])
        if f[2] == f[3]:  # «Más de…» o «Cualquier avalúo» repetido en Desde y en Hasta
            return (tarifa, *_rango(f[2]))
        return (tarifa, *_rango(f[2], f[3]))

    resultados.append(
        _comparar(
            "predial 2027, no residenciales",
            [fila_no_residencial(f) for f in no_residencial],
            [
                (_decimal(f["tarifa_por_mil"]), f["desde"], f["hasta"])
                for f in predial["generales"]["no_residencial"]
            ],
        )
    )

    def fila_club(f: list[str]) -> tuple:
        tarifas = (_decimal(f[3]), _decimal(f[4]))
        if f[1] == f[2]:  # «Más de…» repetido en Desde y en Hasta
            return (*tarifas, *_rango(f[1]))
        return (*tarifas, *_rango(f[1], f[2]))

    resultados.append(
        _comparar(
            "predial 2027, clubes campestres, sociales y deportivos",
            [fila_club(f) for f in clubes],
            [
                (
                    _decimal(f["tarifa_por_mil_2027"]),
                    _decimal(f["tarifa_por_mil_desde_2028"]),
                    f["desde"],
                    f["hasta"],
                )
                for f in predial["generales"]["dotacional_clubes_de_particulares"]["rangos"]
            ],
        )
    )

    art_24 = tablas(_articulo(ica, 24))[0]
    resultados.append(
        _comparar(
            "ICA consolidado del SIMPLE, art. 24",
            [(f[0], _decimal(f[1])) for f in art_24],
            [(t["numeral"], _decimal(t["tarifa_por_mil"])) for t in simple["tarifas_por_mil"]],
        )
    )

    art_44 = tablas(_articulo(ICA_1019.read_text(encoding="utf-8"), 44))[0]
    simple_2026 = _yaml("tarifas/ica_2026.yaml")["regimen_simple_2026"]
    resultados.append(
        _comparar(
            "ICA consolidado del SIMPLE 2026, art. 44 del Acuerdo 1019 de 2025",
            [(re.sub(r"\s", "", f[0]), _decimal(f[1])) for f in art_44],
            [
                (re.sub(r"\s", "", t["numeral"]), _decimal(t["tarifa_por_mil"]))
                for t in simple_2026["tarifas_por_mil"]
            ],
        )
    )
    return resultados


if __name__ == "__main__":
    resultados = contrastar()
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(json.dumps(resultados, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for r in resultados:
        print(f"{r['tabla']}: {r['filas_en_el_texto']} filas, {len(r['diferencias'])} diferencias")
        for linea in r["diferencias"]:
            print("   -", linea)
    sys.exit(1 if any(r["diferencias"] for r in resultados) else 0)
