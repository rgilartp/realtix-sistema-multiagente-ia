"""Un turno por la API (sección 3.3, paso 1, y secciones 3.5 y 3.6).

Orden: conversación (y su dueño) → horario → modo humano → grafo → respuesta → registro.

- Fuera de horario (HOR-01 y HOR-02) responde el aviso con la próxima apertura: no ejecuta el grafo,
  no responde la consulta ni la transfiere. Esa respuesta también abre la conversación y lleva el
  aviso de IA si es la primera.
- Una conversación escalada ya no la atienden los agentes (ADR-12): el mensaje se guarda en el caso.
- El contribuyente nunca ve un error técnico (RNF-08): si algo falla fuera de lo previsto, se
  intenta registrar el caso con «fallo de servicio» y se entrega el aviso de transferencia aunque
  el registro falle.
"""

import logging
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from src.agents.agente import fuente_del_contrato
from src.agents.graph import configuracion_de_hilo
from src.agents.nodes.escalamiento import AVISO_TRANSFERENCIA, PREFACIOS
from src.agents.state import entrada_de_turno
from src.api.acceso import Sesion
from src.api.esquemas import AVISO_IA, Fuente, Meta, RespuestaChat
from src.api.evaluacion import EvaluacionTurno
from src.api.servicios import ServiciosAPI
from src.data.models import CasoEscalado
from src.integrations.costos import UsoPorNodo
from src.integrations.robustez import falla_inyectada
from src.integrations.trazas import nombres_de_sesion
from src.services.horario import Horario, RelojFijo
from src.services.resumen import construir_resumen

registro = logging.getLogger(__name__)

AVISO_MODO_HUMANO = (
    "Tu caso ya está en manos de un funcionario, que te responderá por este medio. Guardé tu "
    "mensaje en el caso para que lo vea."
)
AVISO_FALLA = f"{PREFACIOS['fallo de servicio']} {AVISO_TRANSFERENCIA}"


class ConversacionAjenaError(Exception):
    """La conversación es de otro contribuyente: no se mezclan los historiales."""


@dataclass(frozen=True)
class SolicitudTurno:
    id_conversacion: str
    mensaje: str
    sesion: Sesion | None = None
    evaluacion: EvaluacionTurno = EvaluacionTurno()
    documento_adjunto: dict[str, Any] | None = None
    solicitud_explicita: bool = False  # el botón «Hablar con un funcionario» (ADR-18)


def _ms(desde: float) -> int:
    return round((time.perf_counter() - desde) * 1000)


def abrir_conversacion(
    servicios: ServiciosAPI, id_conversacion: str, sesion: Sesion | None
) -> bool:
    """Crea la conversación si no existe y dice si es nueva. Una conversación sin dueño pasa al
    contribuyente que inicia sesión; una de otro contribuyente (o con sesión, pedida sin ella) no
    se puede usar."""
    almacen = servicios.almacen
    contribuyente = sesion.contribuyente_id if sesion else None
    if almacen.estado_conversacion(id_conversacion) is None:
        almacen.asegurar_conversacion(id_conversacion, contribuyente)
        return True
    dueno = almacen.contribuyente_de_conversacion(id_conversacion)
    if dueno is not None and dueno != contribuyente:
        raise ConversacionAjenaError
    if dueno is None and contribuyente is not None:
        almacen.asignar_contribuyente(id_conversacion, contribuyente)
    return False


