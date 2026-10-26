"""Precios de las API y costo de cada llamada, para reportar el gasto (sección 6.1).

Fuentes, consultadas en octubre de 2026:

- Anthropic: https://platform.claude.com/docs/en/about-claude/pricing (Sonnet 5.5, $2 y $10 por
  millón de tokens de entrada y de salida; Haiku 5.5, $0,10 y $0,50 con prompts de hasta 100.000
  tokens; Opus 5.5, $4 y $20).
- OpenAI: https://platform.openai.com/docs/pricing (`text-embedding-3-large`, $0,13 por millón).

Presupuesto del proyecto: US$25 en Anthropic y US$10 en OpenAI.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

MILLON = Decimal(1_000_000)
# Dólares por millón de tokens: (entrada, salida).
PRECIOS: dict[str, tuple[Decimal, Decimal]] = {
    "claude-sonnet-5-5": (Decimal("2"), Decimal("10")),
    "claude-haiku-5-5": (Decimal("0.10"), Decimal("0.50")),
    "claude-opus-5-5": (Decimal("4"), Decimal("20")),
    "text-embedding-3-large": (Decimal("0.13"), Decimal("0")),
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
