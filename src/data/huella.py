"""Huella SHA-256 de la base sintética (RF-OBS-05 · Ejecución repetible de pruebas).

Se calcula sobre el contenido de las tablas, en un orden fijo, y no sobre los bytes del archivo
SQLite: así no depende de cómo SQLite organice las páginas. La base `.db` no se versiona; la
huella con la semilla 42 sí (`huella_realsit.sha256`).
"""

import hashlib
import json
from pathlib import Path

from src.data.database import TABLAS, conexion

RUTA_HUELLA = Path(__file__).resolve().parent / "huella_realsit.sha256"


def calcular_huella(db_path: str | Path) -> str:
    sha = hashlib.sha256()
    with conexion(db_path) as c:
        for tabla, orden in TABLAS.items():
            sha.update(f"#{tabla}\n".encode())
            for fila in c.execute(f"SELECT * FROM {tabla} ORDER BY {orden}"):  # noqa: S608
                linea = json.dumps(list(fila), ensure_ascii=False, separators=(",", ":"))
                sha.update(linea.encode() + b"\n")
    return sha.hexdigest()
