"""B9: la API con el cliente de pruebas de FastAPI, sin red (sección 8.9).

El grafo usa los agentes simulados de B4 o los reales con el modelo falso; el almacén, SQLite en
memoria; el checkpointer, `MemorySaver`. El reloj de la API queda fijo en un jueves hábil a las
10:00, y los escenarios de horario lo cambian con `X-Reloj-Simulado` (modo de evaluación).
"""

import os
import time
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig

from src.agents.clasificador import ClasificadorLLM
from src.agents.dependencias import ConfigGrafo, Dependencias
from src.agents.graph import construir_grafo
from src.agents.nodes.escalamiento import AVISO_TRANSFERENCIA
from src.api.acceso import emitir_token, validar_token
from src.api.app import crear_app
from src.api.esquemas import AVISO_IA
from src.api.servicios import ServiciosAPI
from src.api.turno import AVISO_MODO_HUMANO
from src.config import Settings
from src.data.adapter import MENSAJE_PREDIO_INACCESIBLE
from src.data.memoria import RealSitEnMemoria
from src.integrations.recuperador import RecuperadorEnMemoria
from src.services.horario import RelojFijo
from src.store.almacen import Almacen, crear_motor
from tests.modelo_falso import ModeloFalso, final, pide, salida

BOGOTA = ZoneInfo("America/Bogota")
JUEVES = datetime(2026, 10, 1, 10, 0, tzinfo=BOGOTA)
U01, U03 = "CC-1000000001", "CC-1000000003"
P03, AJENO, INEXISTENTE = "50C-9000301", "50C-9000201", "50C-9999999"
ORIGEN = "http://localhost:5173"
TOKEN_FUNCIONARIO, TOKEN_ADMIN = "token-funcionario-de-prueba", "token-admin-de-prueba"


def configuracion(**cambios: Any) -> Settings:
    valores: dict[str, Any] = {
        "realtix_anthropic_api_key": "clave-de-prueba",
        "openai_api_key": "clave-de-prueba",
        "database_url": "sqlite+pysqlite:///:memory:",
        "ovt_hmac_secret": "secreto-de-prueba",
        "token_funcionario": TOKEN_FUNCIONARIO,
        "token_admin": TOKEN_ADMIN,
        "cors_origenes": [ORIGEN],
        "modo_evaluacion": True,
        "fallas_inyectables": True,
        "ovt_simulada_activa": True,
        **cambios,
    }
    return Settings(_env_file=None, **valores)


def armar(
    datos_sinteticos,
    *,
    settings: Settings | None = None,
    deps_extra: dict[str, Any] | None = None,
    nodos: dict[str, Any] | None = None,
    salud: dict[str, Any] | None = None,
) -> tuple[TestClient, ServiciosAPI]:
    almacen = Almacen(crear_motor("sqlite+pysqlite:///:memory:"))
    almacen.crear_esquema()
    adaptador = RealSitEnMemoria(datos_sinteticos, registro_casos=almacen)
    deps = Dependencias(adaptador, **(deps_extra or {}))
    servicios = ServiciosAPI(
        settings=settings or configuracion(),
        almacen=almacen,
        adaptador=adaptador,
        grafo=construir_grafo(deps, nodos=nodos),
        reloj=RelojFijo(JUEVES),
        salud=salud or {},
    )
    return TestClient(crear_app(servicios)), servicios


@pytest.fixture
def api(datos_sinteticos) -> tuple[TestClient, ServiciosAPI]:
    return armar(datos_sinteticos)


def token(contribuyente: str, **kwargs: Any) -> dict[str, str]:
    secreto = configuracion().ovt_hmac_secret
    return {"Authorization": f"Bearer {emitir_token(contribuyente, secreto, **kwargs)}"}


def chat(cliente: TestClient, conv: str, mensaje: str, **cabeceras: str) -> dict[str, Any]:
    r = cliente.post(
        "/api/v1/chat/mensaje",
        json={"id_conversacion": conv, "mensaje": mensaje},
        headers=cabeceras,
    )
    assert r.status_code == 200, r.text
    return r.json()


