"""Métricas de enrutamiento y de tiempo (RF-OBS-02 y RF-OBS-03), sin LangGraph.

Se calculan con el registro de interacciones y las etiquetas de los escenarios. De cada conversación
con `escenario_id` entra en la matriz solo el primer turno: su categoría se compara con la
`categoria_esperada` del escenario, que es la del primer turno (los turnos siguientes, el botón o el
modo humano no son errores de enrutamiento). Los escenarios sin categoría esperada (los de horario)
no entran. Los tiempos usan todos los turnos; las escaladas se cuentan por conversación.

En el promedio macro, una categoría con soporte que el sistema nunca predijo cuenta con precisión
0 (su precisión por categoría queda indefinida, `None`).
"""

import math
import statistics
from collections.abc import Iterable, Mapping
from typing import Any

SIN_CATEGORIA = "sin_categoria"


def _redondear(valor: float | None) -> float | None:
    return None if valor is None else round(valor, 3)


def percentil(valores: list[float], p: float) -> float | None:
    """Percentil `p` (0 a 100) por el método del rango más cercano."""
    if not valores:
        return None
    ordenados = sorted(valores)
    posicion = max(1, math.ceil(p / 100 * len(ordenados)))
    return ordenados[min(posicion, len(ordenados)) - 1]


def matriz_de_confusion(
    pares: Iterable[tuple[str, str]], categorias: Iterable[str]
) -> dict[str, dict[str, int]]:
    """`matriz[esperada][predicha]`, con todas las categorías en filas y columnas."""
    nombres = list(dict.fromkeys([*categorias, SIN_CATEGORIA]))
    matriz = {e: dict.fromkeys(nombres, 0) for e in nombres}
    for esperada, predicha in pares:
        matriz.setdefault(esperada, dict.fromkeys(nombres, 0))
        matriz[esperada][predicha] = matriz[esperada].get(predicha, 0) + 1
    return matriz


def por_categoria(matriz: Mapping[str, Mapping[str, int]]) -> dict[str, dict[str, Any]]:
    """Precisión, exhaustividad y F1 de cada categoría con datos (las demás quedan en `None`)."""
    salida: dict[str, dict[str, Any]] = {}
    for categoria in matriz:
        verdaderos = matriz[categoria].get(categoria, 0)
        predichos = sum(fila.get(categoria, 0) for fila in matriz.values())
        reales = sum(matriz[categoria].values())
        precision = verdaderos / predichos if predichos else None
        exhaustividad = verdaderos / reales if reales else None
        f1 = (
            2 * precision * exhaustividad / (precision + exhaustividad)
            if precision and exhaustividad
            else (0.0 if precision == 0 or exhaustividad == 0 else None)
        )
        salida[categoria] = {
            "soporte": reales,
            "precision": _redondear(precision),
            "exhaustividad": _redondear(exhaustividad),
            "f1": _redondear(f1),
        }
    return salida


def calcular_metricas(
    interacciones: list[Mapping[str, Any]],
    etiquetas: Mapping[str, str | None],
    categorias: Iterable[str],
) -> dict[str, Any]:
    """Matriz de confusión, métricas por categoría (y su promedio macro) y tiempos."""
    primeros: dict[Any, Mapping[str, Any]] = {}
    for i in interacciones:  # vienen en orden de registro
        primeros.setdefault(i.get("id_conversacion"), i)
    pares = [
        (str(etiquetas[i["escenario_id"]]), i.get("categoria") or SIN_CATEGORIA)
        for i in primeros.values()
        if i.get("escenario_id") in etiquetas and etiquetas[i["escenario_id"]]
    ]
    matriz = matriz_de_confusion(pares, categorias)
    metricas = por_categoria(matriz)
    con_soporte = [m for m in metricas.values() if m["soporte"]]
    macro = {
        clave: _redondear(statistics.fmean(m[clave] or 0.0 for m in con_soporte))
        if con_soporte
        else None
        for clave in ("precision", "exhaustividad", "f1")
    }
    duraciones = [
        float(i["duracion_ms"]) for i in interacciones if i.get("duracion_ms") is not None
    ]
    estados: dict[str, int] = {}
    for i in interacciones:
        estado = i.get("estado") or "sin_estado"
        estados[estado] = estados.get(estado, 0) + 1
    return {
        "turnos": len(interacciones),
        "turnos_etiquetados": len(pares),
        "exactitud": _redondear(sum(e == p for e, p in pares) / len(pares)) if pares else None,
        "matriz_de_confusion": matriz,
        "por_categoria": metricas,
        "promedio_macro": macro,
        "tiempos_ms": {
            "mediana": statistics.median(duraciones) if duraciones else None,
            "p95": percentil(duraciones, 95),
            "maximo": max(duraciones) if duraciones else None,
        },
        "por_estado": estados,
        "conversaciones": len(primeros),
        "conversaciones_escaladas": len(
            {i.get("id_conversacion") for i in interacciones if i.get("escalada")}
        ),
    }
