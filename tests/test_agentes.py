"""Agentes reales de B7 con un modelo falso: prompts, herramientas, notas, reloj, errores y datos.

Sin red: el modelo sigue un guion y se guarda todo lo que recibe. Las cifras se comparan con las
referencias aprobadas de B6 (IPU-10, IPU-11, ICA-05) y con `usuarios_prueba.yaml`.
"""

import json
from pathlib import Path
from typing import Any

import pytest
import yaml
from langchain_core.messages import AIMessage, ToolMessage

from src.agents.agente import (
    FORMATO_SALIDA,
    ConfigAgente,
    SalidaAgente,
    anio_de_la_consulta,
    ejecutar_agente,
    hoy_del_turno,
    similitud_de_la_parte,
)
from src.agents.clasificador import (
    ClasificadorLLM,
    SalidaOrquestador,
    interpretar,
)
from src.agents.dependencias import Clasificacion, Dependencias
from src.agents.graph import configuracion_de_hilo, construir_grafo
from src.agents.herramientas.ica import HERRAMIENTAS_ICA
from src.agents.herramientas.ipu import HERRAMIENTAS_IPU
from src.agents.nodes.escalamiento import AVISO_TRANSFERENCIA
from src.agents.nodes.general import FUERA_DE_ALCANCE, FUERA_DEL_CANAL
from src.agents.prompts import cargar_prompt, prompt_de_agente
from src.agents.state import entrada_de_turno
from src.data.adapter import MENSAJE_PREDIO_INACCESIBLE
from src.data.memoria import RealSitEnMemoria
from src.integrations.recuperador import Fragmento, RecuperadorEnMemoria
from src.integrations.robustez import ServicioNoDisponibleError
from src.integrations.trazas import Anonimizador
from src.services import notas
from src.store.almacen import Almacen, crear_motor
from tests.ayudas_postgres import exigir_postgres, url_postgres_pruebas
from tests.modelo_falso import ModeloFalso, final, negativa, pide, salida

RAIZ = Path(__file__).resolve().parent.parent
U03, P03 = "CC-1000000003", "50C-9000301"
U04, P04 = "NIT-9000000004", "50C-9000401"
U07, P07 = "CC-1000000007", "50C-9000701"
U12, P12 = "NIT-9000000012", "50C-9001201"
AJENO = "50C-9000201"
RELOJ_ESCENARIOS = "2026-10-01T10:00:00-05:00"

AGENTE_IPU = ConfigAgente("ipu", prompt_de_agente("ipu"), ("normativa_ipu",), HERRAMIENTAS_IPU)
AGENTE_ICA = ConfigAgente("ica", prompt_de_agente("ica"), ("normativa_ica",), HERRAMIENTAS_ICA)


@pytest.fixture(scope="module")
def recuperador() -> RecuperadorEnMemoria:
    return RecuperadorEnMemoria()


@pytest.fixture
def adaptador(datos_sinteticos) -> RealSitEnMemoria:
    almacen = Almacen(crear_motor("sqlite+pysqlite:///:memory:"))
    almacen.crear_esquema()
    return RealSitEnMemoria(datos_sinteticos, registro_casos=almacen)


def dependencias(adaptador, modelo: ModeloFalso, recuperador=None, **extra) -> Dependencias:
    return Dependencias(adaptador, modelos=lambda _nodo: modelo, recuperador=recuperador, **extra)


def estado(texto: str, contribuyente=None, predios=None, **extra) -> dict[str, Any]:
    entrada = entrada_de_turno(texto, "conv-prueba", contribuyente, predios)
    entrada["parte_actual"] = {"categoria": "ipu", "texto": texto}
    return {**entrada, **extra}


def correr(
    agente, adaptador, guion, texto, contribuyente=None, predios=None, ahora=RELOJ_ESCENARIOS,
    recuperador=None,
):  # fmt: skip
    modelo = ModeloFalso(guion)
    deps = dependencias(adaptador, modelo, recuperador)
    respuesta, datos = ejecutar_agente(
        agente, deps, estado(texto, contribuyente, predios), configuracion_de_hilo("c", ahora)
    )
    return respuesta, datos, modelo


def resultados_de_herramientas(modelo: ModeloFalso) -> list[dict[str, Any]]:
    mensajes = modelo.llamadas[-1][0]
    return [json.loads(m.content) for m in mensajes if isinstance(m, ToolMessage)]


# -- Prompts y esquemas -------------------------------------------------------------------------


def regla_de_categorias() -> list[str]:
    lineas = (RAIZ / "tests/componentes/enrutamiento.yaml").read_text(encoding="utf-8").splitlines()
    inicio = next(i for i, x in enumerate(lineas) if x.startswith("# Regla de categorías")) + 1
    fin = next(
        i for i, x in enumerate(lineas) if x.startswith("# - Las consultas de este conjunto")
    )
    return [x.removeprefix("#").removeprefix(" ") for x in lineas[inicio:fin]]


@pytest.mark.unit
@pytest.mark.req("RF-ORQ-01 · Clasificación de la consulta")
def test_el_prompt_del_orquestador_lleva_la_regla_de_categorias_del_conjunto() -> None:
    prompt = cargar_prompt("orquestador")
    assert prompt.version == "v2"
    regla = regla_de_categorias()
    assert len(regla) >= 15
    for linea in regla:
        assert linea in prompt.texto, linea


