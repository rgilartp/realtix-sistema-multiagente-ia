"""Modelo de datos de RealSit simulado v2 (sección 4.1 de la especificación técnica).

Contenedores simples (dataclasses); el acceso vive en `adapter.py`. Los tipos de retorno del
adaptador siguen la Tabla 7 de arquitectura. El dinero va en pesos enteros y las tarifas en
`Decimal` (por mil).
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

TipoTributo = Literal["IPU", "ICA"]
EstadoPago = Literal["AL_DIA", "PENDIENTE", "VENCIDO", "NO_OBLIGADO"]
Destino = Literal["residencial", "comercial", "lote"]
TipoPersona = Literal["natural", "juridica"]
RegimenICA = Literal["comun_bimestral", "comun_anual", "preferencial"]
Periodicidad = Literal["anual", "bimestral"]
OrigenTarifa = Literal["oficial", "sintetica"]

ESTADOS_VIGENTES: tuple[str, ...] = ("PENDIENTE", "VENCIDO")


@dataclass
class Contribuyente:
    id_contribuyente: str  # PK: cédula o NIT, sintéticos
    tipo_documento: str  # "CC" o "NIT"
    numero_documento: str
    nombre: str
    tipo_persona: TipoPersona
    codigo_ciiu: str | None = None  # solo si declara ICA
    actividad_economica: str | None = None
    regimen_ica: RegimenICA | None = None


@dataclass
class Predio:
    matricula_catastral: str  # PK
    chip: str
    id_contribuyente: str  # FK -> Contribuyente
    direccion: str
    localidad: str
    estrato: int | None  # None en comerciales y lotes
    destino: Destino
    avaluo_catastral: int  # COP, de la vigencia actual
    municipio: str = "Bogotá D.C."


@dataclass
class ObligacionTributaria:
    id_obligacion: str  # PK
    matricula_catastral: str  # FK -> Predio
    tipo_tributo: TipoTributo
    vigencia_fiscal: int
    base_gravable: int  # IPU: avalúo; ICA: ingresos gravados del periodo
    tarifa_por_mil: Decimal
    valor_liquidado: int
    descuento_pronto_pago: int
    fecha_limite_descuento: date | None
    fecha_limite_pago: date
    estado_pago: EstadoPago
    periodicidad: Periodicidad = "anual"
    origen_tarifa: OrigenTarifa = "oficial"  # 'sintetica' en 2023 a 2025 (cambio 7)
    en_spac: bool = False  # IPU pagado por cuotas (SPAC)


@dataclass
class Pago:
    id_pago: str  # PK
    id_obligacion: str  # FK -> ObligacionTributaria
    fecha_pago: date
    valor_pagado: int
    medio_pago: str  # "PSE", "Corresponsal bancario", "Ventanilla"


@dataclass
class Conversacion:
    id_conversacion: str
    id_contribuyente: str | None
    fecha_inicio: datetime
    categoria_detectada: str | None = None


@dataclass
class CasoEscalado:
    id_caso: str
    id_conversacion: str
    resumen: str
    nivel_confianza: float  # 0.0 si escala antes de la confianza (ADR-13)
    fecha_escalamiento: datetime = field(default_factory=datetime.now)
    motivo: str = ""
    categoria: str | None = None
    resumen_json: dict[str, Any] = field(default_factory=dict)
    intentos: int = 0
    estado: str = "abierto"


# Tipos de retorno del adaptador (Tabla 7 de arquitectura) ---------------------------------


@dataclass
class EstadoCuenta:
    matricula_catastral: str
    contribuyente: str  # identificador del contribuyente, no su nombre (M-06)
    obligaciones_pendientes: int
    saldo_total_pendiente: int  # valor liquidado menos lo pagado, en pendientes y vencidas
    obligaciones: list[ObligacionTributaria]


@dataclass
class Avaluo:
    matricula_catastral: str
    avaluo_catastral: int
    vigencia_fiscal: int


@dataclass
class Tarifa:
    actividad_economica: str  # código CIIU
    tarifa_por_mil: Decimal
    descripcion: str
    vigencia: int = 2026
    fuente: str = ""
    grupo: str | None = None


@dataclass
class Ack:
    ok: bool
    mensaje: str
