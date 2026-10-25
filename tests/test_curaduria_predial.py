"""Predial: tarifas preferenciales de 2026 y de 2027 (RF-IPU-03 · Liquidación estimada)."""

import re
from decimal import Decimal
from pathlib import Path

import pytest
import yaml

RAIZ = Path(__file__).resolve().parents[1]
DATOS = RAIZ / "datos"
KB = RAIZ / "knowledge_base"

pytestmark = [pytest.mark.unit, pytest.mark.req("RF-IPU-03 · Liquidación estimada")]


def _yaml(ruta: str) -> dict:
    return yaml.safe_load((DATOS / ruta).read_text(encoding="utf-8"))


def _smmlv(anio: int) -> int:
    return next(s["valor"] for s in _yaml("uvt_smmlv.yaml")["smmlv"] if s["anio"] == anio)


def _filas_2026() -> list[dict]:
    return _yaml("tarifas/ipu_2026.yaml")["preferenciales"]["residencial"]


def _filas_2027() -> list[dict]:
    return _yaml("tarifas/ipu_2027.yaml")["preferenciales"][
        "residencial_urbano_y_rural_agropecuario"
    ]


def _a_pesos(valor: Decimal, unidad: str, smmlv: int) -> Decimal:
    return valor * smmlv if unidad == "SMMLV" else valor


def _tarifa(filas: list[dict], estrato: int, avaluo: Decimal, smmlv: int) -> str | None:
    """Tarifa preferencial por mil de un predio, o None si ninguna fila le aplica."""
    for fila in filas:
        if estrato not in fila["estratos"]:
            continue
        desde = _a_pesos(Decimal(fila["desde_valor"]), fila["unidad_desde"], smmlv)
        arriba_del_desde = avaluo > desde if fila["desde_exclusivo"] else avaluo >= desde
        hasta = fila["hasta_valor"]
        debajo_del_hasta = hasta is None or avaluo <= _a_pesos(
            Decimal(hasta), fila["unidad_hasta"], smmlv
        )
        if arriba_del_desde and debajo_del_hasta:
            return fila["tarifa_por_mil"]
    return None


def test_las_preferenciales_de_2026_traen_valores_fuentes_y_pesos_del_smmlv_de_2026() -> None:
    datos = _yaml("tarifas/ipu_2026.yaml")
    preferenciales = datos["preferenciales"]
    assert [(f["estratos"], f["tarifa_por_mil"]) for f in preferenciales["residencial"]] == [
        ([1, 2], "1"),
        ([1, 2], "3"),
        ([3], "3"),
    ]
    assert preferenciales["smmlv_del_anio_gravable"]["anio"] == 2026
    assert preferenciales["smmlv_del_anio_gravable"]["valor"] == _smmlv(2026) == 1_750_905
    assert preferenciales["limites_en_pesos"] == {
        "16_smmlv": 28_014_480,
        "107_smmlv": 187_346_835,
        "135_smmlv": 236_372_175,
    }
    for norma in (
        "Acuerdo 648 de 2016, art. 1",
        "Acuerdo 780 de 2020, art. 3",
        "Decreto 639 de 2025, art. 207",
    ):
        assert norma in datos["fuente"]
        assert any(norma.split(",")[0] in f for f in preferenciales["fuentes"])


def test_las_preferenciales_de_2026_coinciden_con_la_tabla_del_acuerdo_648() -> None:
    texto = (KB / "normativa_ipu" / "acuerdo_648_2016.md").read_text(encoding="utf-8")
    articulo = texto[texto.index("\n## Artículo 1\n") : texto.index("\n## Artículo 2\n")]
    filas = [
        [c.strip() for c in linea.strip("|").split("|")]
        for linea in articulo.splitlines()
        if re.match(r"\| (1 y 2|3) \|", linea)
    ]
    digital = [(f[0], f[1], f[2], f[3]) for f in filas]
    assert digital == [
        ("1 y 2", "16 smlmv", "107 smlmv", "1 por mil"),
        ("1 y 2", "Más de 107 smlmv", "135 smlmv", "3 por mil"),
        ("3", "0", "135 smlmv", "3 por mil"),
    ]
    propias = [(f["desde"], f["hasta"], f["tarifa_por_mil"]) for f in _filas_2026()]
    assert propias == [(d[1], d[2], d[3].split()[0]) for d in digital]


