"""`nodo_orquestador` simulado: clasifica por palabras clave, sin modelo ni red.

Plan: categoría o categorías con su parte de la consulta y su consulta de búsqueda (`busqueda`;
el clasificador simulado usa el mismo texto), y las marcas (sesión requerida,
solicitud explícita, pregunta por la IA, tributario fuera del MVP y municipio distinto de Bogotá).
Guarda la parte actual (`parte_actual`) para que cada worker responda la suya y, al reclasificar,
clasifica solo la parte rechazada (sección 3.3). B7 lo reemplaza por Sonnet 5.5 con la misma firma.
"""

import re
from collections.abc import Callable
from typing import Any

from src.agents.dependencias import Clasificacion, Dependencias
from src.agents.nodes._comun import MATRICULA, contiene, es_personal, normalizar, ultimo_texto
from src.agents.state import AgentState
from src.services.documentos import interpretar_confirmacion

SOLICITUD_EXPLICITA = (
    "hablar con una persona", "hablar con un funcionario", "hablar con un humano",
    "hablar con un asesor", "quiero un funcionario", "quiero un asesor", "quiero una persona",
    "pasame con", "transfiereme", "que me atienda un", "que me atienda una",
)  # fmt: skip
ACEPTACIONES = ("si", "claro", "por favor", "ok", "dale", "si por favor", "si, por favor")
PREGUNTA_IA = (
    "estoy hablando con una persona", "hablo con una persona", "eres una persona", "eres un robot",
    "eres humano", "eres un bot", "hablando con un humano", "eres una inteligencia artificial",
)  # fmt: skip
NO_TRIBUTARIO = ("clima", "receta", "futbol", "pelicula", "pico y placa", "licencia de conduccion")
TRIBUTARIO_FUERA_DEL_MVP = (
    "impuesto de renta", "declaracion de renta", "impuesto vehicular",
    "impuesto de vehiculos", "plusvalia", "valorizacion", "delineacion urbana", "aduana",
)  # fmt: skip
TRIBUTARIO_FUERA_PALABRA = re.compile(r"\b(renta|iva)\b")
OTROS_MUNICIPIOS = ("medellin", "cali", "barranquilla", "cartagena", "bucaramanga")
PALABRAS_IPU = ("predial", "predio", "avaluo", "matricula", "spac", "sobretasa", "impuesto predial")
PALABRAS_ICA = ("industria y comercio", "actividad economica", "ciiu", "retencion")
PALABRAS_OCR = ("recibo", "documento adjunto", "adjunto", "adjunte", "te envio")
PALABRAS_TRIBUTARIAS = PALABRAS_IPU + PALABRAS_ICA + ("impuesto", "tributo", "declarar")


def _tiene_ica(texto: str) -> bool:
    return bool(re.search(r"\bica\b", normalizar(texto))) or contiene(texto, PALABRAS_ICA)


def _tiene_ipu(texto: str) -> bool:
    return (
        bool(MATRICULA.search(texto))
        or contiene(texto, PALABRAS_IPU)
        or "ipu" in normalizar(texto).split()
    )


def _segmento(segmentos: list[str], detecta: Callable[[str], bool], completo: str) -> str:
    """Primer segmento donde aparece la categoría; si no, el texto completo."""
    return next((s for s in segmentos if detecta(s)), completo)


def clasificar_por_palabras(texto: str, state: AgentState) -> Clasificacion:
    """Clasificador simulado y determinista. Respeta las categorías ya descartadas."""
    marcas: dict[str, Any] = {}
    t = normalizar(texto)
    oferta = state.get("datos_extraidos", {}).get("oferta_transferencia")
    if contiene(texto, SOLICITUD_EXPLICITA) or (oferta and t.strip(" .,!¡") in ACEPTACIONES):
        marcas["solicitud_explicita"] = True
    if contiene(texto, PREGUNTA_IA):
        marcas["pregunta_ia"] = True
    otro_municipio = contiene(texto, OTROS_MUNICIPIOS)
    if otro_municipio:
        marcas["municipio_distinto"] = True
    if (
        contiene(texto, TRIBUTARIO_FUERA_DEL_MVP)
        or TRIBUTARIO_FUERA_PALABRA.search(t)
        or (otro_municipio and contiene(texto, PALABRAS_TRIBUTARIAS))
    ):
        marcas["tributario_fuera_mvp"] = True

    adjunto = state.get("documento_adjunto") is not None
    candidatas: list[str] = []
    if adjunto or contiene(texto, PALABRAS_OCR):
        candidatas.append("ocr")
    if _tiene_ipu(texto):
        candidatas.append("ipu")
    if _tiene_ica(texto):
        candidatas.append("ica")
    if not candidatas:
        if contiene(texto, NO_TRIBUTARIO):
            marcas["no_tributario"] = True
            candidatas.append("fuera_de_alcance")
        else:
            candidatas.append("general")
    if (es_personal(texto) or adjunto) and not state.get("contribuyente_id"):
        marcas["sesion_requerida"] = True
        candidatas = ["general"]
    if marcas.get("pregunta_ia"):
        candidatas = ["general"]
    descartadas = state.get("categorias_descartadas", [])
    segmentos = [x.strip() for x in re.split(r"\s+y\s+|;", texto) if x.strip()]
    detectores = {"ipu": _tiene_ipu, "ica": _tiene_ica}
    multiple = len(candidatas) > 1
    partes = [
        {
            "categoria": c,
            "texto": _segmento(segmentos, detectores[c], texto)
            if multiple and c in detectores
            else texto,
        }
        for c in candidatas
        if c not in descartadas
    ]
    return Clasificacion(partes or [{"categoria": "general", "texto": texto}], marcas)