@pytest.mark.unit
@pytest.mark.req("RF-IPU-05 · Citación de la norma", "RNF-09 · Lenguaje accesible")
def test_los_prompts_de_los_agentes_llevan_las_reglas_comunes() -> None:
    for nombre in ("ipu", "ica", "general"):
        prompt = prompt_de_agente(nombre)
        assert prompt.version.endswith("+comun.v2")
        texto = prompt.texto
        assert "Cita la norma y el artículo" in texto
        assert "Di siempre de qué año gravable hablas" in texto
        assert "nunca digas que vencieron" in texto  # Ley 1995 (adenda)
        assert "lenguaje claro" in texto
        assert "sistema de inteligencia artificial" in texto
        assert "No pidas ni menciones nombres ni números de documento" in texto


@pytest.mark.unit
@pytest.mark.req("RF-ORQ-05 · Modelo de razonamiento")
def test_los_esquemas_de_salida_no_piden_razonamiento() -> None:
    for esquema in (SalidaOrquestador, SalidaAgente):
        campos = " ".join(esquema.model_json_schema()["properties"]).lower()
        for prohibido in ("razon", "paso", "pensa", "justific", "reasoning"):
            assert prohibido not in campos
    assert FORMATO_SALIDA["format"]["type"] == "json_schema"


# -- Orquestador --------------------------------------------------------------------------------


def salida_orquestador(partes, **marcas) -> SalidaOrquestador:
    base = dict.fromkeys(
        ("consulta_personal", "solicitud_explicita", "pregunta_ia", "tributario_fuera_mvp",
         "municipio_distinto", "no_tributario"),
        False,
    )  # fmt: skip
    return SalidaOrquestador(partes=partes, **{**base, **marcas})


@pytest.mark.unit
@pytest.mark.req("RF-AUT-04 · Aviso de sesión requerida")
def test_la_sesion_requerida_la_decide_el_codigo_y_no_el_modelo() -> None:
    s = salida_orquestador(
        [{"categoria": "ipu", "texto": "¿Cuánto debo?", "busqueda": "saldo del impuesto predial"}],
        consulta_personal=True,
    )
    sin_sesion = interpretar(s, estado("¿Cuánto debo?"))
    assert sin_sesion.marcas["sesion_requerida"] and sin_sesion.partes[0]["categoria"] == "general"
    con_sesion = interpretar(s, estado("¿Cuánto debo?", U03, [P03]))
    assert "sesion_requerida" not in con_sesion.marcas
    assert con_sesion.partes == [
        {"categoria": "ipu", "texto": "¿Cuánto debo?", "busqueda": "saldo del impuesto predial"}
    ]


@pytest.mark.unit
@pytest.mark.req("RF-ORQ-01 · Clasificación de la consulta")
def test_un_adjunto_va_a_ocr_y_las_categorias_descartadas_no_vuelven() -> None:
    s = salida_orquestador(
        [{"categoria": "ipu", "texto": "Revisa mi recibo", "busqueda": "recibo"}]
    )
    adjunto = estado("Revisa mi recibo", U03, [P03], documento_adjunto={"tipo": "imagen"})
    assert interpretar(s, adjunto).partes[0]["categoria"] == "ocr"
    descartada = estado("Algo", U03, [P03], categorias_descartadas=["ipu"])
    assert interpretar(s, descartada).partes[0]["categoria"] == "general"


@pytest.mark.unit
@pytest.mark.req("RF-ORQ-05 · Modelo de razonamiento", "RNF-03 · Protección de datos personales")
def test_el_clasificador_llm_anonimiza_y_trata_la_negativa_como_falla() -> None:
    respuesta = salida(
        partes=[{"categoria": "ipu", "texto": "¿Cuánto debo?", "busqueda": "saldo del predial"}],
        consulta_personal=True, solicitud_explicita=False, pregunta_ia=False,
        tributario_fuera_mvp=False, municipio_distinto=False, no_tributario=False,
    )  # fmt: skip
    modelo = ModeloFalso([respuesta, negativa()])
    clasificar = ClasificadorLLM(modelo, timeout_s=5)
    texto = "Mi cédula es 1000000003, ¿cuánto debo?"
    clasificacion = clasificar(texto, estado(texto, U03, [P03]))
    assert clasificacion.partes[0]["categoria"] == "ipu"
    enviado = modelo.texto_enviado()
    assert "1000000003" not in enviado and U03 not in enviado
    assert "Sesión iniciada: sí" in enviado
    with pytest.raises(ServicioNoDisponibleError):
        clasificar(texto, estado(texto, U03, [P03]))


@pytest.mark.unit
@pytest.mark.req("RF-ORQ-03 · Consultas multiagente", "RF-GEN-03 · Respuesta sustentada en fuentes")
def test_cada_parte_trae_su_consulta_de_busqueda_en_los_terminos_de_la_norma() -> None:
    """Revisión externa: el orquestador devuelve, en la misma llamada, la búsqueda de cada parte."""
    s = salida_orquestador(
        [
            {"categoria": "ipu", "texto": "¿Cuánto sube mi predial?",
             "busqueda": "límite al aumento anual del impuesto predial"},
            {"categoria": "ica", "texto": "¿y el ICA?", "busqueda": ""},
        ],
        pregunta_ia=False,
    )  # fmt: skip
    partes = interpretar(s, estado("x", U03, [P03])).partes
    assert partes[0]["busqueda"] == "límite al aumento anual del impuesto predial"
    assert partes[1]["busqueda"] == "¿y el ICA?"  # sin búsqueda, el texto de la parte
    # Al juntar las partes (pregunta por la IA, sesión requerida), se juntan las búsquedas.
    (unida,) = interpretar(salida_orquestador(s.partes, pregunta_ia=True), estado("x")).partes
    assert unida["busqueda"] == "límite al aumento anual del impuesto predial ¿y el ICA?"
    assert "busqueda" in SalidaOrquestador.model_json_schema()["$defs"]["Parte"]["required"]
    assert "## Consulta de búsqueda" in cargar_prompt("orquestador").texto


