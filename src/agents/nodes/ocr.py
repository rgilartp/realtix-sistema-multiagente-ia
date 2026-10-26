"""`nodo_ocr`: lectura del recibo, confirmación y contraste con la cuenta (RF-OCR-01 a RF-OCR-06).

Turno con adjunto:

1. legibilidad por código (resolución, recorte y desenfoque): si falla, rechazo con el motivo, sin
   llamar al modelo (RF-OCR-04);
2. lectura con el modelo de visión (Haiku 5.5): si no es un recibo predial o faltan campos,
   rechazo con el motivo;
3. los seis campos de RF-OCR-02, normalizados, se presentan y se pide la confirmación (RF-OCR-03).
   Quedan en `datos_extraidos["ocr"]`, sin el nombre del propietario ni la imagen.

Turno siguiente, sin adjunto: si el contribuyente confirma, se contrastan el avalúo y el valor
liquidado con la obligación del predial en el adaptador, sin modificarla; si dice que no, se
descartan los datos; si pregunta otra cosa, la parte no le corresponde y el orquestador la
reclasifica. El archivo lo borra la API al terminar la solicitud.

Sin modelos configurados, usa el simulado de B4 (las pruebas del grafo).
"""

import logging
from collections.abc import Callable
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import RunnableConfig
from PIL import Image

from src.agents.agente import hoy_del_turno
from src.agents.dependencias import Dependencias
from src.agents.herramientas import FUENTE_REALSIT
from src.agents.nodes._comun import (
    agregar_parcial,
    formatear_pesos,
    parcial,
    texto_de_la_parte,
)
from src.agents.nodes.general import AVISO_SESION
from src.agents.state import AgentState
from src.agents.vision import abrir_documento, leer_documento
from src.data.adapter import MENSAJE_PREDIO_INACCESIBLE, PredioInaccesibleError
from src.integrations.robustez import con_tiempo_y_reintento
from src.services import obligaciones
from src.services.documentos import (
    CamposRecibo,
    contrastar,
    interpretar_confirmacion,
    problemas_de_legibilidad,
    validar_campos,
)

registro = logging.getLogger(__name__)

MOTIVOS = {
    "no_es_recibo": "el documento no es un recibo predial",
    "recortado": "el recibo está recortado (falta una parte del documento)",
    "baja_resolucion": "la imagen tiene baja resolución",
    "desenfocado": "la imagen está desenfocada",
    "ilegible": "no se pueden leer los datos del recibo",
    "incompleto": "faltan datos del recibo",
}
ROTULOS = {
    "matricula": "Matrícula catastral",
    "vigencia": "Vigencia fiscal",
    "avaluo": "Avalúo catastral",
    "valor_liquidado": "Valor liquidado",
    "descuento": "Descuento por pronto pago",
    "fecha_limite": "Fecha límite de pago",
}
PEDIR_RECIBO = "Adjunta el recibo del predial que quieres revisar (JPG, PNG o PDF)."
DESCARTADOS = (
    "Entendido: no usaré esos datos. Vuelve a cargar el recibo en una foto más clara o en PDF, o "
    "pregúntame lo que necesites."
)


def leer_recibo(
    modelo: BaseChatModel, imagen: Image.Image, timeout_s: float
) -> tuple[CamposRecibo | None, list[str]]:
    """Legibilidad por código, lectura con el modelo y validación de los campos: los campos, o
    `None` con los problemas que explican el rechazo. Una falla del modelo se propaga."""
    problemas = problemas_de_legibilidad(imagen)
    if problemas:
        return None, list(problemas)
    salida = leer_documento(modelo, imagen, timeout_s)
    if not salida.es_recibo_predial:
        return None, ["no_es_recibo"]
    campos, invalidos = validar_campos(salida.campos.model_dump())
    if not salida.legible or campos is None:
        vistos: list[str] = list(salida.problemas)
        if not vistos:
            vistos = ["incompleto" if 0 < len(invalidos) < len(ROTULOS) else "ilegible"]
        return None, vistos
    return campos, []


