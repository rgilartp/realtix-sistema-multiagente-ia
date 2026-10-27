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


@pytest.mark.unit
@pytest.mark.req("RNF-09 · Lenguaje accesible")
def test_no_quita_una_oracion_con_una_cifra_que_la_nota_no_tiene() -> None:
    """Revisión independiente: una oración con un dato real (un monto inventado) se queda aunque
    comparta palabras con la nota; los años y los números de norma no cuentan como palabras."""
    nota = (
        "Como hay un trámite inventado pendiente (Norma 1234 de 2091), la oficina inventada "
        "calcula el recargo; el valor exacto lo da la oficina inventada del distrito."
    )
    con_cifra = (
        "Según tu cuenta, el saldo es de $7.654.000, y el recargo lo calcula la oficina "
        "inventada del distrito, no esta información."
    )
    assert sin_repetir_notas(con_cifra, [nota]) == con_cifra
    copia = (
        "Como hay un trámite inventado pendiente (Norma 1234 de 2091), la oficina inventada "
        "calcula el recargo; el valor exacto lo da la oficina del distrito."
    )
    assert sin_repetir_notas(f"Tu saldo es de $7.654.000. **{copia}**", [nota]) == (
        "Tu saldo es de $7.654.000."
    )
