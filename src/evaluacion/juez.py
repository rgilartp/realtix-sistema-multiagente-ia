"""Juez guiado por referencia (sección 6.4 y ADR-24): `claude-opus-5-5`, salida JSON.

- Recibe solo la conversación, la referencia, sus fuentes, lo que no debe hacer y, si los hay, los
  fragmentos recuperados y las fuentes citadas. Nunca ve qué modelo respondió (ni `meta`) y todo
  pasa antes por el anonimizador con los nombres y documentos de los usuarios de prueba.
- No se le pide el razonamiento paso a paso: devuelve el veredicto y una justificación breve. Sin
  `temperature` (los modelos 5.5 la rechazan).
- `huella_del_juez()` resume el modelo, las instrucciones, la rúbrica, el esquema y los parámetros:
  la calibración guarda la huella del juez calificado y la corrida 3 exige la misma (A5).
"""

import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Any, Literal

from anthropic import transform_schema
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, ConfigDict, Field

from src.api.servicios import usuarios_de_prueba
from src.config import Settings
from src.integrations.modelos import PARAMETROS, crear_modelo, texto_de_respuesta
from src.integrations.robustez import con_tiempo_y_reintento
from src.integrations.trazas import Anonimizador

INSTRUCCIONES = Path(__file__).resolve().parent / "juez.v1.md"
VERSION = "juez.v1"
TIEMPO_MAXIMO_S = 120.0


class Veredicto(BaseModel):
    """Lo que devuelve el juez (sección 6.4)."""

    model_config = ConfigDict(extra="forbid")
    veredicto: Literal["correcta", "parcialmente correcta", "incorrecta"]
    alucinacion: bool
    cito_norma: bool
    cita_sustenta: bool = Field(description="false si no citó o si la cita no sustenta lo dicho")
    cobertura_completa: bool
    claridad: int = Field(ge=1, le=5)
    justificacion: str


FORMATO = {"format": {"type": "json_schema", "schema": transform_schema(Veredicto)}}


@cache
def instrucciones() -> str:
    return INSTRUCCIONES.read_text(encoding="utf-8")


def huella_del_juez(settings: Settings) -> str:
    """SHA-256 de todo lo que define al juez; si cambia, se repite la calibración (A5)."""
    definicion = {
        "modelo": settings.modelo_juez,
        "parametros": PARAMETROS["juez"],
        "version": VERSION,
        "instrucciones": instrucciones(),
        "esquema": Veredicto.model_json_schema(),
    }
    return hashlib.sha256(
        json.dumps(definicion, ensure_ascii=False, sort_keys=True).encode()
    ).hexdigest()


@cache
def anonimizador_de_prueba() -> Anonimizador:
    """Nombres y documentos de los usuarios de prueba, para lo que ven el juez y RAGAS."""
    nombres = [u["nombre"] for u in usuarios_de_prueba()]
    return Anonimizador(nombres, para_modelos=True)


@dataclass(frozen=True)
class CasoJuez:
    """Lo que ve el juez de un ensayo; nada más."""

    conversacion: list[dict[str, str]]  # [{"contribuyente": …, "asistente": …}]
    referencia: str
    fuentes_referencia: list[str]
    no_debe: list[str]
    contextos: list[str]
    fuentes_citadas: list[str]

    def anonimizado(self) -> "CasoJuez":
        a = anonimizador_de_prueba()
        return CasoJuez(
            a(self.conversacion),
            a(self.referencia),
            a(self.fuentes_referencia),
            a(self.no_debe),
            a(self.contextos),
            a(self.fuentes_citadas),
        )

    def como_texto(self) -> str:
        partes = ["## Conversación"]
        for i, t in enumerate(self.conversacion, 1):
            partes += [
                f"Contribuyente ({i}): {t['contribuyente']}",
                f"Asistente ({i}): {t['asistente']}",
            ]
        partes += ["", "## Respuesta de referencia", self.referencia]
        partes += ["", "## Fuentes de la referencia", *(f"- {f}" for f in self.fuentes_referencia)]
        if self.no_debe:
            partes += ["", "## La respuesta no debe", *(f"- {n}" for n in self.no_debe)]
        if self.fuentes_citadas:
            partes += [
                "",
                "## Fuentes que citó el asistente",
                *(f"- {f}" for f in self.fuentes_citadas),
            ]
        if self.contextos:
            partes += ["", "## Fragmentos que recuperó el asistente"]
            partes += [f"[{i}] {c}" for i, c in enumerate(self.contextos, 1)]
        return "\n".join(partes)


def _cita(fuente: dict[str, Any]) -> str:
    return ", ".join(str(fuente[k]) for k in ("norma", "articulo") if fuente.get(k))


def caso_del_ensayo(esc: dict[str, Any], ensayo: dict[str, Any]) -> CasoJuez:
    """Arma lo que ve el juez; de `meta` toma solo los fragmentos y las fuentes citadas."""
    contextos: list[str] = []
    citadas: list[str] = []
    for turno in ensayo["turnos"]:
        meta = turno.get("meta") or {}
        contextos += [c for c in meta.get("contextos") or [] if c not in contextos]
        citadas += [c for f in meta.get("fuentes") or [] if (c := _cita(f)) and c not in citadas]
    return CasoJuez(
        [
            {"contribuyente": t["usuario"], "asistente": t.get("respuesta") or ""}
            for t in ensayo["turnos"]
        ],
        str(esc["respuesta_referencia"]).strip(),
        list(esc.get("fuentes_esperadas") or []),
        list(esc.get("no_debe") or []),
        contextos,
        citadas,
    )


@dataclass
class Calificacion:
    veredicto: Veredicto
    entrada: int
    salida: int


class Juez:
    """Califica un caso con el modelo del juez (`MODELO_JUEZ`)."""

    def __init__(self, settings: Settings, modelo: BaseChatModel | None = None) -> None:
        self.settings = settings
        self.modelo_id = settings.modelo_juez
        if modelo is None:
            largo = settings.model_copy(update={"timeout_modelo_s": TIEMPO_MAXIMO_S})
            modelo = crear_modelo("juez", largo)
        self._modelo = modelo.bind(output_config=FORMATO)

    def mensajes(self, caso: CasoJuez) -> list[Any]:
        return [SystemMessage(instrucciones()), HumanMessage(caso.anonimizado().como_texto())]

    def calificar(self, caso: CasoJuez) -> Calificacion:
        mensajes = self.mensajes(caso)
        llamar: Callable[[], Any] = lambda: self._modelo.invoke(mensajes)  # noqa: E731
        respuesta = con_tiempo_y_reintento(llamar, TIEMPO_MAXIMO_S, servicio="juez")
        uso = getattr(respuesta, "usage_metadata", None) or {}
        return Calificacion(
            Veredicto.model_validate_json(texto_de_respuesta(respuesta)),
            int(uso.get("input_tokens", 0)),
            int(uso.get("output_tokens", 0)),
        )


def superado(codigo_pasa: bool, veredicto: Veredicto | None) -> tuple[bool, bool]:
    """(meta, estricta): código y juez «correcta» o «parcialmente correcta» sin alucinación; la
    estricta exige «correcta» (A3)."""
    if not codigo_pasa or veredicto is None or veredicto.alucinacion:
        return False, False
    return veredicto.veredicto != "incorrecta", veredicto.veredicto == "correcta"