class RecuperadorQueAnota:
    """Recuperador falso que guarda cada consulta y no devuelve fragmentos."""

    def __init__(self) -> None:
        self.consultas: list[str] = []

    def recuperar(self, consulta: str, **_: Any) -> list[Fragmento]:
        self.consultas.append(consulta)
        return []


@pytest.mark.unit
@pytest.mark.req(
    "RF-IPU-01 · Consultas conceptuales de IPU", "RNF-03 · Protección de datos personales"
)
def test_el_agente_recupera_con_la_busqueda_y_responde_el_texto_del_contribuyente(
    adaptador,
) -> None:
    texto = "Soy Ana Pérez, ¿cuánto puede subir mi predial de un año a otro?"
    recuperador = RecuperadorQueAnota()
    modelo = ModeloFalso([final("Respuesta.")])
    deps = dependencias(adaptador, modelo, recuperador)
    entrada = estado(texto)
    entrada["parte_actual"] = {
        "categoria": "ipu",
        "texto": texto,
        "busqueda": "límite al aumento anual del impuesto predial",
    }
    agente = ConfigAgente("ipu", prompt_de_agente("ipu"), ("normativa_ipu",))
    ejecutar_agente(agente, deps, entrada, configuracion_de_hilo("c", RELOJ_ESCENARIOS))
    assert recuperador.consultas == ["límite al aumento anual del impuesto predial"]
    enviado = modelo.texto_enviado()
    assert "¿cuánto puede subir mi predial de un año a otro?" in enviado  # «Parte que atiendes»
    assert "límite al aumento anual" not in enviado and "Ana Pérez" not in enviado


@pytest.mark.unit
@pytest.mark.req("RF-ORQ-01 · Clasificación de la consulta")
def test_el_clasificador_simulado_usa_el_texto_como_busqueda(adaptador) -> None:
    grafo = construir_grafo(Dependencias(adaptador))
    entrada = entrada_de_turno("¿Qué es el predial?", "conv-busqueda")
    final_ = grafo.invoke(entrada, configuracion_de_hilo("conv-busqueda", RELOJ_ESCENARIOS))
    assert final_["parte_actual"]["busqueda"] == final_["parte_actual"]["texto"]


# -- Agente del predial -------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.req("RF-IPU-03 · Liquidación estimada", "RNF-09 · Lenguaje accesible")
def test_ipu_10_estimacion_con_notas_tal_cual_e_intereses_por_vencimiento(adaptador) -> None:
    guion = [pide(("estimar_predial", {"anio": 2026})), final("Tu predial de 2026 es $2.135.000.")]
    respuesta, datos, modelo = correr(
        AGENTE_IPU, adaptador, guion, "¿Cuánto me tocaría pagar de predial este año?", U03, [P03]
    )
    (resultado,) = resultados_de_herramientas(modelo)
    assert resultado["impuesto"] == "$2.135.000" and resultado["tarifa"] == "6,1 por mil"
    assert resultado["descuento_aun_vigente"] is False  # venció el 17 de abril de 2026
    assert resultado["obligacion_registrada_del_anio"]["vencida_a_hoy"] is True
    texto = respuesta["texto"]
    for nota in (
        notas.NOTA_ESTIMACION,
        notas.NOTA_APROXIMACION_PREDIAL,
        notas.NOTA_LEY_1995,
        notas.NOTA_INTERESES_MORA,
    ):
        assert texto.count(nota) == 1
    assert "no vinculante" in texto and "intereses" in texto
    assert "Resolución SDH-000194 de 2025" in texto
    assert respuesta["similitud"] is None  # solo datos de los servicios: se renormaliza
    assert datos["predio"] == P03
    # Llamada 1: herramientas sin formato; llamada 2: sin más herramientas y con el JSON.
    primera, segunda = (parametros for _, parametros in modelo.llamadas)
    assert primera["tool_choice"] is None and "output_config" not in primera
    assert segunda["tool_choice"] == {"type": "none"}
    assert segunda["output_config"] == FORMATO_SALIDA