def procesar_turno(servicios: ServiciosAPI, solicitud: SolicitudTurno) -> RespuestaChat:
    """Respuesta del turno con el contrato de la sección 3.8."""
    inicio = time.perf_counter()
    id_conversacion = solicitud.id_conversacion
    momento = solicitud.evaluacion.ahora or servicios.reloj.ahora()
    nueva = abrir_conversacion(servicios, id_conversacion, solicitud.sesion)
    aviso_ia = AVISO_IA if nueva else None

    def responder(
        texto: str, interlocutor: str, estado: str, meta: dict[str, Any] | None = None
    ) -> RespuestaChat:
        datos = {**(meta or {}), "version": servicios.version}
        datos["tiempos_ms"] = {"total": _ms(inicio), **datos.get("tiempos_ms", {})}
        respuesta = RespuestaChat(
            id_conversacion=id_conversacion,
            respuesta=texto,
            aviso_ia=aviso_ia,
            interlocutor=interlocutor,  # type: ignore[arg-type]
            estado=estado,  # type: ignore[arg-type]
            meta=Meta(**datos),
        )
        registrar_interaccion(servicios, respuesta, solicitud.evaluacion.escenario_id)
        return respuesta

    horario = Horario.desde_settings(servicios.settings, RelojFijo(momento))
    if not horario.en_horario():  # RNF-06 y RNF-07
        return responder(horario.aviso_fuera_de_horario(), "sistema", "fuera_de_horario")

    if servicios.almacen.estado_conversacion(id_conversacion) == "escalada":  # ADR-12
        caso = servicios.almacen.caso_de_conversacion(id_conversacion)
        if caso:
            servicios.almacen.guardar_mensaje(caso["id_caso"], "contribuyente", solicitud.mensaje)
        return responder(
            AVISO_MODO_HUMANO,
            "sistema",
            "escalada",
            {"caso_id": caso["id_caso"] if caso else None},
        )

    try:
        estado, tiempos, uso = correr_grafo(servicios, solicitud, momento)
    except Exception as error:  # RNF-08: nunca un error técnico
        registro.error(
            "Falla inesperada en el turno; se escala",
            extra={"id_conversacion": id_conversacion, "error": type(error).__name__},
        )
        caso_id = escalar_por_falla(servicios, id_conversacion)
        return responder(
            AVISO_FALLA,
            "agente",
            "escalada",
            {
                "motivo_escalamiento": "fallo de servicio",
                "caso_id": caso_id,
                "nivel_confianza": 0.0,
            },
        )
    texto, estado_api, meta = interpretar_estado(servicios, estado)
    meta["tiempos_ms"] = tiempos
    meta["agentes_invocados"] = list(tiempos)
    meta["tokens"] = uso.totales()
    meta["modelo_por_nodo"] = uso.modelo_por_nodo()
    return responder(texto, "agente", estado_api, meta)


def correr_grafo(
    servicios: ServiciosAPI, solicitud: SolicitudTurno, momento: datetime
) -> tuple[dict[str, Any], dict[str, int], UsoPorNodo]:
    """Ejecuta el grafo y mide cada nodo; devuelve el estado final, los tiempos y los tokens."""
    sesion = solicitud.sesion
    entrada = entrada_de_turno(
        solicitud.mensaje,
        solicitud.id_conversacion,
        sesion.contribuyente_id if sesion else None,
        sesion.predios if sesion else None,
        solicitud.documento_adjunto,
    )
    if solicitud.solicitud_explicita:
        entrada["marcas"] = {"solicitud_explicita": True}
    simulado = momento.isoformat() if solicitud.evaluacion.ahora else None
    config: dict[str, Any] = configuracion_de_hilo(solicitud.id_conversacion, simulado)
    uso = UsoPorNodo()
    config["callbacks"] = [uso]
    tiempos: dict[str, float] = {}
    with (
        nombres_de_sesion(sesion.nombres if sesion else ()),
        falla_inyectada(solicitud.evaluacion.falla),
    ):
        anterior = time.perf_counter()
        for actualizacion in servicios.grafo.stream(entrada, config, stream_mode="updates"):
            ahora = time.perf_counter()
            for nodo in actualizacion:  # el grafo es secuencial: un nodo por paso
                tiempos[nodo] = tiempos.get(nodo, 0.0) + (ahora - anterior) * 1000
            anterior = ahora
    estado = servicios.grafo.get_state(configuracion_de_hilo(solicitud.id_conversacion)).values
    return dict(estado), {n: round(t) for n, t in tiempos.items()}, uso