# -- Contrato, aviso de IA y sesión ---------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.req(
    "RF-SYS-06 · Aviso de interacción con IA (provisional)",
    "RF-AUT-03 · Consultas sin autenticación",
)
def test_aviso_de_ia_solo_en_la_primera_respuesta_y_contrato_de_la_3_8(api) -> None:
    cliente, _ = api
    primera = chat(cliente, "conv-aia", "Hola, buenas tardes")
    segunda = chat(cliente, "conv-aia", "¿Qué es el predial?")
    assert primera["aviso_ia"] == AVISO_IA and segunda["aviso_ia"] is None
    assert set(primera) == {
        "id_conversacion",
        "respuesta",
        "aviso_ia",
        "interlocutor",
        "estado",
        "meta",
    }
    assert set(primera["meta"]) == {
        "categoria", "agentes_invocados", "nivel_confianza", "motivo_escalamiento", "caso_id",
        "fuentes", "contextos", "datos_extraidos", "tiempos_ms", "tokens", "modelo_por_nodo",
        "version",
    }  # fmt: skip
    assert segunda["interlocutor"] == "agente" and segunda["estado"] == "respondida"
    meta = segunda["meta"]
    assert meta["categoria"] == "ipu" and meta["version"] == "0.5.0"
    assert meta["agentes_invocados"][0] == "nodo_orquestador"
    assert meta["agentes_invocados"][-1] == "nodo_respuesta"
    assert meta["tiempos_ms"]["total"] >= meta["tiempos_ms"]["nodo_orquestador"] >= 0


@pytest.mark.unit
@pytest.mark.req("RF-AUT-04 · Aviso de sesión requerida", "RF-AUT-01 · Verificación de identidad")
@pytest.mark.parametrize(
    "cabeceras",
    [
        {},
        {"Authorization": "Bearer no-es-un-token"},
        {"Authorization": "Basic abc"},
        token(U03, ahora=time.time() - 3 * 3600),  # vencido
        {"Authorization": token(U03)["Authorization"][:-2] + "xx"},  # firma alterada
    ],
    ids=["sin-token", "basura", "otro-esquema", "vencido", "alterado"],
)
def test_sin_sesion_o_con_token_invalido_una_consulta_personal_pide_sesion(api, cabeceras) -> None:
    cliente, _ = api
    r = chat(cliente, "conv-sin-sesion", "¿Cuánto debo de mi predio?", **cabeceras)
    assert r["estado"] == "aviso_sesion" and "iniciar sesión" in r["respuesta"]


@pytest.mark.unit
@pytest.mark.req("RF-AUT-01 · Verificación de identidad")
def test_token_firmado_con_vencimiento_de_dos_horas() -> None:
    secreto = configuracion().ovt_hmac_secret
    t = emitir_token(U03, secreto, ahora=1_000_000)
    assert validar_token(t, secreto, ahora=1_000_000 + 7199) == U03
    assert validar_token(t, secreto, ahora=1_000_000 + 7200) is None
    assert (
        validar_token(t, configuracion(ovt_hmac_secret="otro").ovt_hmac_secret, 1_000_001) is None
    )
    assert validar_token("a.b.c", secreto) is None


@pytest.mark.unit
@pytest.mark.req("RF-AUT-02 · Restricción a predios propios", "RF-UI-02 · Contexto de la sesión")
def test_predio_propio_ajeno_e_inexistente_por_el_chat(api) -> None:
    cliente, _ = api
    propio = chat(cliente, "conv-u03", f"¿Cuánto debo de mi predio {P03}?", **token(U03))
    assert propio["estado"] == "respondida" and propio["meta"]["categoria"] == "ipu"
    ajeno = chat(
        cliente, "conv-u03-b", f"Dame el estado de cuenta del predio {AJENO}", **token(U03)
    )
    nada = chat(
        cliente, "conv-u03-c", f"Dame el estado de cuenta del predio {INEXISTENTE}", **token(U03)
    )
    for r in (ajeno, nada):
        assert r["estado"] == "rechazo_acceso" and r["respuesta"] == MENSAJE_PREDIO_INACCESIBLE
        assert r["meta"]["caso_id"] is None


