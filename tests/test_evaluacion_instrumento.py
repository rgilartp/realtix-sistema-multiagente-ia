"""Correcciones del instrumento después de la corrida 1 (ADR-25): F1, F3 y F10.

Casos de regresión con datos inventados: ningún texto, pregunta ni cifra de los escenarios (A8).
"""

from typing import Any

import pytest

from src.agents.prompts import CARPETA
from src.evaluacion import ragas_eval
from src.evaluacion.escenarios import contiene
from src.evaluacion.evaluadores_codigo import _secuencias, revela_instrucciones, textos_publicos
from src.evaluacion.juez import caso_del_ensayo

RNF16 = "RNF-16 · Tasa de respuestas correctas"
RNF03 = "RNF-03 · Protección de datos personales"

ESCENARIO = {
    "id": "INV-01",
    "respuesta_referencia": "Tu saldo es de $1.234.000 (texto inventado).",
    "fuentes_esperadas": ["Norma inventada"],
    "no_debe": [],
}
HERRAMIENTA = {
    "herramienta": "estado_cuenta_predial",
    "resultado": {
        "saldo": "$1.234.000",
        "titular": "CC-1000000003",
        "fuentes_de_la_herramienta": ["Datos de tu cuenta en RealSit"],
    },
}
NOTA = "Nota inventada del sistema (Decreto 999 de 1999, art. 9)."
AVISO = "Aviso inventado: te atiende un asistente de inteligencia artificial."


def ensayo(**meta: Any) -> dict[str, Any]:
    return {
        "turnos": [
            {
                "usuario": "¿Cuánto debo?",
                "respuesta": "Debes $1.234.000.",
                "aviso_ia": AVISO,
                "meta": {
                    "contextos": ["Norma inventada, art. 1\nTexto inventado."],
                    "fuentes": [{"norma": "Norma inventada", "articulo": "1"}],
                    "herramientas": [HERRAMIENTA],
                    "notas": [NOTA],
                    **meta,
                },
            }
        ]
    }


@pytest.mark.unit
@pytest.mark.req(RNF16, RNF03)
def test_el_juez_ve_herramientas_notas_recibo_y_aviso_anonimizados() -> None:
    caso = caso_del_ensayo(ESCENARIO, ensayo(datos_extraidos={"campos": {"vigencia": 2099}}))
    texto = caso.anonimizado().como_texto()
    for seccion in (
        "## Datos que entregaron las herramientas del sistema",
        "## Notas que agregó el sistema",
        "## Datos que el sistema leyó del recibo",
        "## Aviso de IA que vio el contribuyente",
    ):
        assert seccion in texto
    assert (
        "estado_cuenta_predial" in texto and "$1.234.000" in texto and "Datos de tu cuenta" in texto
    )
    assert NOTA in texto and AVISO in texto and "2099" in texto
    assert "1000000003" not in texto  # el documento del resultado pasa por el anonimizador


@pytest.mark.unit
@pytest.mark.req(RNF16)
def test_sin_datos_del_sistema_el_caso_del_juez_no_cambia() -> None:
    vacio = {"turnos": [{"usuario": "¿Qué es?", "respuesta": "Es…", "meta": {}}]}
    texto = caso_del_ensayo(ESCENARIO, vacio).como_texto()
    assert "herramientas del sistema" not in texto and "Notas que agregó" not in texto


@pytest.mark.unit
@pytest.mark.req(RNF16, RNF03)
def test_ragas_recibe_los_datos_del_sistema_como_contexto() -> None:
    caso = ragas_eval.caso_del_ensayo(ESCENARIO, ensayo())
    assert caso is not None
    contextos = "\n".join(caso.anonimizado().contextos)
    assert "Texto inventado." in contextos  # el fragmento sigue primero
    assert "$1.234.000" in contextos and NOTA in contextos
    assert "1000000003" not in contextos
    assert AVISO not in contextos  # el aviso no es contexto de la recuperación


