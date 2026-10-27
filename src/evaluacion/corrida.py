"""Calificación y métricas de una corrida (secciones 6.4 y 6.5).

Cada ensayo pasa por los evaluadores de código y por el juez (todos, también los que fallan en el
código: la exactitud con el juez y la muestra de calibración los necesitan). Las calificaciones del
juez se guardan en `juez.jsonl` a medida que llegan, para reanudar sin volver a pagarlas. Los
conjuntos adicionales (R1, R3 y R4 de ADR-24) se calculan y se reportan aparte de los 60.
"""

import json
from collections.abc import Callable, Iterable
from decimal import Decimal
from pathlib import Path
from statistics import mean
from typing import Any

from src.agents.state import CATEGORIAS
from src.evaluacion.ejecutor import leer_resultados, tokens_por_modelo
from src.evaluacion.evaluadores_codigo import evaluar_codigo
from src.evaluacion.juez import Juez, Veredicto, caso_del_ensayo, superado
from src.evaluacion.metricas_eval import consistencia, latencias, por_escenario, tasa_con_intervalos
from src.integrations.costos import costo_usd
from src.services.metricas import matriz_de_confusion, por_categoria

SIN_CATEGORIA = "sin_categoria"
# Conjuntos que se reportan aparte (ADR-24): grupo del escenario -> nombre del conjunto.
CONJUNTOS_APARTE = {"generalizacion": "R1", "cadena": "R3", "seguridad": "R4"}


def resumen_del_turno(turno: dict[str, Any]) -> dict[str, Any]:
    """Latencias y estado del turno, si llegó a los agentes (gastó tokens) y si recuperó
    fragmentos: la latencia de RNF-01 se separa así, no por el `tipo_latencia` del YAML."""
    meta = turno.get("meta") or {}
    return {
        "latencia_cliente_ms": turno.get("latencia_cliente_ms"),
        "latencia_servidor_ms": turno.get("latencia_servidor_ms"),
        "estado": turno.get("estado"),
        "con_agentes": sum((meta.get("tokens") or {}).values()) > 0,
        "con_recuperacion": bool(meta.get("contextos")),
    }