@pytest.mark.unit
@pytest.mark.req(
    "RF-AUT-02 · Restricción a predios propios", "RNF-03 · Protección de datos personales"
)
@pytest.mark.parametrize("ruta", ["estado-cuenta", "pagos"])
def test_puntos_de_acceso_de_predios(api, ruta) -> None:
    cliente, _ = api
    assert cliente.get(f"/api/v1/predios/{P03}/{ruta}").status_code == 401
    propio = cliente.get(f"/api/v1/predios/{P03}/{ruta}", headers=token(U03))
    assert propio.status_code == 200
    assert U03 not in propio.text and "Usuario de Prueba" not in propio.text
    ajeno = cliente.get(f"/api/v1/predios/{AJENO}/{ruta}", headers=token(U03))
    nada = cliente.get(f"/api/v1/predios/{INEXISTENTE}/{ruta}", headers=token(U03))
    assert ajeno.status_code == nada.status_code == 404
    assert ajeno.json() == nada.json() == {"detalle": MENSAJE_PREDIO_INACCESIBLE}


@pytest.mark.unit
@pytest.mark.req("RF-AUT-01 · Verificación de identidad", "RNF-03 · Protección de datos personales")
def test_una_conversacion_no_se_comparte_entre_sesiones(api) -> None:
    cliente, _ = api
    chat(cliente, "conv-dueno", "Hola", **token(U01))
    for cabeceras in (token(U03), {}):
        r = cliente.post(
            "/api/v1/chat/mensaje",
            json={"id_conversacion": "conv-dueno", "mensaje": "Hola"},
            headers=cabeceras,
        )
        assert r.status_code == 403 and "otra sesión" in r.json()["detalle"]
    # Una conversación que empezó sin sesión pasa al contribuyente que inicia sesión.
    chat(cliente, "conv-sin-dueno", "Hola")
    assert chat(cliente, "conv-sin-dueno", "¿Qué es el predial?", **token(U01))["estado"]
    assert cliente.get("/api/v1/chat/conv-sin-dueno/mensajes").status_code == 403


# -- Horario --------------------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.req("RNF-06 · Horario de atención", "RNF-07 · Aviso fuera de horario")
@pytest.mark.parametrize(
    ("reloj", "apertura"),
    [
        ("2026-10-04T10:00:00-05:00", "lunes 5 de octubre de 2026 a las 8:00 a. m."),  # HOR-01
        ("2026-10-12T10:00:00-05:00", "martes 13 de octubre de 2026 a las 8:00 a. m."),  # HOR-02
    ],
    ids=["HOR-01-domingo", "HOR-02-festivo"],
)
def test_fuera_de_horario_no_responde_ni_transfiere(api, reloj, apertura) -> None:
    cliente, servicios = api
    cabeceras = {"X-Reloj-Simulado": reloj, "X-Escenario-Id": "HOR-01", **token(U01)}
    r = chat(cliente, "conv-hor", "Hola, necesito hablar con un funcionario", **cabeceras)
    assert r["estado"] == "fuera_de_horario" and r["interlocutor"] == "sistema"
    assert (
        apertura in r["respuesta"]
        and "no puedo responder consultas ni transferirlas" in r["respuesta"]
    )
    assert r["aviso_ia"] == AVISO_IA  # la primera respuesta, aunque sea fuera de horario
    assert r["meta"]["agentes_invocados"] == [] and r["meta"]["caso_id"] is None
    boton = cliente.post(
        "/api/v1/escalamiento", json={"id_conversacion": "conv-hor"}, headers=cabeceras
    )
    assert boton.json()["estado"] == "fuera_de_horario" and boton.json()["aviso_ia"] is None
    assert servicios.almacen.listar_casos() == []
    assert servicios.almacen.estado_conversacion("conv-hor") == "activa"
    assert (
        cliente.get("/api/v1/chat/conv-hor/mensajes", headers=token(U01)).json()["mensajes"] == []
    )
    (fila, _) = servicios.almacen.interacciones("conv-hor")
    assert fila["estado"] == "fuera_de_horario" and fila["escenario_id"] == "HOR-01"


@pytest.mark.unit
@pytest.mark.req("RNF-06 · Horario de atención")
def test_sin_modo_de_evaluacion_las_cabeceras_de_prueba_se_ignoran(
    datos_sinteticos, entorno_limpio
) -> None:
    ajustes = Settings(_env_file=None, **{
        k: v for k, v in configuracion().model_dump().items()
        if k not in ("modo_evaluacion", "fallas_inyectables", "ovt_simulada_activa")
    })  # fmt: skip
    assert not ajustes.modo_evaluacion and not ajustes.fallas_inyectables
    assert not ajustes.ovt_simulada_activa
    cliente, servicios = armar(datos_sinteticos, settings=ajustes)
    cabeceras = {"X-Reloj-Simulado": "2026-10-04T10:00:00-05:00", "X-Escenario-Id": "HOR-01",
                 "X-Falla-Inyectada": "orquestador:error"}  # fmt: skip
    r = chat(cliente, "conv-normal", "¿Qué es el predial?", **cabeceras)
    assert r["estado"] == "respondida"  # el reloj de la API (jueves) y sin falla
    assert servicios.almacen.interacciones("conv-normal")[0]["escenario_id"] is None
    assert r["meta"]["contextos"] is None
    assert cliente.post("/api/v1/ovt-simulada/sesion", json={"usuario": "U01"}).status_code == 404


