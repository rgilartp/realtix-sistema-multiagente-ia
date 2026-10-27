"""Ejecutor común de los agentes de IPU, ICA e información general (sección 3.3, paso 3).

Un turno de agente:

1. recupera, sin modelo, los fragmentos de su colección vigentes en el año gravable de la parte,
   con la consulta de búsqueda que escribió el orquestador en los términos de las normas (el año,
   el prompt y la respuesta salen del texto del contribuyente);
2. llamada 1 al modelo, con las herramientas (en paralelo si hacen falta varias) y sin formato:
   con la salida en `json_schema` desde la primera llamada, Haiku 5.5 tendía a contestar sin pedir
   las herramientas (prueba de humo de B7). La llamada 2, sin más herramientas, entrega la
   respuesta en `json_schema`. Un agente sin herramientas (el general) hace una sola llamada;
3. arma la respuesta parcial: el texto del modelo, más las notas de los servicios tal cual y las
   fuentes, que pone el código (el modelo no las reescribe).

El código decide lo que no debe decidir el modelo: el rechazo por acceso (mismo mensaje, OC-06), la
falla del adaptador, del recuperador o del modelo (escala por «fallo de servicio», RNF-08), la
aclaración cuando la actividad no se reconoce y la similitud que alimenta la confianza.
"""

import json
import logging
import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Literal
from zoneinfo import ZoneInfo

from anthropic import transform_schema
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, ConfigDict

from src.agents.clasificador import historial_anonimizado
from src.agents.dependencias import Dependencias
from src.agents.herramientas import Contexto, Herramienta, Resultado, fecha
from src.agents.nodes._comun import busqueda_de_la_parte, parcial, texto_de_la_parte
from src.agents.prompts import Prompt
from src.agents.state import AgentState
from src.data.adapter import MENSAJE_PREDIO_INACCESIBLE, PredioInaccesibleError
from src.integrations.modelos import texto_de_respuesta
from src.integrations.recuperador import Fragmento
from src.integrations.robustez import con_tiempo_y_reintento
from src.integrations.trazas import Anonimizador
from src.services.citas import citas_sin_fuente
from src.services.horario import RelojSistema

registro = logging.getLogger(__name__)

ANIO_EN_TEXTO = re.compile(r"\b(20[2-3]\d)\b")
CODIGO_ANTES = re.compile(r"(?:ciiu|c[oó]digo|actividad)\D{0,12}$", re.IGNORECASE)
K_FRAGMENTOS = 5
MAX_CARACTERES_FRAGMENTO = 3000  # el recuperador en memoria entrega artículos enteros


class SalidaAgente(BaseModel):
    """Esquema de la respuesta del agente; no pide razonamiento (sección 3.2)."""

    model_config = ConfigDict(extra="forbid")
    respuesta: str
    suficiencia: Literal["completa", "parcial", "no_pudo", "aclaracion", "no_corresponde"]
    cobertura: float
    fuera_del_mvp: bool
    fragmentos_citados: list[int]


FORMATO_SALIDA = {"format": {"type": "json_schema", "schema": transform_schema(SalidaAgente)}}
PEDIR_JSON = (
    "Entrega ahora la respuesta para el contribuyente en el JSON pedido; si ya la escribiste, "
    "cópiala en `respuesta`."
)
CITAS_SIN_FUENTE = (
    "Revisa la respuesta: cita {citas}, y ese artículo no está en los encabezados de los "
    "fragmentos, en las fuentes de las herramientas ni en las notas del sistema. Corrígela: "
    "cita solo artículos que estén ahí, o quita la cita, sin cambiar lo demás. Devuelve el JSON "
    "completo."
)


@dataclass(frozen=True)
class ConfigAgente:
    categoria: str  # ipu, ica o general
    prompt: Prompt
    colecciones: tuple[str, ...]
    herramientas: tuple[Herramienta, ...] = ()


def hoy_del_turno(config: RunnableConfig | None, deps: Dependencias) -> date:
    """Fecha de hoy en Bogotá: la del turno (`ahora`, fecha ISO del modo de evaluación) o la del
    reloj del sistema. «Este año» sale de aquí, no de la vigencia fija del adaptador."""
    zona = ZoneInfo(deps.config.zona_horaria)
    ahora = ((config or {}).get("configurable") or {}).get("ahora")
    if ahora:
        momento = datetime.fromisoformat(str(ahora))
        return (momento.astimezone(zona) if momento.tzinfo else momento).date()
    reloj = deps.reloj or RelojSistema(deps.config.zona_horaria)
    return reloj.ahora().astimezone(zona).date()


