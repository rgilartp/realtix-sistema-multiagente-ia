"""
Adaptador de datos — implementación del contrato de la Tabla 7 del
Documento de Arquitectura v2 (sección 8.1).

Los agentes (Fase 3, actividades 6.3.4 y 6.3.5) solo deben hablar con la
interfaz `RealSitAdapter`. Hoy la implementación concreta es
`MockRealSitAdapter`, sobre la base de datos sintética; el día que Realtix
otorgue acceso real, se escribe una `RealSitAdapter` concreta que hable con
el sistema real y los agentes no cambian una sola línea (RF-SYS-05).

Cada método que expone datos de un predio recibe el `contribuyente_id`
autenticado y valida la propiedad del predio antes de responder (sección 6.1
y Tabla 7 de arquitectura v2; RF-AUT-02).

Estado a octubre de 2026: versión de la actividad 6.3.1, con 6 métodos.
El séptimo, `get_predios_contribuyente` (decisión D1), y las correcciones
H-01 a H-06 y M-01, M-02, M-03 y M-07 se aplican en el Paso 2 del plan de
desarrollo. Ver ESTADO_DEL_CODIGO.md.
"""

from datetime import date
from abc import ABC, abstractmethod

from database import get_connection
from models import Ack, Avaluo, CasoEscalado, EstadoCuenta, ObligacionTributaria, Pago, Tarifa


class PredioNoEncontradoError(Exception):
    pass


class PredioNoAutorizadoError(Exception):
    """Se lanza cuando un contribuyente autenticado consulta un predio que no
    le pertenece (RF-AUT-02). Regla vigente (decisión D3, sección 6.1 de
    arquitectura v2): el sistema multiagente de IA rechaza la consulta con un
    mensaje explícito, sin revelar datos del predio y sin escalar; nunca la
    trata como un error técnico genérico."""
    pass


class RealSitAdapter(ABC):
    @abstractmethod
    def get_estado_cuenta(self, predio_id: str, contribuyente_id: str) -> EstadoCuenta: ...

    @abstractmethod
    def get_historial_pagos(self, predio_id: str, contribuyente_id: str) -> list[Pago]: ...

    @abstractmethod
    def get_avaluo_catastral(self, predio_id: str, contribuyente_id: str) -> Avaluo: ...

    @abstractmethod
    def get_tarifa_ica(self, actividad_economica: str) -> Tarifa: ...

    @abstractmethod
    def get_obligaciones_vigentes(self, predio_id: str, contribuyente_id: str, tributo: str) -> list[ObligacionTributaria]: ...

    @abstractmethod
    def registrar_caso_escalado(self, resumen: CasoEscalado) -> Ack: ...


class MockRealSitAdapter(RealSitAdapter):
    """Implementación sobre la base de datos sintética (SQLite). Lee los datos
    del contribuyente; su única escritura es el registro de casos escalados.
    Ver database.py y generate_synthetic_data.py."""

    def __init__(self, db_path=None):
        self._conn = get_connection(db_path) if db_path else get_connection()

    # -- helpers internos -----------------------------------------------

    def _predio_o_falla(self, predio_id: str, contribuyente_id: str) -> dict:
        row = self._conn.execute(
            "SELECT * FROM predio WHERE matricula_catastral = ?", (predio_id,)
        ).fetchone()
        if row is None:
            raise PredioNoEncontradoError(f"No existe el predio {predio_id}.")
        if row["id_contribuyente"] != contribuyente_id:
            raise PredioNoAutorizadoError(
                f"El predio {predio_id} no está asociado al contribuyente autenticado."
            )
        return dict(row)

    # -- contrato público (Tabla 7 de arquitectura v2) -------------------

    def get_estado_cuenta(self, predio_id: str, contribuyente_id: str) -> EstadoCuenta:
        predio = self._predio_o_falla(predio_id, contribuyente_id)
        rows = self._conn.execute(
            "SELECT * FROM obligacion_tributaria WHERE matricula_catastral = ? ORDER BY vigencia_fiscal DESC",
            (predio_id,),
        ).fetchall()
        obligaciones = [self._row_to_obligacion(r) for r in rows]
        pendientes = [o for o in obligaciones if o.estado_pago in ("PENDIENTE", "VENCIDO")]
        return EstadoCuenta(
            matricula_catastral=predio_id,
            contribuyente=contribuyente_id,
            obligaciones_pendientes=len(pendientes),
            saldo_total_pendiente=sum(o.valor_liquidado for o in pendientes),
            obligaciones=obligaciones,
        )

    def get_historial_pagos(self, predio_id: str, contribuyente_id: str) -> list[Pago]:
        self._predio_o_falla(predio_id, contribuyente_id)
        rows = self._conn.execute(
            """SELECT p.* FROM pago p
               JOIN obligacion_tributaria o ON p.id_obligacion = o.id_obligacion
               WHERE o.matricula_catastral = ? ORDER BY p.fecha_pago DESC""",
            (predio_id,),
        ).fetchall()
        return [
            Pago(id_pago=r["id_pago"], id_obligacion=r["id_obligacion"],
                 fecha_pago=date.fromisoformat(r["fecha_pago"]), valor_pagado=r["valor_pagado"], medio_pago=r["medio_pago"])
            for r in rows
        ]

    def get_avaluo_catastral(self, predio_id: str, contribuyente_id: str) -> Avaluo:
        predio = self._predio_o_falla(predio_id, contribuyente_id)
        return Avaluo(matricula_catastral=predio_id, avaluo_catastral=predio["avaluo_catastral"], vigencia_fiscal=2026)

    def get_tarifa_ica(self, actividad_economica: str) -> Tarifa:
        row = self._conn.execute(
            "SELECT * FROM tarifa_ica WHERE actividad_economica = ?", (actividad_economica,)
        ).fetchone()
        if row is None:
            raise ValueError(f"Actividad económica no reconocida: {actividad_economica}")
        return Tarifa(actividad_economica=row["actividad_economica"], tarifa_por_mil=row["tarifa_por_mil"], descripcion=row["descripcion"])

    def get_obligaciones_vigentes(self, predio_id: str, contribuyente_id: str, tributo: str) -> list[ObligacionTributaria]:
        self._predio_o_falla(predio_id, contribuyente_id)
        rows = self._conn.execute(
            "SELECT * FROM obligacion_tributaria WHERE matricula_catastral = ? AND tipo_tributo = ? ORDER BY vigencia_fiscal DESC",
            (predio_id, tributo),
        ).fetchall()
        return [self._row_to_obligacion(r) for r in rows]

    def registrar_caso_escalado(self, resumen: CasoEscalado) -> Ack:
        self._conn.execute(
            "INSERT INTO caso_escalado VALUES (?, ?, ?, ?, ?)",
            (resumen.id_caso, resumen.id_conversacion, resumen.resumen,
             resumen.nivel_confianza, resumen.fecha_escalamiento.isoformat()),
        )
        self._conn.commit()
        return Ack(ok=True, mensaje=f"Caso {resumen.id_caso} registrado para atención humana.")

    @staticmethod
    def _row_to_obligacion(r) -> ObligacionTributaria:
        return ObligacionTributaria(
            id_obligacion=r["id_obligacion"], matricula_catastral=r["matricula_catastral"],
            tipo_tributo=r["tipo_tributo"], vigencia_fiscal=r["vigencia_fiscal"],
            valor_liquidado=r["valor_liquidado"], estado_pago=r["estado_pago"],
            fecha_limite_pago=date.fromisoformat(r["fecha_limite_pago"]),
        )
