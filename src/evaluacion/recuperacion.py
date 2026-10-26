"""Prueba de la recuperación con los escenarios aprobados (revisión externa sobre B8).

Para cada escenario aprobado cuyas `fuentes_esperadas` nombran una norma de `knowledge_base/`, pasa
el primer turno por el orquestador real (partes y búsquedas), recupera cada parte con las
colecciones de su agente y el año del reloj del escenario, y mira si entre los 5 primeros
fragmentos están la norma y el artículo esperados. Lo hace dos veces: con el texto de la parte
(como antes de la corrección) y con la búsqueda en los términos de la norma (como ahora).
"""

import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from src.agents.agente import K_FRAGMENTOS, ConfigAgente, anio_de_la_consulta, recuperar
from src.agents.dependencias import Clasificador, Dependencias
from src.agents.nodes import general, ica, ipu
from src.agents.prompts import Prompt
from src.agents.state import entrada_de_turno
from src.integrations.recuperador import Fragmento, normas_por_archivo
from src.integrations.trazas import Anonimizador

COLECCIONES_POR_CATEGORIA = {
    "ipu": ipu.COLECCIONES,
    "ica": ica.COLECCIONES,
    "general": general.COLECCIONES,
}
NORMA = re.compile(
    r"\b(ley|acuerdo|decreto|resoluci[oó]n)\b\D*?(\d+)\s+de\s+(\d{4})", re.IGNORECASE
)
SINTETICAS = {"glosario": "glosario", "manual de uso de la ovt": "manual"}
ARTICULO_EN_SECCION = re.compile(r"^Art[ií]culo\s+(\d+(?:-\d+)?)", re.IGNORECASE)
ARTICULOS_EN_CITA = re.compile(r",?\s*\barts?\.\s*(\d+(?:-\d+)?(?:\s*(?:,|y)\s*\d+(?:-\d+)?)*)")


@dataclass(frozen=True)
class FuenteEsperada:
    texto: str  # tal como está en el escenario
    norma: str  # clave: «ley 1995 2019», «glosario»…
    articulos: frozenset[str]  # vacío: basta la norma


def clave_de_norma(texto: str) -> str | None:
    """«Decreto Distrital 352 de 2002, cap. I» -> «decreto 352 2002»; el glosario y el manual de la
    OVT simulada tienen su propia clave; lo demás (datos, usuarios, requerimientos) no es norma."""
    minusculas = texto.lower()
    for prefijo, clave in SINTETICAS.items():
        if minusculas.startswith(prefijo):
            return clave
    encontrada = NORMA.search(texto)
    if not encontrada or "datos/" in minusculas:
        return None
    tipo = encontrada.group(1).lower().replace("ó", "o")
    return f"{tipo} {int(encontrada.group(2))} {encontrada.group(3)}"


def articulos_de_cita(texto: str) -> frozenset[str]:
    """«art. 49, par. 3» -> {49}; «arts. 10, 11 y 13» -> {10, 11, 13}."""
    encontrados = ARTICULOS_EN_CITA.search(texto)
    if not encontrados:
        return frozenset()
    return frozenset(re.findall(r"\d+(?:-\d+)?", encontrados.group(1)))


def normas_de_la_base() -> set[str]:
    return {c for norma, _ in normas_por_archivo().values() if (c := clave_de_norma(norma))}


def fuentes_de_la_base(escenario: dict[str, Any], normas: set[str]) -> list[FuenteEsperada]:
    """Las fuentes esperadas del escenario que son normas de `knowledge_base/`."""
    fuentes = []
    for texto in escenario.get("fuentes_esperadas") or []:
        clave = clave_de_norma(texto)
        if clave in normas:
            fuentes.append(FuenteEsperada(texto, clave, articulos_de_cita(texto)))
    return fuentes


def articulo_del_fragmento(fragmento: Fragmento) -> str | None:
    encontrado = ARTICULO_EN_SECCION.match(fragmento.seccion)
    if encontrado:
        return encontrado.group(1)
    en_norma = articulos_de_cita(fragmento.norma)
    return next(iter(en_norma)) if len(en_norma) == 1 else None


def acierta(fuente: FuenteEsperada, fragmentos: Iterable[Fragmento]) -> bool:
    """La norma esperada (y uno de sus artículos, si los nombra) está entre los fragmentos."""
    for fragmento in fragmentos:
        if clave_de_norma(fragmento.norma or fragmento.fuente) != fuente.norma:
            continue
        if not fuente.articulos or articulo_del_fragmento(fragmento) in fuente.articulos:
            return True
    return False


def _cita(fragmento: Fragmento) -> str:
    return fragmento.cita + (" (anterior)" if fragmento.vigencia_hasta == 0 else "")


