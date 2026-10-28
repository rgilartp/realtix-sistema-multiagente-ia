"""Un turno por la API (sección 3.3, paso 1, y secciones 3.5 y 3.6).

Orden: conversación (y su dueño) → horario → modo humano → grafo → respuesta → registro.

- Fuera de horario (HOR-01 y HOR-02) responde el aviso con la próxima apertura: no ejecuta el grafo,
  no responde la consulta ni la transfiere. Esa respuesta también abre la conversación y lleva el
  aviso de IA si es la primera.
- Una conversación escalada ya no la atienden los agentes (ADR-12): el mensaje se guarda en el caso.
- El contribuyente nunca ve un error técnico (RNF-08): si algo falla fuera de lo previsto, se
  intenta registrar el caso con «fallo de servicio» y se entrega el aviso de transferencia; si el
  registro falla, el aviso lo dice y no da un número de caso.
"""

import logging
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from src.agents.agente import fuente_del_contrato
from src.agents.dependencias import Dependencias
from src.agents.graph import configuracion_de_hilo
from src.agents.nodes.escalamiento import crear_nodo_escalamiento
from src.agents.state import entrada_de_turno
from src.api.acceso import Sesion, SesionNoVerificada
from src.api.esquemas import AVISO_IA, Fuente, Meta, RespuestaChat
from src.api.evaluacion import EvaluacionTurno
from src.api.servicios import ServiciosAPI
from src.integrations.costos import UsoPorNodo
from src.integrations.robustez import falla_inyectada
from src.integrations.trazas import metadatos_de_traza, nombres_de_sesion
from src.services.horario import Horario, RelojFijo

registro = logging.getLogger(__name__)

AVISO_MODO_HUMANO = (
    "Tu caso ya está registrado para un funcionario. Guardé tu mensaje en el caso para que lo vea."
)
AVISO_SESION_NO_VERIFICADA = (
    "En este momento no pude verificar tu sesión de la Oficina Virtual Tributaria. Intenta de "
    "nuevo en unos minutos."
)


class ConversacionAjenaError(Exception):
    """La conversación es de otro contribuyente: no se mezclan los historiales."""