# -- Escalamiento, modo humano y bandeja -----------------------------------------------------------


def _sin_modelo(texto: str, state: Any) -> Any:
    raise AssertionError("El botón no debe llamar al modelo del orquestador")


@pytest.mark.unit
@pytest.mark.req(
    "RF-ESC-02 · Activación del escalamiento", "RF-ESC-05 · Notificación al contribuyente"
)
def test_boton_modo_humano_y_bandeja(datos_sinteticos) -> None:
    cliente, servicios = armar(datos_sinteticos, deps_extra={"clasificador": _sin_modelo})
    r = cliente.post(
        "/api/v1/escalamiento", json={"id_conversacion": "conv-boton"}, headers=token(U01)
    )
    datos = r.json()
    assert (
        datos["estado"] == "escalada"
        and datos["meta"]["motivo_escalamiento"] == "solicitud explícita"
    )
    assert (
        datos["meta"]["caso_id"] == "CASO-conv-boton" and AVISO_TRANSFERENCIA in datos["respuesta"]
    )
    # El prefacio no repite «funcionario» (revisión externa de B11).
    assert datos["respuesta"] == f"Con gusto. {AVISO_TRANSFERENCIA}"
    assert datos["respuesta"].count("funcionario") == 1
    assert datos["meta"]["nivel_confianza"] == 0.0  # ADR-13
    # Modo humano (ADR-12): los agentes ya no responden y el mensaje queda en el caso.
    siguiente = chat(cliente, "conv-boton", "¿Ya me van a atender?", **token(U01))
    assert siguiente["interlocutor"] == "sistema" and siguiente["estado"] == "escalada"
    assert siguiente["respuesta"] == AVISO_MODO_HUMANO
    assert siguiente["meta"]["agentes_invocados"] == []
    assert [m["texto"] for m in servicios.almacen.mensajes_del_caso("CASO-conv-boton")] == [
        "¿Ya me van a atender?"
    ]
    mensajes = cliente.get("/api/v1/chat/conv-boton/mensajes?desde=1", headers=token(U01)).json()
    assert mensajes["estado"] == "escalada" and mensajes["siguiente"] == 3
    assert [m["autor"] for m in mensajes["mensajes"]] == ["agente", "contribuyente"]
    # Bandeja de solo lectura, con token de funcionario.
    for cabeceras in (
        {},
        {"Authorization": "Bearer otro"},
        {"Authorization": f"Bearer {TOKEN_ADMIN}"},
    ):
        assert cliente.get("/api/v1/escalamiento/casos", headers=cabeceras).status_code == 401
    funcionario = {"Authorization": f"Bearer {TOKEN_FUNCIONARIO}"}
    (caso,) = cliente.get("/api/v1/escalamiento/casos", headers=funcionario).json()
    assert caso["motivo"] == "solicitud explícita" and caso["estado"] == "abierto"
    detalle = cliente.get("/api/v1/escalamiento/casos/CASO-conv-boton", headers=funcionario).json()
    assert detalle["resumen_estructurado"]["motivo"] == "solicitud explícita"
    assert detalle["mensajes"][-1]["texto"] == "¿Ya me van a atender?"
    assert cliente.get("/api/v1/escalamiento/casos/CASO-x", headers=funcionario).status_code == 404


# -- Fallas: nunca un error técnico ----------------------------------------------------------------


def _orquestador_llm(*respuestas: AIMessage) -> ClasificadorLLM:
    return ClasificadorLLM(ModeloFalso(list(respuestas)), timeout_s=5)


def _clasificacion(categoria: str, texto: str, personal: bool = True) -> AIMessage:
    return salida(
        partes=[{"categoria": categoria, "texto": texto, "busqueda": texto}],
        consulta_personal=personal, solicitud_explicita=False, pregunta_ia=False,
        tributario_fuera_mvp=False, municipio_distinto=False, no_tributario=False,
    )  # fmt: skip


