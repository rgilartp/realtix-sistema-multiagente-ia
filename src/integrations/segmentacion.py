"""Segmentación de `knowledge_base/` en fragmentos por artículo, con sus metadatos (sección 5.2).

- Un fragmento por `## Artículo`; los de más de unos 800 tokens se parten con 75 de solape, y las
  tablas repiten su encabezado en cada parte. Los cortos quedan enteros.
- Lo que sigue a «El texto original/anterior era el siguiente:» va en un fragmento aparte, marcado
  como texto anterior; también la sección que empieza con «Texto anterior, no vigente».
- Las notas del encabezado del archivo («Vigencia por año gravable», «Publicación»…) van al
  inicio de cada fragmento del archivo, para que el agente las vea (nota de B2).
- Metadatos: `norma`, `articulo`, `coleccion`, `url`, `vigencia_desde`, `vigencia_hasta` (enteros
  AAAAMMDD), `archivo`, `parte`, `texto_anterior` y `hash`. Las vigencias que no salen del texto
  están en `knowledge_base/vigencias.yaml`, con su fuente. Un texto anterior sin vigencia conocida
  queda fuera de toda búsqueda filtrada por año.
"""

import hashlib
import re
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path
from typing import Any

import tiktoken
import yaml

from src.integrations.recuperador import RAIZ_BASE, normas_por_archivo
from src.services.horario import MESES

MAX_TOKENS = 800
SOLAPE_TOKENS = 75
SIN_INICIO = 0
SIN_FIN = 99991231
ANTERIOR = re.compile(
    r"^El texto (?:original|anterior)(?: del artículo)? era el siguiente:?\s*$",
    re.IGNORECASE | re.MULTILINE,
)
NOTA_ENCABEZADO = re.compile(r"^> \*\*.+$", re.MULTILINE)
NO_VIGENTE = re.compile(r"^> \*\*Texto anterior, no vigente\.\*\*", re.MULTILINE)
FILA_TABLA = re.compile(r"^\|.*\|\s*$")


@cache
def _codificador() -> tiktoken.Encoding:
    return tiktoken.get_encoding("cl100k_base")  # el de text-embedding-3-large


def contar_tokens(texto: str) -> int:
    return len(_codificador().encode(texto))


@dataclass(frozen=True)
class FragmentoBase:
    id: str
    texto: str
    metadatos: dict[str, Any] = field(default_factory=dict)


def fecha_entera(valor: Any, por_defecto: int) -> int:
    """`2026-11-01` (o una fecha de YAML) -> 20261101; vacío -> el valor por defecto."""
    if valor in (None, ""):
        return por_defecto
    return int(str(valor).replace("-", ""))


@cache
def reglas_de_vigencia(raiz: Path = RAIZ_BASE) -> dict[tuple[str, str], dict[str, Any]]:
    """(`coleccion/archivo.md`, encabezado) -> regla de `vigencias.yaml`."""
    ruta = raiz / "vigencias.yaml"
    if not ruta.is_file():
        return {}
    datos = yaml.safe_load(ruta.read_text(encoding="utf-8")) or {}
    reglas = {}
    for regla in datos.get("reglas", []):
        archivos = regla["archivo"] if isinstance(regla["archivo"], list) else [regla["archivo"]]
        for archivo in archivos:
            reglas[(archivo, regla["articulo"])] = regla
    return reglas


def _vigencia(regla: dict[str, Any] | None, parte: str, anterior: bool) -> tuple[int, int]:
    """Desde y hasta de una parte (`vigente` o `anterior`); un texto anterior sin regla no rige."""
    tramo = (regla or {}).get(parte)
    if tramo is None:
        return (SIN_INICIO, SIN_INICIO) if anterior else (SIN_INICIO, SIN_FIN)
    return fecha_entera(tramo.get("desde"), SIN_INICIO), fecha_entera(tramo.get("hasta"), SIN_FIN)


def _fecha_larga(valor: int) -> str:
    anio, mes, dia = valor // 10000, valor // 100 % 100, valor % 100
    return f"{dia} de {MESES[mes - 1]} de {anio}"


def _etiqueta(encabezado: str) -> str:
    """«Artículo 3» -> «art. 3»; otros encabezados (glosario, manual) quedan igual."""
    return re.sub(r"^Art[ií]culo\s+", "art. ", encabezado)


def _unidades(cuerpo: str) -> list[tuple[str, str | None]]:
    """Párrafos y filas de tabla; cada fila lleva el encabezado de su tabla (sus dos líneas)."""
    unidades: list[tuple[str, str | None]] = []
    for bloque in re.split(r"\n\s*\n", cuerpo.strip()):
        lineas = bloque.strip().splitlines()
        if len(lineas) > 2 and all(FILA_TABLA.match(x) for x in lineas):
            encabezado = "\n".join(lineas[:2])
            unidades += [(fila, encabezado) for fila in lineas[2:]]
        elif lineas:
            unidades.append(("\n".join(lineas), None))
    return unidades


def _unir(piezas: list[tuple[str, str | None]]) -> str:
    """Junta las piezas: las filas de una misma tabla, con su encabezado una vez y sin línea en
    blanco entre ellas; los párrafos, separados por una línea en blanco."""
    salida: list[str] = []
    tabla: str | None = None
    for texto, encabezado in piezas:
        if encabezado is not None and encabezado == tabla:
            salida[-1] += "\n" + texto
        elif encabezado is not None:
            salida.append(f"{encabezado}\n{texto}")
        else:
            salida.append(texto)
        tabla = encabezado
    return "\n\n".join(salida)


