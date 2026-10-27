"""Contrato de la API (sección 3.8): nombres de campos, estados e interlocutores tal cual."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

Interlocutor = Literal["agente", "funcionario", "sistema"]
Estado = Literal[
    "respondida",
    "aclaracion",
    "escalada",
    "rechazo_acceso",
    "aviso_sesion",
    "fuera_de_horario",
    "fuera_de_alcance",
]
PATRON_ID = r"^[A-Za-z0-9_-]+$"
ID_CONVERSACION = Field(min_length=1, max_length=64, pattern=PATRON_ID)
AVISO_IA = (
    "Te atiende un asistente de inteligencia artificial. Sus respuestas son orientativas y "
    "puedes pedir que te atienda un funcionario en cualquier momento"
)


class SolicitudMensaje(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id_conversacion: str = ID_CONVERSACION
    mensaje: str = Field(min_length=1, max_length=2000)


class SolicitudEscalamiento(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id_conversacion: str = ID_CONVERSACION


class Fuente(BaseModel):
    norma: str
    articulo: str | None = None
    coleccion: str | None = None
    puntaje: float | None = None


class Meta(BaseModel):
    categoria: str | None = None
    agentes_invocados: list[str] = []
    nivel_confianza: float | None = None
    motivo_escalamiento: str | None = None
    caso_id: str | None = None
    fuentes: list[Fuente] = []
    contextos: list[str] | None = None  # solo en el modo de evaluación (RAGAS)
    herramientas: list[dict[str, Any]] | None = None  # solo en el modo de evaluación (juez)
    notas: list[str] | None = None  # solo en el modo de evaluación (juez)
    datos_extraidos: dict[str, Any] | None = None
    tiempos_ms: dict[str, int] = {}
    tokens: dict[str, int] = {}
    tokens_por_modelo: dict[str, dict[str, int]] | None = None  # solo en el modo de evaluación
    modelo_por_nodo: dict[str, str] = {}
    version: str = "dev"


class RespuestaChat(BaseModel):
    id_conversacion: str
    respuesta: str
    aviso_ia: str | None = None  # solo en la primera respuesta de la conversación
    interlocutor: Interlocutor
    estado: Estado
    meta: Meta = Meta()


class SolicitudSesionSimulada(BaseModel):
    model_config = ConfigDict(extra="forbid")
    usuario: str = Field(pattern=r"^U\d{2}$")


class SesionSimulada(BaseModel):
    token: str
    usuario: str
    expira_en_s: int


class UsuarioSimulado(BaseModel):
    usuario: str
    nombre: str  # sintético («Usuario de Prueba 01»)
    tipo_persona: str


class MensajeConversacion(BaseModel):
    indice: int
    autor: Literal["contribuyente", "agente", "funcionario", "sistema"]
    texto: str


class MensajesConversacion(BaseModel):
    id_conversacion: str
    estado: str
    mensajes: list[MensajeConversacion]
    siguiente: int  # el `desde` de la próxima consulta


class Detalle(BaseModel):
    """Cuerpo de un error, en español y sin detalles técnicos."""

    detalle: str