def vigentes(ensayos: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """El último resultado de cada (escenario, ensayo): al reanudar se repiten los fallidos."""
    ultimos: dict[tuple[str, int], dict[str, Any]] = {}
    for e in ensayos:
        ultimos[(e["escenario"], e["ensayo"])] = e
    return [ultimos[k] for k in sorted(ultimos)]


def calificar(
    escenarios: dict[str, dict[str, Any]],
    ensayos: list[dict[str, Any]],
    juez: Juez | None,
    archivo_juez: Path,
    al_avanzar: Callable[[dict[str, Any]], None] | None = None,
    huella: str | None = None,
    al_juzgar: Callable[[dict[str, Any]], None] | None = None,
) -> list[dict[str, Any]]:
    """Código y juez de cada ensayo; `juez=None` reutiliza lo ya guardado (y no llama al modelo).

    Cada calificación guarda la huella del juez que la hizo; con `huella`, una calificación de
    otro juez no se reutiliza en silencio (A5). `al_juzgar` recibe solo las calificaciones nuevas
    (las que se pagan), para llevar el gasto de la corrida."""
    previas = {
        (j["escenario"], j["ensayo"], j["id_conversacion"]): j
        for j in leer_resultados(archivo_juez)
    }
    if huella:
        distintas = sorted({j["escenario"] for j in previas.values() if j.get("huella") != huella})
        if distintas:
            raise RuntimeError(
                f"{archivo_juez} tiene calificaciones de otro juez ({', '.join(distintas)}); "
                "con el juez cambiado hay que volver a calificar en un archivo nuevo (A5)."
            )
    calificados = []
    for ensayo in vigentes(ensayos):
        esc = escenarios[ensayo["escenario"]]
        codigo = evaluar_codigo(esc, ensayo)
        clave = (ensayo["escenario"], ensayo["ensayo"], ensayo["id_conversacion"])
        registro_juez = previas.get(clave)
        if registro_juez is None and juez is not None and not ensayo.get("error"):
            calificacion = juez.calificar(caso_del_ensayo(esc, ensayo))
            registro_juez = {
                "escenario": clave[0],
                "ensayo": clave[1],
                "id_conversacion": clave[2],
                "veredicto": calificacion.veredicto.model_dump(),
                "tokens_por_modelo": {
                    juez.modelo_id: {"entrada": calificacion.entrada, "salida": calificacion.salida}
                },
                "huella": huella,
            }
            with archivo_juez.open("a", encoding="utf-8") as f:
                f.write(json.dumps(registro_juez, ensure_ascii=False) + "\n")
            if al_juzgar:
                al_juzgar(registro_juez)
        veredicto = Veredicto(**registro_juez["veredicto"]) if registro_juez else None
        meta, estricta = superado(codigo["pasa"], veredicto)
        primera = (ensayo["turnos"][0].get("meta") or {}) if ensayo["turnos"] else {}
        fila = {
            "escenario": ensayo["escenario"],
            "ensayo": ensayo["ensayo"],
            "id_conversacion": ensayo["id_conversacion"],
            "grupo": esc["grupo"],
            "conjunto": CONJUNTOS_APARTE.get(esc["grupo"], "principal"),
            "tipo_latencia": esc.get("tipo_latencia"),
            "categoria_esperada": _esperada(esc, primera.get("categoria")),
            "categoria": primera.get("categoria"),
            "con_recuperacion": any(
                (t.get("meta") or {}).get("contextos") for t in ensayo["turnos"]
            ),
            "codigo": codigo,
            "juez": veredicto.model_dump() if veredicto else None,
            "superado": meta,
            "superado_estricto": estricta,
            "turnos": [resumen_del_turno(t) for t in ensayo["turnos"]],
            "tokens_sistema": tokens_por_modelo(ensayo),
            "tokens_juez": (registro_juez or {}).get("tokens_por_modelo", {}),
            "error": ensayo.get("error"),
        }
        calificados.append(fila)
        if al_avanzar:
            al_avanzar(fila)
    return calificados


def _esperada(esc: dict[str, Any], hubo: str | None) -> str | None:
    """La categoría esperada para la matriz: si hubo una de `categorias_aceptadas`, esa."""
    if hubo in (esc.get("categorias_aceptadas") or []):
        return hubo
    return esc.get("categoria_esperada")


def costo_de(tokens: Iterable[dict[str, dict[str, int]]]) -> Decimal:
    total = Decimal(0)
    for por_modelo in tokens:
        for modelo, t in por_modelo.items():
            total += costo_usd(modelo, t["entrada"], t["salida"])
    return total


def enrutamiento_de_sistema(calificados: list[dict[str, Any]]) -> dict[str, Any]:
    """Matriz y métricas por clase con el primer turno de cada ensayo que tiene categoría."""
    pares = [
        (c["categoria_esperada"], c["categoria"] or SIN_CATEGORIA)
        for c in calificados
        if c["categoria_esperada"]
    ]
    matriz = matriz_de_confusion(pares, CATEGORIAS)
    return {"pares": len(pares), "por_categoria": por_categoria(matriz), "matriz": matriz}


def metricas(calificados: list[dict[str, Any]]) -> dict[str, Any]:
    """Métricas de un conjunto de ensayos calificados."""
    if not calificados:
        return {"ensayos": 0}
    jueces = [c["juez"] for c in calificados if c["juez"]]
    return {
        "ensayos": len(calificados),
        "escenarios": len({c["escenario"] for c in calificados}),
        "tasa_meta": tasa_con_intervalos(por_escenario(calificados, "superado")),
        "tasa_estricta": tasa_con_intervalos(por_escenario(calificados, "superado_estricto")),
        "consistencia_meta": consistencia(por_escenario(calificados, "superado")),
        "codigo_pasa": mean(c["codigo"]["pasa"] for c in calificados),
        "juez": {
            "calificados": len(jueces),
            "correcta": sum(j["veredicto"] == "correcta" for j in jueces),
            "parcialmente correcta": sum(j["veredicto"] == "parcialmente correcta" for j in jueces),
            "incorrecta": sum(j["veredicto"] == "incorrecta" for j in jueces),
            "alucinacion": mean(j["alucinacion"] for j in jueces) if jueces else None,
            "cito_norma": mean(j["cito_norma"] for j in jueces) if jueces else None,
            "cita_sustenta": mean(j["cita_sustenta"] for j in jueces) if jueces else None,
            "cobertura_completa": mean(j["cobertura_completa"] for j in jueces) if jueces else None,
            "claridad_media": mean(j["claridad"] for j in jueces) if jueces else None,
        },
        "enrutamiento": enrutamiento_de_sistema(calificados),
        "latencia": latencias(calificados),
        "costo_usd": {
            "sistema": str(costo_de(c["tokens_sistema"] for c in calificados)),
            "juez": str(costo_de(c["tokens_juez"] for c in calificados)),
        },
        "errores_de_ejecucion": sum(bool(c["error"]) for c in calificados),
    }


def metricas_por_conjunto(calificados: list[dict[str, Any]]) -> dict[str, Any]:
    conjuntos = sorted({c["conjunto"] for c in calificados}, key=lambda x: (x != "principal", x))
    return {n: metricas([c for c in calificados if c["conjunto"] == n]) for n in conjuntos}
