"""Tablas del almacén propio (SQLAlchemy Core): estado de la conversación y registro de casos.

Se crean en PostgreSQL en producción y en SQLite en las pruebas unitarias. No guardan el texto de
los mensajes del contribuyente ni datos personales en `interaccion` (ADR-11).
"""

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    String,
    Table,
    Text,
)

metadata = MetaData()

conversacion = Table(
    "conversacion",
    metadata,
    Column("id_conversacion", String(64), primary_key=True),
    Column("id_contribuyente", String(32), nullable=True),
    Column("estado", String(16), nullable=False, default="activa"),  # activa, escalada, cerrada
    Column("categoria_detectada", String(32), nullable=True),
    Column("fecha_inicio", DateTime(timezone=True), nullable=False),
    Column("fecha_actualizacion", DateTime(timezone=True), nullable=False),
)

caso_escalado = Table(
    "caso_escalado",
    metadata,
    Column("id_caso", String(64), primary_key=True),
    Column(
        "id_conversacion", String(64), ForeignKey("conversacion.id_conversacion"), nullable=False
    ),
    Column("motivo", String(64), nullable=False, default=""),
    Column("categoria", String(32), nullable=True),
    Column("nivel_confianza", Float, nullable=False),
    Column("resumen_texto", Text, nullable=False),
    Column("resumen_json", JSON, nullable=False),
    Column("intentos", Integer, nullable=False, default=0),
    Column("estado", String(16), nullable=False, default="abierto"),
    Column("fecha_escalamiento", DateTime(timezone=True), nullable=False),
    Index("idx_caso_conversacion", "id_conversacion"),
)

mensaje_funcionario = Table(
    "mensaje_funcionario",
    metadata,
    Column("id_mensaje", Integer, primary_key=True, autoincrement=True),
    Column("id_caso", String(64), ForeignKey("caso_escalado.id_caso"), nullable=False),
    Column("autor", String(16), nullable=False),  # contribuyente o funcionario
    Column("texto", Text, nullable=False),
    Column("fecha", DateTime(timezone=True), nullable=False),
    Index("idx_mensaje_caso", "id_caso"),
)

interaccion = Table(
    "interaccion",
    metadata,
    Column("id_interaccion", Integer, primary_key=True, autoincrement=True),
    Column("id_conversacion", String(64), nullable=False),
    Column("categoria", String(32), nullable=True),
    Column("nivel_confianza", Float, nullable=True),
    Column("escalada", Boolean, nullable=False, default=False),
    Column("duracion_ms", Integer, nullable=False),
    Column("fecha", DateTime(timezone=True), nullable=False),
    Index("idx_interaccion_conversacion", "id_conversacion"),
)
