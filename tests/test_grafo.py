"""Grafo de B4: enrutamiento puro, transiciones, tope, multiagente, continuidad y sección 3.4."""

from typing import Any

import pytest

from src.agents.dependencias import Clasificacion, ConfigGrafo, Dependencias
from src.agents.graph import (
    DESTINOS_CONFIANZA,
    DESTINOS_ORQUESTADOR,
    FABRICAS,
    configuracion_de_hilo,
    construir_grafo,
    ruta_confianza,
    ruta_orquestador,
)
from src.agents.nodes._comun import agregar_parcial, parcial
from src.agents.nodes.escalamiento import AVISO_TRANSFERENCIA
from src.agents.nodes.orquestador import clasificar_por_palabras
from src.agents.state import (
    CAMPOS_DE_ACCESO,
    CAMPOS_DE_CONVERSACION,
    CAMPOS_DEL_TURNO,
    MOTIVOS_ESCALAMIENTO,
    AgentState,
    entrada_de_turno,
)
from src.data.memoria import RealSitEnMemoria
from src.services.confianza import calcular_nivel, normalizar_similitud
from src.store.almacen import Almacen, crear_motor
from tests.ayudas_postgres import exigir_postgres, url_postgres_pruebas

U03, P03 = "CC-1000000003", "50C-9000301"
U02, P02 = "CC-1000000002", ["50C-9000201", "50C-9000202"]
AJENO = "50C-9000201"


@pytest.fixture
def almacen() -> Almacen:
    almacen = Almacen(crear_motor("sqlite+pysqlite:///:memory:"))
    almacen.crear_esquema()
    return almacen


@pytest.fixture
def adaptador(datos_sinteticos, almacen: Almacen) -> RealSitEnMemoria:
    return RealSitEnMemoria(datos_sinteticos, registro_casos=almacen)


@pytest.fixture
def deps(adaptador: RealSitEnMemoria) -> Dependencias:
    return Dependencias(adaptador)


@pytest.fixture
def grafo(deps: Dependencias):
    return construir_grafo(deps)


def turno(grafo, mensaje: str, conv: str, contribuyente=None, predios=None, **extra) -> AgentState:
    entrada = entrada_de_turno(mensaje, conv, contribuyente, predios, **extra)
    return grafo.invoke(entrada, configuracion_de_hilo(conv))


# -- Funciones de enrutamiento puras ------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.req("RF-ORQ-02 · Enrutamiento y consolidación")
@pytest.mark.parametrize(
    ("estado", "destino"),
    [
        ({"categoria": "ipu"}, "nodo_ipu"),
        ({"categoria": "ica"}, "nodo_ica"),
        ({"categoria": "ocr"}, "nodo_ocr"),
        ({"categoria": "general"}, "nodo_general"),
        ({"categoria": "fuera_de_alcance"}, "nodo_general"),
        ({"categoria": "ipu", "requiere_escalamiento": True}, "nodo_escalamiento"),
        ({"categoria": "ipu", "marcas": {"sesion_requerida": True}}, "nodo_general"),
        ({"categoria": "general", "marcas": {"pregunta_ia": True}}, "nodo_general"),
    ],
)
def test_ruta_del_orquestador(estado: dict[str, Any], destino: str) -> None:
    assert ruta_orquestador(estado) == destino  # type: ignore[arg-type]


@pytest.mark.unit
@pytest.mark.req("RF-ORQ-02 · Enrutamiento y consolidación")
def test_ruta_del_orquestador_rechaza_una_categoria_desconocida() -> None:
    with pytest.raises(ValueError):
        ruta_orquestador({"categoria": "inventada"})


@pytest.mark.unit
@pytest.mark.req("RF-ORQ-02 · Enrutamiento y consolidación")
@pytest.mark.parametrize(
    ("estado", "destino"),
    [
        ({}, "nodo_respuesta"),
        ({"requiere_escalamiento": True}, "nodo_escalamiento"),
        ({"marcas": {"reclasificar": True}}, "nodo_orquestador"),
        ({"categorias_pendientes": [{"categoria": "ica", "texto": "x"}]}, "nodo_orquestador"),
        (
            {"requiere_escalamiento": True, "categorias_pendientes": [{"categoria": "ica"}]},
            "nodo_escalamiento",
        ),
    ],
)
def test_ruta_de_confianza(estado: dict[str, Any], destino: str) -> None:
    assert ruta_confianza(estado) == destino  # type: ignore[arg-type]