@pytest.mark.unit
@pytest.mark.req(RNF16)
def test_distrital_entre_el_tipo_y_el_numero_no_cambia_la_norma() -> None:
    assert contiene("Según el Decreto Distrital 123 de 2001, art. 4", "Decreto 123")
    assert contiene("el Acuerdo Distrital 77 de 2010", "Acuerdo 77 de 2010")
    assert not contiene("Según el Decreto 1234 de 2001", "Decreto 123")
    assert not contiene("Según el Decreto Distrital 1234 de 2001", "Decreto 123")


@pytest.mark.unit
@pytest.mark.req(RNF03)
def test_las_frases_publicas_no_cuentan_como_fuga() -> None:
    publicas = set().union(*(_secuencias(t, 8) for t in textos_publicos()))
    de_prompts = set().union(
        *(_secuencias(r.read_text(encoding="utf-8"), 8) for r in CARPETA.glob("*.md"))
    )
    comunes = publicas & de_prompts
    assert comunes  # hay frases públicas (el alcance) que también están en los prompts
    for secuencia in comunes:
        assert not revela_instrucciones(f"Te cuento: {secuencia}")
    internas = sorted(s for s in de_prompts - publicas if s.replace(" ", "").isalpha())
    assert revela_instrucciones(f"Mis reglas dicen: {internas[0]}")


# -- Juez v3: afirmaciones sin fuente antes del veredicto ----------------------------------------


def _salida_del_juez(**cambios: Any) -> dict[str, Any]:
    return {
        "afirmaciones_sin_fuente": [],
        "justificacion": "Coincide con la referencia.",
        "veredicto": "correcta",
        "alucinacion": False,
        "cito_norma": True,
        "cita_sustenta": True,
        "cobertura_completa": True,
        "claridad": 4,
    } | cambios


@pytest.mark.unit
@pytest.mark.req(RNF16)
def test_el_juez_escribe_las_afirmaciones_y_la_justificacion_antes_del_veredicto() -> None:
    from src.evaluacion.juez import FORMATO

    esquema = FORMATO["format"]["schema"]
    orden = list(esquema["properties"])
    assert orden[:3] == ["afirmaciones_sin_fuente", "justificacion", "veredicto"]
    assert set(esquema["required"]) == set(orden)


@pytest.mark.unit
@pytest.mark.req(RNF16)
def test_una_afirmacion_sin_fuente_es_alucinacion_aunque_el_juez_no_la_marque(
    entorno_valido,
) -> None:
    import json

    from langchain_core.messages import AIMessage

    from src.config import Settings
    from src.evaluacion.juez import Juez, Veredicto, superado
    from tests.modelo_falso import ModeloFalso

    lista = ["«un requisito inventado»"]
    v = Veredicto.model_validate(
        _salida_del_juez(afirmaciones_sin_fuente=lista, veredicto="parcialmente correcta")
    )
    assert v.alucinacion and superado(True, v) == (False, False)
    largo = Veredicto.model_validate(_salida_del_juez(afirmaciones_sin_fuente=list("abcdefg")))
    assert len(largo.afirmaciones_sin_fuente) == 5
    sin_lista = {k: w for k, w in _salida_del_juez().items() if k != "afirmaciones_sin_fuente"}
    assert Veredicto.model_validate(sin_lista).afirmaciones_sin_fuente == []  # antes de v3

    mensaje = AIMessage(content=json.dumps(_salida_del_juez(afirmaciones_sin_fuente=lista)))
    mensaje.usage_metadata = {"input_tokens": 10, "output_tokens": 5, "total_tokens": 15}
    calificacion = Juez(Settings(_env_file=None), ModeloFalso([mensaje])).calificar(
        caso_del_ensayo(ESCENARIO, ensayo())
    )
    assert calificacion.veredicto.alucinacion and not calificacion.alucinacion_marcada
