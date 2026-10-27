"""Métricas de las corridas (sección 6.5 y ADR-24): tasas, intervalos, consistencia y acuerdo.

- Tasa de la meta (RNF-16): el ensayo pasa todas las verificaciones de código y el juez lo califica
  correcta o parcialmente correcta, sin alucinación. Tasa estricta (A3): además, «correcta».
- Intervalo de Wilson al 95 % con n = número de escenarios (A2): los ensayos de un mismo escenario
  no son independientes. Además, un bootstrap por escenario del promedio de sus ensayos.
- pass@k y pass^k con el estimador combinatorio (Chen y colaboradores), por escenario.
- Kappa de Cohen, binario o ponderado lineal de 3 niveles (A6), con intervalo por bootstrap.
Todo con semilla fija, para que el reporte sea repetible (RF-OBS-05).
"""

import math
import random
from collections import defaultdict
from collections.abc import Callable, Sequence
from statistics import mean
from typing import Any

from src.services.metricas import percentil

Z_95 = 1.959963984540054
SEMILLA = 42
REPETICIONES_BOOTSTRAP = 10_000
VEREDICTOS = ("incorrecta", "parcialmente correcta", "correcta")  # orden de los 3 niveles


def wilson(tasa: float, n: int, z: float = Z_95) -> tuple[float, float]:
    """Intervalo de Wilson para una proporción `tasa` observada en `n` unidades independientes."""
    if n <= 0:
        raise ValueError("El intervalo de Wilson necesita n > 0.")
    if not 0 <= tasa <= 1:
        raise ValueError("La tasa debe estar entre 0 y 1.")
    denominador = 1 + z**2 / n
    centro = (tasa + z**2 / (2 * n)) / denominador
    margen = z * math.sqrt(tasa * (1 - tasa) / n + z**2 / (4 * n**2)) / denominador
    return max(0.0, centro - margen), min(1.0, centro + margen)


def bootstrap(
    unidades: Sequence[Any],
    estadistico: Callable[[Sequence[Any]], float],
    repeticiones: int = REPETICIONES_BOOTSTRAP,
    semilla: int = SEMILLA,
    nivel: float = 0.95,
) -> tuple[float, float]:
    """Intervalo de percentiles remuestreando las unidades con reemplazo."""
    if not unidades:
        raise ValueError("El bootstrap necesita al menos una unidad.")
    azar = random.Random(semilla)
    valores = sorted(
        estadistico([azar.choice(unidades) for _ in unidades]) for _ in range(repeticiones)
    )
    cola = (1 - nivel) / 2
    return valores[int(cola * repeticiones)], valores[
        min(repeticiones - 1, int((1 - cola) * repeticiones))
    ]


def pass_at_k(n: int, c: int, k: int) -> float:
    """Probabilidad de acertar al menos una vez en k intentos, con c aciertos de n ensayos."""
    if not 0 <= c <= n or not 1 <= k <= n:
        raise ValueError("Se necesita 0 <= c <= n y 1 <= k <= n.")
    if n - c < k:
        return 1.0
    return 1 - math.comb(n - c, k) / math.comb(n, k)


def pass_hat_k(n: int, c: int, k: int) -> float:
    """pass^k: probabilidad de acertar en los k intentos (consistencia)."""
    if not 0 <= c <= n or not 1 <= k <= n:
        raise ValueError("Se necesita 0 <= c <= n y 1 <= k <= n.")
    return math.comb(c, k) / math.comb(n, k)


def kappa(a: Sequence[Any], b: Sequence[Any], niveles: Sequence[Any] | None = None) -> float:
    """Kappa de Cohen; con `niveles` ordenados, ponderado lineal (un desacuerdo lejano pesa más)."""
    if len(a) != len(b) or not a:
        raise ValueError("Las dos calificaciones deben tener el mismo tamaño, mayor que 0.")
    categorias = list(niveles) if niveles else sorted(set(a) | set(b), key=str)
    indice = {c: i for i, c in enumerate(categorias)}
    k = len(categorias)
    if niveles:
        peso = [[abs(i - j) / (k - 1) if k > 1 else 0.0 for j in range(k)] for i in range(k)]
    else:
        peso = [[0.0 if i == j else 1.0 for j in range(k)] for i in range(k)]
    n = len(a)
    observada = [[0.0] * k for _ in range(k)]
    for x, y in zip(a, b, strict=True):
        observada[indice[x]][indice[y]] += 1 / n
    filas = [sum(f) for f in observada]
    columnas = [sum(observada[i][j] for i in range(k)) for j in range(k)]
    desacuerdo_obs = sum(peso[i][j] * observada[i][j] for i in range(k) for j in range(k))
    desacuerdo_esp = sum(peso[i][j] * filas[i] * columnas[j] for i in range(k) for j in range(k))
    if desacuerdo_esp == 0:
        return 1.0  # las dos calificaciones son constantes e iguales
    return 1 - desacuerdo_obs / desacuerdo_esp