def texto_de_rechazo(problemas: list[str]) -> str:
    """El motivo específico del rechazo y la petición de un nuevo intento (RF-OCR-04)."""
    motivos = [MOTIVOS[p] for p in dict.fromkeys(problemas) if p in MOTIVOS] or [
        MOTIVOS["ilegible"]
    ]
    lista = motivos[0] if len(motivos) == 1 else ", ".join(motivos[:-1]) + " y " + motivos[-1]
    return (
        f"No pude usar el documento: {lista}. Envía un nuevo intento con el recibo predial "
        "completo y legible (JPG, PNG o PDF)."
    )


def texto_de_confirmacion(campos: dict[str, str]) -> str:
    lineas = "\n".join(f"- {ROTULOS[c]}: {v}" for c, v in campos.items())
    return f"Estos son los datos que leí del recibo:\n{lineas}\n\n¿Es correcto?"


def _respuesta_simulada(state: AgentState) -> tuple[dict[str, Any], dict[str, Any]]:
    """El nodo de B4: no lee imágenes; devuelve los campos simulados del adjunto."""
    adjunto = state.get("documento_adjunto")
    datos = dict(state.get("datos_extraidos", {}))
    if not adjunto:
        return parcial("ocr", PEDIR_RECIBO, suficiencia="aclaracion"), datos
    datos["ocr"] = {"campos": dict(adjunto.get("campos_simulados", {})), "confirmado": False}
    texto = "Esto fue lo que leí del recibo. ¿Es correcto? (simulado)"
    return parcial("ocr", texto), datos


def crear_nodo_ocr(deps: Dependencias) -> Callable[..., dict[str, Any]]:
    timeout = deps.config.timeout_modelo_s

    def fallo(state: AgentState, etapa: str, error: BaseException) -> dict[str, Any]:
        registro.warning(
            "Falla de servicio en el agente OCR",
            extra={"id_conversacion": state.get("id_conversacion"), "etapa": etapa,
                   "error": type(error).__name__},
        )  # fmt: skip
        return parcial("ocr", "", suficiencia="no_pudo", cobertura=0.0, fallo_servicio=True)

    def rechazo(problemas: list[str]) -> dict[str, Any]:
        return parcial("ocr", texto_de_rechazo(problemas), suficiencia="aclaracion")

    def leer(state: AgentState, datos: dict[str, Any]) -> dict[str, Any]:
        adjunto = state["documento_adjunto"] or {}
        datos.pop("ocr", None)  # un documento nuevo reemplaza lo que estuviera por confirmar
        try:
            imagen = abrir_documento(adjunto["ruta"], adjunto.get("tipo", ""))
        except Exception:  # un archivo dañado no es una falla del servicio: no se puede leer
            return rechazo(["ilegible"])
        try:
            campos, problemas = leer_recibo(deps.modelos("ocr"), imagen, timeout)  # type: ignore[misc]
        except Exception as error:  # modelo, negativa o salida inválida (RNF-08)
            return fallo(state, "lectura", error)
        if campos is None:
            return rechazo(problemas)
        datos["ocr"] = {"campos": campos.como_texto(), "pendiente": True, "confirmado": False}
        return parcial("ocr", texto_de_confirmacion(campos.como_texto()), suficiencia="aclaracion")

    def confirmar(
        state: AgentState, datos: dict[str, Any], config: RunnableConfig | None
    ) -> dict[str, Any]:
        confirmacion = interpretar_confirmacion(texto_de_la_parte(state))
        if confirmacion == "no":
            datos.pop("ocr", None)
            return parcial("ocr", DESCARTADOS, suficiencia="aclaracion")
        if confirmacion is None:  # el orquestador solo envía respuestas claras
            return parcial("ocr", "", suficiencia="no_corresponde", cobertura=0.0)
        campos, _ = validar_campos(datos["ocr"]["campos"])
        contribuyente = state.get("contribuyente_id")
        if campos is None:  # no debería pasar: se guardaron ya validados
            datos.pop("ocr", None)
            return parcial("ocr", PEDIR_RECIBO, suficiencia="aclaracion")
        if not contribuyente:  # la sesión venció: el aviso de sesión (RF-AUT-04)
            datos.pop("ocr", None)
            return parcial("ocr", AVISO_SESION, suficiencia="aclaracion")
        try:
            estado = con_tiempo_y_reintento(
                lambda: deps.adaptador.get_estado_cuenta(campos.matricula, contribuyente),
                deps.config.timeout_adaptador_s,
                servicio="adaptador",
            )
            pagos = con_tiempo_y_reintento(
                lambda: deps.adaptador.get_historial_pagos(campos.matricula, contribuyente),
                deps.config.timeout_adaptador_s,
                servicio="adaptador",
            )
        except PredioInaccesibleError:  # el recibo es de un predio ajeno o inexistente (OC-06)
            datos.pop("ocr", None)
            return parcial("ocr", MENSAJE_PREDIO_INACCESIBLE, rechazo_acceso=True)
        except Exception as error:
            return fallo(state, "contraste", error)
        cuenta = obligaciones.de_tributo(estado, pagos, "IPU", hoy_del_turno(config, deps))
        texto = texto_del_contraste(campos, cuenta)
        datos["ocr"] = {**datos["ocr"], "pendiente": False, "confirmado": True}
        datos["predio"] = campos.matricula
        return parcial("ocr", texto, fuentes=(FUENTE_REALSIT,))

    def nodo_ocr(state: AgentState, config: RunnableConfig) -> dict[str, Any]:
        if deps.modelos is None:
            respuesta, datos = _respuesta_simulada(state)
        else:
            datos = dict(state.get("datos_extraidos", {}))
            if state.get("documento_adjunto"):
                respuesta = leer(state, datos)
            elif (datos.get("ocr") or {}).get("pendiente"):
                respuesta = confirmar(state, datos, config)
            else:
                respuesta = parcial("ocr", PEDIR_RECIBO, suficiencia="aclaracion")
        return {
            "respuestas_parciales": agregar_parcial(state, respuesta),
            "datos_extraidos": datos,
        }

    return nodo_ocr


