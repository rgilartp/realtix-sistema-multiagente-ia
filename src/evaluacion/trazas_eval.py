"""Verificador de trazas (adenda, escenario 15; RNF-05 · Registro auditable).

Lee de la API de LangSmith las ejecuciones de la corrida (todas, no solo las raíz) y busca en sus
entradas, salidas y metadatos las cédulas, los NIT y los nombres de los usuarios de prueba. El
reporte dice cuántas se revisaron y en cuáles apareció un identificador, por tipo, sin copiarlo.

Limitación: solo se revisa texto. La imagen del recibo que recibe el modelo de visión no se
inspecciona (queda anotado en `docs/cambios_para_documento.md` desde B10).
"""

import json
import re
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from src.api.servicios import usuarios_de_prueba
from src.config import Settings


@dataclass(frozen=True)
class Identificador:
    tipo: str  # «documento» o «nombre»
    patron: re.Pattern[str]


def identificadores_de_prueba() -> list[Identificador]:
    """Documentos (con y sin tipo, con y sin puntos) y nombres de los 12 usuarios de prueba."""
    salida: list[Identificador] = []
    for u in usuarios_de_prueba():
        numero = u["contribuyente_id"].split("-", 1)[-1]
        con_puntos = f"{int(numero):,}".replace(",", ".")
        for forma in {u["contribuyente_id"], numero, con_puntos}:
            salida.append(
                Identificador("documento", re.compile(rf"(?<!\d){re.escape(forma)}(?!\d)"))
            )
        partes = r"\s+".join(re.escape(p) for p in u["nombre"].split())
        salida.append(Identificador("nombre", re.compile(partes, re.IGNORECASE)))
    return salida


def _texto_de_la_ejecucion(ejecucion: Any) -> str:
    partes = [
        getattr(ejecucion, "inputs", None),
        getattr(ejecucion, "outputs", None),
        (getattr(ejecucion, "extra", None) or {}).get("metadata"),
        getattr(ejecucion, "error", None),
    ]
    return json.dumps(partes, ensure_ascii=False, default=str)


def revisar_ejecuciones(
    ejecuciones: Iterable[Any], identificadores: list[Identificador] | None = None
) -> dict[str, Any]:
    """Cuántas ejecuciones se revisaron y cuáles traen un identificador (por tipo)."""
    identificadores = identificadores or identificadores_de_prueba()
    revisadas = 0
    hallazgos: list[dict[str, str]] = []
    for ejecucion in ejecuciones:
        revisadas += 1
        texto = _texto_de_la_ejecucion(ejecucion)
        tipos = sorted({i.tipo for i in identificadores if i.patron.search(texto)})
        if tipos:
            hallazgos.append(
                {
                    "ejecucion": str(getattr(ejecucion, "id", "?")),
                    "nombre": str(getattr(ejecucion, "name", "?")),
                    "tipos": ", ".join(tipos),
                }
            )
    return {
        "ejecuciones_revisadas": revisadas,
        "con_identificadores": len(hallazgos),
        "hallazgos": hallazgos,
        "pasa": revisadas > 0 and not hallazgos,
    }


def ejecuciones_de_langsmith(settings: Settings, desde: datetime) -> Iterable[Any]:
    """Todas las ejecuciones del proyecto desde `desde` (el inicio de la corrida)."""
    if not (settings.langsmith_tracing and settings.langsmith_api_key):
        raise RuntimeError("LangSmith no está configurado (LANGSMITH_TRACING y LANGSMITH_API_KEY).")
    from langsmith import Client

    cliente = Client(api_key=settings.langsmith_api_key.get_secret_value())
    return cliente.list_runs(project_name=settings.langsmith_project, start_time=desde)
