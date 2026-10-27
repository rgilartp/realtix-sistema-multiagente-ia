"""Notas del sistema que el modelo no debe repetir (F11 de la corrida 1), con textos inventados."""

import pytest

from src.services.notas import sin_repetir_notas

NOTA = (
    "Como el trámite inventado está pendiente, la oficina inventada revisará cada documento "
    "adjunto antes de aprobar la solicitud del contribuyente."
)


@pytest.mark.unit
@pytest.mark.req("RNF-09 · Lenguaje accesible")
def test_quita_solo_la_oracion_que_repite_la_nota() -> None:
    texto = (
        "Tu trámite inventado está en curso.\n\nComo el trámite está pendiente, la oficina "
        "inventada revisará cada documento adjunto antes de aprobar la solicitud. Puedes "
        "consultarlo de nuevo mañana."
    )
    limpio = sin_repetir_notas(texto, [NOTA])
    assert limpio == "Tu trámite inventado está en curso.\n\nPuedes consultarlo de nuevo mañana."


@pytest.mark.unit
@pytest.mark.req("RNF-09 · Lenguaje accesible")
def test_no_toca_las_oraciones_distintas_ni_las_cortas_ni_las_citas() -> None:
    texto = "La oficina inventada atiende de lunes a viernes. Revisa el art. 12 del documento."
    assert sin_repetir_notas(texto, [NOTA]) == texto
    assert sin_repetir_notas(texto, []) == texto
    assert (
        sin_repetir_notas("Documento adjunto pendiente.", [NOTA]) == "Documento adjunto pendiente."
    )
