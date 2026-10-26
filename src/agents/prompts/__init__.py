"""Prompts versionados de los agentes (sección 8.7).

Cada prompt es un archivo `nombre.vN.md`; `cargar_prompt` toma la versión más alta y la devuelve
con su versión, que va en los metadatos de la traza. Cambiar un prompt es agregar una versión.
"""

import re
from dataclasses import dataclass
from functools import cache
from pathlib import Path

CARPETA = Path(__file__).resolve().parent
VERSION = re.compile(r"^(?P<nombre>[a-z_]+)\.v(?P<n>\d+)\.md$")


@dataclass(frozen=True)
class Prompt:
    nombre: str
    version: str  # «v1», «v2»…
    texto: str


@cache
def cargar_prompt(nombre: str) -> Prompt:
    """La versión más alta de `nombre`; los agentes agregan las reglas comunes (`comun`)."""
    versiones = [
        (int(m["n"]), ruta)
        for ruta in CARPETA.glob(f"{nombre}.v*.md")
        if (m := VERSION.match(ruta.name)) and m["nombre"] == nombre
    ]
    if not versiones:
        raise FileNotFoundError(f"No hay prompt «{nombre}» en {CARPETA}.")
    n, ruta = max(versiones)
    return Prompt(nombre, f"v{n}", ruta.read_text(encoding="utf-8").strip())


def prompt_de_agente(nombre: str) -> Prompt:
    """Prompt de un agente (ipu, ica o general) con las reglas comunes al final."""
    propio, comun = cargar_prompt(nombre), cargar_prompt("comun")
    version = f"{propio.version}+comun.{comun.version}"
    return Prompt(nombre, version, f"{propio.texto}\n\n{comun.texto}")
