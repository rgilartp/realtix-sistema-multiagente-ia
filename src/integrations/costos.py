"""Precios de las API y costo de cada llamada, para reportar el gasto (sección 6.1).

Fuentes, consultadas en octubre de 2026:

- Anthropic: https://platform.claude.com/docs/en/about-claude/pricing (Sonnet 5.5, $2 y $10 por
  millón de tokens de entrada y de salida; Haiku 5.5, $0,10 y $0,50 con prompts de hasta 100.000
  tokens; Opus 5.5, $4 y $20).
- OpenAI: https://developers.openai.com/api/docs/pricing (`text-embedding-3-large`, $0,13 por
  millón; `gpt-4.1-mini`, el evaluador de RAGAS, $0,40 y $1,60; `gpt-4o-mini`, que no pasó la
  validación de A4, $0,15 y $0,60).

Haiku 5.5 cobra $0,50 y $2,50 con prompts de más de 100.000 tokens; los del sistema multiagente de
IA no pasan de unos 25.000.

Presupuesto del proyecto: US$25 en Anthropic y US$10 en OpenAI.
"""

import threading
from dataclasses import dataclass
from decimal import Decimal
from typing import Any
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

MILLON = Decimal(1_000_000)
# Dólares por millón de tokens: (entrada, salida).
PRECIOS: dict[str, tuple[Decimal, Decimal]] = {
    "claude-sonnet-5-5": (Decimal("2"), Decimal("10")),
    "claude-haiku-5-5": (Decimal("0.10"), Decimal("0.50")),
    "claude-opus-5-5": (Decimal("4"), Decimal("20")),
    "text-embedding-3-large": (Decimal("0.13"), Decimal("0")),
    "gpt-4o-mini": (Decimal("0.15"), Decimal("0.60")),
    "gpt-4.1-mini": (Decimal("0.40"), Decimal("1.60")),
}
PRESUPUESTO_USD = {"anthropic": Decimal("25"), "openai": Decimal("10")}


@dataclass(frozen=True)
class Uso:
    modelo: str
    entrada: int
    salida: int = 0

    @property
    def costo_usd(self) -> Decimal:
        return costo_usd(self.modelo, self.entrada, self.salida)


def costo_usd(modelo: str, entrada: int, salida: int = 0) -> Decimal:
    """Costo en dólares de una llamada; falla si el modelo no tiene precio registrado."""
    for prefijo, (p_entrada, p_salida) in PRECIOS.items():
        if modelo.startswith(prefijo):
            return (entrada * p_entrada + salida * p_salida) / MILLON
    raise KeyError(f"Sin precio registrado para «{modelo}».")


def usos_desde_metadatos(por_modelo: dict[str, Any]) -> list[Uso]:
    """Convierte la salida de `get_usage_metadata_callback()` (por modelo) en usos."""
    return [
        Uso(modelo, int(u.get("input_tokens", 0)), int(u.get("output_tokens", 0)))
        for modelo, u in por_modelo.items()
    ]


class UsoPorNodo(BaseCallbackHandler):
    """Tokens y modelo de cada llamada a un modelo, por nodo del grafo (`meta.tokens` y
    `meta.modelo_por_nodo` de la sección 3.8). El nodo sale del metadato `langgraph_node`."""

    def __init__(self) -> None:
        self._nodo_de: dict[UUID, str] = {}
        self.llamadas: list[tuple[str, str, int, int]] = []  # (nodo, modelo, entrada, salida)
        self._candado = threading.Lock()

    def on_chat_model_start(
        self,
        serialized: dict[str, Any],
        messages: list[list[Any]],
        *,
        run_id: UUID,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        with self._candado:
            self._nodo_de[run_id] = str((metadata or {}).get("langgraph_node") or "sin_nodo")

    def on_llm_end(self, response: LLMResult, *, run_id: UUID, **kwargs: Any) -> None:
        for generaciones in response.generations:
            for generacion in generaciones:
                mensaje = getattr(generacion, "message", None)
                uso = getattr(mensaje, "usage_metadata", None) or {}
                datos = getattr(mensaje, "response_metadata", None) or {}
                modelo = str(datos.get("model_name") or datos.get("model") or "desconocido")
                with self._candado:
                    nodo = self._nodo_de.get(run_id, "sin_nodo")
                    self.llamadas.append(
                        (nodo, modelo, int(uso.get("input_tokens", 0)),
                         int(uso.get("output_tokens", 0)))
                    )  # fmt: skip

    def totales(self) -> dict[str, int]:
        return {
            "entrada": sum(e for _, _, e, _ in self.llamadas),
            "salida": sum(s for _, _, _, s in self.llamadas),
        }

    def por_modelo(self) -> dict[str, dict[str, int]]:
        """Tokens de entrada y de salida por modelo (para el costo del turno)."""
        salida: dict[str, dict[str, int]] = {}
        for _, modelo, entrada, sal in self.llamadas:
            acumulado = salida.setdefault(modelo, {"entrada": 0, "salida": 0})
            acumulado["entrada"] += entrada
            acumulado["salida"] += sal
        return salida

    def modelo_por_nodo(self) -> dict[str, str]:
        return {nodo: modelo for nodo, modelo, _, _ in self.llamadas}

    def costo_usd(self) -> Decimal:
        return sum(
            (costo_usd(m, e, s) for _, m, e, s in self.llamadas if m != "desconocido"),
            Decimal(0),
        )