@pytest.mark.unit
@pytest.mark.req("RF-SYS-01 · Patrón Supervisor-Worker")
def test_ocho_nodos_y_las_transiciones_de_la_tabla_2(grafo) -> None:
    g = grafo.get_graph()
    nodos = set(g.nodes) - {"__start__", "__end__"}
    assert nodos == set(FABRICAS) and len(nodos) == 8
    aristas = {(e.source, e.target) for e in g.edges}
    esperado = {("__start__", "nodo_orquestador")}
    esperado |= {("nodo_orquestador", d) for d in DESTINOS_ORQUESTADOR}
    esperado |= {
        (w, "nodo_confianza") for w in ("nodo_ipu", "nodo_ica", "nodo_general", "nodo_ocr")
    }
    esperado |= {("nodo_confianza", d) for d in DESTINOS_CONFIANZA}
    esperado |= {("nodo_escalamiento", "__end__"), ("nodo_respuesta", "__end__")}
    assert aristas == esperado


@pytest.mark.unit
@pytest.mark.req("RF-SYS-01 · Patrón Supervisor-Worker")
def test_la_figura_mermaid_coincide_con_el_grafo() -> None:
    from pathlib import Path

    from scripts.exportar_grafo import mermaid_del_grafo

    figura = Path("docs/figuras/grafo_implementado.mmd").read_text(encoding="utf-8")
    assert figura == mermaid_del_grafo()


@pytest.mark.unit
@pytest.mark.req("RF-ESC-01 · Cálculo del nivel de confianza")
def test_formula_de_confianza() -> None:
    assert calcular_nivel(1.0, "completa", 1.0) == pytest.approx(1.0)
    assert calcular_nivel(0.5, "parcial", 1.0) == pytest.approx(0.2 + 0.2 + 0.2)
    assert calcular_nivel(None, "completa", 1.0) == pytest.approx(1.0)  # renormaliza
    assert calcular_nivel(None, "parcial", 1.0) == pytest.approx((0.2 + 0.2) / 0.6)
    assert calcular_nivel(0.9, "no_pudo", 0.0) == pytest.approx(0.36)


@pytest.mark.unit
@pytest.mark.req("RF-ORQ-04 · Implementación en LangGraph")
def test_config_del_grafo_desde_la_configuracion(entorno_valido) -> None:
    from src.config import cargar_configuracion

    config = ConfigGrafo.desde_settings(cargar_configuracion(env_file=None))
    assert config.umbral_confianza == 0.7 and config.max_reclasificaciones == 2
    assert config.pesos.similitud == 0.4


# -- Categorías y consulta multiagente ----------------------------------------------------------


@pytest.mark.unit
@pytest.mark.req("RF-ORQ-02 · Enrutamiento y consolidación")
@pytest.mark.parametrize(
    ("mensaje", "categoria"),
    [
        ("¿Qué es el impuesto predial?", "ipu"),
        ("¿Cuándo declaro el ICA?", "ica"),
        ("¿Cómo uso la Oficina Virtual?", "general"),
    ],
)
def test_cada_categoria_llega_a_su_worker(grafo, mensaje: str, categoria: str) -> None:
    r = turno(grafo, mensaje, f"cat-{categoria}")
    assert r["categoria"] == categoria
    assert [p["categoria"] for p in r["respuestas_parciales"]] == [categoria]
    assert r["respuesta_final"] and not r["requiere_escalamiento"]


@pytest.mark.unit
@pytest.mark.req("RF-ORQ-02 · Enrutamiento y consolidación")
def test_categoria_ocr_con_adjunto(grafo) -> None:
    adjunto = {"tipo": "imagen", "campos_simulados": {"matricula": P03}}
    r = turno(grafo, "Revisa este recibo", "ocr-1", U03, [P03], documento_adjunto=adjunto)
    assert r["categoria"] == "ocr"
    assert r["datos_extraidos"]["ocr"] == {"campos": {"matricula": P03}, "confirmado": False}


@pytest.mark.unit
@pytest.mark.req("RF-ORQ-03 · Consultas multiagente")
def test_consulta_multiagente_ipu_e_ica(grafo) -> None:
    r = turno(grafo, "Explícame el predial y el ICA", "multi-1")
    assert [p["categoria"] for p in r["respuestas_parciales"]] == ["ipu", "ica"]
    assert r["categorias_pendientes"] == []
    assert (
        r["respuesta_final"].startswith("Predial:")
        and "Industria y comercio:" in r["respuesta_final"]
    )


