"""Almacén propio: conversaciones, casos escalados, mensajes del funcionario e interacciones.

Resuelve H-02 (registrar un caso crea la conversación si no existe) y OC-08 (un caso que escala
antes de calcular la confianza se guarda con `nivel_confianza = 0.0` y su motivo, ADR-13).
RealSit no se escribe nunca (ADR-05); este almacén es el único estado propio.
"""

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Engine, create_engine, insert, inspect, select, text, update
from sqlalchemy.pool import StaticPool

from src.data.models import CasoEscalado
from src.store.tablas import (
    caso_escalado,
    conversacion,
    interaccion,
    mensaje_funcionario,
    metadata,
)

ESTADOS_CONVERSACION = ("activa", "escalada", "cerrada")


def crear_motor(url: str) -> Engine:
    """Motor de SQLAlchemy. `postgresql://` usa el controlador psycopg 3; SQLite en memoria
    comparte una sola conexión para que varios hilos vean la misma base."""
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    if url.startswith("sqlite") and ":memory:" in url:
        return create_engine(url, connect_args={"check_same_thread": False}, poolclass=StaticPool)
    return create_engine(url)


def _ahora() -> datetime:
    return datetime.now(UTC)


class Almacen:
    """Acceso a las tablas del almacén; cada método es una transacción."""

    def __init__(self, motor: Engine, reloj: Callable[[], datetime] = _ahora) -> None:
        self._motor = motor
        self._reloj = reloj

    def crear_esquema(self) -> None:
        """Crea las tablas y agrega las columnas nuevas a una tabla que ya existía: `create_all`
        no altera tablas (B9 sumó columnas a `interaccion`). Las columnas nuevas son nulables."""
        metadata.create_all(self._motor)
        inspector = inspect(self._motor)
        for tabla in metadata.sorted_tables:
            existentes = {c["name"] for c in inspector.get_columns(tabla.name)}
            faltantes = [c for c in tabla.columns if c.name not in existentes]
            # Con varias réplicas que arrancan a la vez (sección 3.7), PostgreSQL usa
            # IF NOT EXISTS; SQLite (las pruebas) no lo admite y tiene un solo proceso.
            si_falta = "IF NOT EXISTS " if self._motor.dialect.name == "postgresql" else ""
            with self._motor.begin() as c:
                for columna in faltantes:
                    tipo = columna.type.compile(dialect=self._motor.dialect)
                    c.execute(
                        text(
                            f'ALTER TABLE {tabla.name} ADD COLUMN {si_falta}"{columna.name}" {tipo}'
                        )
                    )

    def comprobar(self) -> None:
        """Consulta mínima para `/health`; falla si la base no responde."""
        with self._motor.connect() as c:
            c.execute(text("SELECT 1"))

    # -- conversaciones ------------------------------------------------------------------------

    def asegurar_conversacion(
        self, id_conversacion: str, id_contribuyente: str | None = None
    ) -> None:
        """Crea la conversación si no existe; no toca una existente."""
        ahora = self._reloj()
        with self._motor.begin() as c:
            existe = c.execute(
                select(conversacion.c.id_conversacion).where(
                    conversacion.c.id_conversacion == id_conversacion
                )
            ).first()
            if existe is None:
                c.execute(
                    insert(conversacion).values(
                        id_conversacion=id_conversacion,
                        id_contribuyente=id_contribuyente,
                        estado="activa",
                        fecha_inicio=ahora,
                        fecha_actualizacion=ahora,
                    )
                )

    def contribuyente_de_conversacion(self, id_conversacion: str) -> str | None:
        with self._motor.connect() as c:
            fila = c.execute(
                select(conversacion.c.id_contribuyente).where(
                    conversacion.c.id_conversacion == id_conversacion
                )
            ).first()
        return fila[0] if fila else None

    def asignar_contribuyente(self, id_conversacion: str, id_contribuyente: str) -> None:
        """Una conversación que empezó sin sesión queda del contribuyente que inicia sesión."""
        with self._motor.begin() as c:
            c.execute(
                update(conversacion)
                .where(conversacion.c.id_conversacion == id_conversacion)
                .values(id_contribuyente=id_contribuyente, fecha_actualizacion=self._reloj())
            )

    def estado_conversacion(self, id_conversacion: str) -> str | None:
        with self._motor.connect() as c:
            fila = c.execute(
                select(conversacion.c.estado).where(
                    conversacion.c.id_conversacion == id_conversacion
                )
            ).first()
        return fila[0] if fila else None

    def cambiar_estado(self, id_conversacion: str, estado: str) -> None:
        if estado not in ESTADOS_CONVERSACION:
            raise ValueError(f"Estado de conversación inválido: {estado}")
        with self._motor.begin() as c:
            c.execute(
                update(conversacion)
                .where(conversacion.c.id_conversacion == id_conversacion)
                .values(estado=estado, fecha_actualizacion=self._reloj())
            )

    # -- casos ---------------------------------------------------------------------------------

    def registrar_caso(self, caso: CasoEscalado) -> None:
        """Registra el caso y deja la conversación en estado `escalada` (ADR-12)."""
        self.asegurar_conversacion(caso.id_conversacion)
        with self._motor.begin() as c:
            c.execute(
                insert(caso_escalado).values(
                    id_caso=caso.id_caso,
                    id_conversacion=caso.id_conversacion,
                    motivo=caso.motivo,
                    categoria=caso.categoria,
                    nivel_confianza=caso.nivel_confianza,
                    resumen_texto=caso.resumen,
                    resumen_json=caso.resumen_json,
                    intentos=caso.intentos,
                    estado=caso.estado,
                    fecha_escalamiento=caso.fecha_escalamiento,
                )
            )
            c.execute(
                update(conversacion)
                .where(conversacion.c.id_conversacion == caso.id_conversacion)
                .values(estado="escalada", fecha_actualizacion=self._reloj())
            )

    def obtener_caso(self, id_caso: str) -> dict[str, Any] | None:
        with self._motor.connect() as c:
            fila = c.execute(
                select(caso_escalado).where(caso_escalado.c.id_caso == id_caso)
            ).first()
        return dict(fila._mapping) if fila else None

    def caso_de_conversacion(self, id_conversacion: str) -> dict[str, Any] | None:
        with self._motor.connect() as c:
            fila = c.execute(
                select(caso_escalado)
                .where(caso_escalado.c.id_conversacion == id_conversacion)
                .order_by(caso_escalado.c.fecha_escalamiento.desc())
            ).first()
        return dict(fila._mapping) if fila else None

    def listar_casos(self) -> list[dict[str, Any]]:
        with self._motor.connect() as c:
            filas = c.execute(
                select(caso_escalado).order_by(caso_escalado.c.fecha_escalamiento.desc())
            ).all()
        return [dict(f._mapping) for f in filas]

    # -- mensajes del funcionario e interacciones ------------------------------------------------

    def guardar_mensaje(self, id_caso: str, autor: str, texto: str) -> None:
        with self._motor.begin() as c:
            c.execute(
                insert(mensaje_funcionario).values(
                    id_caso=id_caso, autor=autor, texto=texto, fecha=self._reloj()
                )
            )

    def mensajes_del_caso(self, id_caso: str) -> list[dict[str, Any]]:
        with self._motor.connect() as c:
            filas = c.execute(
                select(mensaje_funcionario)
                .where(mensaje_funcionario.c.id_caso == id_caso)
                .order_by(mensaje_funcionario.c.id_mensaje)
            ).all()
        return [dict(f._mapping) for f in filas]

    def registrar_interaccion(
        self,
        id_conversacion: str,
        duracion_ms: int,
        categoria: str | None = None,
        nivel_confianza: float | None = None,
        escalada: bool = False,
        **detalle: Any,
    ) -> None:
        """Una fila por turno, sin el texto de los mensajes ni datos personales (ADR-11).

        `detalle`: `escenario_id`, `estado`, `motivo`, `agentes`, `tiempos_ms`, `tokens` y
        `modelos` (sección 3.11).
        """
        permitidos = {"escenario_id", "estado", "motivo", "agentes", "tiempos_ms", "tokens",
                      "modelos"}  # fmt: skip
        desconocidos = set(detalle) - permitidos
        if desconocidos:
            raise ValueError(f"Campos de interacción desconocidos: {sorted(desconocidos)}")
        with self._motor.begin() as c:
            c.execute(
                insert(interaccion).values(
                    id_conversacion=id_conversacion,
                    categoria=categoria,
                    nivel_confianza=nivel_confianza,
                    escalada=escalada,
                    duracion_ms=duracion_ms,
                    fecha=self._reloj(),
                    **detalle,
                )
            )

    def todas_las_interacciones(self) -> list[dict[str, Any]]:
        with self._motor.connect() as c:
            filas = c.execute(select(interaccion).order_by(interaccion.c.id_interaccion)).all()
        return [dict(f._mapping) for f in filas]

    def interacciones(self, id_conversacion: str) -> list[dict[str, Any]]:
        with self._motor.connect() as c:
            filas = c.execute(
                select(interaccion)
                .where(interaccion.c.id_conversacion == id_conversacion)
                .order_by(interaccion.c.id_interaccion)
            ).all()
        return [dict(f._mapping) for f in filas]