def anio_de_la_consulta(texto: str, hoy: date) -> int:
    """El año gravable que nombra la consulta o, si no nombra ninguno, el del reloj.

    Un número que sigue a «CIIU», «código» o «actividad» es un código, no un año (CIIU 2029).
    """
    for encontrado in ANIO_EN_TEXTO.finditer(texto):
        if not CODIGO_ANTES.search(texto[: encontrado.start()]):
            return int(encontrado.group(1))
    return hoy.year


def similitud_de_la_parte(
    fragmentos: list[Fragmento], citados: list[Fragmento], uso_datos: bool
) -> float | None:
    """Similitud que alimenta la confianza (regla de B7, documentada en `b07.md`).

    - Si cita fragmentos, el coseno más alto de los citados.
    - Si no cita ninguno y la respuesta sale de datos del adaptador o de los servicios, `None`:
      la confianza se renormaliza sin la similitud (sección 3.3).
    - Si no cita ninguno en una consulta conceptual, el coseno más alto de los recuperados.
    """
    if citados:
        return max(f.similitud for f in citados)
    if uso_datos or not fragmentos:
        return None
    return max(f.similitud for f in fragmentos)


def _bloque_fragmentos(fragmentos: list[Fragmento]) -> str:
    if not fragmentos:
        return "(no se recuperaron fragmentos)"
    return "\n\n".join(
        f"[{i}] {f.cita}\n{f.texto[:MAX_CARACTERES_FRAGMENTO]}" for i, f in enumerate(fragmentos, 1)
    )


def _contexto_del_turno(
    texto: str,
    state: AgentState,
    hoy: date,
    fragmentos: list[Fragmento],
    anonimizar: Anonimizador,
) -> str:
    predios = ", ".join(state.get("predios_autorizados", [])) or "ninguno"
    sesion = "sí" if state.get("contribuyente_id") else "no"
    recordado = state.get("datos_extraidos", {}).get("predio")
    lineas = [
        f"Fecha de hoy: {fecha(hoy)} (año gravable en curso: {hoy.year})",
        f"Sesión iniciada: {sesion}. Predios de la sesión: {predios}",
    ]
    if recordado:
        lineas.append(f"Predio del que se habló antes en la conversación: {recordado}")
    return (
        "\n".join(lineas)
        + f"\n\nConversación previa:\n{historial_anonimizado(state, anonimizar.texto)}"
        + f"\n\nFragmentos de normas:\n{_bloque_fragmentos(fragmentos)}"
        + f"\n\nParte que atiendes:\n{anonimizar.texto(texto)}"
    )


def recuperar(deps: Dependencias, config: ConfigAgente, texto: str, anio: int) -> list[Fragmento]:
    """Los 5 fragmentos más cercanos de las colecciones del agente (con tiempo y un reintento)."""
    if deps.recuperador is None or not config.colecciones:
        return []
    recuperador = deps.recuperador
    encontrados: list[Fragmento] = []
    for coleccion in config.colecciones:
        encontrados += con_tiempo_y_reintento(
            lambda c=coleccion: recuperador.recuperar(
                texto, coleccion=c, k=K_FRAGMENTOS, anio=anio
            ),
            deps.config.timeout_recuperacion_s,
            servicio="recuperación",
        )
    if len(config.colecciones) > 1:  # varias colecciones: se juntan por similitud
        encontrados.sort(key=lambda f: f.similitud, reverse=True)
    return encontrados[:K_FRAGMENTOS]  # una colección: el orden de la fusión RRF


def fuente_del_contrato(
    norma: str,
    articulo: str | None = None,
    coleccion: str | None = None,
    puntaje: float | None = None,
) -> dict[str, Any]:
    """Una fuente con la forma de `meta.fuentes` de la sección 3.8."""
    return {"norma": norma, "articulo": articulo, "coleccion": coleccion, "puntaje": puntaje}


def fuentes_del_contrato(resultados: list[Resultado], citados: list[Fragmento]) -> list[dict]:
    """Las fuentes de las herramientas (sin artículo ni puntaje) y las de los fragmentos citados,
    con su colección y su coseno."""
    salida = [
        fuente_del_contrato(f)
        for f in _sin_repetir([f for r in resultados if r.tipo == "ok" for f in r.fuentes])
    ]
    for fragmento in citados:
        articulo = re.match(r"^Art[ií]culo\s+(.+)$", fragmento.seccion)
        salida.append(
            fuente_del_contrato(
                fragmento.norma or fragmento.fuente,
                articulo.group(1) if articulo else fragmento.seccion or None,
                fragmento.fuente.split("/")[0] if "/" in fragmento.fuente else None,
                round(fragmento.similitud, 3),
            )
        )
    return salida


def _sin_repetir(valores: list[str]) -> list[str]:
    return list(dict.fromkeys(v for v in valores if v))