@pytest.mark.unit
@pytest.mark.req("RF-ORQ-03 · Consultas multiagente")
def test_una_parte_bajo_el_umbral_escala_con_las_partes_resueltas(deps, almacen) -> None:
    def ica_dudoso(state: AgentState) -> dict[str, Any]:
        mala = parcial("ica", "Respuesta dudosa", similitud=0.2, suficiencia="parcial")
        return {"respuestas_parciales": [*state["respuestas_parciales"], mala]}

    grafo = construir_grafo(deps, nodos={"nodo_ica": ica_dudoso})
    r = turno(grafo, "Explícame el predial y el ICA", "multi-2")
    assert r["requiere_escalamiento"] and r["motivo_escalamiento"] == "confianza insuficiente"
    assert "Explicación del impuesto predial" in r["respuesta_final"]  # parte ya resuelta
    assert "Respuesta dudosa" not in r["respuesta_final"]  # la rechazada no se le muestra
    assert "transferir" in r["respuesta_final"]
    caso = almacen.obtener_caso("CASO-multi-2")
    similitud = normalizar_similitud(0.2, deps.config.escala_similitud)  # escala de B8
    assert caso["nivel_confianza"] == pytest.approx(0.4 * similitud + 0.4 * 0.5 + 0.2 * 1.0)
    assert almacen.estado_conversacion("multi-2") == "escalada"
    rechazadas = caso["resumen_json"]["partes_rechazadas"]  # sí van en el resumen del funcionario
    assert [p["texto"] for p in rechazadas] == ["Respuesta dudosa"]


@pytest.mark.unit
@pytest.mark.req("RF-ESC-05 · Notificación al contribuyente")
@pytest.mark.parametrize(
    ("respuesta", "motivo"),
    [
        (
            dict(texto="Respuesta dudosa", similitud=0.2, suficiencia="parcial"),
            "confianza insuficiente",
        ),
        (dict(texto="Sin base", suficiencia="no_pudo", cobertura=0.0), "sin cobertura"),
    ],
)
def test_bajo_el_umbral_o_sin_cobertura_solo_recibe_el_aviso(deps, respuesta, motivo) -> None:
    def ipu_malo(state: AgentState) -> dict[str, Any]:
        return {"respuestas_parciales": [parcial("ipu", **respuesta)]}

    r = turno(
        construir_grafo(deps, nodos={"nodo_ipu": ipu_malo}), "El predial", f"aviso-{motivo[:4]}"
    )
    assert r["motivo_escalamiento"] == motivo
    assert r["respuesta_final"] == AVISO_TRANSFERENCIA


@pytest.mark.unit
@pytest.mark.req("RF-ORQ-03 · Consultas multiagente")
def test_reclasificar_la_parte_rechazada_no_repite_la_parte_respondida(deps) -> None:
    textos: list[str] = []
    base = deps.clasificador or clasificar_por_palabras

    def clasificador(texto: str, state: AgentState) -> Clasificacion:
        textos.append(texto)
        return base(texto, state)

    def ica_no_corresponde(state: AgentState) -> dict[str, Any]:
        sin = parcial("ica", "", suficiencia="no_corresponde", cobertura=0.0)
        return {"respuestas_parciales": agregar_parcial(state, sin)}

    deps.clasificador = clasificador
    grafo = construir_grafo(deps, nodos={"nodo_ica": ica_no_corresponde})
    r = turno(grafo, "Explícame el predial y el ICA", "multi-3")
    assert textos == ["Explícame el predial y el ICA", "el ICA"]  # reclasifica solo su parte
    partes = [(p["categoria"], p["parte"]) for p in r["respuestas_parciales"]]
    assert partes == [("ipu", "Explícame el predial"), ("ica", "el ICA"), ("general", "el ICA")]
    assert len(set(partes)) == len(partes)
    assert r["respuesta_final"].count("Explicación del impuesto predial") == 1
    assert not r["requiere_escalamiento"] and r["parte_actual"]["categoria"] == "general"


@pytest.mark.unit
@pytest.mark.req("RF-ORQ-03 · Consultas multiagente")
def test_cada_worker_recibe_su_parte(grafo) -> None:
    r = turno(grafo, "Explícame el predial y el ICA", "multi-4")
    assert [p["parte"] for p in r["respuestas_parciales"]] == ["Explícame el predial", "el ICA"]