@pytest.mark.unit
@pytest.mark.req("RF-IPU-05 · Citación de la norma", "RF-GEN-03 · Respuesta sustentada en fuentes")
def test_ipu_10_la_cifra_llega_al_modelo_con_la_fuente_de_la_herramienta(adaptador) -> None:
    """Revisión externa: en la prueba de humo de B7, IPU-10 citó el Acuerdo 648 para la tarifa de
    6,1 por mil, que en 2026 sale de la Resolución SDH-000194 de 2025, art. 1."""
    guion = [pide(("estimar_predial", {"anio": 2026})), final("Tu predial de 2026 es $2.135.000.")]
    _, _, modelo = correr(
        AGENTE_IPU, adaptador, guion, "¿Cuánto me tocaría pagar de predial este año?", U03, [P03]
    )
    prompt = modelo.llamadas[0][0][0].content
    assert "nunca con la norma de un fragmento" in prompt
    (resultado,) = resultados_de_herramientas(modelo)
    assert resultado["tarifa"] == "6,1 por mil"
    assert resultado["fuente_de_la_tarifa"].startswith("Resolución SDH-000194 de 2025, art. 1")
    fuentes = resultado["fuentes_de_la_herramienta"]
    assert any(f.startswith("Resolución SDH-000194 de 2025") for f in fuentes)
    assert not any("Acuerdo 648" in f for f in fuentes)


@pytest.mark.unit
@pytest.mark.req("RNF-16 · Tasa de respuestas correctas")
def test_en_el_modo_de_evaluacion_el_parcial_lleva_lo_que_vio_el_modelo(adaptador) -> None:
    """F1 de la corrida 1 (ADR-25): el juez y RAGAS reciben cada resultado de herramienta tal
    como lo vio el modelo y las notas que agregó el sistema; fuera del modo de evaluación, no."""
    guion = lambda: [pide(("estimar_predial", {"anio": 2026})), final("Tu estimación.")]  # noqa: E731
    texto = "¿Cuánto pagaría de predial?"
    for modo in (True, False):
        modelo = ModeloFalso(guion())
        deps = dependencias(adaptador, modelo, modo_evaluacion=modo)
        respuesta, _ = ejecutar_agente(
            AGENTE_IPU,
            deps,
            estado(texto, U03, [P03]),
            configuracion_de_hilo("c", RELOJ_ESCENARIOS),
        )
        if not modo:
            assert "herramientas" not in respuesta and "notas" not in respuesta
            continue
        (visto,) = respuesta["herramientas"]
        assert visto["herramienta"] == "estimar_predial"
        assert visto["resultado"] == resultados_de_herramientas(modelo)[0]
        assert visto["resultado"]["fuentes_de_la_herramienta"]
        assert notas.NOTA_ESTIMACION in respuesta["notas"]
        assert all(n in respuesta["texto"] for n in respuesta["notas"])


@pytest.mark.unit
@pytest.mark.req("RF-IPU-03 · Liquidación estimada")
def test_ipu_11_estimacion_de_2027_con_lo_que_aun_no_se_publica(adaptador) -> None:
    guion = [pide(("estimar_predial", {"anio": 2027})), final("Estimación de 2027.")]
    respuesta, _, modelo = correr(
        AGENTE_IPU, adaptador, guion, "¿Cuánto sería mi predial en 2027?", U03, [P03]
    )
    (resultado,) = resultados_de_herramientas(modelo)
    assert resultado["impuesto"] == "$2.135.000"
    assert resultado["sobretasa_alumbrado"]["valor"] == "$140.000"
    assert resultado["total_estimado_impuesto_mas_sobretasa"] == "$2.275.000"
    assert resultado["vigencia_del_avaluo"] == 2026
    for nota in (notas.NOTA_IVIUR_2027, notas.NOTA_DESCUENTO_2027, notas.NOTA_TOPE_SOBRETASA):
        assert nota in respuesta["texto"]
    assert notas.nota_avaluo_anterior(2027, 2026) in respuesta["texto"]


@pytest.mark.unit
@pytest.mark.req("RF-IPU-03 · Liquidación estimada")
def test_un_dato_no_publicado_vuelve_al_modelo_y_no_se_estima(adaptador) -> None:
    guion = [
        pide(("estimar_predial", {"anio": 2027})),
        final("El SMMLV de 2027 aún no se publica."),
    ]
    respuesta, _, modelo = correr(AGENTE_IPU, adaptador, guion, "Mi predial de 2027", U07, [P07])
    (resultado,) = resultados_de_herramientas(modelo)
    assert set(resultado) == {"no_publicado"} and "aún no se publica" in resultado["no_publicado"]
    assert notas.NOTA_ESTIMACION not in respuesta["texto"]  # sin estimación no hay sus notas


@pytest.mark.unit
@pytest.mark.req("RF-IPU-04 · Plazos y descuentos")
def test_este_anio_y_los_plazos_salen_del_reloj_del_turno(adaptador) -> None:
    def descuento(ahora: str) -> tuple[bool, str]:
        guion = [pide(("fechas_predial", {"anio": 2026})), final("Plazos.")]
        _, _, modelo = correr(AGENTE_IPU, adaptador, guion, "Plazos del predial", U03, [P03], ahora)
        (resultado,) = resultados_de_herramientas(modelo)
        return resultado["descuento_aun_vigente"], modelo.texto_enviado()

    vigente, enviado = descuento("2026-03-01T09:00:00-05:00")
    assert vigente and "Fecha de hoy: 1 de marzo de 2026" in enviado
    vencido, enviado = descuento(RELOJ_ESCENARIOS)
    assert not vencido and "año gravable en curso: 2026" in enviado
    assert anio_de_la_consulta("¿y en 2027?", hoy_del_turno(None, Dependencias(adaptador))) == 2027


