"""Ejecutor, evaluadores de código y juez de B12, sin red: API y modelo falsos."""

import json
from pathlib import Path
from typing import Any

import pytest
from langchain_core.messages import AIMessage

from src.evaluacion.corrida import calificar, metricas_por_conjunto, vigentes
from src.evaluacion.ejecutor import Ejecutor, leer_resultados, tokens_por_modelo
from src.evaluacion.escenarios import DIR_ESCENARIOS, cargar_escenarios
from src.evaluacion.evaluadores_codigo import evaluar_codigo, revela_instrucciones, verificar
from src.evaluacion.juez import Juez, caso_del_ensayo, huella_del_juez, superado
from tests.modelo_falso import ModeloFalso

OBS05 = "RF-OBS-05 · Ejecución repetible de pruebas"
RNF16 = "RNF-16 · Tasa de respuestas correctas"
RNF05 = "RNF-05 · Registro auditable"


class Respuesta:
    def __init__(self, codigo: int, datos: dict[str, Any]) -> None:
        self.status_code = codigo
        self._datos = datos

    def json(self) -> dict[str, Any]:
        return self._datos


class APIFalsa:
    """Registra cada llamada y contesta con un guion por ruta."""

    def __init__(self, respuestas: list[dict[str, Any]]) -> None:
        self.respuestas = list(respuestas)
        self.llamadas: list[tuple[str, dict[str, Any]]] = []

    def post(self, url: str, **kwargs: Any) -> Respuesta:
        self.llamadas.append((url, kwargs))
        if url.endswith("/ovt-simulada/sesion"):
            return Respuesta(200, {"token": f"tok-{kwargs['json']['usuario']}"})
        return Respuesta(200, self.respuestas.pop(0))


def chat(respuesta: str, estado: str = "respondida", **meta: Any) -> dict[str, Any]:
    return {
        "respuesta": respuesta,
        "estado": estado,
        "aviso_ia": None,
        "interlocutor": "agente",
        "meta": {"tiempos_ms": {"total": 4000}, **meta},
    }


def escenario(id_: str) -> dict[str, Any]:
    return next(e for e in cargar_escenarios(DIR_ESCENARIOS) if e["id"] == id_)


@pytest.mark.unit
@pytest.mark.req(OBS05, "RNF-08 · Tiempos de espera y degradación")
def test_ejecutor_manda_reloj_escenario_falla_y_sesion() -> None:
    api = APIFalsa([chat("Te transfiero con un funcionario.", "escalada")])
    ensayo = Ejecutor(api, "prueba").correr_ensayo(escenario("ROB-01"))
    url, kwargs = api.llamadas[-1]
    assert url == "/api/v1/chat/mensaje"
    assert kwargs["headers"]["X-Escenario-Id"] == "ROB-01"
    assert kwargs["headers"]["X-Reloj-Simulado"] == "2026-10-01T10:00:00-05:00"
    assert kwargs["headers"]["X-Falla-Inyectada"] == "orquestador:tiempo"
    assert kwargs["headers"]["Authorization"] == "Bearer tok-U03"
    assert ensayo["error"] is None and ensayo["turnos"][0]["latencia_servidor_ms"] == 4000


@pytest.mark.unit
@pytest.mark.req(OBS05, "RF-OCR-01 · Carga de archivos")
def test_ejecutor_sube_el_recibo_y_mantiene_la_conversacion(tmp_path: Path) -> None:
    (tmp_path / "recibo_valido_U03.png").write_bytes(b"\x89PNG falso")
    api = APIFalsa([chat("¿Es correcto?", "aclaracion"), chat("Los datos coinciden.")])
    ensayo = Ejecutor(api, "prueba", dir_recibos=tmp_path).correr_ensayo(escenario("OCR-07"))
    (url1, k1), (url2, k2) = [c for c in api.llamadas if "/chat/" in c[0]]
    assert url1 == "/api/v1/chat/documento" and url2 == "/api/v1/chat/mensaje"
    assert k1["files"]["archivo"][1] == b"\x89PNG falso"
    assert k1["data"]["id_conversacion"] == k2["json"]["id_conversacion"]
    assert "X-Falla-Inyectada" not in k1["headers"]
    assert [t["estado"] for t in ensayo["turnos"]] == ["aclaracion", "respondida"]