@pytest.mark.unit
@pytest.mark.req("RF-ORQ-06 · Prevención de bucles")
def test_sin_categoria_nueva_para_la_parte_escala_sin_cobertura(deps, almacen) -> None:
    ordenes = [
        Clasificacion([{"categoria": "ipu", "texto": "t"}, {"categoria": "ica", "texto": "u"}]),
        Clasificacion([{"categoria": "ipu", "texto": "t"}]),  # la parte «t» ya la respondió ipu
    ]
    deps.clasificador = lambda texto, state: ordenes.pop(0)

    def ica_no_corresponde(state: AgentState) -> dict[str, Any]:
        sin = parcial("ica", "", suficiencia="no_corresponde", cobertura=0.0)
        return {"respuestas_parciales": agregar_parcial(state, sin)}

    grafo = construir_grafo(deps, nodos={"nodo_ica": ica_no_corresponde})
    r = turno(grafo, "algo", "dup-1")
    assert r["motivo_escalamiento"] == "sin cobertura" and r["nivel_confianza"] == 0.0
    assert r["respuesta_final"].count("Explicación del impuesto predial") == 1  # no se repite
    assert almacen.obtener_caso("CASO-dup-1")["nivel_confianza"] == 0.0


# -- Reclasificación hasta el tope (RF-ORQ-06) --------------------------------------------------


@pytest.mark.unit
@pytest.mark.req("RF-ORQ-06 · Prevención de bucles")
def test_reclasificacion_hasta_el_tope_y_luego_escala(deps, almacen) -> None:
    llamadas = {"clasificador": 0, "ipu": 0}

    def siempre_ipu(texto: str, state: AgentState) -> Clasificacion:
        llamadas["clasificador"] += 1
        return Clasificacion([{"categoria": "ipu", "texto": texto}])

    def ipu_no_corresponde(state: AgentState) -> dict[str, Any]:
        llamadas["ipu"] += 1
        sin = parcial("ipu", "", suficiencia="no_corresponde", cobertura=0.0)
        return {"respuestas_parciales": [*state["respuestas_parciales"], sin]}

    deps.clasificador = siempre_ipu
    grafo = construir_grafo(deps, nodos={"nodo_ipu": ipu_no_corresponde})
    r = turno(grafo, "pregunta rara", "tope-1")
    assert llamadas == {"clasificador": 3, "ipu": 3}  # 1 clasificación y 2 reclasificaciones
    assert r["intentos_clasificacion"] == 2
    assert r["requiere_escalamiento"] and r["motivo_escalamiento"] == "tope de reclasificaciones"
    assert almacen.obtener_caso("CASO-tope-1")["motivo"] == "tope de reclasificaciones"


@pytest.mark.unit
@pytest.mark.req("RF-ORQ-06 · Prevención de bucles")
def test_una_reclasificacion_que_acierta_responde(deps) -> None:
    ordenes = [
        Clasificacion([{"categoria": "ipu", "texto": "t"}]),
        Clasificacion([{"categoria": "general", "texto": "t"}]),
    ]
    deps.clasificador = lambda texto, state: ordenes.pop(0)

    def ipu_no_corresponde(state: AgentState) -> dict[str, Any]:
        sin = parcial("ipu", "", suficiencia="no_corresponde", cobertura=0.0)
        return {"respuestas_parciales": [*state["respuestas_parciales"], sin]}

    grafo = construir_grafo(deps, nodos={"nodo_ipu": ipu_no_corresponde})
    r = turno(grafo, "algo", "reclas-1")
    assert r["intentos_clasificacion"] == 1 and not r["requiere_escalamiento"]
    assert r["categorias_descartadas"] == ["ipu"]
    assert r["respuestas_parciales"][-1]["categoria"] == "general"


# -- Escalamiento y fuera de alcance -------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.req("RF-ESC-02 · Activación del escalamiento")
def test_solicitud_explicita_escala_con_cero_y_su_motivo(grafo, almacen) -> None:
    r = turno(grafo, "Quiero hablar con una persona", "esc-1")
    assert r["requiere_escalamiento"] and r["motivo_escalamiento"] == "solicitud explícita"
    assert r["nivel_confianza"] == 0.0 and r["respuestas_parciales"] == []
    caso = almacen.obtener_caso("CASO-esc-1")
    assert caso["nivel_confianza"] == 0.0 and caso["motivo"] == "solicitud explícita"  # ADR-13
    assert r["resumen_caso"].startswith("Motivo: solicitud explícita")


@pytest.mark.unit
@pytest.mark.req("RF-GEN-04 · Detección de fuera de alcance")
def test_no_tributario_se_informa_y_no_se_escala(grafo) -> None:
    r = turno(grafo, "Dame la receta de ajiaco", "fuera-1")
    assert r["categoria"] == "fuera_de_alcance" and not r["requiere_escalamiento"]
    assert "no es tributario" in r["respuesta_final"]


