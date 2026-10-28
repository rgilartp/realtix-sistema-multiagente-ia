"""Resumen del caso para el funcionario, sin modelo (RF-ESC-03).

Texto y JSON salen de los mismos datos. No lleva el texto de los mensajes del contribuyente ni
datos personales: solo el motivo, la categoría, el nivel, los intentos y las partes del turno.
"""

import re
from collections.abc import Mapping, Sequence
from typing import Any


def _decimal_con_coma(valor: float) -> str:
    """Dos decimales con la coma decimal del español, como el resto del sistema (F12)."""
    return f"{valor:.2f}".replace(".", ",")


def construir_resumen(
    *,
    motivo: str,
    categoria: str | None,
    nivel_confianza: float,
    intentos: int,
    resueltas: Sequence[Mapping[str, Any]],
    rechazadas: Sequence[Mapping[str, Any]],
    motivo_original: str | None = None,
) -> tuple[str, dict[str, Any]]:
    """Devuelve el resumen en texto y en JSON (la bandeja de B9 muestra ambos)."""
    texto = (
        f"Motivo: {motivo}. Categoría: {categoria or 'sin clasificar'}. "
        f"Nivel de confianza: {_decimal_con_coma(nivel_confianza)}. "
        f"Reclasificaciones: {intentos}. "
        f"Partes ya resueltas: {len(resueltas)}. Partes rechazadas: {len(rechazadas)}."
    )
    datos: dict[str, Any] = {
        "motivo": motivo,
        "categoria": categoria,
        "nivel_confianza": nivel_confianza,
        "intentos": intentos,
        "partes_resueltas": [p["texto"] for p in resueltas],
        "partes_rechazadas": [
            {"categoria": p["categoria"], "texto": p["texto"], "nivel": p.get("nivel")}
            for p in rechazadas
        ],
    }
    if motivo_original is not None:
        datos["motivo_original"] = motivo_original
    return texto, datos


def codigo_de_caso(id_conversacion: str) -> str:
    """Número corto del caso para el contribuyente: los 6 últimos caracteres del último tramo
    alfanumérico de la conversación, en mayúsculas. Es un pedazo literal del identificador del caso,
    así que el funcionario lo encuentra con el buscador de la bandeja (no distingue mayúsculas)."""
    tramos = re.findall(r"[0-9A-Za-z]+", id_conversacion) or [id_conversacion]
    return tramos[-1][-6:].upper()
