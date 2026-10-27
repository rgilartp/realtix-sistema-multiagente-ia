"""RAGAS sobre el pipeline RAG (sección 6.5; integración de componentes).

`ragas` 0.4.3 con un modelo evaluador de OpenAI de bajo costo y `text-embedding-3-large` para la
relevancia. El evaluador es `gpt-4.1-mini` (acepta la `temperature` que fija RAGAS): en la
validación con casos conocidos (A4), `gpt-4o-mini` calificó como sustentada una frase de GEN-02 que
el manual no dice, y `gpt-4.1-mini` la detectó. Mide la precisión y la
exhaustividad del contexto, la fidelidad y la relevancia de la respuesta. Los ejemplos de los
prompts se traducen al español una vez por corrida (A9). Lo que recibe RAGAS pasa antes por el
mismo anonimizador del juez y no incluye qué modelo respondió.

`ragas` 0.4.3 importa `langchain_community.chat_models.vertexai`, que ya no existe en
`langchain-community` 0.4; solo lo usa para una comprobación de tipo, así que se le da un módulo
vacío antes de importarlo. También se apaga su telemetría.
"""

import asyncio
import logging
import os
import sys
import types
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from src.config import Settings
from src.evaluacion.juez import anonimizador_de_prueba
from src.integrations.costos import costo_usd

registro = logging.getLogger(__name__)

MODELO_EVALUADOR = "gpt-4.1-mini"
IDIOMA = "spanish"
MAX_TOKENS_EVALUADOR = 4096
METRICAS = ("context_precision", "context_recall", "faithfulness", "answer_relevancy")


def preparar_importacion() -> None:
    os.environ.setdefault("RAGAS_DO_NOT_TRACK", "true")
    nombre = "langchain_community.chat_models.vertexai"
    if nombre not in sys.modules:
        try:
            __import__(nombre)
        except ModuleNotFoundError:
            modulo = types.ModuleType(nombre)
            modulo.ChatVertexAI = type("ChatVertexAI", (), {})  # type: ignore[attr-defined]
            sys.modules[nombre] = modulo


@dataclass
class CasoRagas:
    pregunta: str
    respuesta: str
    contextos: list[str]
    referencia: str

    def anonimizado(self) -> "CasoRagas":
        a = anonimizador_de_prueba()
        return CasoRagas(a(self.pregunta), a(self.respuesta), a(self.contextos), a(self.referencia))


@dataclass
class Consumo:
    """Tokens que gastó RAGAS en OpenAI, leídos de las respuestas de la API."""

    por_modelo: dict[str, dict[str, int]] = field(default_factory=dict)

    def sumar(self, modelo: str, entrada: int, salida: int) -> None:
        t = self.por_modelo.setdefault(modelo, {"entrada": 0, "salida": 0})
        t["entrada"] += entrada
        t["salida"] += salida

    def costo_usd(self) -> Decimal:
        return sum(
            (costo_usd(m, t["entrada"], t["salida"]) for m, t in self.por_modelo.items()),
            Decimal(0),
        )


def caso_del_ensayo(esc: dict[str, Any], ensayo: dict[str, Any]) -> CasoRagas | None:
    """Solo escenarios de un turno con fragmentos recuperados y referencia con contenido."""
    if len(ensayo.get("turnos", [])) != 1 or ensayo.get("error"):
        return None
    turno = ensayo["turnos"][0]
    contextos = (turno.get("meta") or {}).get("contextos") or []
    referencia = str(esc["respuesta_referencia"]).strip()
    if not contextos or referencia.startswith("PENDIENTE"):
        return None
    return CasoRagas(turno["usuario"], turno.get("respuesta") or "", contextos, referencia)


class EvaluadorRagas:
    def __init__(self, settings: Settings, modelo: str = MODELO_EVALUADOR) -> None:
        preparar_importacion()
        import httpx2
        from openai import AsyncOpenAI
        from ragas.embeddings import OpenAIEmbeddings
        from ragas.llms import llm_factory
        from ragas.metrics.collections import (
            AnswerRelevancy,
            ContextPrecision,
            ContextRecall,
            Faithfulness,
        )

        self.consumo = Consumo()
        self.modelo = modelo

        async def contar(respuesta: Any) -> None:
            if respuesta.status_code != 200:
                return
            await respuesta.aread()
            datos = respuesta.json()
            uso = datos.get("usage") or {}
            self.consumo.sumar(
                str(datos.get("model") or modelo),
                int(uso.get("prompt_tokens", 0)),
                int(uso.get("completion_tokens", 0)),
            )

        cliente = AsyncOpenAI(
            api_key=settings.openai_api_key.get_secret_value(),
            http_client=httpx2.AsyncClient(event_hooks={"response": [contar]}, timeout=60),
        )
        # El tope de salida de RAGAS (1.024) no alcanza para los veredictos de una respuesta larga.
        llm = llm_factory(modelo, client=cliente, max_tokens=MAX_TOKENS_EVALUADOR)
        embeddings = OpenAIEmbeddings(client=cliente, model=settings.modelo_embeddings)
        self._llm = llm
        self.metricas = {
            "context_precision": ContextPrecision(llm=llm),
            "context_recall": ContextRecall(llm=llm),
            "faithfulness": Faithfulness(llm=llm),
            "answer_relevancy": AnswerRelevancy(llm=llm, embeddings=embeddings),
        }
        self._adaptado = False

    async def adaptar_al_espanol(self) -> None:
        """Traduce los ejemplos de cada prompt al español (una vez)."""
        if self._adaptado:
            return
        for metrica in self.metricas.values():
            for nombre, valor in list(vars(metrica).items()):
                if nombre.endswith("prompt") and hasattr(valor, "adapt"):
                    setattr(metrica, nombre, await valor.adapt(IDIOMA, self._llm))
        self._adaptado = True

    async def evaluar(self, caso: CasoRagas) -> dict[str, float | None]:
        await self.adaptar_al_espanol()
        c = caso.anonimizado()
        contexto = {"user_input": c.pregunta, "retrieved_contexts": c.contextos}
        argumentos = {
            "context_precision": contexto | {"reference": c.referencia},
            "context_recall": contexto | {"reference": c.referencia},
            "faithfulness": contexto | {"response": c.respuesta},
            "answer_relevancy": {"user_input": c.pregunta, "response": c.respuesta},
        }
        puntajes: dict[str, float | None] = {}
        for nombre, metrica in self.metricas.items():
            try:
                resultado = await metrica.ascore(**argumentos[nombre])
                puntajes[nombre] = float(resultado.value)
            except Exception as error:  # una métrica que falla no tumba la corrida: queda vacía
                registro.warning(
                    "Métrica de RAGAS sin resultado",
                    extra={"metrica": nombre, "error": type(error).__name__},
                )
                puntajes[nombre] = None
        return puntajes

    def evaluar_varios(self, casos: list[CasoRagas]) -> list[dict[str, float | None]]:
        async def todos() -> list[dict[str, float | None]]:
            return [await self.evaluar(c) for c in casos]

        return asyncio.run(todos())