@pytest.mark.unit
@pytest.mark.req("RF-ESC-02 · Activación del escalamiento")
@pytest.mark.parametrize(
    "mensaje",
    ["¿Cómo declaro renta?", "¿Cuánto es el IVA?", "Quiero pagar el predial en Medellín"],
)
def test_tributario_fuera_del_mvp_escala(grafo, mensaje: str) -> None:
    r = turno(grafo, mensaje, f"fuera-{abs(hash(mensaje))}")
    assert r["requiere_escalamiento"] and r["motivo_escalamiento"] == "fuera de alcance"


@pytest.mark.unit
@pytest.mark.req("RF-ESC-02 · Activación del escalamiento")
def test_retencion_de_ica_la_detecta_el_worker_y_escala(grafo) -> None:
    r = turno(grafo, "¿Cómo manejo la retención de ICA?", "ret-1")
    assert r["motivo_escalamiento"] == "fuera de alcance"
    assert r["respuestas_parciales"][0]["fuera_de_alcance"]


@pytest.mark.unit
@pytest.mark.req("RNF-08 · Tiempos de espera y degradación")
def test_falla_del_adaptador_escala(adaptador, almacen) -> None:
    def roto(*args: Any, **kwargs: Any) -> Any:
        raise TimeoutError("sin respuesta")

    adaptador.get_estado_cuenta = roto  # type: ignore[method-assign]
    grafo = construir_grafo(Dependencias(adaptador))
    r = turno(grafo, f"¿Cuánto debo de {P03}?", "falla-1", U03, [P03])
    assert r["requiere_escalamiento"] and r["motivo_escalamiento"] == "fallo de servicio"
    assert almacen.obtener_caso("CASO-falla-1")["nivel_confianza"] == 0.0


@pytest.mark.unit
@pytest.mark.req("RNF-08 · Tiempos de espera y degradación")
def test_falla_del_orquestador_escala(deps, almacen) -> None:
    def roto(texto: str, state: AgentState) -> Clasificacion:
        raise RuntimeError("modelo caído")

    deps.clasificador = roto
    r = turno(construir_grafo(deps), "hola", "falla-2")
    assert r["motivo_escalamiento"] == "fallo de servicio"
    assert almacen.obtener_caso("CASO-falla-2")["motivo"] == "fallo de servicio"


@pytest.mark.unit
@pytest.mark.req("RNF-08 · Tiempos de espera y degradación")
def test_si_el_registro_del_caso_falla_el_aviso_se_entrega(adaptador) -> None:
    def roto(caso: Any) -> None:
        raise OSError("sin almacén")

    adaptador._registro_casos.registrar_caso = roto  # type: ignore[union-attr,method-assign]
    r = turno(construir_grafo(Dependencias(adaptador)), "Quiero hablar con una persona", "falla-3")
    assert r["marcas"]["registro_fallido"] and "transferir" in r["respuesta_final"]


# -- Los cuatro casos de la sección 3.4 (ADR-14) --------------------------------------------------


@pytest.mark.unit
@pytest.mark.req("RF-AUT-04 · Aviso de sesión requerida")
def test_caso_1_sesion_requerida_pasa_por_general_y_confianza(grafo) -> None:
    r = turno(grafo, f"¿Cuánto debo de {P03}?", "caso1")
    assert r["marcas"]["sesion_requerida"] and r["categoria"] == "general"
    assert "iniciar sesión" in r["respuesta_final"]
    assert r["respuestas_parciales"][0]["similitud"] is None  # sin fragmentos
    assert not r["requiere_escalamiento"] and r["nivel_confianza"] >= 0.7


@pytest.mark.unit
@pytest.mark.req("RF-AUT-02 · Restricción a predios propios")
def test_caso_2_predio_ajeno_e_inexistente_mismo_mensaje_sin_escalar(grafo) -> None:
    ajeno = turno(grafo, f"Mi predio {AJENO}", "caso2a", U03, [P03])
    inexistente = turno(grafo, "Mi predio 50C-0000000", "caso2b", U03, [P03])
    for r in (ajeno, inexistente):
        assert r["respuestas_parciales"][0]["rechazo_acceso"] and not r["requiere_escalamiento"]
    assert ajeno["respuesta_final"] == inexistente["respuesta_final"]
    assert AJENO not in ajeno["respuesta_final"] and "COP" not in ajeno["respuesta_final"]


