"""LangSmith con metadatos y anonimizador (RF-OBS-01 y RNF-05 · Registro auditable).

Las trazas llevan el `id_conversacion`, nunca el `contribuyente_id`, y un anonimizador enmascara
cédulas, NIT y nombres en las entradas y las salidas. La prueba de trazas de B12 lo verifica.
"""

import re
from collections.abc import Iterable
from typing import Any

from langsmith import Client

from src.config import Settings

MASCARA_DOCUMENTO = "[DOCUMENTO]"
MASCARA_NOMBRE = "[NOMBRE]"
PROHIBIDOS_EN_METADATOS = frozenset({"contribuyente_id", "id_contribuyente", "nombre"})
# Documentos con tipo: CC-1000000003, NIT-9000000012, NIT 900.123.456-7, cédula 1.020.304.050.
CON_TIPO = re.compile(r"\b(?:CC|CE|TI|PA|NIT)[-\s:]*\d[\d.]{5,}(?:-\d)?", re.IGNORECASE)
CON_PALABRA = re.compile(
    r"(\b(?:c[eé]dula|nit|documento|identificaci[oó]n)\b[^\d\n]{0,15})\d[\d.]{5,}(?:-\d)?",
    re.IGNORECASE,
)
SIN_ROTULO = re.compile(r"(?<![\w$.\-])(?:\d{1,3}(?:\.\d{3}){3}|\d{9,10})(?![\w.\-])")


class Anonimizador:
    """Enmascara documentos y los nombres conocidos en cualquier estructura de texto."""

    def __init__(self, nombres: Iterable[str] = ()) -> None:
        limpios = sorted({n.strip() for n in nombres if len(n.strip()) > 2}, key=len, reverse=True)
        self._nombres = (
            re.compile("|".join(re.escape(n) for n in limpios), re.IGNORECASE) if limpios else None
        )

    def texto(self, valor: str) -> str:
        valor = CON_TIPO.sub(MASCARA_DOCUMENTO, valor)
        valor = CON_PALABRA.sub(lambda m: m.group(1) + MASCARA_DOCUMENTO, valor)
        valor = SIN_ROTULO.sub(MASCARA_DOCUMENTO, valor)
        if self._nombres:
            valor = self._nombres.sub(MASCARA_NOMBRE, valor)
        return valor

    def __call__(self, valor: Any) -> Any:
        if isinstance(valor, str):
            return self.texto(valor)
        if isinstance(valor, dict):
            return {k: self(v) for k, v in valor.items()}
        if isinstance(valor, list | tuple):
            return [self(v) for v in valor]
        return valor


def metadatos_de_traza(
    id_conversacion: str, escenario_id: str | None = None, version: str = "dev", **otros: Any
) -> dict[str, Any]:
    """Metadatos de LangSmith: conversación, escenario y versión; nunca el contribuyente."""
    metadatos = {
        "id_conversacion": id_conversacion,
        "escenario_id": escenario_id,
        "version": version,
        **{k: v for k, v in otros.items() if k not in PROHIBIDOS_EN_METADATOS},
    }
    return metadatos


def crear_cliente_langsmith(settings: Settings, anonimizador: Anonimizador) -> Client | None:
    """Cliente de LangSmith con el anonimizador en entradas y salidas; `None` si está apagado."""
    if not settings.langsmith_tracing or settings.langsmith_api_key is None:
        return None
    return Client(
        api_key=settings.langsmith_api_key.get_secret_value(),
        hide_inputs=anonimizador,
        hide_outputs=anonimizador,
    )
