"""Adaptador de datos: contrato de la Tabla 7 de arquitectura y su implementación sintética.

Los agentes solo hablan con `RealSitAdapter`. `MockRealSitAdapter` lee la base SQLite sintética
(solo lectura) y `RealSitEnMemoria` (memoria.py) sirve los mismos datos desde listas; el día que
Realtix dé acceso real se escribe otra implementación y los agentes no cambian (RF-SYS-05).

Todo método que expone datos de un predio recibe el `contribuyente_id` autenticado y valida la
propiedad antes de responder (RF-AUT-02). Esa regla vive una sola vez, en `AdaptadorBase`.
"""

import sqlite3
from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Protocol

from src.data.database import conexion
from src.data.models import (
    ESTADOS_VIGENTES,
    Ack,
    Avaluo,
    CasoEscalado,
    EstadoCuenta,
    ObligacionTributaria,
    Pago,
    Predio,
    Tarifa,
)
from src.services.errores import ActividadNoReconocidaError

__all__ = [
    "ActividadNoReconocidaError",
    "AdaptadorBase",
    "MockRealSitAdapter",
    "PredioInaccesibleError",
    "PredioNoAutorizadoError",
    "PredioNoEncontradoError",
    "RealSitAdapter",
    "RegistroDeCasos",
]

VIGENCIA_ACTUAL = 2026
MENSAJE_PREDIO_INACCESIBLE = (
    "No fue posible consultar el predio indicado. Verifica la matrícula catastral; solo puedo "
    "informarte sobre los predios asociados a tu sesión."
)


class PredioInaccesibleError(Exception):
    """Base de los dos rechazos de predio. Mismo mensaje para un predio ajeno y para uno
    inexistente, sin revelar si la matrícula existe (OC-06)."""

    def __init__(self) -> None:
        super().__init__(MENSAJE_PREDIO_INACCESIBLE)


class PredioNoEncontradoError(PredioInaccesibleError):
    """El predio no existe."""


class PredioNoAutorizadoError(PredioInaccesibleError):
    """El predio existe pero no es del contribuyente autenticado (RF-AUT-02). Regla vigente
    (D3): rechazo explícito, sin revelar datos y sin escalar."""


class RegistroDeCasos(Protocol):
    """Lo que el adaptador necesita del almacén propio para registrar un caso (ADR-05)."""

    def registrar_caso(self, caso: CasoEscalado) -> None: ...


class RealSitAdapter(ABC):
    """Contrato de la Tabla 7 de arquitectura."""

    @abstractmethod
    def get_predios_contribuyente(self, contribuyente_id: str) -> list[Predio]: ...

    @abstractmethod
    def get_estado_cuenta(self, predio_id: str, contribuyente_id: str) -> EstadoCuenta: ...

    @abstractmethod
    def get_historial_pagos(self, predio_id: str, contribuyente_id: str) -> list[Pago]: ...

    @abstractmethod
    def get_avaluo_catastral(
        self, predio_id: str, contribuyente_id: str, vigencia: int | None = None
    ) -> Avaluo: ...

    @abstractmethod
    def get_tarifa_ica(self, actividad_economica: str) -> Tarifa: ...

    @abstractmethod
    def get_obligaciones_vigentes(
        self, predio_id: str, contribuyente_id: str, tributo: str
    ) -> list[ObligacionTributaria]: ...

    @abstractmethod
    def registrar_caso_escalado(self, resumen: CasoEscalado) -> Ack: ...