@pytest.mark.unit
@pytest.mark.req("RF-ESC-01 · Cálculo del nivel de confianza")
def test_cada_parte_dice_de_donde_sale_su_nivel(grafo) -> None:
    ajeno = turno(grafo, f"Mi predio {AJENO}", "origen-1", U03, [P03])
    conceptual = turno(grafo, "¿Qué es el impuesto predial?", "origen-2")
    aclaracion = turno(grafo, "¿Cuánto debo de mi predio?", "origen-3", U02, P02)
    assert ajeno["respuestas_parciales"][0]["origen_nivel"] == "rechazo_acceso"
    assert conceptual["respuestas_parciales"][0]["origen_nivel"] == "formula"
    assert aclaracion["respuestas_parciales"][0]["origen_nivel"] == "aclaracion"


@pytest.mark.unit
@pytest.mark.req("RF-ORQ-06 · Prevención de bucles")
def test_caso_3_no_corresponde_con_el_tope_alcanzado_escala(deps) -> None:
    deps.config = ConfigGrafo(max_reclasificaciones=0)

    def ipu_no_corresponde(state: AgentState) -> dict[str, Any]:
        sin = parcial("ipu", "", suficiencia="no_corresponde", cobertura=0.0)
        return {"respuestas_parciales": [*state["respuestas_parciales"], sin]}

    grafo = construir_grafo(deps, nodos={"nodo_ipu": ipu_no_corresponde})
    r = turno(grafo, "Explícame el predial", "caso3")
    assert r["motivo_escalamiento"] == "tope de reclasificaciones"


@pytest.mark.unit
@pytest.mark.req("RF-ESC-05 · Notificación al contribuyente")
def test_caso_4_multiagente_escalada_entrega_lo_resuelto(deps, almacen) -> None:
    def ica_sin_servicio(state: AgentState) -> dict[str, Any]:
        roto = parcial("ica", "", suficiencia="no_pudo", cobertura=0.0, fallo_servicio=True)
        return {"respuestas_parciales": [*state["respuestas_parciales"], roto]}

    r = turno(
        construir_grafo(deps, nodos={"nodo_ica": ica_sin_servicio}), "El predial y el ICA", "caso4"
    )
    assert r["motivo_escalamiento"] == "fallo de servicio"
    assert "Explicación del impuesto predial" in r["respuesta_final"]
    # ADR-13: la parte que escala no tiene confianza; no hereda la del predial (0,94).
    assert r["nivel_confianza"] == 0.0
    assert almacen.obtener_caso("CASO-caso4")["nivel_confianza"] == 0.0


@pytest.mark.unit
@pytest.mark.req("RF-ESC-02 · Activación del escalamiento")
def test_todo_escalamiento_lleva_un_motivo_de_la_lista(deps, adaptador) -> None:
    def roto(*args: Any, **kwargs: Any) -> Any:
        raise TimeoutError("sin respuesta")

    def fallan(texto: str, state: AgentState) -> Clasificacion:
        raise RuntimeError("modelo caído")

    adaptador.get_estado_cuenta = roto  # type: ignore[method-assign]
    casos = [
        (construir_grafo(deps), "Quiero hablar con una persona", None, None),
        (construir_grafo(deps), "¿Cómo declaro renta?", None, None),
        (construir_grafo(deps), "¿Cómo manejo la retención de ICA?", None, None),
        (construir_grafo(deps), f"¿Cuánto debo de {P03}?", U03, [P03]),
        (construir_grafo(Dependencias(adaptador, clasificador=fallan)), "hola", None, None),
    ]
    motivos = []
    for i, (grafo, mensaje, contribuyente, predios) in enumerate(casos):
        r = turno(grafo, mensaje, f"motivo-{i}", contribuyente, predios)
        assert r["requiere_escalamiento"]
        motivos.append(r["motivo_escalamiento"])
    assert set(motivos) <= set(MOTIVOS_ESCALAMIENTO)
    assert motivos == [
        "solicitud explícita",
        "fuera de alcance",
        "fuera de alcance",
        "fallo de servicio",
        "fallo de servicio",
    ]


@pytest.mark.unit
@pytest.mark.req("RNF-08 · Tiempos de espera y degradación")
def test_un_motivo_fuera_de_la_lista_no_impide_el_aviso(deps, almacen, caplog) -> None:
    def motivo_raro(state: AgentState) -> dict[str, Any]:
        return {"requiere_escalamiento": True, "motivo_escalamiento": "motivo inventado"}

    grafo = construir_grafo(deps, nodos={"nodo_orquestador": motivo_raro})
    with caplog.at_level("WARNING"):
        r = turno(grafo, "hola", "raro-1")
    assert r["motivo_escalamiento"] == "fallo de servicio" and "transferir" in r["respuesta_final"]
    caso = almacen.obtener_caso("CASO-raro-1")
    assert caso["motivo"] == "fallo de servicio"
    assert caso["resumen_json"]["motivo_original"] == "motivo inventado"
    assert any("fuera de la lista" in m for m in caplog.messages)