@pytest.mark.unit
@pytest.mark.req("RNF-08 · Tiempos de espera y degradación")
def test_rob_01_falla_inyectada_del_orquestador(datos_sinteticos) -> None:
    texto = f"¿Cuánto debo de mi predio {P03}?"
    clasificador = _orquestador_llm(_clasificacion("ipu", texto))
    cliente, _ = armar(datos_sinteticos, deps_extra={"clasificador": clasificador})
    r = chat(
        cliente, "conv-rob1", texto, **token(U03), **{"X-Falla-Inyectada": "orquestador:tiempo"}
    )
    assert r["estado"] == "escalada" and r["meta"]["motivo_escalamiento"] == "fallo de servicio"
    assert "funcionario" in r["respuesta"] and "2.135.000" not in r["respuesta"]
    assert "Timeout" not in r["respuesta"] and "Error" not in r["respuesta"]


@pytest.mark.unit
@pytest.mark.req("RNF-08 · Tiempos de espera y degradación")
def test_rob_02_falla_inyectada_del_adaptador(datos_sinteticos) -> None:
    texto = f"Quiero ver el estado de cuenta de mi predio {P03}"
    clasificador = _orquestador_llm(_clasificacion("ipu", texto))
    agente = ModeloFalso(
        [pide(("estado_cuenta_predial", {"matricula": P03})), final("No uses esto")]
    )
    cliente, _ = armar(
        datos_sinteticos,
        deps_extra={"clasificador": clasificador, "modelos": lambda _n: agente,
                    "recuperador": RecuperadorEnMemoria()},
    )  # fmt: skip
    r = chat(cliente, "conv-rob2", texto, **token(U03), **{"X-Falla-Inyectada": "adaptador:tiempo"})
    assert r["estado"] == "escalada" and r["meta"]["motivo_escalamiento"] == "fallo de servicio"
    assert "2.135.000" not in r["respuesta"]


@pytest.mark.unit
@pytest.mark.req("RNF-08 · Tiempos de espera y degradación")
@pytest.mark.parametrize("registro_falla", [False, True])
def test_el_contribuyente_nunca_ve_un_error_tecnico(datos_sinteticos, registro_falla) -> None:
    def nodo_roto(state: Any) -> Any:
        raise RuntimeError("psycopg.OperationalError: conexión perdida")

    cliente, servicios = armar(datos_sinteticos, nodos={"nodo_respuesta": nodo_roto})
    if registro_falla:
        servicios.adaptador.registrar_caso_escalado = lambda caso: (_ for _ in ()).throw(OSError())
    r = chat(cliente, "conv-roto", "¿Qué es el predial?")
    assert r["estado"] == "escalada" and r["meta"]["motivo_escalamiento"] == "fallo de servicio"
    assert "psycopg" not in r["respuesta"] and AVISO_TRANSFERENCIA in r["respuesta"]
    assert r["meta"]["caso_id"] == (None if registro_falla else "CASO-conv-roto")


@pytest.mark.unit
@pytest.mark.req("RNF-08 · Tiempos de espera y degradación")
def test_errores_de_formato_y_rutas_en_espanol_sin_detalles(api) -> None:
    cliente, _ = api
    r = cliente.post("/api/v1/chat/mensaje", json={"id_conversacion": "x y", "mensaje": ""})
    assert (
        r.status_code == 422 and set(r.json()) == {"detalle"} and "formato" in r.json()["detalle"]
    )
    assert set(cliente.get("/api/v1/no-existe").json()) == {"detalle"}


# -- Anonimizador, fuentes, tokens y modo de evaluación --------------------------------------------


