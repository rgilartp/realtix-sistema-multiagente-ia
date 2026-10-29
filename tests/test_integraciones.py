"""Integraciones de B5 con dobles de prueba: no gastan API ni usan la red."""

import uuid
from itertools import count

import pytest
from langchain_core.messages import AIMessage
from sqlalchemy import text

from src.config import cargar_configuracion
from src.container import Contenedor
from src.data.models import CasoEscalado
from src.integrations.embeddings import DIMENSIONES, crear_embeddings
from src.integrations.modelos import crear_modelo, nombre_del_modelo, texto_de_respuesta
from src.integrations.recuperacion_hibrida import RecuperadorHibrido
from src.integrations.recuperador import RecuperadorEnMemoria
from src.integrations.robustez import ServicioNoDisponibleError, con_tiempo_y_reintento
from src.integrations.trazas import (
    Anonimizador,
    AnonimizadorDeTrazas,
    crear_cliente_langsmith,
    metadatos_de_traza,
)
from src.store.almacen import crear_motor
from tests.ayudas_postgres import exigir_postgres, url_postgres_pruebas


@pytest.fixture
def settings(entorno_valido):
    return cargar_configuracion(env_file=None)


# -- Fábrica de modelos ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.req("RF-SYS-04 · Modelo sustituible")
def test_cada_nodo_toma_su_modelo_de_la_configuracion(settings) -> None:
    assert nombre_del_modelo("orquestador", settings) == "claude-sonnet-5-5"
    for nodo in ("ipu", "ica", "general", "ocr"):
        assert nombre_del_modelo(nodo, settings) == "claude-haiku-5-5"
    assert nombre_del_modelo("juez", settings) == "claude-opus-5-5"
    with pytest.raises(ValueError):  # confianza, respuesta y escalamiento no usan modelo (ADR-03)
        nombre_del_modelo("confianza", settings)


@pytest.mark.unit
@pytest.mark.req("RNF-10 · Portabilidad del modelo")
def test_cambiar_de_modelo_es_cambiar_una_variable_de_entorno(entorno_valido) -> None:
    entorno_valido.setenv("MODELO_IPU", "claude-sonnet-5-5")
    s = cargar_configuracion(env_file=None)
    assert crear_modelo("ipu", s).model == "claude-sonnet-5-5"
    assert crear_modelo("ica", s).model == "claude-haiku-5-5"  # los demás no cambian


@pytest.mark.unit
@pytest.mark.req("RF-SYS-04 · Modelo sustituible")
def test_reglas_de_la_api_de_los_modelos_5_5(settings) -> None:
    orq = crear_modelo("orquestador", settings)
    assert orq.thinking == {"type": "between_tools"} and orq.reasoning_effort == "low"
    haiku = crear_modelo("ipu", settings)
    assert haiku.thinking == {"type": "disabled"} and haiku.reasoning_effort == "medium"
    for modelo in (orq, haiku, crear_modelo("juez", settings)):
        assert (modelo.temperature, modelo.top_p, modelo.top_k) == (None, None, None)
        assert modelo.max_retries == 1 and modelo.default_request_timeout == 20.0
        carga = modelo._get_request_payload("hola")
        assert not {"temperature", "top_p", "top_k"} & set(carga)
    assert crear_modelo("juez", settings).reasoning_effort == "medium"


@pytest.mark.unit
@pytest.mark.req("RF-SYS-04 · Modelo sustituible")
def test_la_clave_es_la_del_sistema_y_no_se_lee_anthropic_api_key(entorno_valido, settings) -> None:
    entorno_valido.setenv("ANTHROPIC_API_KEY", "clave-ajena")
    modelo = crear_modelo("ipu", settings)
    assert modelo.anthropic_api_key.get_secret_value() == "clave-de-prueba-anthropic"


@pytest.mark.unit
@pytest.mark.req("RNF-08 · Tiempos de espera y degradación")
def test_los_bloques_se_leen_por_tipo_y_la_negativa_es_una_falla() -> None:
    bloques = [
        {"type": "thinking", "thinking": "interno"},
        {"type": "text", "text": "Hola "},
        {"type": "text", "text": "mundo"},
    ]
    assert texto_de_respuesta(AIMessage(content=bloques)) == "Hola mundo"
    assert texto_de_respuesta(AIMessage(content="plano")) == "plano"
    negativa = AIMessage(content="no", response_metadata={"stop_reason": "refusal"})
    with pytest.raises(ServicioNoDisponibleError):
        texto_de_respuesta(negativa)


# -- Tiempos máximos y un reintento ---------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.req("RNF-08 · Tiempos de espera y degradación")
def test_una_falla_transitoria_se_reintenta_una_vez() -> None:
    intentos = count()

    def inestable() -> str:
        if next(intentos) == 0:
            raise ConnectionError("corte")
        return "ok"

    assert con_tiempo_y_reintento(inestable, 1.0) == "ok"