@pytest.mark.unit
@pytest.mark.req("RF-ORQ-02 · Enrutamiento y consolidación")
def test_la_respuesta_final_omite_las_partes_no_aprobadas(deps) -> None:
    from src.agents.nodes.respuesta import crear_nodo_respuesta

    nodo = crear_nodo_respuesta(deps)
    aprobada = {**parcial("ipu", "Bien"), "aprobada": True}
    no_corresponde = {**parcial("ica", "Texto ajeno", suficiencia="no_corresponde")}
    r = nodo({"respuestas_parciales": [aprobada, {**no_corresponde, "aprobada": False}]})
    assert r["respuesta_final"] == "Bien"


# -- Pregunta por la IA (RF-SYS-06) y continuidad (RF-UI-02) ------------------------------------


@pytest.mark.unit
@pytest.mark.req("RF-SYS-06 · Aviso de interacción con IA (provisional)")
def test_pregunta_por_la_ia_se_responde_y_si_acepta_se_escala(grafo, almacen) -> None:
    r1 = turno(grafo, "¿Estoy hablando con una persona?", "ia-1")
    assert r1["marcas"]["pregunta_ia"] and "inteligencia artificial" in r1["respuesta_final"]
    assert not r1["requiere_escalamiento"]
    r2 = turno(grafo, "Sí, por favor", "ia-1")
    assert r2["requiere_escalamiento"] and r2["motivo_escalamiento"] == "solicitud explícita"
    assert almacen.obtener_caso("CASO-ia-1") is not None


@pytest.mark.unit
@pytest.mark.req("RF-UI-02 · Contexto de la sesión")
def test_continuidad_entre_turnos_y_reinicio_de_los_campos_del_turno(grafo) -> None:
    t1 = turno(grafo, f"¿Cuánto debo de {P03}?", "cont-1", U03, [P03])
    assert t1["datos_extraidos"]["predio"] == P03 and t1["marcas"]["confianza_calculada"]
    t2 = turno(grafo, "¿Y cuánto debo de ese predio?", "cont-1", U03, [P03])
    assert P03 in t2["respuesta_final"]  # resolvió «ese predio» con el turno anterior
    assert len(t2["messages"]) == 4 and t2["intentos_clasificacion"] == 0
    assert len(t2["respuestas_parciales"]) == 1  # no se acumula con el turno 1


@pytest.mark.unit
@pytest.mark.req("RF-UI-02 · Contexto de la sesión")
def test_una_bandera_de_escalamiento_no_pasa_al_turno_siguiente(grafo) -> None:
    t1 = turno(grafo, "Quiero hablar con una persona", "cont-2")
    assert t1["requiere_escalamiento"]
    t2 = turno(grafo, "¿Qué es el impuesto predial?", "cont-2")
    assert not t2["requiere_escalamiento"] and t2["motivo_escalamiento"] is None


@pytest.mark.unit
@pytest.mark.req("RF-ORQ-06 · Prevención de bucles")
def test_los_intentos_de_clasificacion_se_acumulan_por_conversacion(deps) -> None:
    ordenes = [Clasificacion([{"categoria": "ipu", "texto": "t"}])] * 4 + [
        Clasificacion([{"categoria": "general", "texto": "t"}])
    ] * 4

    def ipu_no_corresponde(state: AgentState) -> dict[str, Any]:
        sin = parcial("ipu", "", suficiencia="no_corresponde", cobertura=0.0)
        return {"respuestas_parciales": [*state["respuestas_parciales"], sin]}

    clasifica = iter(ordenes)
    deps.clasificador = lambda texto, state: next(clasifica)
    grafo = construir_grafo(deps, nodos={"nodo_ipu": ipu_no_corresponde})
    t1 = turno(grafo, "uno", "acum-1")
    t2 = turno(grafo, "dos", "acum-1")
    assert t1["intentos_clasificacion"] == 2 and t2["intentos_clasificacion"] == 2


@pytest.mark.unit
@pytest.mark.req("RF-UI-02 · Contexto de la sesión")
def test_ciclo_de_vida_de_los_campos() -> None:
    entrada = entrada_de_turno("hola", "c", "CC-1", ["50C-1"])
    todos = set(CAMPOS_DE_CONVERSACION) | set(CAMPOS_DE_ACCESO) | set(CAMPOS_DEL_TURNO)
    assert set(entrada) <= todos
    assert set(CAMPOS_DEL_TURNO) <= set(entrada)  # los del turno se reinician siempre
    assert "intentos_clasificacion" not in entrada and "datos_extraidos" not in entrada
    assert len(AgentState.__annotations__) == 14 + 4  # Tabla 3 más cuatro auxiliares (ADR-23)


