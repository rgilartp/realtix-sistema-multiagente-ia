"""Esquema y conexión SQLite de la base sintética de RealSit.

La base de RealSit se abre siempre en solo lectura (`mode=ro`, ADR-05 y RF-SYS-02): cada operación
abre su conexión y la cierra, de modo que sirve a varios hilos (H-01). Solo el generador la crea,
con `crear_base`, que es el único camino de escritura.
"""

import sqlite3
from collections.abc import Iterator
from contextlib import closing, contextmanager
from pathlib import Path

SCHEMA = """
CREATE TABLE contribuyente (
    id_contribuyente     TEXT PRIMARY KEY,
    tipo_documento       TEXT NOT NULL,
    numero_documento     TEXT NOT NULL,
    nombre               TEXT NOT NULL,
    tipo_persona         TEXT NOT NULL CHECK (tipo_persona IN ('natural', 'juridica')),
    codigo_ciiu          TEXT,
    actividad_economica  TEXT,
    regimen_ica          TEXT CHECK (regimen_ica IN
                             ('comun_bimestral', 'comun_anual', 'preferencial'))
);

CREATE TABLE predio (
    matricula_catastral  TEXT PRIMARY KEY,
    chip                 TEXT NOT NULL UNIQUE,
    id_contribuyente     TEXT NOT NULL REFERENCES contribuyente(id_contribuyente),
    direccion            TEXT NOT NULL,
    localidad            TEXT NOT NULL,
    estrato              INTEGER CHECK (estrato BETWEEN 1 AND 6),
    destino              TEXT NOT NULL CHECK (destino IN ('residencial', 'comercial', 'lote')),
    avaluo_catastral     INTEGER NOT NULL,
    municipio            TEXT NOT NULL DEFAULT 'Bogotá D.C.'
);

CREATE TABLE avaluo_vigencia (
    matricula_catastral  TEXT NOT NULL REFERENCES predio(matricula_catastral),
    vigencia_fiscal      INTEGER NOT NULL,
    avaluo_catastral     INTEGER NOT NULL,
    PRIMARY KEY (matricula_catastral, vigencia_fiscal)
);

CREATE TABLE obligacion_tributaria (
    id_obligacion          TEXT PRIMARY KEY,
    matricula_catastral    TEXT NOT NULL REFERENCES predio(matricula_catastral),
    tipo_tributo           TEXT NOT NULL CHECK (tipo_tributo IN ('IPU', 'ICA')),
    vigencia_fiscal        INTEGER NOT NULL,
    periodicidad           TEXT NOT NULL CHECK (periodicidad IN ('anual', 'bimestral')),
    base_gravable          INTEGER NOT NULL,
    tarifa_por_mil         TEXT NOT NULL,
    valor_liquidado        INTEGER NOT NULL,
    descuento_pronto_pago  INTEGER NOT NULL,
    fecha_limite_descuento TEXT,
    fecha_limite_pago      TEXT NOT NULL,
    estado_pago            TEXT NOT NULL CHECK (estado_pago IN
                               ('AL_DIA', 'PENDIENTE', 'VENCIDO', 'NO_OBLIGADO')),
    origen_tarifa          TEXT NOT NULL CHECK (origen_tarifa IN ('oficial', 'sintetica')),
    en_spac                INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE pago (
    id_pago        TEXT PRIMARY KEY,
    id_obligacion  TEXT NOT NULL REFERENCES obligacion_tributaria(id_obligacion),
    fecha_pago     TEXT NOT NULL,
    valor_pagado   INTEGER NOT NULL,
    medio_pago     TEXT NOT NULL
);

CREATE TABLE tarifa_ica (
    codigo_ciiu     TEXT PRIMARY KEY,
    actividad       TEXT NOT NULL,
    grupo           TEXT,
    tarifa_por_mil  TEXT NOT NULL,
    vigencia        INTEGER NOT NULL,
    fuente          TEXT NOT NULL
);

CREATE INDEX idx_predio_contribuyente ON predio(id_contribuyente);
CREATE INDEX idx_obligacion_predio ON obligacion_tributaria(matricula_catastral);
CREATE INDEX idx_pago_obligacion ON pago(id_obligacion);
"""

# Orden y llave de cada tabla: lo usan la carga y la huella.
TABLAS: dict[str, str] = {
    "contribuyente": "id_contribuyente",
    "predio": "matricula_catastral",
    "avaluo_vigencia": "matricula_catastral, vigencia_fiscal",
    "obligacion_tributaria": "id_obligacion",
    "pago": "id_pago",
    "tarifa_ica": "codigo_ciiu",
}


def abrir_solo_lectura(db_path: str | Path) -> sqlite3.Connection:
    """Abre una conexión nueva con `mode=ro`; cualquier escritura falla (RF-SYS-02)."""
    ruta = Path(db_path).resolve()
    conn = sqlite3.connect(f"{ruta.as_uri()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def conexion(db_path: str | Path) -> Iterator[sqlite3.Connection]:
    """Una conexión de solo lectura por operación, cerrada al terminar."""
    with closing(abrir_solo_lectura(db_path)) as conn:
        yield conn


@contextmanager
def crear_base(db_path: str | Path) -> Iterator[sqlite3.Connection]:
    """Borra y recrea la base: único camino de escritura, solo para el generador."""
    ruta = Path(db_path)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.unlink(missing_ok=True)
    with closing(sqlite3.connect(ruta)) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.executescript(SCHEMA)
        yield conn
        conn.commit()
