"""Modelo de chat falso con guion, para probar los agentes sin red.

Devuelve las respuestas en orden y guarda cada llamada (mensajes y parámetros enlazados), para
verificar qué recibe el modelo: herramientas, formato de salida y que no lleguen datos personales.
"""

import json
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage
from pydantic import BaseModel


def salida(**campos: Any) -> AIMessage:
    """Respuesta final del modelo en JSON."""
    return AIMessage(content=json.dumps(campos, ensure_ascii=False))


def final(
    respuesta: str = "Respuesta.",
    suficiencia: str = "completa",
    cobertura: float = 1.0,
    fuera_del_mvp: bool = False,
    fragmentos_citados: list[int] | None = None,
) -> AIMessage:
    """Salida del agente con valores por defecto."""
    return salida(
        respuesta=respuesta,
        suficiencia=suficiencia,
        cobertura=cobertura,
        fuera_del_mvp=fuera_del_mvp,
        fragmentos_citados=fragmentos_citados or [],
    )


def pide(*llamadas: tuple[str, dict[str, Any]]) -> AIMessage:
    """El modelo pide una o varias herramientas a la vez."""
    return AIMessage(
        content="",
        tool_calls=[
            {"name": nombre, "args": args, "id": f"llamada-{i}", "type": "tool_call"}
            for i, (nombre, args) in enumerate(llamadas)
        ],
    )


def negativa() -> AIMessage:
    return AIMessage(content="", response_metadata={"stop_reason": "refusal"})


class _Enlazado:
    def __init__(self, modelo: "ModeloFalso", parametros: dict[str, Any]) -> None:
        self.modelo = modelo
        self.parametros = parametros

    def bind(self, **parametros: Any) -> "_Enlazado":
        return _Enlazado(self.modelo, {**self.parametros, **parametros})

    def bind_tools(self, tools: list[Any], tool_choice: Any = None, **_: Any) -> "_Enlazado":
        return self.bind(tools=tools, tool_choice=tool_choice)

    def invoke(self, mensajes: list[BaseMessage], *_: Any, **__: Any) -> AIMessage:
        self.modelo.llamadas.append((list(mensajes), dict(self.parametros)))
        if not self.modelo.respuestas:
            raise AssertionError("El guion del modelo falso se agotó.")
        respuesta = self.modelo.respuestas.pop(0)
        if isinstance(respuesta, BaseException):
            raise respuesta
        return respuesta


class _Estructurado:
    def __init__(self, modelo: "ModeloFalso", esquema: type[BaseModel]) -> None:
        self.enlazado = _Enlazado(modelo, {"esquema": esquema.__name__})
        self.esquema = esquema

    def invoke(self, mensajes: list[BaseMessage], *_: Any, **__: Any) -> dict[str, Any]:
        crudo = self.enlazado.invoke(mensajes)
        try:
            return {"raw": crudo, "parsed": self.esquema.model_validate_json(crudo.content)}
        except Exception as error:
            return {"raw": crudo, "parsed": None, "parsing_error": error}


class ModeloFalso(_Enlazado):
    """Modelo con guion; `llamadas` guarda (mensajes, parámetros) de cada invocación."""

    def __init__(self, respuestas: list[AIMessage | BaseException] | None = None) -> None:
        super().__init__(self, {})
        self.respuestas = list(respuestas or [])
        self.llamadas: list[tuple[list[BaseMessage], dict[str, Any]]] = []

    def with_structured_output(self, esquema: type[BaseModel], **_: Any) -> _Estructurado:
        return _Estructurado(self, esquema)

    def texto_enviado(self) -> str:
        """Todo lo que recibió el modelo, como texto, para buscar datos personales."""
        return "\n".join(str(m.content) for mensajes, _ in self.llamadas for m in mensajes)
