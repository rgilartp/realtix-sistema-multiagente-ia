"""Juez guiado por referencia (sección 6.4 y ADR-24): `claude-opus-5-5`, salida JSON.

- Recibe solo la conversación, la referencia, sus fuentes, lo que no debe hacer y, si los hay, los
  fragmentos recuperados, las fuentes citadas, los datos de las herramientas, las notas del
  sistema, los datos leídos del recibo y el aviso de IA (F1 de la corrida 1, ADR-25). Nunca ve
  qué modelo respondió (ni el resto de `meta`) y todo pasa antes por el anonimizador con los
  nombres y documentos de los usuarios de prueba.
- No se le pide el razonamiento paso a paso: devuelve el veredicto y una justificación breve. Sin
  `temperature` (los modelos 5.5 la rechazan).
- `huella_del_juez()` resume el modelo, las instrucciones, la rúbrica, el esquema y los parámetros:
  la calibración guarda la huella del juez calificado y la corrida 3 exige la misma (A5).
"""

import hashlib
import inspect
import json
from collections.abc import Callable
from dataclasses import dataclass, field, fields
from functools import cache
from pathlib import Path
from typing import Any, Literal

from anthropic import transform_schema
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.api.servicios import usuarios_de_prueba
from src.config import Settings
from src.integrations.modelos import PARAMETROS, crear_modelo, texto_de_respuesta
from src.integrations.robustez import con_tiempo_y_reintento
from src.integrations.trazas import Anonimizador

INSTRUCCIONES = Path(__file__).resolve().parent / "juez.v3.md"
VERSION = "juez.v3"
MAX_AFIRMACIONES = 5
TIEMPO_MAXIMO_S = 120.0


class Veredicto(BaseModel):
    """Lo que devuelve el juez (sección 6.4), en el orden en que lo escribe (juez v3, ADR-25):
    primero las afirmaciones sin fuente y la justificación, y al final el veredicto. Así decide
    después de revisar las afirmaciones, no antes.

    La alucinación es la bandera del juez o la lista no vacía; la bandera tal como la dio el
    juez queda en `Calificacion.alucinacion_marcada`."""

    model_config = ConfigDict(extra="forbid")
    afirmaciones_sin_fuente: list[str] = Field(
        default_factory=list,
        description=f"Hasta {MAX_AFIRMACIONES} citas breves de afirmaciones (cifra, fecha, "
        "porcentaje, norma, artículo, requisito o procedimiento) que no salen de ninguna fuente "
        "válida o que la contradicen; vacía si no hay",
    )
    justificacion: str
    veredicto: Literal["correcta", "parcialmente correcta", "incorrecta"]
    alucinacion: bool
    cito_norma: bool
    cita_sustenta: bool = Field(description="false si no citó o si la cita no sustenta lo dicho")
    cobertura_completa: bool
    claridad: int = Field(ge=1, le=5)

    @model_validator(mode="after")
    def _alucinacion_con_la_lista(self) -> "Veredicto":
        self.afirmaciones_sin_fuente = self.afirmaciones_sin_fuente[:MAX_AFIRMACIONES]
        self.alucinacion = self.alucinacion or bool(self.afirmaciones_sin_fuente)
        return self


def _formato() -> dict[str, Any]:
    """El esquema JSON del juez; la lista es obligatoria para el modelo (las calificaciones
    guardadas antes de v3 no la traen y se leen con la lista vacía)."""
    esquema = transform_schema(Veredicto)
    esquema["required"] = list(esquema["properties"])
    return {"format": {"type": "json_schema", "schema": esquema}}


FORMATO = _formato()


@cache
def instrucciones() -> str:
    return INSTRUCCIONES.read_text(encoding="utf-8")