def componer_texto(
    respuesta: str, resultados: list[Resultado], citados: list[Fragmento], con_anexos: bool
) -> tuple[str, list[str]]:
    """Texto final: la respuesta del modelo, las notas tal cual y la lista de fuentes."""
    texto = respuesta.strip()
    exitosos = [r for r in resultados if r.tipo == "ok"]
    fuentes = _sin_repetir([f for r in exitosos for f in r.fuentes] + [f.cita for f in citados])
    if not con_anexos:
        return texto, fuentes
    notas = [n for n in notas_del_sistema(resultados) if n not in texto]
    if notas:
        texto += "\n\n" + "\n\n".join(notas)
    if fuentes:
        texto += "\n\nFuentes: " + "; ".join(fuentes) + "."
    return texto, fuentes


def notas_del_sistema(resultados: list[Resultado]) -> list[str]:
    """Las notas de los servicios que el sistema agrega al final, sin repetir."""
    return _sin_repetir([n for r in resultados if r.tipo == "ok" for n in r.notas])


def para_el_modelo(resultado: Resultado) -> dict[str, Any]:
    """Lo que ve el modelo de un resultado: los datos y sus fuentes, para que cite cada cifra con
    la fuente de la herramienta y no con la norma de un fragmento (revisión externa, IPU-10)."""
    if not resultado.fuentes:
        return resultado.datos
    return {**resultado.datos, "fuentes_de_la_herramienta": list(resultado.fuentes)}


class _Rechazo(Exception):
    """Una herramienta encontró un predio ajeno o inexistente."""