@pytest.mark.unit
@pytest.mark.req("RF-AUT-02 · Restricción a predios propios")
def test_un_predio_ajeno_se_rechaza_con_el_mensaje_unico_sin_segunda_llamada(adaptador) -> None:
    guion = [pide(("estado_cuenta_predial", {"matricula": AJENO}))]
    respuesta, _, modelo = correr(AGENTE_IPU, adaptador, guion, f"Estado de {AJENO}", U03, [P03])
    assert respuesta["texto"] == MENSAJE_PREDIO_INACCESIBLE and respuesta["rechazo_acceso"]
    assert len(modelo.llamadas) == 1


@pytest.mark.unit
@pytest.mark.req("RNF-08 · Tiempos de espera y degradación")
@pytest.mark.parametrize(
    "guion",
    [
        [negativa()],
        [AIMessage(content="El predial es…"), AIMessage(content="no es JSON")],
        [TimeoutError("modelo")],
    ],
    ids=["negativa", "salida-invalida", "tiempo"],
)
def test_una_falla_del_modelo_es_fallo_de_servicio(adaptador, guion) -> None:
    respuesta, _, _ = correr(AGENTE_IPU, adaptador, guion, "¿Qué es el predial?", U03, [P03])
    assert respuesta["fallo_servicio"] and respuesta["suficiencia"] == "no_pudo"


@pytest.mark.unit
@pytest.mark.req("RNF-08 · Tiempos de espera y degradación")
def test_una_falla_del_adaptador_es_fallo_de_servicio(adaptador, monkeypatch) -> None:
    def caido(*_: Any) -> None:
        raise ConnectionError("RealSit no responde")

    monkeypatch.setattr(adaptador, "get_estado_cuenta", caido)
    guion = [pide(("estado_cuenta_predial", {}))]
    respuesta, _, _ = correr(AGENTE_IPU, adaptador, guion, "¿Cuánto debo?", U03, [P03])
    assert respuesta["fallo_servicio"]


# -- Tributos separados y agente del ICA --------------------------------------------------------


@pytest.mark.unit
@pytest.mark.req("RF-IPU-02 · Estado de cuenta e historial", "RF-ICA-03 · Fechas de declaración")
def test_el_predial_y_el_ica_no_se_mezclan_en_el_saldo(adaptador) -> None:
    guion = [pide(("estado_cuenta_predial", {})), final("Tu predial está al día.")]
    _, _, modelo = correr(AGENTE_IPU, adaptador, guion, "¿Cuánto debo de predial?", U12, [P12])
    (predial,) = resultados_de_herramientas(modelo)
    assert predial["saldo_pendiente_predial"] == "$0"
    assert {o["vigencia_fiscal"] for o in predial["obligaciones"]}  # solo obligaciones del IPU
    guion = [pide(("mi_situacion_ica", {})), final("Debes el ICA de 2026.")]
    _, _, modelo = correr(AGENTE_ICA, adaptador, guion, "¿Qué debo de ICA?", U12, [P12])
    (ica,) = resultados_de_herramientas(modelo)
    assert ica["saldo_pendiente_ica"] == "$8.694.000"
    assert ica["periodicidad_registrada"] == "anual"


@pytest.mark.unit
@pytest.mark.req("RF-ICA-02 · Estimación por actividad")
def test_ica_05_bimestral_de_2026_con_las_dos_tablas(adaptador) -> None:
    args = {"ciiu": "5611", "ingresos": 250_000_000, "anio": 2026, "periodicidad": "bimestral"}
    guion = [pide(("estimar_ica", args)), final("Estimación del ICA.")]
    respuesta, _, modelo = correr(AGENTE_ICA, adaptador, guion, "ICA bimestral", U04, [P04])
    (resultado,) = resultados_de_herramientas(modelo)
    tramos = {e["periodo"]: (e["tarifa"], e["impuesto"]) for e in resultado["estimaciones"]}
    assert tramos == {
        "bimestres 1 a 5 de 2026": ("13,8 por mil", "$3.450.000"),
        "bimestre 6 de 2026": ("12 por mil", "$3.000.000"),
    }
    assert notas.NOTA_COMPLEMENTARIOS_ICA in respuesta["texto"]
    assert "Acuerdo 1084 de 2026, art. 21" in respuesta["texto"]


@pytest.mark.unit
@pytest.mark.req("RF-ICA-02 · Estimación por actividad")
def test_una_actividad_no_reconocida_pide_el_codigo(adaptador) -> None:
    args = {"ciiu": "0000", "ingresos": 1_000_000, "anio": 2026, "periodicidad": "anual"}
    guion = [pide(("estimar_ica", args)), final("¿Puedes confirmar el código CIIU?")]
    respuesta, _, _ = correr(AGENTE_ICA, adaptador, guion, "ICA de la actividad 0000", U04, [P04])
    assert respuesta["suficiencia"] == "aclaracion"
    assert "Fuentes" not in respuesta["texto"]


@pytest.mark.unit
@pytest.mark.req("RF-ICA-04 · Retenciones fuera de alcance")
def test_la_retencion_del_ica_la_marca_el_agente_y_escala(adaptador) -> None:
    clasificar = lambda texto, state: Clasificacion([{"categoria": "ica", "texto": texto}], {})  # noqa: E731
    sin_cobertura = final("", suficiencia="no_pudo", cobertura=0.0, fuera_del_mvp=True)
    modelo = ModeloFalso([AIMessage(content="La retención no la cubro."), sin_cobertura])
    deps = dependencias(adaptador, modelo, clasificador=clasificar)
    r = construir_grafo(deps).invoke(
        entrada_de_turno("¿Cómo funciona la retención de ICA?", "ret", U04, [P04]),
        configuracion_de_hilo("ret", RELOJ_ESCENARIOS),
    )
    assert r["motivo_escalamiento"] == "fuera de alcance"
    assert r["respuesta_final"].endswith(AVISO_TRANSFERENCIA)
    assert "retención del ICA" in r["respuesta_final"]