@pytest.mark.unit
@pytest.mark.req(OBS05)
def test_sin_sesion_y_con_token_invalido() -> None:
    api = APIFalsa([chat("a"), chat("b")])
    ejecutor = Ejecutor(api, "prueba")
    ejecutor.correr_ensayo(escenario("ACC-02"))
    ejecutor.correr_ensayo(escenario("ACC-03"))
    cabeceras = [k["headers"] for u, k in api.llamadas if "/chat/" in u]
    assert "Authorization" not in cabeceras[0]
    assert cabeceras[1]["Authorization"] == "Bearer token-invalido-de-prueba"


@pytest.mark.unit
@pytest.mark.req(OBS05)
def test_un_error_de_red_queda_en_el_ensayo_y_se_reanuda(tmp_path: Path) -> None:
    class Caida(APIFalsa):
        def post(self, url: str, **kwargs: Any) -> Respuesta:
            raise ConnectionError("sin red")

    salida = tmp_path / "resultados.jsonl"
    esc = escenario("GEN-01")
    Ejecutor(Caida([]), "prueba").correr([esc], k=2, salida=salida)
    assert all(r["error"].startswith("ConnectionError") for r in leer_resultados(salida))
    Ejecutor(APIFalsa([chat("x"), chat("y")]), "prueba").correr([esc], k=2, salida=salida)
    assert len(leer_resultados(salida)) == 4 and not any(
        r["error"] for r in vigentes(leer_resultados(salida))
    )
    Ejecutor(Caida([]), "prueba").correr([esc], k=2, salida=salida)  # ya corridos: no llama
    assert len(leer_resultados(salida)) == 4


@pytest.mark.unit
@pytest.mark.req(OBS05)
def test_tokens_por_modelo_suma_los_turnos() -> None:
    ensayo = {
        "turnos": [
            {"meta": {"tokens_por_modelo": {"m1": {"entrada": 10, "salida": 1}}}},
            {
                "meta": {
                    "tokens_por_modelo": {
                        "m1": {"entrada": 5, "salida": 2},
                        "m2": {"entrada": 1, "salida": 1},
                    }
                }
            },
        ]
    }
    assert tokens_por_modelo(ensayo) == {
        "m1": {"entrada": 15, "salida": 3},
        "m2": {"entrada": 1, "salida": 1},
    }


def ensayo_con(*turnos: dict[str, Any]) -> dict[str, Any]:
    return {"turnos": [{"codigo_http": 200, "usuario": "?", **t} for t in turnos], "error": None}


@pytest.mark.unit
@pytest.mark.req(RNF16)
def test_verificaciones_miran_toda_la_conversacion() -> None:
    """AMB-02: la deuda sale en el primer turno y la liquidación en el segundo."""
    esc = escenario("AMB-02")
    ensayo = ensayo_con(
        {"respuesta": "Debes $5.166.000.", "estado": "respondida", "meta": {"categoria": "ipu"}},
        {
            "respuesta": "Te liquidaron $2.646.000.",
            "estado": "respondida",
            "meta": {"categoria": "ipu"},
        },
    )
    resultado = evaluar_codigo(esc, ensayo)
    assert resultado["pasa"], resultado


@pytest.mark.unit
@pytest.mark.req(RNF16)
def test_categoria_y_comportamiento_cuentan() -> None:
    esc = escenario("ICA-10")  # retención que escala, categoría ica
    escalo_en_ipu = ensayo_con(
        {
            "respuesta": "Te paso con un funcionario.",
            "estado": "escalada",
            "meta": {"categoria": "ipu", "motivo_escalamiento": "fuera de alcance"},
        }
    )
    detalle = {v["tipo"]: v["pasa"] for v in evaluar_codigo(esc, escalo_en_ipu)["verificaciones"]}
    assert detalle["categoria"] is False and detalle["comportamiento"] is True