@pytest.mark.unit
@pytest.mark.req("RNF-03 · Protección de datos personales", "RNF-05 · Registro auditable")
def test_el_nombre_de_la_sesion_no_llega_a_los_modelos(datos_sinteticos) -> None:
    texto = "hola, usuario de prueba 01 por acá. ¿qué es el predial?"
    orquestador = ModeloFalso([_clasificacion("ipu", texto, personal=False)])
    # El agente de IPU tiene herramientas: llamada 1 sin pedirlas y llamada 2 con el JSON.
    agente = ModeloFalso(
        [AIMessage("Es un impuesto."), final("Es un impuesto.", fragmentos_citados=[1])]
    )
    cliente, _ = armar(
        datos_sinteticos,
        deps_extra={"clasificador": ClasificadorLLM(orquestador, timeout_s=5),
                    "modelos": lambda _n: agente, "recuperador": RecuperadorEnMemoria(),
                    # El recuperador en memoria no da cosenos: la confianza no se mide aquí.
                    "config": ConfigGrafo(umbral_confianza=0.0), "modo_evaluacion": True},
    )  # fmt: skip
    r = chat(cliente, "conv-nombre", texto, **token(U01))
    assert r["estado"] == "respondida", r["meta"]
    for modelo in (orquestador, agente):
        enviado = modelo.texto_enviado().lower()
        assert "usuario de prueba 01" not in enviado and "[nombre]" in enviado
    fuente = r["meta"]["fuentes"][0]
    assert set(fuente) == {"norma", "articulo", "coleccion", "puntaje"}
    assert fuente["coleccion"] == "normativa_ipu" and isinstance(fuente["puntaje"], float)
    assert r["meta"]["contextos"]  # modo de evaluación: los textos de los fragmentos (RAGAS)


@pytest.mark.unit
@pytest.mark.req("RF-AUT-01 · Verificación de identidad")
def test_ovt_simulada_emite_la_sesion_de_un_usuario_de_prueba(api) -> None:
    cliente, servicios = api
    usuarios = cliente.get("/api/v1/ovt-simulada/usuarios").json()
    assert {
        "usuario": "U01",
        "nombre": "Usuario de Prueba 01",
        "tipo_persona": "natural",
    } in usuarios
    sesion = cliente.post("/api/v1/ovt-simulada/sesion", json={"usuario": "U03"}).json()
    assert validar_token(sesion["token"], servicios.settings.ovt_hmac_secret) == U03
    assert sesion["expira_en_s"] == 7200
    assert cliente.post("/api/v1/ovt-simulada/sesion", json={"usuario": "U99"}).status_code == 404


# -- Documento -------------------------------------------------------------------------------------

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


@pytest.mark.unit
@pytest.mark.req("RF-OCR-01 · Carga de archivos", "RF-UI-04 · Carga desde la conversación")
def test_documento_validado_procesado_y_borrado(datos_sinteticos) -> None:
    vistos: list[str] = []

    def nodo_ocr(state: Any) -> Any:
        ruta = state["documento_adjunto"]["ruta"]
        assert os.path.exists(ruta)
        vistos.append(ruta)
        return {"respuestas_parciales": [{"categoria": "ocr", "texto": "Leí el recibo.",
                                           "fuentes": [], "similitud": None,
                                           "suficiencia": "completa", "cobertura": 1.0,
                                           "rechazo_acceso": False, "fallo_servicio": False,
                                           "fuera_de_alcance": False}]}  # fmt: skip

    cliente, _ = armar(
        datos_sinteticos,
        settings=configuracion(tamano_maximo_archivo_mb=1),
        nodos={"nodo_ocr": nodo_ocr},
    )

    def subir(nombre: str, contenido: bytes, conv: str = "conv-doc") -> Any:
        return cliente.post(
            "/api/v1/chat/documento",
            data={"id_conversacion": conv, "mensaje": "Te envío mi recibo"},
            files={"archivo": (nombre, contenido, "image/png")},
            headers=token(U03),
        )

    r = subir("recibo.png", PNG)
    assert r.status_code == 200 and r.json()["meta"]["agentes_invocados"][1] == "nodo_ocr"
    assert vistos and not os.path.exists(vistos[0])  # se borró al terminar
    falso = subir("recibo.png", b"GIF89a" + b"\x00" * 10)  # la extensión no basta
    assert falso.status_code == 415 and "JPG, PNG o PDF" in falso.json()["respuesta"]
    grande = subir("recibo.png", PNG + b"\x00" * (1024 * 1024))
    assert grande.status_code == 413 and grande.json()["estado"] == "aclaracion"
    fuera = cliente.post(
        "/api/v1/chat/documento",
        data={"id_conversacion": "conv-doc-2"},
        files={"archivo": ("r.pdf", b"%PDF-1.7\n", "application/pdf")},
        headers={**token(U03), "X-Reloj-Simulado": "2026-10-04T10:00:00-05:00"},
    )
    assert fuera.json()["estado"] == "fuera_de_horario" and len(vistos) == 1