def test_los_campos_numericos_salen_del_texto_literal_de_los_limites() -> None:
    for anio, filas in ((2026, _filas_2026()), (2027, _filas_2027())):
        for fila in filas:
            literal = fila["desde"]
            numero = int(re.sub(r"\D", "", literal))
            assert fila["desde_valor"] == numero, (anio, literal)
            en_salarios = "smlmv" in literal.lower() or "smmlv" in literal.lower()
            assert fila["unidad_desde"] == ("SMMLV" if en_salarios else "pesos")
            if literal.lower().startswith("más de"):
                assert fila["desde_exclusivo"] is True
            assert fila["unidad_hasta"] == "SMMLV"
            assert fila["hasta_valor"] == int(re.sub(r"\D", "", fila["hasta"]))
    rural = _yaml("tarifas/ipu_2027.yaml")["preferenciales"]["residencial_rural"]
    assert [(f["desde_valor"], f["desde_exclusivo"], f["hasta_valor"]) for f in rural] == [
        (16, False, 107),
        (107, True, 135),
        (135, True, None),
    ]
    assert [f.get("unidad_hasta") for f in rural][-1] is None


def test_el_estrato_3_deja_clara_la_unidad_de_cada_limite() -> None:
    for filas in (_filas_2026(), _filas_2027()):
        estrato_3 = next(f for f in filas if f["estratos"] == [3])
        assert estrato_3["unidad_desde"] == "pesos"
        assert estrato_3["unidad_hasta"] == "SMMLV"
        assert "unidad" not in estrato_3  # mezcla unidades: no hay una sola


def test_el_limite_de_16_smmlv_cambia_de_2026_a_2027() -> None:
    smmlv_2026 = _smmlv(2026)
    en_2026, en_2027 = _filas_2026(), _filas_2027()
    dieciseis = Decimal(16 * smmlv_2026)
    un_peso_mas = dieciseis + 1
    # 2026: «igual o menor» a 16 SMMLV no paga (Decreto 639, art. 207)
    assert _tarifa(en_2026, 2, dieciseis, smmlv_2026) is None
    assert _tarifa(en_2026, 2, un_peso_mas, smmlv_2026) == "1"
    # 2027: solo queda excluido lo «inferior a 16 SMMLV» (Acuerdo 1084, art. 20)
    assert _tarifa(en_2027, 2, dieciseis - 1, smmlv_2026) is None
    assert _tarifa(en_2027, 2, dieciseis, smmlv_2026) == "1"
    assert "igual o menor" in _yaml("tarifas/ipu_2026.yaml")["preferenciales"]["limite_de_16_smmlv"]
    assert (
        "inferior a 16 SMMLV"
        in _yaml("tarifas/ipu_2027.yaml")["preferenciales"]["limite_de_16_smmlv"]
    )


def test_las_preferenciales_de_2026_cobran_menos_que_la_tabla_general() -> None:
    """Estrato 2 con avalúo de $150.000.000 en 2026: 1 por mil son $150.000, no $825.000."""
    smmlv = _smmlv(2026)
    avaluo = Decimal(150_000_000)
    assert _tarifa(_filas_2026(), 2, avaluo, smmlv) == "1"
    assert avaluo * Decimal("1") / 1000 == Decimal("150000")
    general = _yaml("tarifas/ipu_2026.yaml")["residencial_urbano"]
    fila = next(
        f for f in general if f["desde"] <= avaluo and (f["hasta"] is None or avaluo <= f["hasta"])
    )
    assert fila["tarifa_por_mil"] == "5.5"
    assert avaluo * Decimal(fila["tarifa_por_mil"]) / 1000 == Decimal("825000")
    # más de 135 SMMLV ya no es preferencial
    assert _tarifa(_filas_2026(), 2, Decimal(135 * smmlv + 1), smmlv) is None
    # el estrato 3 paga 3 por mil hasta 135 SMMLV y no tiene exclusión
    assert _tarifa(_filas_2026(), 3, Decimal(1), smmlv) == "3"
    assert _tarifa(_filas_2026(), 3, Decimal(135 * smmlv), smmlv) == "3"


def test_las_preferenciales_de_2027_dicen_que_no_son_nuevas() -> None:
    texto = _yaml("tarifas/ipu_2027.yaml")["preferenciales"]["mantiene"]
    assert "desde 2017" in texto and "Acuerdo 648 de 2016" in texto
    assert "de 2021 a 2026" in texto and "Acuerdo 780 de 2020" in texto