@pytest.mark.unit
@pytest.mark.req(RNF16)
def test_categorias_y_comportamientos_aceptados_admiten_alternativas() -> None:
    """Un escenario que no mide la categoría acepta las de su lista, y nada más."""
    esc = escenario("GEN-01") | {
        "verificaciones_codigo": [{"tipo": "no_escala"}],
        "categoria_esperada": "general",
        "categorias_aceptadas": ["general", "fuera_de_alcance"],
        "comportamiento_esperado": "responder",
        "comportamientos_aceptados": ["responder", "informar_fuera_de_alcance"],
    }

    def resultado(categoria: str, estado: str) -> dict[str, bool]:
        ensayo = ensayo_con({"respuesta": "x", "estado": estado, "meta": {"categoria": categoria}})
        return {v["tipo"]: v["pasa"] for v in evaluar_codigo(esc, ensayo)["verificaciones"]}

    assert resultado("fuera_de_alcance", "fuera_de_alcance") == {
        "no_escala": True, "categoria": True, "comportamiento": True
    }  # fmt: skip
    assert resultado("general", "respondida")["comportamiento"]
    assert not resultado("ipu", "respondida")["categoria"]
    assert not resultado("general", "escalada")["comportamiento"]


@pytest.mark.unit
@pytest.mark.req(RNF16, "RF-OBS-02 · Matriz de confusión de enrutamiento")
def test_la_matriz_cuenta_una_categoria_aceptada_como_acierto() -> None:
    from src.evaluacion.corrida import _esperada

    esc = {"categoria_esperada": "general", "categorias_aceptadas": ["general", "fuera_de_alcance"]}
    assert _esperada(esc, "fuera_de_alcance") == "fuera_de_alcance"
    assert _esperada(esc, "ipu") == "general"
    assert _esperada({"categoria_esperada": "ica"}, "ipu") == "ica"


@pytest.mark.unit
@pytest.mark.req(RNF16, "RNF-08 · Tiempos de espera y degradación")
@pytest.mark.parametrize(
    ("verificacion", "turno", "pasa"),
    [
        ({"tipo": "sin_error_tecnico"}, {"respuesta": "Valor: $500.000."}, True),
        ({"tipo": "sin_error_tecnico"}, {"respuesta": "Traceback (most recent call last)"}, False),
        ({"tipo": "sin_error_tecnico"}, {"respuesta": "", "codigo_http": 500}, False),
        (
            {"tipo": "escala", "motivo": "fallo de servicio"},
            {"estado": "escalada", "meta": {"motivo_escalamiento": "fallo de servicio"}},
            True,
        ),
        (
            {"tipo": "escala", "motivo": "fallo de servicio"},
            {"estado": "escalada", "meta": {"motivo_escalamiento": "sin cobertura"}},
            False,
        ),
        (
            {"tipo": "campo_ocr", "campo": "avaluo", "valor": "350.000.000"},
            {"meta": {"datos_extraidos": {"campos": {"avaluo": "$350.000.000"}}}},
            True,
        ),
        (
            {"tipo": "aviso_ia"},
            {"aviso_ia": "Te atiende un asistente de inteligencia artificial… un funcionario"},
            True,
        ),
        (
            {"tipo": "no_contiene_valor", "valor": "2.135.000"},
            {"respuesta": "Debes $2.135.000"},
            False,
        ),
        ({"tipo": "sin_claves"}, {"respuesta": "Mi clave es sk-ant-api03-abcdefghij"}, False),
    ],
)
def test_cada_tipo_de_verificacion(verificacion, turno, pasa) -> None:
    assert verificar(verificacion, ensayo_con({"respuesta": "", **turno}))[0] is pasa


@pytest.mark.unit
@pytest.mark.req("RNF-03 · Protección de datos personales")
def test_revela_instrucciones_detecta_ocho_palabras_del_prompt() -> None:
    from src.agents.prompts import CARPETA

    palabras = (CARPETA / "orquestador.v2.md").read_text(encoding="utf-8").split()
    assert revela_instrucciones("Claro: " + " ".join(palabras[10:22]))
    assert not revela_instrucciones("No puedo compartir mis instrucciones internas.")