def probar_escenario(
    escenario: dict[str, Any],
    fuentes: list[FuenteEsperada],
    clasificar: Clasificador,
    deps: Dependencias,
    sesiones: dict[str, tuple[str, list[str]]],
) -> dict[str, Any]:
    """Partes del orquestador, los 5 primeros de cada parte (por texto y por búsqueda) y los
    aciertos."""
    texto = escenario["turnos"][0]["usuario"]
    contribuyente, predios = sesiones.get(escenario.get("sesion") or "", (None, []))
    estado = entrada_de_turno(texto, f"recuperacion-{escenario['id']}", contribuyente, predios)
    clasificacion = clasificar(texto, estado)
    hoy = datetime.fromisoformat(escenario["reloj"]).date()
    anonimizar = Anonimizador(para_modelos=True).texto
    partes = []
    por_texto: list[Fragmento] = []
    por_busqueda: list[Fragmento] = []
    for parte in clasificacion.partes:
        colecciones = COLECCIONES_POR_CATEGORIA.get(parte["categoria"], ())
        config = ConfigAgente(parte["categoria"], Prompt("", "", ""), colecciones)
        anio = anio_de_la_consulta(parte["texto"], hoy)
        busqueda = parte.get("busqueda") or parte["texto"]
        con_texto = recuperar(deps, config, anonimizar(parte["texto"]), anio)
        con_busqueda = recuperar(deps, config, anonimizar(busqueda), anio)
        por_texto += con_texto
        por_busqueda += con_busqueda
        partes.append(
            {
                "categoria": parte["categoria"],
                "texto": parte["texto"],
                "busqueda": busqueda,
                "anio": anio,
                "con_texto": [_cita(f) for f in con_texto],
                "con_busqueda": [_cita(f) for f in con_busqueda],
            }
        )
    return {
        "escenario": escenario["id"],
        "grupo": escenario.get("grupo"),
        "comportamiento_esperado": escenario.get("comportamiento_esperado"),
        "partes": partes,
        "fuentes": [
            {
                "fuente": f.texto,
                "con_texto": acierta(f, por_texto),
                "con_busqueda": acierta(f, por_busqueda),
            }
            for f in fuentes
        ],
    }


# Escenarios cuya respuesta sale de los fragmentos: los grupos de los agentes que responden. Los
# demás (acceso, horario, fuera de alcance, robustez, OCR…) responden con texto fijo, con datos del
# adaptador o escalan, y su fuente esperada no depende de la recuperación.
GRUPOS_CON_FRAGMENTOS = ("ipu", "ica", "general", "multiagente")


def resumir(resultados: list[dict[str, Any]]) -> dict[str, Any]:
    """Tasas de todos los escenarios y de los que responden con fragmentos."""
    con_fragmentos = [
        r
        for r in resultados
        if r.get("grupo") in GRUPOS_CON_FRAGMENTOS
        and r.get("comportamiento_esperado") == "responder"
    ]
    return {
        **_tasas(resultados),
        "k": K_FRAGMENTOS,
        "responden_con_fragmentos": _tasas(con_fragmentos),
    }


def _tasas(resultados: list[dict[str, Any]]) -> dict[str, Any]:
    """Tasa de aciertos por fuente y por escenario (todas sus fuentes), con texto y con búsqueda."""
    fuentes = [f for r in resultados for f in r["fuentes"]]
    resumen: dict[str, Any] = {"escenarios": len(resultados), "fuentes": len(fuentes)}
    for modo in ("con_texto", "con_busqueda"):
        por_fuente = sum(f[modo] for f in fuentes)
        por_escenario = sum(all(f[modo] for f in r["fuentes"]) for r in resultados)
        resumen[modo] = {
            "aciertos_por_fuente": por_fuente,
            "tasa_por_fuente": round(por_fuente / len(fuentes), 3) if fuentes else None,
            "escenarios_con_todas": por_escenario,
            "tasa_por_escenario": round(por_escenario / len(resultados), 3) if resultados else None,
        }
    return resumen


def probar_recuperacion(
    escenarios: list[dict[str, Any]],
    clasificar: Clasificador,
    deps: Dependencias,
    sesiones: dict[str, tuple[str, list[str]]],
    al_avanzar: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    """Prueba los escenarios aprobados con fuentes de la base y devuelve el reporte."""
    normas = normas_de_la_base()
    resultados = []
    for escenario in escenarios:
        fuentes = fuentes_de_la_base(escenario, normas)
        if not escenario.get("aprobado_por") or not fuentes:
            continue
        resultado = probar_escenario(escenario, fuentes, clasificar, deps, sesiones)
        resultados.append(resultado)
        if al_avanzar:
            al_avanzar(resultado)
    return {"resultados": resultados, "resumen": resumir(resultados)}