# -- Similitud de la parte ----------------------------------------------------------------------


def fragmento(similitud: float) -> Fragmento:
    return Fragmento("texto", "normativa_ipu/x.md", "Artículo 1", similitud, "Norma X")


@pytest.mark.unit
@pytest.mark.req("RF-ESC-01 · Cálculo del nivel de confianza")
def test_regla_de_la_similitud() -> None:
    recuperados = [fragmento(0.9), fragmento(0.4)]
    assert similitud_de_la_parte(recuperados, [recuperados[1]], uso_datos=True) == 0.4
    assert similitud_de_la_parte(recuperados, [], uso_datos=True) is None
    assert similitud_de_la_parte(recuperados, [], uso_datos=False) == 0.9
    assert similitud_de_la_parte([], [], uso_datos=False) is None


@pytest.mark.unit
@pytest.mark.req(
    "RF-ESC-01 · Cálculo del nivel de confianza", "RF-IPU-01 · Consultas conceptuales de IPU"
)
def test_similitud_en_una_consulta_de_cuenta_y_en_una_conceptual(adaptador, recuperador) -> None:
    # CA-01: estado de cuenta, sin citar normas: la similitud no cuenta.
    guion = [pide(("estado_cuenta_predial", {})), final("Debes el predial de 2026.")]
    cuenta, _, _ = correr(
        AGENTE_IPU, adaptador, guion, "¿Cuánto debo?", U03, [P03], recuperador=recuperador
    )
    assert cuenta["similitud"] is None
    # IPU-04: conceptual, cita el fragmento 1: su similitud.
    guion = [AIMessage(content="El predial es…"), final("El predial es…", fragmentos_citados=[1])]
    texto = "¿Qué es el impuesto predial unificado y cómo se calcula?"
    conceptual, _, modelo = correr(
        AGENTE_IPU, adaptador, guion, texto, U03, [P03], recuperador=recuperador
    )
    primero = recuperador.recuperar(texto, coleccion="normativa_ipu", k=5)[0]
    assert conceptual["similitud"] == primero.similitud > 0
    assert primero.cita in conceptual["texto"] and "[1] " in modelo.texto_enviado()


# -- Datos personales ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.req("RNF-03 · Protección de datos personales")
def test_el_modelo_no_recibe_nombres_ni_documentos_de_u01_a_u12(
    adaptador, datos_sinteticos
) -> None:
    usuarios = yaml.safe_load((RAIZ / "tests/fixtures/usuarios_prueba.yaml").read_text("utf-8"))
    personas = {c.id_contribuyente: c for c in datos_sinteticos.contribuyentes}
    for usuario in usuarios["usuarios"]:
        cid = usuario["contribuyente_id"]
        predios = [p["matricula"] for p in usuario["predios"]]
        persona = personas[cid]
        direcciones = [p.direccion for p in datos_sinteticos.predios if p.id_contribuyente == cid]
        texto = (
            f"Me llamo {persona.nombre}, mi documento es {persona.tipo_documento} "
            f"{persona.numero_documento} y la cédula {persona.numero_documento}. ¿Cuánto debo?"
        )
        enviados = []
        for agente, herramienta in (
            (AGENTE_IPU, ("estado_cuenta_predial", {"matricula": predios[0]})),
            (AGENTE_IPU, ("mis_predios", {})),
            (AGENTE_ICA, ("mi_situacion_ica", {})),
        ):
            _, _, modelo = correr(
                agente, adaptador, [pide(herramienta), final()], texto, cid, predios
            )
            enviados.append(modelo.texto_enviado())
        enviado = "\n".join(enviados)
        assert persona.nombre not in enviado, usuario["id"]
        assert persona.numero_documento not in enviado, usuario["id"]
        assert cid not in enviado, usuario["id"]
        for direccion in direcciones:
            assert direccion not in enviado, usuario["id"]


# -- El reloj en el checkpointer de PostgreSQL --------------------------------------------------


@pytest.mark.integration
@pytest.mark.req("RF-ORQ-04 · Implementación en LangGraph")
def test_el_reloj_del_turno_viaja_como_texto_con_el_checkpointer_postgres(adaptador) -> None:
    import uuid

    import psycopg

    from src.agents.graph import checkpointer_postgres

    url = url_postgres_pruebas()
    try:
        psycopg.connect(url, connect_timeout=3).close()
    except psycopg.OperationalError as error:
        exigir_postgres(error)
    clasificar = lambda texto, state: Clasificacion([{"categoria": "ipu", "texto": texto}], {})  # noqa: E731
    guion = [pide(("fechas_predial", {"anio": 2026})), final("Plazos de 2026.")] * 2
    modelo = ModeloFalso(guion)
    deps = dependencias(adaptador, modelo, clasificador=clasificar)
    conv = f"reloj-{uuid.uuid4().hex[:8]}"
    with checkpointer_postgres(url) as saver:
        grafo = construir_grafo(deps, checkpointer=saver)
        for ahora in ("2026-03-01T09:00:00-05:00", RELOJ_ESCENARIOS):
            r = grafo.invoke(
                entrada_de_turno("Plazos del predial", conv, U03, [P03]),
                configuracion_de_hilo(conv, ahora),
            )
            assert not r["requiere_escalamiento"]
    vigencias = [
        json.loads(m.content)["descuento_aun_vigente"]
        for mensajes, _ in modelo.llamadas
        for m in mensajes
        if isinstance(m, ToolMessage)
    ]
    assert vigencias[0] is True and vigencias[-1] is False