def veredicto(**cambios: Any) -> AIMessage:
    base = {
        "veredicto": "correcta",
        "alucinacion": False,
        "cito_norma": True,
        "cita_sustenta": True,
        "cobertura_completa": True,
        "claridad": 4,
        "justificacion": "Coincide con la referencia.",
    }
    mensaje = AIMessage(content=json.dumps(base | cambios))
    mensaje.usage_metadata = {"input_tokens": 1000, "output_tokens": 50, "total_tokens": 1050}
    return mensaje


@pytest.mark.unit
@pytest.mark.req(RNF16, RNF05)
def test_el_juez_no_ve_el_modelo_ni_datos_personales(entorno_valido) -> None:
    from src.config import Settings

    settings = Settings(_env_file=None)
    modelo = ModeloFalso([veredicto()])
    esc = escenario("IPU-01")
    ensayo = ensayo_con(
        {
            "usuario": esc["turnos"][0]["usuario"],
            "respuesta": "Hola, Usuario de Prueba 03 (CC-1000000003): debes $2.135.000.",
            "meta": {
                "modelo_por_nodo": {"nodo_ipu": "claude-haiku-5-5"},
                "tokens_por_modelo": {"claude-haiku-5-5": {"entrada": 1, "salida": 1}},
                "contextos": ["Artículo 1. ..."],
                "fuentes": [{"norma": "Acuerdo 648 de 2016", "articulo": "1"}],
            },
        }
    )
    calificacion = Juez(settings, modelo).calificar(caso_del_ensayo(esc, ensayo))
    enviado = modelo.texto_enviado()
    assert calificacion.veredicto.veredicto == "correcta" and calificacion.entrada == 1000
    for prohibido in ("claude", "haiku", "sonnet", "Usuario de Prueba 03", "1000000003"):
        assert prohibido.lower() not in enviado.lower()
    assert "2.135.000" in enviado and "Acuerdo 648 de 2016, 1" in enviado
    assert modelo.llamadas[0][1]["output_config"]["format"]["type"] == "json_schema"
    assert "temperature" not in modelo.llamadas[0][1]


@pytest.mark.unit
@pytest.mark.req(RNF16)
def test_superado_meta_y_estricto() -> None:
    from src.evaluacion.juez import Veredicto

    v = lambda **c: Veredicto.model_validate_json(veredicto(**c).content)  # noqa: E731
    assert superado(True, v()) == (True, True)
    assert superado(True, v(veredicto="parcialmente correcta")) == (True, False)
    assert superado(True, v(alucinacion=True)) == (False, False)
    assert superado(False, v()) == (False, False)
    assert superado(True, None) == (False, False)


@pytest.mark.unit
@pytest.mark.req(RNF16)
def test_la_huella_cambia_si_cambia_el_juez(entorno_valido) -> None:
    from src.config import Settings

    settings = Settings(_env_file=None)
    assert huella_del_juez(settings) == huella_del_juez(settings)
    otro = settings.model_copy(update={"modelo_juez": "claude-sonnet-5-5"})
    assert huella_del_juez(otro) != huella_del_juez(settings)


@pytest.mark.unit
@pytest.mark.req(RNF16, OBS05)
def test_calificar_guarda_el_juez_y_lo_reutiliza(entorno_valido, tmp_path: Path) -> None:
    from src.config import Settings

    settings = Settings(_env_file=None)
    esc = escenario("GEN-01")
    ensayo = {
        "escenario": "GEN-01",
        "ensayo": 1,
        "id_conversacion": "c1",
        "error": None,
        **ensayo_con({"respuesta": "x", "meta": {"categoria": "general"}}),
    }
    archivo = tmp_path / "juez.jsonl"
    modelo = ModeloFalso([veredicto(veredicto="parcialmente correcta")])
    primera = calificar({"GEN-01": esc}, [ensayo], Juez(settings, modelo), archivo)
    segunda = calificar({"GEN-01": esc}, [ensayo], None, archivo)  # sin modelo: usa lo guardado
    assert len(modelo.llamadas) == 1
    assert primera[0]["juez"] == segunda[0]["juez"]
    m = metricas_por_conjunto(segunda)
    assert m["principal"]["juez"]["parcialmente correcta"] == 1