def kappa_con_intervalo(
    a: Sequence[Any], b: Sequence[Any], niveles: Sequence[Any] | None = None
) -> dict[str, Any]:
    pares = list(zip(a, b, strict=True))

    def estadistico(muestra: Sequence[tuple[Any, Any]]) -> float:
        x, y = zip(*muestra, strict=True)
        return kappa(x, y, niveles)

    bajo, alto = bootstrap(pares, estadistico)
    return {"kappa": kappa(a, b, niveles), "ic95": [bajo, alto], "n": len(pares)}


def por_escenario(ensayos: Sequence[dict[str, Any]], campo: str) -> dict[str, list[bool]]:
    """Escenario -> resultado (`campo`) de cada uno de sus ensayos, en orden."""
    agrupados: dict[str, list[tuple[int, bool]]] = defaultdict(list)
    for e in ensayos:
        agrupados[e["escenario"]].append((e.get("ensayo", 1), bool(e[campo])))
    return {esc: [ok for _, ok in sorted(v)] for esc, v in sorted(agrupados.items())}


def tasa_con_intervalos(resultados: dict[str, list[bool]]) -> dict[str, Any]:
    """Promedio de los ensayos de cada escenario; Wilson con n = escenarios y bootstrap."""
    if not resultados:
        return {"escenarios": 0, "tasa": None, "wilson95": None, "bootstrap95": None}
    tasas = [mean(v) for v in resultados.values()]
    tasa = mean(tasas)
    return {
        "escenarios": len(tasas),
        "ensayos": sum(len(v) for v in resultados.values()),
        "tasa": tasa,
        "wilson95": list(wilson(tasa, len(tasas))),
        "bootstrap95": list(bootstrap(tasas, mean)),
    }


def consistencia(resultados: dict[str, list[bool]]) -> dict[str, Any]:
    """pass@1 promedio, pass@k y pass^k con k = ensayos de cada escenario (3 en la corrida 3)."""
    if not resultados:
        return {}
    k = min(len(v) for v in resultados.values())
    filas = [(len(v), sum(v)) for v in resultados.values()]
    return {
        "k": k,
        "pass@1": mean(pass_at_k(n, c, 1) for n, c in filas),
        f"pass@{k}": mean(pass_at_k(n, c, k) for n, c in filas),
        f"pass^{k}": mean(pass_hat_k(n, c, k) for n, c in filas),
    }


def latencias(ensayos: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """p50 y p95 de RNF-01, del servidor y del cliente (A9), por turno: «rag» si el turno recuperó
    fragmentos y «simple» si no. Solo cuentan los turnos que llegaron a los agentes (los de modo
    humano, horario o falla inyectada responden sin modelo y bajarían la mediana)."""
    salida: dict[str, Any] = {}
    meta_ms = {"simple": 8000, "rag": 15000}
    turnos = [t for e in ensayos for t in e.get("turnos", []) if t.get("con_agentes")]
    for tipo in ("simple", "rag"):
        delt = [t for t in turnos if bool(t.get("con_recuperacion")) == (tipo == "rag")]
        servidor = [float(t["latencia_servidor_ms"]) for t in delt if t.get("latencia_servidor_ms")]
        cliente = [float(t["latencia_cliente_ms"]) for t in delt if t.get("latencia_cliente_ms")]
        salida[tipo] = {
            "turnos": len(delt),
            "meta_ms": meta_ms[tipo],
            "servidor_p50_ms": percentil(servidor, 50),
            "servidor_p95_ms": percentil(servidor, 95),
            "cliente_p50_ms": percentil(cliente, 50),
            "cliente_p95_ms": percentil(cliente, 95),
            "cumplen_meta": sum(v < meta_ms[tipo] for v in servidor),
        }
    return salida
