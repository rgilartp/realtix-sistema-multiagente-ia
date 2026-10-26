"""LangSmith con metadatos y anonimizador (RF-OBS-01 y RNF-05 · Registro auditable).

Las trazas llevan el `id_conversacion`, nunca el `contribuyente_id`, y un anonimizador enmascara
cédulas, NIT y nombres en las entradas y las salidas. La prueba de trazas de B12 lo verifica.
"""

import re
from collections.abc import Iterable
from typing import Any

from langsmith import Client

from src.config import Settings

MASCARA_DOCUMENTO = "[DOCUMENTO]"
MASCARA_NOMBRE = "[NOMBRE]"
PROHIBIDOS_EN_METADATOS = frozenset({"contribuyente_id", "id_contribuyente", "nombre"})
# Documentos con tipo: CC-1000000003, NIT-9000000012, NIT 900.123.456-7, cédula 1.020.304.050.
CON_TIPO = re.compile(r"\b(?:CC|CE|TI|PA|NIT)[-\s:]*\d[\d.]{5,}(?:-\d)?", re.IGNORECASE)
CON_PALABRA = re.compile(
    r"(\b(?:c[eé]dula|nit|documento|identificaci[oó]n)\b[^\d\n]{0,15})\d[\d.]{5,}(?:-\d)?",
    re.IGNORECASE,
)
SIN_ROTULO = re.compile(r"(?<![\w$.\-])(?:\d{1,3}(?:\.\d{3}){3}|\d{9,10})(?![\w.\-])")
# Para los modelos: una cifra sin rótulo precedida de una palabra de cuantía (avalúo, ingresos…) o
# seguida de «pesos» o «millones» es un valor, no un documento, y se conserva.
CUANTIA_ANTES = re.compile(
    r"(?:aval[uú]o|ingreso|valor|base|monto|cuant[ií]a|pesos|cop|\$)[^\d\n]{0,15}$", re.IGNORECASE
)
CUANTIA_DESPUES = re.compile(r"^\s*(?:pesos|millones|cop)\b", re.IGNORECASE)
# Nombre que el contribuyente declara: «me llamo Ana Pérez», «mi nombre es…», «soy Ana Pérez».
_PALABRA_NOMBRE = r"(?:[A-ZÁÉÍÓÚÑ][\w.áéíóúñü]*|\d{1,3})"
NOMBRE_DECLARADO = re.compile(
    r"(\b(?:[Mm]e llamo|[Mm]i nombre es|[Ss]oy)\s+)"
    rf"({_PALABRA_NOMBRE}(?:\s+(?:(?:de|del|la|los|las|y)\s+)*{_PALABRA_NOMBRE}){{0,5}})"
)


class Anonimizador:
    """Enmascara documentos y los nombres conocidos en cualquier estructura de texto.

    Para las trazas se prefiere perder detalle (toda cifra de 9 o 10 dígitos sin rótulo se
    enmascara). Para lo que se envía a los modelos (`para_modelos=True`) se conservan las cuantías
    (un avalúo o unos ingresos) y se enmascaran también los nombres que el contribuyente declara.
    """

    def __init__(self, nombres: Iterable[str] = (), *, para_modelos: bool = False) -> None:
        limpios = sorted({n.strip() for n in nombres if len(n.strip()) > 2}, key=len, reverse=True)
        self._nombres = (
            re.compile("|".join(re.escape(n) for n in limpios), re.IGNORECASE) if limpios else None
        )
        self._para_modelos = para_modelos

    def _sin_rotulo(self, encontrado: re.Match[str]) -> str:
        texto = encontrado.string
        if self._para_modelos and (
            CUANTIA_ANTES.search(texto[: encontrado.start()])
            or CUANTIA_DESPUES.match(texto[encontrado.end() :])
        ):
            return encontrado.group(0)
        return MASCARA_DOCUMENTO

    def texto(self, valor: str) -> str:
        valor = CON_TIPO.sub(MASCARA_DOCUMENTO, valor)
        valor = CON_PALABRA.sub(lambda m: m.group(1) + MASCARA_DOCUMENTO, valor)
        valor = SIN_ROTULO.sub(self._sin_rotulo, valor)
        if self._para_modelos:
            valor = NOMBRE_DECLARADO.sub(lambda m: m.group(1) + MASCARA_NOMBRE, valor)
        if self._nombres:
            valor = self._nombres.sub(MASCARA_NOMBRE, valor)
        return valor

    def __call__(self, valor: Any) -> Any:
        if isinstance(valor, str):
            return self.texto(valor)
        if isinstance(valor, dict):
            return {k: self(v) for k, v in valor.items()}
        if isinstance(valor, list | tuple):
            return [self(v) for v in valor]
        return valor


def metadatos_de_traza(
    id_conversacion: str, escenario_id: str | None = None, version: str = "dev", **otros: Any
) -> dict[str, Any]:
    """Metadatos de LangSmith: conversación, escenario y versión; nunca el contribuyente."""
    metadatos = {
        "id_conversacion": id_conversacion,
        "escenario_id": escenario_id,
        "version": version,
        **{k: v for k, v in otros.items() if k not in PROHIBIDOS_EN_METADATOS},
    }
    return metadatos


def crear_cliente_langsmith(settings: Settings, anonimizador: Anonimizador) -> Client | None:
    """Cliente de LangSmith con el anonimizador en entradas y salidas; `None` si está apagado."""
    if not settings.langsmith_tracing or settings.langsmith_api_key is None:
        return None
    return Client(
        api_key=settings.langsmith_api_key.get_secret_value(),
        hide_inputs=anonimizador,
        hide_outputs=anonimizador,
    )
