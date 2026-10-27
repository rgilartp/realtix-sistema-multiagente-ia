"""Evaluador de la recuperación (revisión externa): normas, artículos y aciertos, sin red."""

import pytest

from src.evaluacion.recuperacion import (
    FuenteEsperada,
    acierta,
    articulos_de_cita,
    clave_de_norma,
    fuentes_de_la_base,
    normas_de_la_base,
    resumir,
)
from src.integrations.recuperador import Fragmento


@pytest.mark.unit
@pytest.mark.req("RF-OBS-05 · Ejecución repetible de pruebas")
@pytest.mark.parametrize(
    ("texto", "clave", "articulos"),
    [
        ("Ley 2294 de 2023, art. 49, par. 3", "ley 2294 2023", {"49"}),
        ("Acuerdo 1084 de 2026, arts. 13, 14 y 20", "acuerdo 1084 2026", {"13", "14", "20"}),
        ("Acuerdo 1084 de 2026, art. 27, num. 3", "acuerdo 1084 2026", {"27"}),
        ("Decreto 807 de 1993 art. 18", "decreto 807 1993", {"18"}),  # sin coma
        ("Decreto Distrital 352 de 2002, cap. I", "decreto 352 2002", set()),
        ("Resolución SDH-000194 de 2025, art. 1", "resolucion 194 2025", {"1"}),
        ("Glosario (plataforma_general)", "glosario", set()),
        ("Usuario de prueba U03 (usuarios_prueba.yaml)", None, set()),
        ("datos/tarifas/ipu_2026.yaml", None, set()),
    ],
)  # fmt: skip
def test_clave_de_norma_y_articulos(texto, clave, articulos) -> None:
    assert clave_de_norma(texto) == clave
    assert articulos_de_cita(texto) == articulos


@pytest.mark.unit
@pytest.mark.req("RF-OBS-05 · Ejecución repetible de pruebas")
def test_solo_cuentan_las_fuentes_de_la_base_y_el_articulo_debe_coincidir() -> None:
    escenario = {"fuentes_esperadas": ["Ley 1995 de 2019, art. 2", "RNF-06 · Horario de atención",
                                       "datos/calendario/2026.yaml"]}  # fmt: skip
    (fuente,) = fuentes_de_la_base(escenario, normas_de_la_base())
    assert fuente == FuenteEsperada("Ley 1995 de 2019, art. 2", "ley 1995 2019", frozenset({"2"}))
    art_2 = Fragmento("…", "normativa_ipu/ley_1995_2019.md", "Artículo 2", 0.6, "Ley 1995 de 2019")
    art_1 = Fragmento("…", "normativa_ipu/ley_1995_2019.md", "Artículo 1", 0.6, "Ley 1995 de 2019")
    assert acierta(fuente, [art_1, art_2]) and not acierta(fuente, [art_1])


@pytest.mark.unit
@pytest.mark.req("RF-OBS-05 · Ejecución repetible de pruebas")
def test_resumen_con_texto_y_con_busqueda() -> None:
    resultados = [
        {"grupo": "ipu", "comportamiento_esperado": "responder",
         "fuentes": [{"con_texto": False, "con_busqueda": True}]},
        {"grupo": "robustez", "comportamiento_esperado": "escalar",
         "fuentes": [{"con_texto": False, "con_busqueda": False}]},
    ]  # fmt: skip
    resumen = resumir(resultados)
    assert resumen["con_texto"]["aciertos_por_fuente"] == 0
    assert resumen["con_busqueda"]["tasa_por_fuente"] == 0.5
    assert resumen["responden_con_fragmentos"]["con_busqueda"]["tasa_por_escenario"] == 1.0


@pytest.mark.unit
@pytest.mark.req("RF-GEN-03 · Respuesta sustentada en fuentes")
def test_la_fusion_de_dos_consultas_desempata_a_favor_de_la_busqueda() -> None:
    """Revisión del PR #49: dos fragmentos con el mismo puntaje RRF (cada uno en una sola lista y
    en el mismo rango) se ordenan por canal (primero la búsqueda) y no por el nombre del archivo;
    el que está en las dos listas conserva la similitud de la búsqueda; si el texto falla, queda
    la búsqueda sola. Fragmentos inventados."""
    from typing import Any

    from src.agents.agente import ConfigAgente, recuperar_con_dos_consultas
    from src.agents.dependencias import Dependencias
    from src.agents.prompts import Prompt
    from src.integrations.recuperador import Fragmento

    def frag(id_: str, similitud: float) -> Fragmento:
        return Fragmento("Texto inventado.", f"normativa_ipu/{id_}.md", "Artículo 1", similitud,
                         norma="Norma inventada", id=id_)  # fmt: skip

    busqueda = [frag("z1", 0.6), frag("z2", 0.6), frag("z3", 0.6), frag("z4", 0.6), frag("z5", 0.6)]
    texto = [frag("z1", 0.45), frag("a2", 0.5), frag("a3", 0.5), frag("a4", 0.5), frag("a5", 0.5)]

    class Recuperador:
        def __init__(self, falla: bool = False) -> None:
            self.falla = falla

        def recuperar(self, consulta: str, **_: Any) -> list[Fragmento]:
            if consulta == "t" and self.falla:
                raise TimeoutError("texto")
            return list(busqueda if consulta == "b" else texto)

    config = ConfigAgente("ipu", Prompt("", "", ""), ("normativa_ipu",))
    deps = Dependencias(None, recuperador=Recuperador())  # type: ignore[arg-type]
    fusion = recuperar_con_dos_consultas(deps, config, "b", "t", 2026)
    assert [f.id for f in fusion] == ["z1", "z2", "a2", "z3", "a3"]  # empates: la búsqueda primero
    assert fusion[0].similitud == 0.6  # en las dos listas: la similitud de la búsqueda
    deps_con_falla = Dependencias(None, recuperador=Recuperador(falla=True))  # type: ignore[arg-type]
    assert [f.id for f in recuperar_con_dos_consultas(deps_con_falla, config, "b", "t", 2026)] == [
        "z1", "z2", "z3", "z4", "z5"
    ]  # fmt: skip
