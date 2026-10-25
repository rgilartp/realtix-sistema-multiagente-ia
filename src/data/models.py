"""
Modelo de datos del sistema multiagente de IA — Realtix.

Replica exactamente las entidades definidas en el Documento de Arquitectura
(Objetivo Específico 2, sección 5 / Figura 2): Contribuyente, Predio,
ObligacionTributaria, Pago, Conversacion y CasoEscalado.

Estas clases son simples contenedores de datos (dataclasses); la lógica de
acceso vive en adapter.py, no aquí.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Literal, Optional

TipoTributo = Literal["IPU", "ICA"]
EstadoPago = Literal["AL_DIA", "PENDIENTE", "VENCIDO"]


@dataclass
class Contribuyente:
    id_contribuyente: str          # PK — cédula o NIT
    tipo_documento: str            # "CC", "NIT", "CE"
    numero_documento: str
    nombre: str
    actividad_economica: Optional[str] = None  # solo si declara ICA


@dataclass
class Predio:
    matricula_catastral: str       # PK
    id_contribuyente: str          # FK -> Contribuyente
    direccion: str
    avaluo_catastral: int          # COP
    municipio: str = "Bogotá D.C."


@dataclass
class ObligacionTributaria:
    id_obligacion: str             # PK
    matricula_catastral: str       # FK -> Predio
    tipo_tributo: TipoTributo
    vigencia_fiscal: int           # año, p.ej. 2026
    valor_liquidado: int           # COP
    estado_pago: EstadoPago
    fecha_limite_pago: date


@dataclass
class Pago:
    id_pago: str                   # PK
    id_obligacion: str             # FK -> ObligacionTributaria
    fecha_pago: date
    valor_pagado: int              # COP
    medio_pago: str                # "PSE", "Corresponsal bancario", "Ventanilla"


@dataclass
class Conversacion:
    id_conversacion: str           # PK
    id_contribuyente: Optional[str]  # FK -> Contribuyente; None si no autenticado
    fecha_inicio: datetime
    categoria_detectada: Optional[str] = None


@dataclass
class CasoEscalado:
    id_caso: str                   # PK
    id_conversacion: str           # FK -> Conversacion
    resumen: str
    nivel_confianza: float
    fecha_escalamiento: datetime = field(default_factory=datetime.now)


# Tipos de retorno del adaptador (Tabla 7 del documento de arquitectura v2) --

@dataclass
class EstadoCuenta:
    matricula_catastral: str
    contribuyente: str             # identificador del contribuyente, no su nombre (M-06)
    obligaciones_pendientes: int
    saldo_total_pendiente: int
    obligaciones: list  # list[ObligacionTributaria]


@dataclass
class Avaluo:
    matricula_catastral: str
    avaluo_catastral: int
    vigencia_fiscal: int


@dataclass
class Tarifa:
    actividad_economica: str
    tarifa_por_mil: float          # tarifa ICA por mil sobre ingresos brutos
    descripcion: str


@dataclass
class Ack:
    ok: bool
    mensaje: str
