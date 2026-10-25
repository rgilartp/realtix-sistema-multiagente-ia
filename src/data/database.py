"""
Esquema y conexión SQLite para el ambiente de datos sintético.

Este archivo reemplaza, únicamente durante el desarrollo y la evaluación
del MVP, al sistema RealSit real (Documento de Requerimientos, sección 3.3,
decisión de ambiente de datos; Documento de Arquitectura v2, sección 6.3).
El contrato que exponen los agentes
(adapter.py) es el mismo sin importar qué hay detrás de esta capa.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "realtix_sintetico.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS contribuyente (
    id_contribuyente     TEXT PRIMARY KEY,
    tipo_documento       TEXT NOT NULL,
    numero_documento     TEXT NOT NULL,
    nombre               TEXT NOT NULL,
    actividad_economica  TEXT
);

CREATE TABLE IF NOT EXISTS predio (
    matricula_catastral  TEXT PRIMARY KEY,
    id_contribuyente     TEXT NOT NULL REFERENCES contribuyente(id_contribuyente),
    direccion            TEXT NOT NULL,
    avaluo_catastral     INTEGER NOT NULL,
    municipio            TEXT NOT NULL DEFAULT 'Bogotá D.C.'
);

CREATE TABLE IF NOT EXISTS obligacion_tributaria (
    id_obligacion        TEXT PRIMARY KEY,
    matricula_catastral  TEXT NOT NULL REFERENCES predio(matricula_catastral),
    tipo_tributo         TEXT NOT NULL CHECK (tipo_tributo IN ('IPU', 'ICA')),
    vigencia_fiscal      INTEGER NOT NULL,
    valor_liquidado      INTEGER NOT NULL,
    estado_pago          TEXT NOT NULL CHECK (estado_pago IN ('AL_DIA', 'PENDIENTE', 'VENCIDO')),
    fecha_limite_pago    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS pago (
    id_pago              TEXT PRIMARY KEY,
    id_obligacion        TEXT NOT NULL REFERENCES obligacion_tributaria(id_obligacion),
    fecha_pago           TEXT NOT NULL,
    valor_pagado         INTEGER NOT NULL,
    medio_pago           TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS conversacion (
    id_conversacion      TEXT PRIMARY KEY,
    id_contribuyente     TEXT REFERENCES contribuyente(id_contribuyente),
    fecha_inicio         TEXT NOT NULL,
    categoria_detectada  TEXT
);

CREATE TABLE IF NOT EXISTS caso_escalado (
    id_caso              TEXT PRIMARY KEY,
    id_conversacion      TEXT NOT NULL REFERENCES conversacion(id_conversacion),
    resumen              TEXT NOT NULL,
    nivel_confianza      REAL NOT NULL,
    fecha_escalamiento   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tarifa_ica (
    actividad_economica  TEXT PRIMARY KEY,
    tarifa_por_mil       REAL NOT NULL,
    descripcion          TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_predio_contribuyente ON predio(id_contribuyente);
CREATE INDEX IF NOT EXISTS idx_obligacion_predio ON obligacion_tributaria(matricula_catastral);
CREATE INDEX IF NOT EXISTS idx_pago_obligacion ON pago(id_obligacion);
"""


def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def reset_database(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """Borra y recrea la base desde cero. Útil para regenerar datos sintéticos."""
    if db_path.exists():
        db_path.unlink()
    conn = get_connection(db_path)
    init_schema(conn)
    return conn
