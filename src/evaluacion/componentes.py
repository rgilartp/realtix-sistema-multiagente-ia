"""Ejecutor de componentes (sección 6.2, nivel de componentes).

- **Orquestador:** clasifica las 100 consultas etiquetadas de `tests/componentes/enrutamiento.yaml`
  con sesión iniciada (U03) y, en las de `ocr`, con un adjunto simulado. La categoría predicha es la
  de la primera parte, la que atiende primero el grafo. Métricas: matriz de confusión, precisión,
  exhaustividad y F1 por clase, kappa de Cohen y exactitud de la clase mayoritaria (Powers).
- **Agentes:** los escenarios de un turno que responde un agente (IPU, ICA o información general),
  directo contra su nodo, con el texto del turno como parte y como búsqueda. La respuesta la
  califica el juez con la misma referencia del escenario.
"""

from collections import Counter
from collections.abc import Callable
from decimal import Decimal
from typing import Any

from langchain_core.callbacks import get_usage_metadata_callback

from src.agents.dependencias import Dependencias
from src.agents.graph import configuracion_de_hilo
from src.agents.nodes.general import crear_nodo_general
from src.agents.nodes.ica import crear_nodo_ica
from src.agents.nodes.ipu import crear_nodo_ipu
from src.agents.state import CATEGORIAS, entrada_de_turno
from src.config import Settings
from src.evaluacion.humo import sesiones
from src.evaluacion.metricas_eval import kappa
from src.integrations.costos import usos_desde_metadatos
from src.services.metricas import matriz_de_confusion, por_categoria

SESION_ENRUTAMIENTO = "U03"
ADJUNTO_SIMULADO = {"ruta": "", "tipo": "image/png", "tamano_bytes": 0, "simulado": True}
NODOS_DE_AGENTE: dict[str, Callable[[Dependencias], Callable[..., dict[str, Any]]]] = {
    "ipu": crear_nodo_ipu,
    "ica": crear_nodo_ica,
    "general": crear_nodo_general,
}


def _costo(uso: dict[str, Any]) -> tuple[dict[str, dict[str, int]], Decimal]:
    usos = usos_desde_metadatos(uso)
    tokens = {u.modelo: {"entrada": u.entrada, "salida": u.salida} for u in usos}
    return tokens, sum((u.costo_usd for u in usos), Decimal(0))


def clasificar_consultas(
    deps: Dependencias,
    consultas: list[dict[str, Any]],
    al_avanzar: Callable[[dict[str, Any]], None] | None = None,
) -> list[dict[str, Any]]:
    """Categoría predicha de cada consulta; una falla del modelo queda como «sin_categoria»."""
    if deps.clasificador is None:
        raise RuntimeError("El contenedor no tiene el clasificador con modelo.")
    contribuyente, predios = sesiones()[SESION_ENRUTAMIENTO]
    resultados = []
    for c in consultas:
        estado = entrada_de_turno(
            c["texto"],
            f"componentes-{c['id']}",
            contribuyente,
            predios,
            ADJUNTO_SIMULADO if c.get("adjunto") else None,
        )
        with get_usage_metadata_callback() as uso:
            try:
                predicha = deps.clasificador(c["texto"], estado).partes[0]["categoria"]
            except Exception as error:
                predicha = "sin_categoria"
                c = {**c, "error": type(error).__name__}
        tokens, costo = _costo(uso.usage_metadata)
        fila = {
            "id": c["id"],
            "esperada": c["categoria"],
            "predicha": predicha,
            "error": c.get("error"),
            "tokens_por_modelo": tokens,
            "costo_usd": str(costo),
        }
        resultados.append(fila)
        if al_avanzar:
            al_avanzar(fila)
    return resultados