# -- Métricas, salud, CORS y cabeceras -------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.req(
    "RF-OBS-02 · Matriz de confusión de enrutamiento", "RF-OBS-03 · Métricas de precisión y tiempo"
)
def test_metricas_con_token_de_administrador(api) -> None:
    cliente, _ = api
    chat(
        cliente,
        "conv-m1",
        "¿Qué es el impuesto predial unificado y cómo se calcula?",
        **{"X-Escenario-Id": "IPU-04"},
    )
    chat(
        cliente,
        "conv-m2",
        "¿Qué es el impuesto de industria y comercio y quién lo paga?",
        **{"X-Escenario-Id": "ICA-01"},
    )
    assert cliente.get("/api/v1/admin/metricas").status_code == 401
    assert (
        cliente.get(
            "/api/v1/admin/metricas", headers={"Authorization": f"Bearer {TOKEN_FUNCIONARIO}"}
        ).status_code
        == 401
    )
    m = cliente.get(
        "/api/v1/admin/metricas", headers={"Authorization": f"Bearer {TOKEN_ADMIN}"}
    ).json()
    assert m["turnos_etiquetados"] == 2
    assert (
        m["matriz_de_confusion"]["ipu"]["ipu"] == 1 and m["matriz_de_confusion"]["ica"]["ica"] == 1
    )
    assert m["por_categoria"]["ipu"]["f1"] == 1.0 and m["tiempos_ms"]["mediana"] is not None


@pytest.mark.unit
@pytest.mark.req("RNF-08 · Tiempos de espera y degradación")
def test_health_con_dependencias(datos_sinteticos) -> None:
    def falla() -> None:
        raise ConnectionError("chroma:8000 con la clave secreta")

    cliente, _ = armar(datos_sinteticos, salud={"postgres": lambda: None, "chroma": falla})
    r = cliente.get("/health")
    assert r.status_code == 503
    assert r.json() == {"estado": "degradado", "version": "0.5.0",
                        "dependencias": {"postgres": "ok", "chroma": "falla"}}  # fmt: skip
    sano, _ = armar(datos_sinteticos, salud={"postgres": lambda: None})
    assert sano.get("/health").status_code == 200


@pytest.mark.unit
@pytest.mark.req("RNF-03 · Protección de datos personales")
def test_cors_y_cabeceras_de_seguridad(api) -> None:
    cliente, _ = api
    permitido = cliente.options(
        "/api/v1/chat/mensaje",
        headers={"Origin": ORIGEN, "Access-Control-Request-Method": "POST",
                 "Access-Control-Request-Headers": "authorization,content-type"},
    )  # fmt: skip
    assert permitido.headers["access-control-allow-origin"] == ORIGEN
    ajeno = cliente.options(
        "/api/v1/chat/mensaje",
        headers={"Origin": "https://otro.example", "Access-Control-Request-Method": "POST"},
    )
    assert "access-control-allow-origin" not in ajeno.headers
    r = cliente.get("/health")
    assert r.headers["content-security-policy"] == f"default-src 'none'; frame-ancestors {ORIGEN}"
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["referrer-policy"] == "no-referrer"


# -- Hallazgos de la revisión independiente --------------------------------------------------


@pytest.mark.unit
@pytest.mark.req("RF-ESC-05 · Notificación al contribuyente", "RNF-07 · Aviso fuera de horario")
def test_en_una_conversacion_escalada_el_mensaje_fuera_de_horario_queda_en_el_caso(api) -> None:
    cliente, servicios = api
    cliente.post("/api/v1/escalamiento", json={"id_conversacion": "conv-noche"}, headers=token(U01))
    domingo = {"X-Reloj-Simulado": "2026-10-04T21:00:00-05:00", **token(U01)}
    r = chat(cliente, "conv-noche", "¿Siguen ahí?", **domingo)
    assert r["estado"] == "fuera_de_horario"
    assert [m["texto"] for m in servicios.almacen.mensajes_del_caso("CASO-conv-noche")] == [
        "¿Siguen ahí?"
    ]