@pytest.mark.unit
@pytest.mark.req("RF-IPU-01 · Consultas conceptuales de IPU")
def test_sin_herramientas_la_segunda_llamada_pide_el_json(adaptador) -> None:
    guion = [AIMessage(content="El predial es…"), final("El predial es un impuesto…")]
    respuesta, _, modelo = correr(AGENTE_IPU, adaptador, guion, "¿Qué es el predial?", U03, [P03])
    assert respuesta["texto"].startswith("El predial es un impuesto")
    mensajes, parametros = modelo.llamadas[1]
    assert parametros["output_config"] == FORMATO_SALIDA
    assert mensajes[-1].content.startswith("Entrega ahora la respuesta")


@pytest.mark.unit
@pytest.mark.req("RF-ESC-01 · Cálculo del nivel de confianza")
def test_una_respuesta_vacia_cuenta_como_no_pudo(adaptador) -> None:
    guion = [AIMessage(content=""), final("", suficiencia="aclaracion")]
    respuesta, _, _ = correr(AGENTE_IPU, adaptador, guion, "¿Cuánto me toca?", U03, [P03])
    assert respuesta["suficiencia"] == "no_pudo"


@pytest.mark.unit
@pytest.mark.req("RNF-03 · Protección de datos personales", "RF-IPU-03 · Liquidación estimada")
def test_para_los_modelos_se_conservan_las_cuantias_y_se_enmascaran_los_nombres() -> None:
    modelos, trazas = Anonimizador(para_modelos=True), Anonimizador()
    for cuantia in (
        "Quiero estimar el predial con un avalúo de 280000000",
        "Mis ingresos de 1.250.000.000 en la actividad 5611",
        "Son 1500000000 pesos",
    ):
        assert modelos.texto(cuantia) == cuantia
        assert "[DOCUMENTO]" in trazas.texto(cuantia)  # en las trazas se prefiere perder detalle
    assert modelos.texto("Mi cédula es 1000000003") == "Mi cédula es [DOCUMENTO]"
    assert modelos.texto("Me llamo Ana María de la Peña") == "Me llamo [NOMBRE]"
    assert modelos.texto("Soy propietario del predio") == "Soy propietario del predio"


@pytest.mark.unit
@pytest.mark.req("RF-ICA-02 · Estimación por actividad")
def test_un_codigo_ciiu_no_se_toma_por_el_anio() -> None:
    hoy = hoy_del_turno(configuracion_de_hilo("c", RELOJ_ESCENARIOS), Dependencias(None))
    assert anio_de_la_consulta("ICA de la actividad CIIU 2029 con ingresos de 2027", hoy) == 2027
    assert anio_de_la_consulta("Mi código 2023, ¿cuánto pago?", hoy) == 2026


@pytest.mark.unit
@pytest.mark.req("RF-ICA-03 · Fechas de declaración", "RF-ICA-01 · Consultas conceptuales de ICA")
def test_ica_08_regimen_por_la_periodicidad_y_fecha_de_la_declaracion_anual(adaptador) -> None:
    guion = [
        pide(
            ("mi_situacion_ica", {}),
            ("regimen_ica", {"anio": 2026, "periodicidad": "anual"}),
            ("fechas_ica", {"anio": 2026, "periodicidad": "anual"}),
        ),
        final("Declaras el ICA de 2026 una vez al año."),
    ]
    _, _, modelo = correr(AGENTE_ICA, adaptador, guion, "¿Cuándo declaro el ICA?", U12, [P12])
    situacion, regimen, fechas = resultados_de_herramientas(modelo)
    assert situacion["periodicidad_registrada"] == "anual"
    assert {r["regimen"] for r in regimen["reglas"]} == {"comun_anual", "preferencial"}
    assert {r["periodicidad"] for r in regimen["reglas"]} == {"anual"}
    assert fechas["fechas_limite_declaracion"] == [
        {"fecha": "26 de febrero de 2027", "ya_paso": False}
    ]
    guion = [pide(("regimen_ica", {"anio": 2026, "periodicidad": "bimestral"})), final("Común.")]
    _, _, modelo = correr(AGENTE_ICA, adaptador, guion, "Régimen bimestral", U04, [P04])
    (bimestral,) = resultados_de_herramientas(modelo)
    assert [r["regimen"] for r in bimestral["reglas"]] == ["comun_bimestral"]


# -- Periodicidad del ICA y estimación en la primera ronda (F4 y F8 de la corrida 1) ------------


@pytest.mark.unit
@pytest.mark.req("RF-ICA-03 · Fechas de declaración")
def test_la_periodicidad_registrada_es_la_del_anio_o_la_mas_reciente() -> None:
    from src.services.ica import periodicidad_registrada

    inventadas = [(2031, "anual"), (2033, "bimestral"), (2032, "anual"), (2033, "otra")]
    assert periodicidad_registrada(inventadas, 2032) == ("anual", 2032)
    assert periodicidad_registrada(inventadas, 2040) == ("bimestral", 2033)
    assert periodicidad_registrada([], 2032) is None