@pytest.mark.unit
@pytest.mark.req(RNF16, "RF-OCR-04 · Rechazo de documentos ilegibles")
def test_contiene_texto_acepta_raices_y_los_valores_no() -> None:
    """Revisión de B12: OCR-04 y OCR-05 piden «desenfocad» y «recortad» (raíces)."""
    from src.agents.nodes.ocr import texto_de_rechazo
    from src.evaluacion.escenarios import contiene

    cargar_un = escenario
    for id_, problemas in (
        ("OCR-04", ["desenfocado"]),
        ("OCR-05", ["recortado", "baja_resolucion"]),
    ):
        ensayo = ensayo_con({"respuesta": texto_de_rechazo(problemas), "estado": "aclaracion"})
        verificaciones = cargar_un(id_)["verificaciones_codigo"]
        texto = [v for v in verificaciones if v["tipo"] == "contiene_texto"]
        assert all(verificar(v, ensayo)[0] for v in texto), (id_, texto)
    assert contiene("Ley 44 de 1990", "Ley 44", raiz=True)
    assert not contiene("Ley 440 de 1990", "Ley 44", raiz=True)  # termina en cifra: exige límite
    assert not contiene("$2.135.0001", "2.135.000")  # los valores siguen exigiendo los dos límites


@pytest.mark.unit
@pytest.mark.req(OBS05)
def test_el_token_de_la_sesion_se_renueva_a_la_hora(monkeypatch) -> None:
    import src.evaluacion.ejecutor as ejecutor

    reloj = {"t": 1000.0}
    monkeypatch.setattr(ejecutor.time, "monotonic", lambda: reloj["t"])
    api = APIFalsa([])
    e = Ejecutor(api, "prueba")
    e.autorizacion("U03")
    e.autorizacion("U03")
    reloj["t"] += ejecutor.RENOVAR_TOKEN_S + 1
    e.autorizacion("U03")
    assert sum(u.endswith("/ovt-simulada/sesion") for u, _ in api.llamadas) == 2


@pytest.mark.unit
@pytest.mark.req(RNF16, "RF-OCR-03 · Confirmación de datos extraídos")
def test_comportamiento_del_ocr_mira_si_quedan_datos_por_confirmar() -> None:
    from src.evaluacion.evaluadores_codigo import verificar_comportamiento

    con_datos = {
        "estado": "aclaracion",
        "meta": {"datos_extraidos": {"campos": {}, "pendiente": True}},
    }
    sin_datos = {"estado": "aclaracion", "meta": {"datos_extraidos": None}}
    assert verificar_comportamiento(escenario("OCR-01"), ensayo_con(con_datos))[0]
    assert not verificar_comportamiento(escenario("OCR-01"), ensayo_con(sin_datos))[0]
    assert verificar_comportamiento(escenario("OCR-04"), ensayo_con(sin_datos))[0]
    assert not verificar_comportamiento(escenario("OCR-04"), ensayo_con(con_datos))[0]


@pytest.mark.unit
@pytest.mark.req(RNF16)
def test_no_se_reutiliza_una_calificacion_de_otro_juez(entorno_valido, tmp_path: Path) -> None:
    from src.config import Settings

    settings = Settings(_env_file=None)
    esc = escenario("GEN-01")
    ensayo = {"escenario": "GEN-01", "ensayo": 1, "id_conversacion": "c1", "error": None,
              **ensayo_con({"respuesta": "x", "meta": {"categoria": "general"}})}  # fmt: skip
    archivo = tmp_path / "juez.jsonl"
    pagadas = []
    calificar({"GEN-01": esc}, [ensayo], Juez(settings, ModeloFalso([veredicto()])), archivo,
              huella="h1", al_juzgar=pagadas.append)  # fmt: skip
    assert len(pagadas) == 1 and leer_resultados(archivo)[0]["huella"] == "h1"
    calificar({"GEN-01": esc}, [ensayo], None, archivo, huella="h1", al_juzgar=pagadas.append)
    assert len(pagadas) == 1  # reutilizada: no se paga de nuevo
    with pytest.raises(RuntimeError, match="otro juez"):
        calificar({"GEN-01": esc}, [ensayo], None, archivo, huella="h2")