@pytest.mark.unit
@pytest.mark.req("RNF-08 · Tiempos de espera y degradación")
def test_si_el_reintento_tambien_falla_se_reporta_el_servicio_no_disponible() -> None:
    llamadas = count()

    def roto() -> None:
        next(llamadas)
        raise TimeoutError("sin respuesta")

    with pytest.raises(ServicioNoDisponibleError) as error:
        con_tiempo_y_reintento(roto, 1.0, servicio="chroma")
    assert next(llamadas) == 2 and error.value.servicio == "chroma"  # una llamada y un reintento
    assert "chroma" in str(error.value)


@pytest.mark.unit
@pytest.mark.req("RNF-08 · Tiempos de espera y degradación")
def test_el_tiempo_maximo_corta_la_espera() -> None:
    import time

    with pytest.raises(ServicioNoDisponibleError) as error:
        con_tiempo_y_reintento(lambda: time.sleep(0.5), 0.05, servicio="modelo")
    assert isinstance(error.value.causa, TimeoutError)


@pytest.mark.unit
@pytest.mark.req("RNF-08 · Tiempos de espera y degradación")
def test_un_error_que_no_es_transitorio_no_se_reintenta() -> None:
    llamadas = count()

    def mal() -> None:
        next(llamadas)
        raise ValueError("esquema inválido")

    with pytest.raises(ValueError):
        con_tiempo_y_reintento(mal, 1.0)
    assert next(llamadas) == 1


# -- Embeddings y recuperador ---------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.req("RF-SYS-04 · Modelo sustituible")
def test_el_cliente_de_embeddings_usa_3072_dimensiones(settings) -> None:
    cliente = crear_embeddings(settings)
    assert cliente.model == "text-embedding-3-large" and cliente.dimensions == DIMENSIONES == 3072
    assert cliente.max_retries == 1


@pytest.mark.unit
@pytest.mark.req("RF-SYS-04 · Modelo sustituible")
def test_recuperador_en_memoria_devuelve_fragmentos_con_su_fuente() -> None:
    recuperador = RecuperadorEnMemoria()
    fragmentos = recuperador.recuperar(
        "pronto pago del impuesto predial descuento", coleccion="normativa_ipu", k=3
    )
    assert 0 < len(fragmentos) <= 3
    assert all(f.fuente.startswith("normativa_ipu/") and 0 < f.similitud <= 1 for f in fragmentos)
    assert fragmentos == sorted(fragmentos, key=lambda f: f.similitud, reverse=True)
    assert recuperador.recuperar("¿¿??") == []
    assert all(f.fuente.startswith("normativa_ica/") for f in recuperador.recuperar(
        "tarifa industria comercio actividad", coleccion="normativa_ica")
    )  # fmt: skip


# -- Trazas y anonimizador ------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.req("RNF-05 · Registro auditable")
def test_el_anonimizador_enmascara_documentos_y_nombres_pero_no_valores() -> None:
    anonimizar = Anonimizador(nombres=["María Fernanda Gómez"])
    entrada = {
        "mensaje": "Soy María Fernanda Gómez, CC-1000000003, NIT 900.123.456-7, cédula 1020304050",
        "lista": ["Titular: maría fernanda gómez", "documento: 52.123.456"],
        "valor": "El impuesto es $2.135.000 y la matrícula 50C-9000301 debe $1.921.500",
        "numero": 7,
    }
    salida = anonimizar(entrada)
    plano = str(salida)
    for secreto in ("María Fernanda", "1000000003", "900.123.456", "1020304050", "52.123.456"):
        assert secreto not in plano
    assert salida["valor"] == entrada["valor"]  # valores y matrículas se conservan
    assert salida["numero"] == 7 and "[NOMBRE]" in salida["lista"][0].replace("Titular: ", "")


@pytest.mark.unit
@pytest.mark.req("RF-OBS-01 · Traza del flujo entre agentes")
def test_los_metadatos_de_la_traza_nunca_llevan_al_contribuyente() -> None:
    meta = metadatos_de_traza(
        "conv-1", "ESC-07", "0.1.0", contribuyente_id="CC-1", nombre="Ana", nodo="nodo_ipu"
    )
    assert meta == {
        "id_conversacion": "conv-1",
        "escenario_id": "ESC-07",
        "version": "0.1.0",
        "nodo": "nodo_ipu",
    }


@pytest.mark.unit
@pytest.mark.req("RF-OBS-01 · Traza del flujo entre agentes")
def test_langsmith_apagado_no_crea_cliente_y_encendido_usa_el_anonimizador(entorno_valido) -> None:
    anonimizador = Anonimizador()
    assert crear_cliente_langsmith(cargar_configuracion(env_file=None), anonimizador) is None
    entorno_valido.setenv("LANGSMITH_TRACING", "true")
    entorno_valido.setenv("LANGSMITH_API_KEY", "ls-clave-de-prueba")
    cliente = crear_cliente_langsmith(cargar_configuracion(env_file=None), anonimizador)
    assert cliente is not None and cliente._hide_inputs is anonimizador
    assert cliente._hide_outputs is anonimizador