def interpretar_estado(
    servicios: ServiciosAPI, estado: dict[str, Any]
) -> tuple[str, str, dict[str, Any]]:
    """Texto, `estado` de la API y `meta` a partir del estado final del grafo."""
    marcas = estado.get("marcas", {})
    parciales = estado.get("respuestas_parciales", [])
    aprobadas = [p for p in parciales if p.get("aprobada")]
    escalada = bool(estado.get("requiere_escalamiento"))
    if escalada:
        estado_api = "escalada"
    elif any(p.get("rechazo_acceso") for p in parciales):
        estado_api = "rechazo_acceso"
    elif marcas.get("sesion_requerida"):
        estado_api = "aviso_sesion"
    elif marcas.get("no_tributario") or estado.get("categoria") == "fuera_de_alcance":
        estado_api = "fuera_de_alcance"
    elif any(p.get("suficiencia") == "aclaracion" for p in aprobadas):
        estado_api = "aclaracion"
    else:
        estado_api = "respondida"
    id_conversacion = estado["id_conversacion"]
    caso = servicios.almacen.caso_de_conversacion(id_conversacion) if escalada else None
    fuentes: list[dict[str, Any]] = []
    for parcial in aprobadas:
        propias = parcial.get("fuentes_contrato") or [
            fuente_del_contrato(f) for f in parcial.get("fuentes", [])
        ]
        fuentes += [f for f in propias if f not in fuentes]
    contextos = None
    if servicios.settings.modo_evaluacion:
        contextos = [c for p in parciales for c in p.get("contextos", [])]
    ocr = estado.get("datos_extraidos", {}).get("ocr")
    meta = {
        "categoria": next((p["categoria"] for p in parciales), None)
        or estado.get("categoria")
        or None,
        "nivel_confianza": round(float(estado.get("nivel_confianza") or 0.0), 3),
        "motivo_escalamiento": estado.get("motivo_escalamiento") if escalada else None,
        "caso_id": caso["id_caso"] if caso else None,
        "fuentes": [Fuente(**f) for f in fuentes],
        "contextos": contextos,
        "datos_extraidos": ocr if isinstance(ocr, dict) else None,
    }
    return str(estado.get("respuesta_final") or ""), estado_api, meta


def escalar_por_falla(servicios: ServiciosAPI, id_conversacion: str) -> str | None:
    """Registra el caso de una falla inesperada; si tampoco se puede, sigue sin él."""
    resumen, resumen_json = construir_resumen(
        motivo="fallo de servicio",
        categoria=None,
        nivel_confianza=0.0,
        intentos=0,
        resueltas=[],
        rechazadas=[],
    )
    caso = CasoEscalado(
        id_caso=f"CASO-{id_conversacion}",
        id_conversacion=id_conversacion,
        resumen=resumen,
        nivel_confianza=0.0,
        motivo="fallo de servicio",
        resumen_json=resumen_json,
        fecha_escalamiento=datetime.now(UTC),
    )
    try:
        servicios.adaptador.registrar_caso_escalado(caso)
    except Exception as error:
        registro.error(
            "Tampoco se pudo registrar el caso; se entrega el aviso",
            extra={"id_conversacion": id_conversacion, "error": type(error).__name__},
        )
        return None
    return caso.id_caso


def registrar_interaccion(
    servicios: ServiciosAPI, respuesta: RespuestaChat, escenario_id: str | None
) -> None:
    """Una fila por turno, sin texto ni datos personales (ADR-11); si falla, no rompe el turno."""
    meta = respuesta.meta
    try:
        servicios.almacen.registrar_interaccion(
            respuesta.id_conversacion,
            meta.tiempos_ms.get("total", 0),
            meta.categoria,
            meta.nivel_confianza,
            respuesta.estado == "escalada",
            escenario_id=escenario_id,
            estado=respuesta.estado,
            motivo=meta.motivo_escalamiento,
            agentes=meta.agentes_invocados,
            tiempos_ms=meta.tiempos_ms,
            tokens=meta.tokens,
            modelos=meta.modelo_por_nodo,
        )
    except Exception as error:
        registro.error(
            "No se pudo registrar la interacción",
            extra={"id_conversacion": respuesta.id_conversacion, "error": type(error).__name__},
        )