def metricas_de_enrutamiento(resultados: list[dict[str, Any]]) -> dict[str, Any]:
    pares = [(r["esperada"], r["predicha"]) for r in resultados]
    matriz = matriz_de_confusion(pares, CATEGORIAS)
    clases = por_categoria(matriz)
    con_datos = [m for c, m in clases.items() if c in CATEGORIAS and m["soporte"]]
    aciertos = sum(e == p for e, p in pares)
    mayoritaria = Counter(e for e, _ in pares).most_common(1)[0][1] if pares else 0
    return {
        "consultas": len(pares),
        "exactitud": aciertos / len(pares) if pares else None,
        "exactitud_clase_mayoritaria": mayoritaria / len(pares) if pares else None,
        "kappa": kappa([e for e, _ in pares], [p for _, p in pares]) if pares else None,
        "f1_macro": sum((m["f1"] or 0) for m in con_datos) / len(con_datos) if con_datos else None,
        "por_categoria": clases,
        "matriz": matriz,
    }


def escenarios_de_agente(escenarios: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Un turno, sesión válida o ninguna, que responde un agente con su categoría esperada."""
    return [
        e
        for e in escenarios
        if len(e["turnos"]) == 1
        and e.get("categoria_esperada") in NODOS_DE_AGENTE
        and e["comportamiento_esperado"] == "responder"
        and e.get("sesion") != "TOKEN_INVALIDO"
        and not e.get("adjunto")
        and not e.get("falla_inyectada")
        and not e.get("categorias_esperadas")
    ]


def settings_de_componentes(settings: Settings) -> Settings:
    """La configuración de los componentes, con el modo de evaluación encendido: así el agente
    guarda los fragmentos, los datos de las herramientas y las notas que el juez necesita, como
    en el nivel de sistema (F1, ADR-25)."""
    return settings.model_copy(update={"modo_evaluacion": True})


def correr_agente(deps: Dependencias, esc: dict[str, Any]) -> dict[str, Any]:
    """El turno del escenario directo contra el nodo de su categoría."""
    categoria = esc["categoria_esperada"]
    texto = esc["turnos"][0]["usuario"]
    contribuyente, predios = sesiones().get(esc.get("sesion") or "", (None, []))
    conversacion = f"componentes-{esc['id']}"
    estado = dict(entrada_de_turno(texto, conversacion, contribuyente, predios))
    parte = {"categoria": categoria, "texto": texto, "busqueda": texto}
    estado.update(categoria=categoria, parte_actual=parte, categorias_pendientes=[])
    nodo = NODOS_DE_AGENTE[categoria](deps)
    with get_usage_metadata_callback() as uso:
        try:
            salida = nodo(estado, configuracion_de_hilo(conversacion, esc["reloj"]))
            parcial = (salida.get("respuestas_parciales") or [{}])[-1]
            error = None
        except Exception as e:
            parcial, error = {}, type(e).__name__
    tokens, costo = _costo(uso.usage_metadata)
    return {
        "escenario": esc["id"],
        "categoria": categoria,
        "respuesta": parcial.get("texto", ""),
        "suficiencia": parcial.get("suficiencia"),
        "contextos": parcial.get("contextos", []),
        "herramientas": parcial.get("herramientas", []),
        "notas": parcial.get("notas", []),
        "error": error,
        "tokens_por_modelo": tokens,
        "costo_usd": str(costo),
    }


def como_ensayo(resultado: dict[str, Any], esc: dict[str, Any]) -> dict[str, Any]:
    """El resultado del nodo con la forma de un ensayo, para el juez: con los fragmentos, los datos
    de las herramientas y las notas del sistema, igual que un turno del nivel de sistema."""
    return {
        "escenario": esc["id"],
        "ensayo": 1,
        "error": resultado["error"],
        "turnos": [
            {
                "usuario": esc["turnos"][0]["usuario"],
                "respuesta": resultado["respuesta"],
                "meta": {
                    "contextos": resultado["contextos"],
                    "herramientas": resultado.get("herramientas", []),
                    "notas": resultado.get("notas", []),
                },
            }
        ],
    }