@pytest.mark.unit
@pytest.mark.req("RF-ICA-03 · Fechas de declaración")
def test_con_sesion_las_fechas_son_solo_las_de_la_periodicidad_registrada(adaptador) -> None:
    """Un contribuyente anual recibe solo la fecha anual y uno bimestral solo las bimestrales,
    sin que el modelo pase la periodicidad; sin sesión van las dos, cada una con la suya."""
    vistos = {}
    for contribuyente, predio in ((U12, P12), (U04, P04), (None, None)):
        guion = [pide(("fechas_ica", {"anio": 2026})), final("Fechas.")]
        predios = [predio] if predio else None
        _, _, modelo = correr(AGENTE_ICA, adaptador, guion, "Fechas", contribuyente, predios)
        (vistos[contribuyente],) = resultados_de_herramientas(modelo)
    anual, bimestral, sin_sesion = vistos[U12], vistos[U04], vistos[None]
    assert anual["periodicidad"] == "anual" and len(anual["fechas_limite_declaracion"]) == 1
    assert anual["periodicidad_tomada_de"].startswith("la registrada")
    assert bimestral["periodicidad"] == "bimestral"
    assert len(bimestral["fechas_limite_declaracion"]) == 6
    assert "fechas_limite_declaracion" not in sin_sesion
    assert [p["periodicidad"] for p in sin_sesion["por_periodicidad"]] == ["anual", "bimestral"]


@pytest.mark.unit
@pytest.mark.req("RF-ICA-02 · Estimación por actividad")
def test_la_estimacion_sin_periodicidad_usa_la_de_la_sesion_en_la_primera_ronda(adaptador) -> None:
    """Con el CIIU y los ingresos basta una ronda: la periodicidad sale de la sesión. Sin sesión,
    la herramienta pide la periodicidad en lugar de suponerla."""
    args = {"ciiu": "5611", "ingresos": 12_345_000, "anio": 2026}
    guion = [pide(("estimar_ica", args)), final("Estimación.")]
    respuesta, _, modelo = correr(AGENTE_ICA, adaptador, guion, "Estimación", U04, [P04])
    (resultado,) = resultados_de_herramientas(modelo)
    assert resultado["periodicidad"] == "bimestral" and resultado["estimaciones"]
    assert len(modelo.llamadas) == 2  # una ronda de herramientas y la respuesta
    guion = [pide(("estimar_ica", args)), final("¿Declaras anual o bimestral?")]
    _, _, modelo = correr(AGENTE_ICA, adaptador, guion, "Estimación", None, None)
    (sin_sesion,) = resultados_de_herramientas(modelo)
    assert "anual o bimestral" in sin_sesion["falta_dato"]


@pytest.mark.unit
@pytest.mark.req("RF-ICA-02 · Estimación por actividad", "RF-ICA-03 · Fechas de declaración")
def test_el_prompt_del_ica_pide_estimar_en_la_primera_ronda_y_una_sola_periodicidad() -> None:
    texto = prompt_de_agente("ica").texto
    assert "la bimestral si aún no la sabes" not in texto
    assert "da solo las fechas\n  de esa periodicidad" in texto
    assert "llama\n  `estimar_ica` en esta primera ronda" in texto
    assert "La tarifa de una actividad\n  nunca se toma de los fragmentos" in texto
    assert "o de su base gravable, di cuál\n  es la periodicidad que corresponde" in texto
    esquema = next(h for h in HERRAMIENTAS_ICA if h.nombre == "estimar_ica").especificacion()
    assert "periodicidad" not in esquema["input_schema"]["required"]


@pytest.mark.unit
@pytest.mark.req("RNF-08 · Tiempos de espera y degradación")
def test_un_dato_que_no_se_encuentra_vuelve_al_modelo_y_no_es_falla(adaptador, monkeypatch) -> None:
    def sin_avaluo(*_: Any) -> None:
        raise LookupError("No hay avalúo del predio.")

    monkeypatch.setattr(adaptador, "get_avaluo_catastral", sin_avaluo)
    guion = [pide(("estimar_predial", {"anio": 2026})), final("No encuentro el avalúo.")]
    respuesta, _, modelo = correr(AGENTE_IPU, adaptador, guion, "Estima mi predial", U03, [P03])
    (resultado,) = resultados_de_herramientas(modelo)
    assert "falta_dato" in resultado and not respuesta["fallo_servicio"]


@pytest.mark.unit
@pytest.mark.req("RF-GEN-04 · Detección de fuera de alcance")
def test_el_texto_de_fuera_de_alcance_depende_de_la_marca(adaptador) -> None:
    def clasificador(marcas):
        return lambda texto, state: Clasificacion(
            [{"categoria": "fuera_de_alcance", "texto": texto}], dict(marcas)
        )

    for marcas, esperado in (({"no_tributario": True}, FUERA_DE_ALCANCE), ({}, FUERA_DEL_CANAL)):
        deps = dependencias(adaptador, ModeloFalso(), clasificador=clasificador(marcas))
        r = construir_grafo(deps).invoke(
            entrada_de_turno("Algo", "fa"), configuracion_de_hilo("fa", RELOJ_ESCENARIOS)
        )
        assert r["respuesta_final"] == esperado
