"""Utilidades compartidas por los nodos simulados: texto, marcas y respuestas parciales."""

import re
import unicodedata
from typing import Any

from langchain_core.messages import HumanMessage

from src.agents.state import AgentState

MATRICULA = re.compile(r"\b50C-\d{7}\b", re.IGNORECASE)
PALABRAS_PERSONALES = (
    "mi predio", "mis predios", "mi impuesto", "cuanto debo", "cuanto pago", "mi saldo",
    "mi estado de cuenta", "mi recibo", "mis pagos", "mi avaluo", "mi factura", "debo",
    "pague", "mi apartamento", "mi casa",
)  # fmt: skip


def normalizar(texto: str) -> str:
    """Minúsculas y sin tildes, para comparar palabras clave."""
    sin_tildes = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in sin_tildes if unicodedata.category(c) != "Mn")


def contiene(texto: str, palabras: tuple[str, ...]) -> bool:
    t = normalizar(texto)
    return any(p in t for p in palabras)


def es_personal(texto: str) -> bool:
    """La consulta pide datos de la cuenta del contribuyente."""
    return bool(MATRICULA.search(texto)) or contiene(texto, PALABRAS_PERSONALES)


def ultimo_texto(state: AgentState) -> str:
    """Texto del último mensaje del contribuyente en el turno."""
    for mensaje in reversed(state.get("messages", [])):
        if isinstance(mensaje, HumanMessage):
            return str(mensaje.content)
    return ""


def formatear_pesos(valor: int) -> str:
    return "$" + f"{valor:,}".replace(",", ".")


def parcial(
    categoria: str,
    texto: str,
    *,
    fuentes: tuple[str, ...] = (),
    similitud: float | None = None,
    suficiencia: str = "completa",
    cobertura: float = 1.0,
    **banderas: Any,
) -> dict[str, Any]:
    """Respuesta parcial de un worker: texto, fuentes, factores de la confianza y banderas."""
    return {
        "categoria": categoria,
        "texto": texto,
        "fuentes": list(fuentes),
        "similitud": similitud,
        "suficiencia": suficiencia,
        "cobertura": cobertura,
        "rechazo_acceso": False,
        "fallo_servicio": False,
        "fuera_de_alcance": False,
        **banderas,
    }