class AdaptadorBase(RealSitAdapter):
    """Reglas del contrato sobre un almacenamiento mínimo que cada implementación aporta."""

    def __init__(
        self, registro_casos: RegistroDeCasos | None = None, vigencia: int = VIGENCIA_ACTUAL
    ):
        self._registro_casos = registro_casos
        self._vigencia = vigencia

    # -- almacenamiento: lo implementa cada subclase -------------------------------------

    @abstractmethod
    def _predio(self, matricula: str) -> Predio | None: ...

    @abstractmethod
    def _predios_de(self, contribuyente_id: str) -> list[Predio]: ...

    @abstractmethod
    def _obligaciones(self, matricula: str) -> list[ObligacionTributaria]: ...

    @abstractmethod
    def _pagos(self, matricula: str) -> list[Pago]: ...

    @abstractmethod
    def _avaluo(self, matricula: str, vigencia: int) -> int | None: ...

    @abstractmethod
    def _tarifa_ica(self, codigo: str) -> Tarifa | None: ...

    # -- reglas comunes -------------------------------------------------------------------

    def _predio_o_falla(self, predio_id: str, contribuyente_id: str) -> Predio:
        predio = self._predio(predio_id)
        if predio is None:
            raise PredioNoEncontradoError()
        if predio.id_contribuyente != contribuyente_id:
            raise PredioNoAutorizadoError()
        return predio

    def get_predios_contribuyente(self, contribuyente_id: str) -> list[Predio]:
        return self._predios_de(contribuyente_id)

    def get_estado_cuenta(self, predio_id: str, contribuyente_id: str) -> EstadoCuenta:
        self._predio_o_falla(predio_id, contribuyente_id)
        obligaciones = sorted(
            self._obligaciones(predio_id), key=lambda o: (-o.vigencia_fiscal, o.id_obligacion)
        )
        pagado: dict[str, int] = {}
        for pago in self._pagos(predio_id):
            pagado[pago.id_obligacion] = pagado.get(pago.id_obligacion, 0) + pago.valor_pagado
        pendientes = [o for o in obligaciones if o.estado_pago in ESTADOS_VIGENTES]
        saldo = sum(o.valor_liquidado - pagado.get(o.id_obligacion, 0) for o in pendientes)
        return EstadoCuenta(
            matricula_catastral=predio_id,
            contribuyente=contribuyente_id,
            obligaciones_pendientes=len(pendientes),
            saldo_total_pendiente=saldo,
            obligaciones=obligaciones,
        )

    def get_historial_pagos(self, predio_id: str, contribuyente_id: str) -> list[Pago]:
        self._predio_o_falla(predio_id, contribuyente_id)
        return sorted(self._pagos(predio_id), key=lambda p: (p.fecha_pago, p.id_pago), reverse=True)

    def get_avaluo_catastral(
        self, predio_id: str, contribuyente_id: str, vigencia: int | None = None
    ) -> Avaluo:
        self._predio_o_falla(predio_id, contribuyente_id)
        anio = vigencia or self._vigencia
        avaluo = self._avaluo(predio_id, anio)
        if avaluo is None:
            raise LookupError(f"No hay avalúo del predio para la vigencia {anio}.")
        return Avaluo(matricula_catastral=predio_id, avaluo_catastral=avaluo, vigencia_fiscal=anio)

    def get_tarifa_ica(self, actividad_economica: str) -> Tarifa:
        tarifa = self._tarifa_ica(actividad_economica)
        if tarifa is None:
            raise ActividadNoReconocidaError(actividad_economica)
        return tarifa

    def get_obligaciones_vigentes(
        self, predio_id: str, contribuyente_id: str, tributo: str
    ) -> list[ObligacionTributaria]:
        """Vigentes: pendientes o vencidas, de cualquier vigencia (M-01)."""
        self._predio_o_falla(predio_id, contribuyente_id)
        vigentes = [
            o
            for o in self._obligaciones(predio_id)
            if o.tipo_tributo == tributo and o.estado_pago in ESTADOS_VIGENTES
        ]
        return sorted(vigentes, key=lambda o: (-o.vigencia_fiscal, o.id_obligacion))

    def registrar_caso_escalado(self, resumen: CasoEscalado) -> Ack:
        """Delega en el almacén propio: la base de RealSit no se escribe (ADR-05)."""
        if self._registro_casos is None:
            raise RuntimeError("El adaptador no tiene un almacén para registrar casos.")
        self._registro_casos.registrar_caso(resumen)
        return Ack(ok=True, mensaje=f"Caso {resumen.id_caso} registrado para atención humana.")


def _predio(r: sqlite3.Row) -> Predio:
    return Predio(
        matricula_catastral=r["matricula_catastral"],
        chip=r["chip"],
        id_contribuyente=r["id_contribuyente"],
        direccion=r["direccion"],
        localidad=r["localidad"],
        estrato=r["estrato"],
        destino=r["destino"],
        avaluo_catastral=r["avaluo_catastral"],
        municipio=r["municipio"],
    )