def categoria_clasificada(clasificacion: Clasificacion, marcas: dict[str, Any]) -> str:
    """Una de las 5 clases de RF-ORQ-01: fuera de alcance si es no tributario o tributario fuera
    del MVP; si no, la de la primera parte."""
    if marcas.get("no_tributario") or marcas.get("tributario_fuera_mvp"):
        return "fuera_de_alcance"
    return clasificacion.partes[0]["categoria"] if clasificacion.partes else "general"


def crear_nodo_orquestador(deps: Dependencias) -> Callable[[AgentState], dict[str, Any]]:
    clasificar = deps.clasificador or clasificar_por_palabras
    maximo = deps.config.max_reclasificaciones

    def escalar(motivo: str, marcas: dict[str, Any], intentos: int, **extra: Any) -> dict[str, Any]:
        marcas["confianza_calculada"] = False  # ADR-13: sin confianza propia de esta parte
        return {
            "requiere_escalamiento": True,
            "motivo_escalamiento": motivo,
            "nivel_confianza": 0.0,
            "marcas": marcas,
            "intentos_clasificacion": intentos,
            **extra,
        }

    def nodo_orquestador(state: AgentState) -> dict[str, Any]:
        marcas = dict(state.get("marcas", {}))
        intentos = state.get("intentos_clasificacion", 0)
        pendientes = list(state.get("categorias_pendientes", []))
        datos = dict(state.get("datos_extraidos", {}))
        texto = ultimo_texto(state)

        if marcas.get("solicitud_explicita") and not state.get("respuestas_parciales"):
            # El botón «Hablar con un funcionario» (ADR-18): escala sin llamar al modelo.
            datos.pop("oferta_transferencia", None)
            return escalar("solicitud explícita", marcas, intentos, datos_extraidos=datos)
        if marcas.pop("reclasificar", False):
            if intentos >= maximo:
                return escalar("tope de reclasificaciones", marcas, intentos)
            intentos += 1
            # Solo se vuelve a clasificar la parte que el worker rechazó.
            texto = state.get("parte_actual", {}).get("texto") or texto
        elif pendientes:  # siguiente parte de una consulta multiagente
            siguiente = pendientes.pop(0)
            return {
                "categoria": siguiente["categoria"],
                "parte_actual": siguiente,
                "categorias_pendientes": pendientes,
            }

        ocr = datos.get("ocr") or {}
        if ocr.get("pendiente") and not state.get("documento_adjunto"):
            # Hay datos de un recibo por confirmar (RF-OCR-03). Un «sí» o un «no» claros van al
            # agente OCR, sin modelo y sin contar como reclasificación; cualquier otro mensaje (o
            # una transferencia ofrecida, o una petición de funcionario) hace vencer los datos y
            # se clasifica como siempre.
            confirmacion = interpretar_confirmacion(texto)
            if (
                confirmacion is None
                or datos.get("oferta_transferencia")
                or contiene(texto, SOLICITUD_EXPLICITA)
            ):
                datos["ocr"] = {**ocr, "pendiente": False}
                ocr = {}
        if ocr.get("pendiente") and not state.get("documento_adjunto"):
            parte = {"categoria": "ocr", "texto": texto, "busqueda": texto}
            return {
                "categoria": "ocr",
                "parte_actual": parte,
                "categorias_pendientes": [],
                "marcas": marcas,
                "intentos_clasificacion": intentos,
                "datos_extraidos": datos,
            }
        try:
            clasificacion = clasificar(texto, state)
        except Exception:  # fallo del modelo del orquestador (RNF-08)
            marcas["fallo_servicio"] = True
            return escalar("fallo de servicio", marcas, intentos)
        marcas.update(clasificacion.marcas)
        if not any(p.get("aprobada") for p in state.get("respuestas_parciales", [])):
            # La categoría de la clasificación, la que reporta la API (F2 de la corrida 1): lo no
            # tributario va a nodo_general (ADR-14), pero se clasificó fuera de alcance. Se guarda
            # antes de escalar y se actualiza si se reclasifica la primera parte.
            marcas["categoria_clasificada"] = categoria_clasificada(clasificacion, marcas)
        datos.pop("oferta_transferencia", None)

        if marcas.get("solicitud_explicita"):
            return escalar("solicitud explícita", marcas, intentos, datos_extraidos=datos)
        if marcas.get("tributario_fuera_mvp"):
            return escalar("fuera de alcance", marcas, intentos, datos_extraidos=datos)
        # Ninguna categoría responde dos veces la misma parte en un turno.
        vistas = {
            (p["categoria"], p.get("parte"))
            for p in state.get("respuestas_parciales", [])
            if p["suficiencia"] != "no_corresponde"
        } | {(p["categoria"], p["texto"]) for p in pendientes}
        partes: list[dict[str, str]] = []
        for parte in clasificacion.partes:
            clave = (parte["categoria"], parte["texto"])
            if clave not in vistas:
                vistas.add(clave)
                partes.append({**parte, "busqueda": parte.get("busqueda") or parte["texto"]})
        if not partes:  # nada nuevo que probar para esta parte
            return escalar("sin cobertura", marcas, intentos, datos_extraidos=datos)
        return {
            "categoria": partes[0]["categoria"],
            "parte_actual": partes[0],
            "categorias_pendientes": pendientes + partes[1:],
            "marcas": marcas,
            "intentos_clasificacion": intentos,
            "datos_extraidos": datos,
        }

    return nodo_orquestador