def _cola(piezas: list[tuple[str, str | None]], solape: int) -> list[tuple[str, str | None]]:
    """Solape del trozo siguiente: las últimas piezas enteras que caben en `solape` tokens (filas
    de tabla con su encabezado) o, si la última es más larga, sus últimos `solape` tokens."""
    cola: list[tuple[str, str | None]] = []
    tokens = 0
    for texto, encabezado in reversed(piezas):
        n = contar_tokens(texto)
        if tokens + n > solape:
            break
        cola.insert(0, (texto, encabezado))
        tokens += n
    if cola:
        return cola
    ultimo = _codificador().encode(piezas[-1][0])[-solape:]
    return [(f"[…] {_codificador().decode(ultimo).strip()}", None)]


def partir(cuerpo: str, maximo: int = MAX_TOKENS, solape: int = SOLAPE_TOKENS) -> list[str]:
    """Trozos de hasta unos `maximo` tokens; cada uno empieza con los últimos `solape` del anterior
    y una tabla partida repite su encabezado. Un texto corto queda entero."""
    if contar_tokens(cuerpo) <= maximo:
        return [cuerpo.strip()]
    codificador = _codificador()
    piezas: list[tuple[str, str | None]] = []
    for texto, encabezado in _unidades(cuerpo):
        ids = codificador.encode(texto)
        paso = maximo - solape
        if len(ids) <= paso:
            piezas.append((texto, encabezado))
        else:  # un párrafo enorme se corta por tokens
            cortes = range(0, len(ids), paso)
            piezas += [(codificador.decode(ids[i : i + paso]), None) for i in cortes]
    trozos: list[str] = []
    actual: list[tuple[str, str | None]] = []
    for pieza in piezas:
        candidato = _unir([*actual, pieza])
        if actual and contar_tokens(candidato) > maximo:
            trozos.append(_unir(actual))
            actual = _cola(actual, solape)
            if contar_tokens(_unir([*actual, pieza])) > maximo:  # no cabe con el solape
                actual = []
        actual.append(pieza)
    trozos.append(_unir(actual))
    return trozos


def _hash(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def segmentar_archivo(ruta: Path, raiz: Path = RAIZ_BASE) -> list[FragmentoBase]:
    """Fragmentos de una norma en Markdown, con las notas del encabezado en cada uno."""
    coleccion = ruta.parent.name
    clave = f"{coleccion}/{ruta.name}"
    norma, url = normas_por_archivo(raiz).get(clave, (ruta.stem, ""))
    texto = ruta.read_text(encoding="utf-8")
    preambulo, *secciones = re.split(r"^## ", texto, flags=re.MULTILINE)
    notas = "\n".join(x for x in preambulo.splitlines() if x.startswith(">")).strip()
    reglas = reglas_de_vigencia(raiz)
    fragmentos: list[FragmentoBase] = []
    for indice, seccion in enumerate(secciones, 1):
        encabezado, _, cuerpo = seccion.partition("\n")
        encabezado = encabezado.strip()
        regla = reglas.get((clave, encabezado))
        todo_anterior = bool(NO_VIGENTE.search(cuerpo))
        vigente, _, anterior = _separar(cuerpo)
        for parte, cuerpo_parte, es_anterior in (
            ("vigente", vigente, todo_anterior),
            ("anterior", anterior, True),
        ):
            if not cuerpo_parte.strip():
                continue
            desde, hasta = _vigencia(regla, parte, es_anterior)
            etiqueta = _etiqueta(encabezado)
            titulo = norma if etiqueta in norma else f"{norma}, {etiqueta}"
            if es_anterior:
                titulo += (
                    " (texto anterior, no vigente)"
                    if hasta == SIN_INICIO
                    else f" (texto anterior, rige hasta el {_fecha_larga(hasta)})"
                )
            prefijo = f"{titulo}\n\n{notas}\n\n" if notas else f"{titulo}\n\n"
            presupuesto = MAX_TOKENS - contar_tokens(prefijo)
            for n, trozo in enumerate(partir(cuerpo_parte, maximo=max(presupuesto, 200)), 1):
                contenido = prefijo + trozo
                fragmentos.append(
                    FragmentoBase(
                        id=f"{clave}#{indice:03d}-{parte}-{n}",
                        texto=contenido,
                        metadatos={
                            "norma": norma,
                            "articulo": encabezado,
                            "coleccion": coleccion,
                            "url": url,
                            "vigencia_desde": desde,
                            "vigencia_hasta": hasta,
                            "archivo": clave,
                            "parte": n,
                            "texto_anterior": es_anterior,
                            "hash": _hash(contenido),
                        },
                    )
                )
    return fragmentos


def _separar(cuerpo: str) -> tuple[str, str, str]:
    """(texto vigente, marcador, texto anterior) según «El texto original era el siguiente:»."""
    encontrado = ANTERIOR.search(cuerpo)
    if not encontrado:
        return cuerpo, "", ""
    return cuerpo[: encontrado.start()], encontrado.group(0), cuerpo[encontrado.end() :]


def segmentar_base(raiz: Path = RAIZ_BASE) -> dict[str, list[FragmentoBase]]:
    """Fragmentos de toda la base, por colección."""
    por_coleccion: dict[str, list[FragmentoBase]] = {}
    for ruta in sorted(raiz.glob("*/*.md")):
        por_coleccion.setdefault(ruta.parent.name, []).extend(segmentar_archivo(ruta, raiz))
    return por_coleccion


def version_del_corpus(raiz: Path = RAIZ_BASE) -> str:
    """Hash del contenido de `knowledge_base/` (sección 5.5): cambia con cualquier archivo."""
    resumen = hashlib.sha256()
    for ruta in sorted(p for p in raiz.rglob("*") if p.is_file()):
        resumen.update(str(ruta.relative_to(raiz)).encode("utf-8"))
        resumen.update(ruta.read_bytes())
    return resumen.hexdigest()[:16]