def texto_del_contraste(campos: CamposRecibo, cuenta: obligaciones.CuentaTributo) -> str:
    """Resultado del contraste, con la situación del predio y las notas tal cual."""
    resultado = contrastar(campos, cuenta)
    inicio = (
        "Gracias por confirmar. Contrasté los datos del recibo con el estado de cuenta del predio "
        f"{campos.matricula}"
    )
    if not resultado.encontrada:
        texto = (
            f"{inicio}: no encontré una obligación del predial de {campos.vigencia} para ese "
            "predio, así que no puedo compararlos."
        )
    elif resultado.coinciden:
        texto = (
            f"{inicio}: el avalúo de {formatear_pesos(campos.avaluo)} y el valor liquidado de "
            f"{formatear_pesos(campos.valor_liquidado)} de la vigencia {campos.vigencia} coinciden."
        )
    else:
        nombres = {"avaluo": "el avalúo", "valor_liquidado": "el valor liquidado"}
        diferencias = "; ".join(
            f"{nombres[c]} del recibo es {formatear_pesos(r)} y el registrado es "
            f"{formatear_pesos(g)}"
            for c, r, g in resultado.diferencias
        )
        texto = (
            f"{inicio}: los datos no coinciden: {diferencias}. Si crees que hay un error, puedes "
            "pedir que te atienda un funcionario."
        )
    if resultado.vencidas:
        plural = "obligación vencida" if resultado.vencidas == 1 else "obligaciones vencidas"
        texto += (
            f" En el predial, el predio tiene {resultado.vencidas} {plural} con un saldo de "
            f"{formatear_pesos(resultado.saldo)}."
        )
    elif resultado.pendientes:
        texto += (
            f" En el predial, el predio tiene un saldo pendiente de "
            f"{formatear_pesos(resultado.saldo)}."
        )
    else:
        texto += " El predio está al día en el predial."
    for nota in cuenta.notas:
        texto += f"\n\n{nota}"
    return f"{texto}\n\nFuentes: {FUENTE_REALSIT}."