def ejecutar_agente(
    config: ConfigAgente,
    deps: Dependencias,
    state: AgentState,
    run_config: RunnableConfig | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Respuesta parcial del agente y los `datos_extraidos` actualizados."""
    assert deps.modelos is not None
    categoria = config.categoria
    datos = dict(state.get("datos_extraidos", {}))
    texto = texto_de_la_parte(state)
    hoy = hoy_del_turno(run_config, deps)
    anio = anio_de_la_consulta(texto, hoy)
    id_conversacion = state.get("id_conversacion")

    def fallo(etapa: str, error: BaseException) -> tuple[dict[str, Any], dict[str, Any]]:
        registro.warning(
            "Falla de servicio en el agente",
            extra={
                "id_conversacion": id_conversacion,
                "agente": categoria,
                "etapa": etapa,
                "error": type(error).__name__,
            },
        )
        caida = parcial(categoria, "", suficiencia="no_pudo", cobertura=0.0, fallo_servicio=True)
        return caida, datos

    anonimizador = Anonimizador(para_modelos=True)
    busqueda = anonimizador.texto(busqueda_de_la_parte(state))
    try:  # la consulta va anonimizada también a los embeddings
        fragmentos = recuperar(deps, config, busqueda, anio)
    except Exception as error:  # Chroma o los embeddings no respondieron (RNF-08)
        return fallo("recuperación", error)

    contexto = Contexto(
        adaptador=deps.adaptador,
        contribuyente_id=state.get("contribuyente_id"),
        predios_autorizados=list(state.get("predios_autorizados", [])),
        hoy=hoy,
        timeout_adaptador_s=deps.config.timeout_adaptador_s,
    )
    mensajes: list[BaseMessage] = [
        SystemMessage(config.prompt.texto),
        HumanMessage(_contexto_del_turno(texto, state, hoy, fragmentos, anonimizador)),
    ]
    modelo: BaseChatModel = deps.modelos(categoria)
    especificaciones = [h.especificacion() for h in config.herramientas]
    por_nombre = {h.nombre: h for h in config.herramientas}

    def llamar(con_herramientas: bool, con_formato: bool) -> AIMessage:
        enlazado: Any = modelo
        if especificaciones:
            eleccion = None if con_herramientas else {"type": "none"}
            enlazado = modelo.bind_tools(especificaciones, tool_choice=eleccion)
        if con_formato:
            enlazado = enlazado.bind(output_config=FORMATO_SALIDA)
        respuesta = con_tiempo_y_reintento(
            lambda: enlazado.invoke(mensajes), deps.config.timeout_modelo_s, servicio="modelo"
        )
        texto_de_respuesta(respuesta)  # una negativa del modelo es una falla del servicio
        return respuesta

    resultados: list[Resultado] = []
    vistos: list[dict[str, Any]] = []  # cada resultado tal como lo vio el modelo (evaluación)
    try:
        respuesta = llamar(con_herramientas=True, con_formato=not especificaciones)
        if especificaciones:
            if respuesta.tool_calls or texto_de_respuesta(respuesta).strip():
                mensajes.append(respuesta)
            for llamada in respuesta.tool_calls:
                herramienta = por_nombre.get(llamada["name"])
                if herramienta is None:
                    resultado = Resultado({"error": "herramienta desconocida"}, tipo="argumentos")
                else:
                    try:
                        resultado = herramienta.ejecutar(contexto, dict(llamada["args"]))
                    except PredioInaccesibleError as error:
                        raise _Rechazo from error
                resultados.append(resultado)
                visto = json.dumps(para_el_modelo(resultado), ensure_ascii=False, default=str)
                vistos.append({"herramienta": llamada["name"], "resultado": json.loads(visto)})
                mensajes.append(ToolMessage(visto, tool_call_id=llamada["id"]))
            if not respuesta.tool_calls:
                mensajes.append(HumanMessage(PEDIR_JSON))
            respuesta = llamar(con_herramientas=False, con_formato=True)
        salida = SalidaAgente.model_validate_json(texto_de_respuesta(respuesta))
    except _Rechazo:
        return parcial(categoria, MENSAJE_PREDIO_INACCESIBLE, rechazo_acceso=True), datos
    except Exception as error:  # modelo, negativa, salida inválida o adaptador (RNF-08)
        return fallo("modelo o herramientas", error)

    # Verificador de citas sin modelo (F5): una cita «norma, art. N» que no está en los
    # encabezados de los fragmentos, en las fuentes de las herramientas ni en las notas pide una
    # sola reescritura; si persiste, la parte queda «parcial» y lo decide la confianza.
    validas = [f.cita for f in fragmentos] + [
        f for r in resultados if r.tipo == "ok" for f in (*r.fuentes, *r.notas)
    ]
    sin_fuente = (
        citas_sin_fuente(salida.respuesta, validas)
        if salida.suficiencia in ("completa", "parcial")
        else []
    )
    reescrituras = 0
    if sin_fuente:
        reescrituras = 1
        registro.info(
            "Reescritura por citas sin fuente",
            extra={"id_conversacion": id_conversacion, "agente": categoria},
        )
        mensajes += [respuesta, HumanMessage(CITAS_SIN_FUENTE.format(citas="; ".join(sin_fuente)))]
        try:
            respuesta = llamar(con_herramientas=False, con_formato=True)
            salida = SalidaAgente.model_validate_json(texto_de_respuesta(respuesta))
        except Exception:  # noqa: BLE001 — se queda la primera respuesta, que pasa a «parcial»
            pass
        sin_fuente = citas_sin_fuente(salida.respuesta, validas)

    suficiencia = salida.suficiencia
    if sin_fuente and suficiencia == "completa":
        suficiencia = "parcial"
    if not salida.respuesta.strip() and suficiencia != "no_corresponde":
        suficiencia = "no_pudo"  # una respuesta vacía no es una respuesta
    if any(r.tipo == "actividad_no_reconocida" for r in resultados) and not any(
        r.tipo == "ok" for r in resultados
    ):
        suficiencia = "aclaracion"
    if suficiencia == "no_corresponde":
        return parcial(categoria, "", suficiencia="no_corresponde", cobertura=0.0), datos
    citados = [fragmentos[i - 1] for i in salida.fragmentos_citados if 1 <= i <= len(fragmentos)]
    uso_datos = any(r.tipo == "ok" for r in resultados)
    texto_final, fuentes = componer_texto(
        salida.respuesta, resultados, citados, con_anexos=suficiencia in ("completa", "parcial")
    )
    if contexto.matriculas_usadas:
        datos["predio"] = contexto.matriculas_usadas[-1]
    evaluacion: dict[str, Any] = {}
    if deps.modo_evaluacion:
        # Para el juez y RAGAS: cada fragmento y cada resultado de herramienta tal como los vio
        # el modelo, y las notas que agregó el sistema (F1 de la corrida 1, ADR-25).
        evaluacion = {
            "contextos": [f"{f.cita}\n{f.texto[:MAX_CARACTERES_FRAGMENTO]}" for f in fragmentos],
            "herramientas": vistos,
            "notas": notas_del_sistema(resultados)
            if suficiencia in ("completa", "parcial")
            else [],
            "reescrituras": reescrituras,
            "version_corpus": getattr(deps.recuperador, "version_corpus", None),
        }
    respuesta_parcial = parcial(
        categoria,
        texto_final,
        fuentes=tuple(fuentes),
        fuentes_contrato=fuentes_del_contrato(resultados, citados),
        similitud=similitud_de_la_parte(fragmentos, citados, uso_datos),
        suficiencia=suficiencia,
        cobertura=max(0.0, min(1.0, salida.cobertura)),
        fuera_de_alcance=salida.fuera_del_mvp,
        prompt=config.prompt.version,
        anio_gravable=anio,
        **evaluacion,
    )
    return respuesta_parcial, datos