@dataclass(frozen=True)
class SolicitudTurno:
    id_conversacion: str
    mensaje: str
    sesion: Sesion | SesionNoVerificada | None = None
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
    if isinstance(solicitud.sesion, SesionNoVerificada):
        # El adaptador no respondió al cargar los predios: no se adivina la sesión ni se toca la
        # conversación; el contribuyente recibe un aviso, no un error (RNF-08).
        nueva = servicios.almacen.estado_conversacion(id_conversacion) is None
        return RespuestaChat(
            id_conversacion=id_conversacion,
            respuesta=AVISO_SESION_NO_VERIFICADA,
            aviso_ia=AVISO_IA if nueva else None,
            interlocutor="sistema",
            estado="aviso_sesion",
            meta=Meta(version=servicios.version, tiempos_ms={"total": _ms(inicio)}),
        )
    nueva = abrir_conversacion(servicios, id_conversacion, solicitud.sesion)
    aviso_ia = AVISO_IA if nueva else None

    por_modelo: dict[str, dict[str, int]] = {}

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
        registrar_interaccion(servicios, respuesta, solicitud.evaluacion.escenario_id, por_modelo)
        return respuesta

    escalada = servicios.almacen.estado_conversacion(id_conversacion) == "escalada"
    caso = servicios.almacen.caso_de_conversacion(id_conversacion) if escalada else None
    if caso:  # ADR-12 y sección 3.6: cada mensaje nuevo se guarda en el caso, a cualquier hora
        servicios.almacen.guardar_mensaje(caso["id_caso"], "contribuyente", solicitud.mensaje)

    horario = Horario.desde_settings(servicios.settings, RelojFijo(momento))
    if not horario.en_horario():  # RNF-06 y RNF-07
        return responder(horario.aviso_fuera_de_horario(), "sistema", "fuera_de_horario")

    if escalada:  # ADR-12: los agentes ya no responden
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
        texto, caso_id = escalar_por_falla(servicios, id_conversacion)
        return responder(
            texto,
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
    por_modelo.update(uso.por_modelo())
    if servicios.settings.modo_evaluacion:  # el costo de una corrida contra el despliegue
        meta["tokens_por_modelo"] = uso.por_modelo()
    return responder(texto, "agente", estado_api, meta)


def correr_grafo(
    servicios: ServiciosAPI, solicitud: SolicitudTurno, momento: datetime
) -> tuple[dict[str, Any], dict[str, int], UsoPorNodo]:
    """Ejecuta el grafo y mide cada nodo; devuelve el estado final, los tiempos y los tokens."""
    sesion = solicitud.sesion if isinstance(solicitud.sesion, Sesion) else None
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
    config["callbacks"] = [uso, *servicios.trazadores()]
    # Metadatos de LangSmith (sección 3.13): conversación, escenario y versión; nunca el
    # contribuyente.
    config["metadata"] = metadatos_de_traza(
        solicitud.id_conversacion, solicitud.evaluacion.escenario_id, servicios.version
    )
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
    contextos = herramientas = notas = reescrituras = None
    if servicios.settings.modo_evaluacion:  # lo que usó el sistema, para el juez y RAGAS
        contextos = [c for p in parciales for c in p.get("contextos", [])]
        herramientas = [h for p in aprobadas for h in p.get("herramientas", [])]
        notas = [n for p in aprobadas for n in p.get("notas", [])]
        reescrituras = sum(p.get("reescrituras", 0) for p in parciales)  # F5
    ocr = estado.get("datos_extraidos", {}).get("ocr")
    meta = {
        "categoria": marcas.get("categoria_clasificada")
        or next((p["categoria"] for p in parciales), None)
        or estado.get("categoria")
        or None,
        "nivel_confianza": round(float(estado.get("nivel_confianza") or 0.0), 3),
        "motivo_escalamiento": estado.get("motivo_escalamiento") if escalada else None,
        "caso_id": caso["id_caso"] if caso else None,
        "fuentes": [Fuente(**f) for f in fuentes],
        "contextos": contextos,
        "herramientas": herramientas,
        "notas": notas,
        "reescrituras": reescrituras,
        "datos_extraidos": ocr if isinstance(ocr, dict) else None,
    }
    return str(estado.get("respuesta_final") or ""), estado_api, meta


def escalar_por_falla(servicios: ServiciosAPI, id_conversacion: str) -> tuple[str, str | None]:
    """Si el grafo se cae, la API ejecuta la función de `nodo_escalamiento` con «fallo de
    servicio»: el caso lo sigue registrando solo ese nodo (ADR-18), que nunca falla y entrega el
    aviso aunque el registro falle (RNF-08). Devuelve el texto y el caso, si se registró."""
    nodo = crear_nodo_escalamiento(Dependencias(servicios.adaptador))
    salida = nodo(
        {
            "id_conversacion": id_conversacion,
            "motivo_escalamiento": "fallo de servicio",
            "marcas": {"fallo_servicio": True},
            "respuestas_parciales": [],
            "categoria": "",
            "intentos_clasificacion": 0,
        }
    )
    registrado = not salida["marcas"].get("registro_fallido")
    return salida["respuesta_final"], f"CASO-{id_conversacion}" if registrado else None


def registrar_interaccion(
    servicios: ServiciosAPI,
    respuesta: RespuestaChat,
    escenario_id: str | None,
    por_modelo: dict[str, dict[str, int]] | None = None,
) -> None:
    """Una fila por turno, sin texto ni datos personales (ADR-11); si falla, no rompe el turno.
    Los tokens guardan también el desglose por modelo, para calcular el costo."""
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
            tokens={**meta.tokens, "por_modelo": por_modelo or {}},
            modelos=meta.modelo_por_nodo,
        )
    except Exception as error:
        registro.error(
            "No se pudo registrar la interacción",
            extra={"id_conversacion": respuesta.id_conversacion, "error": type(error).__name__},
        )