@pytest.mark.unit
@pytest.mark.req("RNF-03 · Protección de datos personales", "RNF-05 · Registro auditable")
def test_las_trazas_quitan_imagenes_y_nombres_y_lo_de_los_modelos_no_cambia(
    entorno_valido,
) -> None:
    """Auditoría de seguridad: la imagen del recibo y «me llamo…» no llegan a LangSmith. Lo que ven
    el juez, el clasificador y los agentes (`para_modelos=True`) sigue igual, y la huella del juez
    también (A5)."""
    from src.evaluacion.escenarios import RAIZ
    from src.evaluacion.juez import huella_del_juez

    datos = "iVBORw0KGgo" + "A" * 1200  # una imagen en base64 (inventada)
    entrada = {"messages": [[{"content": [
        {"type": "text", "text": "Hola, me llamo Ana Pérez"},
        {"type": "image", "source": {"type": "base64", "data": datos}},
        {"type": "image_url", "image_url": {"url": "data:image/png;base64,iVBOR"}},
    ]}]]}  # fmt: skip
    trazas = AnonimizadorDeTrazas()(entrada)["messages"][0][0]["content"]
    assert trazas[0]["text"] == "Hola, me llamo [NOMBRE]"
    assert trazas[1]["source"]["data"] == "[IMAGEN]" == trazas[2]["image_url"]["url"]
    assert AnonimizadorDeTrazas().texto("CC-1000000003") == "[DOCUMENTO]"  # lo de antes sigue
    largo = "El avalúo catastral es la base gravable del impuesto predial. " * 30
    assert AnonimizadorDeTrazas().texto(largo) == largo  # un texto largo no es una imagen
    modelos = Anonimizador(para_modelos=True)(entrada)["messages"][0][0]["content"]
    assert modelos[0]["text"] == "Hola, me llamo [NOMBRE]"  # como antes
    assert modelos[1]["source"]["data"] == datos  # el modelo de visión recibe la imagen
    assert modelos[2]["image_url"]["url"] == "data:image/png;base64,iVBOR"
    huella = (RAIZ / "reports" / "calibracion" / "huella_juez.txt").read_text(encoding="utf-8")
    assert huella_del_juez(cargar_configuracion(env_file=None)) == huella.strip()


# -- Contenedor y almacén conectado ---------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.req("RNF-14 · Configuración por entorno")
def test_el_contenedor_arma_las_dependencias_desde_la_configuracion(
    entorno_valido, base_sintetica
) -> None:
    entorno_valido.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    entorno_valido.setenv("REALSIT_DB_PATH", str(base_sintetica))
    entorno_valido.setenv("UMBRAL_CONFIANZA", "0.8")
    contenedor = Contenedor()
    assert contenedor.deps.config.umbral_confianza == 0.8
    assert contenedor.deps.adaptador is contenedor.adaptador
    assert contenedor.modelo("orquestador").model == "claude-sonnet-5-5"
    assert contenedor.horario().inicio.hour == 8
    assert isinstance(contenedor.recuperador, RecuperadorHibrido)  # conecta con Chroma al usarlo
    assert contenedor.deps.recuperador is contenedor.recuperador


@pytest.mark.integration
@pytest.mark.req("RF-ESC-03 · Resumen del caso")
def test_el_contenedor_conecta_el_almacen_en_postgresql(entorno_valido, base_sintetica) -> None:
    url = url_postgres_pruebas()
    motor = crear_motor(url)
    try:
        with motor.connect() as c:
            c.execute(text("SELECT 1"))
    except Exception as error:  # sin PostgreSQL: se salta en local y falla en la CI
        exigir_postgres(error)
    entorno_valido.setenv("DATABASE_URL", url)
    entorno_valido.setenv("REALSIT_DB_PATH", str(base_sintetica))
    conv = f"b5-{uuid.uuid4().hex[:8]}"
    contenedor = Contenedor()
    try:
        ack = contenedor.adaptador.registrar_caso_escalado(
            CasoEscalado(f"CASO-{conv}", conv, "Resumen", 0.0, motivo="fuera de alcance")
        )
        assert ack.ok
        assert contenedor.almacen.obtener_caso(f"CASO-{conv}")["motivo"] == "fuera de alcance"
        assert contenedor.almacen.estado_conversacion(conv) == "escalada"
    finally:
        with motor.begin() as c:
            parametros = {"c": conv, "k": f"CASO-{conv}"}
            c.execute(text("DELETE FROM mensaje_funcionario WHERE id_caso = :k"), parametros)
            c.execute(text("DELETE FROM caso_escalado WHERE id_caso = :k"), parametros)
            c.execute(text("DELETE FROM conversacion WHERE id_conversacion = :c"), parametros)