def _obligacion(r: sqlite3.Row) -> ObligacionTributaria:
    limite_desc = r["fecha_limite_descuento"]
    return ObligacionTributaria(
        id_obligacion=r["id_obligacion"],
        matricula_catastral=r["matricula_catastral"],
        tipo_tributo=r["tipo_tributo"],
        vigencia_fiscal=r["vigencia_fiscal"],
        base_gravable=r["base_gravable"],
        tarifa_por_mil=Decimal(r["tarifa_por_mil"]),
        valor_liquidado=r["valor_liquidado"],
        descuento_pronto_pago=r["descuento_pronto_pago"],
        fecha_limite_descuento=date.fromisoformat(limite_desc) if limite_desc else None,
        fecha_limite_pago=date.fromisoformat(r["fecha_limite_pago"]),
        estado_pago=r["estado_pago"],
        periodicidad=r["periodicidad"],
        origen_tarifa=r["origen_tarifa"],
        en_spac=bool(r["en_spac"]),
    )


def _pago(r: sqlite3.Row) -> Pago:
    return Pago(
        id_pago=r["id_pago"],
        id_obligacion=r["id_obligacion"],
        fecha_pago=date.fromisoformat(r["fecha_pago"]),
        valor_pagado=r["valor_pagado"],
        medio_pago=r["medio_pago"],
    )


class MockRealSitAdapter(AdaptadorBase):
    """Implementación sobre la base SQLite sintética, siempre en solo lectura. Cada operación abre
    y cierra su conexión (H-01), así que una instancia sirve a varios hilos."""

    def __init__(
        self,
        db_path: str | Path,
        registro_casos: RegistroDeCasos | None = None,
        vigencia: int = VIGENCIA_ACTUAL,
    ) -> None:
        super().__init__(registro_casos, vigencia)
        self._db_path = Path(db_path)

    def _predio(self, matricula: str) -> Predio | None:
        with conexion(self._db_path) as c:
            fila = c.execute(
                "SELECT * FROM predio WHERE matricula_catastral = ?", (matricula,)
            ).fetchone()
        return _predio(fila) if fila else None

    def _predios_de(self, contribuyente_id: str) -> list[Predio]:
        with conexion(self._db_path) as c:
            filas = c.execute(
                "SELECT * FROM predio WHERE id_contribuyente = ? ORDER BY matricula_catastral",
                (contribuyente_id,),
            ).fetchall()
        return [_predio(f) for f in filas]

    def _obligaciones(self, matricula: str) -> list[ObligacionTributaria]:
        with conexion(self._db_path) as c:
            filas = c.execute(
                "SELECT * FROM obligacion_tributaria WHERE matricula_catastral = ?", (matricula,)
            ).fetchall()
        return [_obligacion(f) for f in filas]

    def _pagos(self, matricula: str) -> list[Pago]:
        with conexion(self._db_path) as c:
            filas = c.execute(
                """SELECT p.* FROM pago p
                   JOIN obligacion_tributaria o ON p.id_obligacion = o.id_obligacion
                   WHERE o.matricula_catastral = ?""",
                (matricula,),
            ).fetchall()
        return [_pago(f) for f in filas]

    def _avaluo(self, matricula: str, vigencia: int) -> int | None:
        with conexion(self._db_path) as c:
            fila = c.execute(
                "SELECT avaluo_catastral FROM avaluo_vigencia "
                "WHERE matricula_catastral = ? AND vigencia_fiscal = ?",
                (matricula, vigencia),
            ).fetchone()
        return fila["avaluo_catastral"] if fila else None

    def _tarifa_ica(self, codigo: str) -> Tarifa | None:
        with conexion(self._db_path) as c:
            fila = c.execute("SELECT * FROM tarifa_ica WHERE codigo_ciiu = ?", (codigo,)).fetchone()
        if fila is None:
            return None
        return Tarifa(
            actividad_economica=fila["codigo_ciiu"],
            tarifa_por_mil=Decimal(fila["tarifa_por_mil"]),
            descripcion=fila["actividad"],
            vigencia=fila["vigencia"],
            fuente=fila["fuente"],
            grupo=fila["grupo"],
        )
