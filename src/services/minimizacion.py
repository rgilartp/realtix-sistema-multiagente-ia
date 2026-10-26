"""Minimización de lo que se envía a los modelos (RNF-03 · Protección de datos personales).

Las herramientas le entregan al modelo solo matrícula, vigencias, valores y estados; nunca el
nombre, el documento ni la dirección. Lista blanca: un campo que no esté aquí no sale.
"""

from dataclasses import fields, is_dataclass
from datetime import date
from decimal import Decimal
from typing import Any

CAMPOS_PERMITIDOS = frozenset(
    {
        "matricula_catastral", "obligaciones_pendientes", "saldo_total_pendiente", "obligaciones",
        "tipo_tributo", "vigencia_fiscal", "base_gravable", "tarifa_por_mil", "valor_liquidado",
        "descuento_pronto_pago", "fecha_limite_descuento", "fecha_limite_pago", "estado_pago",
        "periodicidad", "en_spac", "avaluo_catastral", "fecha_pago", "valor_pagado", "medio_pago",
        "actividad_economica", "descripcion", "vigencia", "fuente", "grupo", "estrato", "destino",
    }
)  # fmt: skip
PROHIBIDOS = frozenset(
    {
        "nombre", "numero_documento", "tipo_documento", "id_contribuyente", "contribuyente",
        "contribuyente_id", "direccion", "chip", "localidad",
    }
)  # fmt: skip


def minimizar(valor: Any) -> Any:
    """Copia el valor dejando solo los campos permitidos, con tipos serializables."""
    if is_dataclass(valor) and not isinstance(valor, type):
        return minimizar({f.name: getattr(valor, f.name) for f in fields(valor)})
    if isinstance(valor, dict):
        return {k: minimizar(v) for k, v in valor.items() if k in CAMPOS_PERMITIDOS}
    if isinstance(valor, list | tuple):
        return [minimizar(v) for v in valor]
    if isinstance(valor, Decimal):
        return str(valor)
    if isinstance(valor, date):
        return valor.isoformat()
    return valor