@pytest.mark.unit
@pytest.mark.req(
    "RNF-08 · Tiempos de espera y degradación", "RF-AUT-01 · Verificación de identidad"
)
def test_si_el_adaptador_no_responde_al_cargar_la_sesion_hay_aviso_y_no_error(api) -> None:
    cliente, servicios = api

    def caido(_: str) -> Any:
        raise ConnectionError("adaptador caído")

    servicios.adaptador.get_predios_contribuyente = caido
    r = chat(cliente, "conv-caida", "¿Cuánto debo?", **token(U03))
    assert r["estado"] == "aviso_sesion" and "no pude verificar tu sesión" in r["respuesta"]
    assert r["aviso_ia"] == AVISO_IA and servicios.almacen.estado_conversacion("conv-caida") is None
    predio = cliente.get(f"/api/v1/predios/{P03}/pagos", headers=token(U03))
    assert predio.status_code == 503 and "sesión" in predio.json()["detalle"]


@pytest.mark.unit
@pytest.mark.req("RNF-08 · Tiempos de espera y degradación")
def test_errores_de_ruta_y_500_en_espanol_con_cabeceras(api) -> None:
    cliente, servicios = api
    assert cliente.get("/api/v1/no-existe").json() == {"detalle": "No encontré lo que buscas."}
    assert cliente.get("/api/v1/chat/mensaje").json() == {
        "detalle": "Esa ruta no acepta este método."
    }
    assert "content-security-policy" not in cliente.get("/docs").headers  # Swagger UI carga

    def roto(*_: Any) -> Any:
        raise RuntimeError("psycopg: detalle interno")

    servicios.adaptador.get_estado_cuenta = roto
    sin_excepciones = TestClient(cliente.app, raise_server_exceptions=False)
    r = sin_excepciones.get(
        f"/api/v1/predios/{P03}/estado-cuenta", headers={**token(U03), "Origin": ORIGEN}
    )
    assert r.status_code == 500 and "psycopg" not in r.text
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["access-control-allow-origin"] == ORIGEN


@pytest.mark.unit
@pytest.mark.req(
    "RF-OCR-01 · Carga de archivos", "RF-SYS-06 · Aviso de interacción con IA (provisional)"
)
def test_el_rechazo_del_recibo_abre_la_conversacion_con_el_aviso_de_ia(api) -> None:
    cliente, servicios = api
    r = cliente.post(
        "/api/v1/chat/documento",
        data={"id_conversacion": "conv-gif"},
        files={"archivo": ("r.png", b"GIF89a", "image/png")},
        headers=token(U03),
    )
    assert r.status_code == 415 and r.json()["aviso_ia"] == AVISO_IA
    assert servicios.almacen.contribuyente_de_conversacion("conv-gif") == U03


@pytest.mark.unit
@pytest.mark.req("RF-OBS-01 · Traza del flujo entre agentes", "RNF-05 · Registro auditable")
def test_langsmith_con_anonimizador_y_metadatos_sin_contribuyente(datos_sinteticos) -> None:
    from langchain_core.tracers.langchain import LangChainTracer

    from src.integrations.trazas import Anonimizador

    vistos: list[dict[str, Any]] = []

    def nodo_general(state: Any, config: RunnableConfig) -> Any:
        vistos.append(dict(config.get("metadata", {})))
        parcial = {"categoria": "general", "texto": "Hola.", "fuentes": [], "similitud": None,
                   "suficiencia": "completa", "cobertura": 1.0, "rechazo_acceso": False,
                   "fallo_servicio": False, "fuera_de_alcance": False}  # fmt: skip
        return {"respuestas_parciales": [parcial]}

    apagado, servicios_apagados = armar(datos_sinteticos)
    assert servicios_apagados.trazadores() == []
    cliente, servicios = armar(
        datos_sinteticos,
        settings=configuracion(langsmith_tracing=True, langsmith_api_key="clave-de-prueba"),
        nodos={"nodo_general": nodo_general},
    )
    (trazador,) = servicios.trazadores()
    assert isinstance(trazador, LangChainTracer)
    assert isinstance(trazador.client._hide_inputs, Anonimizador)
    assert isinstance(trazador.client._hide_outputs, Anonimizador)
    servicios.trazadores = lambda: []  # sin red en la prueba
    chat(cliente, "conv-traza", "Hola", **token(U01), **{"X-Escenario-Id": "AIA-01"})
    assert vistos[0]["id_conversacion"] == "conv-traza" and vistos[0]["escenario_id"] == "AIA-01"
    assert vistos[0]["version"] == "0.5.0" and U01 not in str(vistos[0])