def huella_del_juez(settings: Settings) -> str:
    """SHA-256 de todo lo que define al juez: modelo, parámetros, instrucciones, esquema y la
    plantilla de lo que ve (el código de `CasoJuez`, `_cita`, `_json`, `fuentes_del_sistema` y
    `caso_del_ensayo`, con el anonimizador).
    Si cambia, se repite la calibración (A5)."""
    definicion = {
        "modelo": settings.modelo_juez,
        "parametros": PARAMETROS["juez"],
        "version": VERSION,
        "instrucciones": instrucciones(),
        "esquema": FORMATO,
        "validacion": inspect.getsource(Veredicto),
        "plantilla": "".join(
            inspect.getsource(f)
            for f in (CasoJuez, _cita, _json, fuentes_del_sistema, caso_del_ensayo)
        ),
        "anonimizador": inspect.getsource(Anonimizador),
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
    datos_herramientas: list[str] = field(default_factory=list)
    notas_sistema: list[str] = field(default_factory=list)
    datos_recibo: list[str] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)

    def anonimizado(self) -> "CasoJuez":
        a = anonimizador_de_prueba()
        return CasoJuez(*(a(getattr(self, c.name)) for c in fields(self)))

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
        secciones = (
            ("Datos que entregaron las herramientas del sistema", self.datos_herramientas),
            ("Notas que agregó el sistema", self.notas_sistema),
            ("Datos que el sistema leyó del recibo", self.datos_recibo),
            ("Aviso de IA que vio el contribuyente", self.avisos),
        )
        for titulo, valores in secciones:
            if valores:
                partes += ["", f"## {titulo}", *(f"- {v}" for v in valores)]
        return "\n".join(partes)


def _cita(fuente: dict[str, Any]) -> str:
    return ", ".join(str(fuente[k]) for k in ("norma", "articulo") if fuente.get(k))


def _json(valor: Any) -> str:
    return json.dumps(valor, ensure_ascii=False, sort_keys=True, default=str)


def fuentes_del_sistema(turno: dict[str, Any]) -> dict[str, list[str]]:
    """Lo que el sistema usó en un turno además de los fragmentos: el resultado de cada
    herramienta como lo vio el modelo (con su fuente), las notas del sistema, los datos leídos
    del recibo y el aviso de IA (F1)."""
    meta = turno.get("meta") or {}
    recibo = (meta.get("datos_extraidos") or {}).get("campos")
    return {
        "datos_herramientas": [
            f"{h.get('herramienta')}: {_json(h.get('resultado'))}"
            for h in meta.get("herramientas") or []
        ],
        "notas_sistema": list(meta.get("notas") or []),
        "datos_recibo": [_json(recibo)] if recibo else [],
        "avisos": [turno["aviso_ia"]] if turno.get("aviso_ia") else [],
    }


def caso_del_ensayo(esc: dict[str, Any], ensayo: dict[str, Any]) -> CasoJuez:
    """Arma lo que ve el juez; de `meta` toma los fragmentos, las fuentes citadas y lo que el
    sistema usó además de los fragmentos (`fuentes_del_sistema`)."""
    contextos: list[str] = []
    citadas: list[str] = []
    sistema: dict[str, list[str]] = {}
    for turno in ensayo["turnos"]:
        meta = turno.get("meta") or {}
        contextos += [c for c in meta.get("contextos") or [] if c not in contextos]
        citadas += [c for f in meta.get("fuentes") or [] if (c := _cita(f)) and c not in citadas]
        for clave, valores in fuentes_del_sistema(turno).items():
            ya = sistema.setdefault(clave, [])
            ya += [v for v in valores if v not in ya]
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
        **sistema,
    )


@dataclass
class Calificacion:
    veredicto: Veredicto
    entrada: int
    salida: int
    alucinacion_marcada: bool  # la bandera tal como la dio el juez, antes de sumar la lista


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
        crudo = json.loads(texto_de_respuesta(respuesta))
        return Calificacion(
            Veredicto.model_validate(crudo),
            int(uso.get("input_tokens", 0)),
            int(uso.get("output_tokens", 0)),
            bool(crudo.get("alucinacion")),
        )


def superado(codigo_pasa: bool, veredicto: Veredicto | None) -> tuple[bool, bool]:
    """(meta, estricta): código y juez «correcta» o «parcialmente correcta» sin alucinación; la
    estricta exige «correcta» (A3)."""
    if not codigo_pasa or veredicto is None or veredicto.alucinacion:
        return False, False
    return veredicto.veredicto != "incorrecta", veredicto.veredicto == "correcta"