@pytest.mark.integration
@pytest.mark.req("RF-ORQ-04 · Implementación en LangGraph")
def test_checkpointer_en_postgresql_conserva_la_conversacion(deps) -> None:
    import uuid

    import psycopg

    from src.agents.graph import checkpointer_postgres

    url = url_postgres_pruebas()
    try:
        psycopg.connect(url, connect_timeout=3).close()
    except psycopg.OperationalError as error:
        exigir_postgres(error)
    conv = f"pg-{uuid.uuid4().hex[:8]}"
    with checkpointer_postgres(url) as saver:
        grafo = construir_grafo(deps, checkpointer=saver)
        turno(grafo, f"¿Cuánto debo de {P03}?", conv, U03, [P03])
        t2 = turno(grafo, "¿Y cuánto debo de ese predio?", conv, U03, [P03])
        assert P03 in t2["respuesta_final"] and len(t2["messages"]) == 4
        assert (
            grafo.get_state(configuracion_de_hilo(conv)).values["datos_extraidos"]["predio"] == P03
        )


# -- Categoría de la clasificación (F2 de la corrida 1) ------------------------------------------


class _AlmacenSinCasos:
    def caso_de_conversacion(self, _id: str) -> None:
        return None


def categoria_reportada(estado: AgentState) -> str | None:
    """La categoría de `meta` que arma la API con el estado final del grafo."""
    from types import SimpleNamespace

    from src.api.turno import interpretar_estado

    servicios = SimpleNamespace(
        settings=SimpleNamespace(modo_evaluacion=False), almacen=_AlmacenSinCasos()
    )
    return interpretar_estado(servicios, dict(estado))[2]["categoria"]  # type: ignore[arg-type]


@pytest.mark.unit
@pytest.mark.req(
    "RF-ORQ-01 · Clasificación de la consulta", "RF-OBS-02 · Matriz de confusión de enrutamiento"
)
def test_lo_no_tributario_se_reporta_fuera_de_alcance_aunque_lo_responda_general(deps) -> None:
    deps.clasificador = lambda texto, state: Clasificacion(
        [{"categoria": "fuera_de_alcance", "texto": texto}], {"no_tributario": True}
    )
    r = turno(construir_grafo(deps), "¿Qué película me recomiendas?", "f2-no-trib")
    assert r["respuestas_parciales"][0]["categoria"] == "general"  # ADR-14 no cambia
    assert r["marcas"]["categoria_clasificada"] == "fuera_de_alcance"
    assert categoria_reportada(r) == "fuera_de_alcance"


@pytest.mark.unit
@pytest.mark.req(
    "RF-ORQ-01 · Clasificación de la consulta", "RF-OBS-02 · Matriz de confusión de enrutamiento"
)
def test_un_escalamiento_antes_del_agente_reporta_su_categoria(deps) -> None:
    deps.clasificador = lambda texto, state: Clasificacion(
        [{"categoria": "ica", "texto": texto}], {"tributario_fuera_mvp": True}
    )
    r = turno(construir_grafo(deps), "¿Cómo funciona un tributo inventado?", "f2-fuera-mvp")
    assert r["requiere_escalamiento"] and not r["respuestas_parciales"]
    assert categoria_reportada(r) == "fuera_de_alcance"
    deps.clasificador = lambda texto, state: Clasificacion(
        [{"categoria": "general", "texto": texto}], {"solicitud_explicita": True}
    )
    r = turno(construir_grafo(deps), "Necesito a alguien de carne y hueso", "f2-explicita")
    assert r["requiere_escalamiento"] and categoria_reportada(r) == "general"


@pytest.mark.unit
@pytest.mark.req("RF-ORQ-03 · Consultas multiagente")
def test_la_reclasificacion_de_otra_parte_no_cambia_la_categoria_reportada(deps) -> None:
    def ica_no_corresponde(state: AgentState) -> dict[str, Any]:
        sin = parcial("ica", "", suficiencia="no_corresponde", cobertura=0.0)
        return {"respuestas_parciales": agregar_parcial(state, sin)}

    grafo = construir_grafo(deps, nodos={"nodo_ica": ica_no_corresponde})
    r = turno(grafo, "Explícame el predial y el ICA", "f2-multi")
    assert categoria_reportada(r) == "ipu"
