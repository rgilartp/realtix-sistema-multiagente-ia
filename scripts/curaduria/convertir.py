"""Convierte las fuentes descargadas a Markdown, corta por artículo y arma `knowledge_base/`.

Escribe un `.md` por norma en `knowledge_base/<colección>/` y el `fuentes.yaml` de cada colección.
Uso: uv run python scripts/curaduria/convertir.py
"""

import re
from pathlib import Path

import pypdfium2
import yaml
from bs4 import BeautifulSoup, Comment, NavigableString
from comun import (
    DESCARGAS,
    KNOWLEDGE_BASE,
    cargar_catalogo,
    cortar_por_articulo,
    filtrar_articulos,
)

_CAPITULO = re.compile(r"^\s*(?:#+\s*)?CAP[ÍI]TULO\s+([IVXLC\d]+)\b", re.IGNORECASE | re.MULTILINE)
_CAPITULOS = {
    "capitulos_25_26": {"25", "26", "XXV", "XXVI"},
    "capitulo_1": {"I", "1"},
    "capitulo_2": {"II", "2"},
}


INSERCIONES = Path(__file__).with_name("inserciones")

_BLOQUES = [
    "p",
    "div",
    "br",
    "li",
    "tr",
    "td",
    "th",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "dd",
    "dt",
]


def textos_de(fuente: dict) -> list[str]:
    """Devuelve el texto de cada parte descargada de la fuente (vacío si no hay archivo)."""
    ext = "html" if fuente["formato"] == "html" else "pdf"
    nombre = fuente.get("archivo", fuente["id"])
    rutas = sorted(DESCARGAS.glob(f"{nombre}.{ext}")) + sorted(DESCARGAS.glob(f"{nombre}__*.{ext}"))
    return [_leer(ruta) for ruta in rutas]


def tabla_markdown(tabla) -> str | None:
    """Pasa una tabla de datos de HTML a Markdown; devuelve None si es de maquetación."""
    filas = []
    for tr in tabla.find_all("tr"):
        celdas = [
            re.sub(r"\s+", " ", c.get_text(" ", strip=True)).replace("|", "/")
            for c in tr.find_all(["td", "th"])
        ]
        if any(celdas):
            filas.append(celdas)
    if len(filas) < 2 or max(sum(bool(c) for c in f) for f in filas) < 2:
        return None
    ancho = max(len(f) for f in filas)
    filas = [f + [""] * (ancho - len(f)) for f in filas]
    lineas = ["| " + " | ".join(filas[0]) + " |", "|" + "---|" * ancho]
    lineas += ["| " + " | ".join(f) + " |" for f in filas[1:]]
    return "\n".join(lineas)


def _html_a_texto(contenido: bytes) -> str:
    """Texto de una página HTML sin enlaces, imágenes ni anclas de javascript.

    Las tablas de datos pasan a Markdown, las tablas vacías se descartan y las notas de vigencia
    («Modificado por…») se conservan como texto.
    """
    sopa = BeautifulSoup(contenido, "html.parser")
    for etiqueta in sopa(["script", "style", "nav", "header", "footer", "img"]):
        etiqueta.decompose()
    for ancla in sopa.find_all("a"):
        href = ancla.get("href") or ""
        if href.startswith("javascript") or ancla.get("title") == "Ir al inicio":
            ancla.decompose()
        else:
            ancla.unwrap()
    hojas = [t for t in sopa.find_all("table") if t.find("table") is None]
    for nodo in sopa.find_all(string=True):  # los saltos del HTML son solo ajuste de línea
        if not isinstance(nodo, Comment):
            nodo.replace_with(re.sub(r"\s+", " ", str(nodo).replace("\xa0", " ")))
    for tabla in hojas:
        markdown = tabla_markdown(tabla)
        if markdown:
            tabla.replace_with(NavigableString(f"\n\n{markdown}\n\n"))
        elif not tabla.get_text(strip=True):
            tabla.decompose()
    for etiqueta in sopa.find_all(_BLOQUES):
        etiqueta.insert_before(NavigableString("\n"))
        etiqueta.insert_after(NavigableString("\n"))
    return sopa.get_text("")


def _leer(ruta) -> str:
    if ruta.suffix == ".html":
        return _html_a_texto(ruta.read_bytes())
    pdf = pypdfium2.PdfDocument(ruta)
    return "\n".join(pdf[i].get_textpage().get_text_range() for i in range(len(pdf)))


_TITULO_FINAL = re.compile(r"^[A-ZÁÉÍÓÚÑÜ0-9 .,;:()ºª°\-]{6,}$")


def sin_titulos_finales(contenido: str) -> str:
    """Quita del final de un artículo los títulos de la sección que sigue (TÍTULO, CAPÍTULO…)."""
    lineas = contenido.rstrip().splitlines()
    while len(lineas) > 1:
        ultima = lineas[-1].strip()
        if ultima and not (_TITULO_FINAL.match(ultima) and re.search(r"[A-ZÁÉÍÓÚÑ]{3}", ultima)):
            break
        lineas.pop()
    return "\n".join(lineas)


def limpiar(texto: str) -> str:
    """Quita el ruido web que quede: enlaces en texto plano, imágenes y anclas de javascript."""
    texto = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", texto)
    texto = re.sub(r"\[([^\]]*)\]\((?:[^()]|\([^)]*\))*\)", r"\1", texto)
    texto = re.sub(r"(?m)^.*(?:javascript:|Ir al inicio).*$\n?", "", texto)
    texto = re.sub(r"(?m)^[ \t]*Jurisprudencia Vigencia[ \t]*$\n?", "", texto)
    texto = re.sub(r"<Ver en Jurisprudencia Vigencia[^>]*>[ \t]*", "", texto)
    texto = re.sub(
        r"(?m)^\|[\s|:-]*\|[ \t]*$\n?", lambda m: m.group(0) if "---" in m.group(0) else "", texto
    )
    texto = re.sub(r"(Art[íi]culo)[ \t]*\n+[ \t]*(?=\d)", r"\1 ", texto, flags=re.IGNORECASE)
    texto = re.sub(r"(?m)^[ \t]+|[ \t]+$", "", texto)
    return re.sub(r"\n{3,}", "\n\n", texto)


def _principal(fuente: dict) -> str:
    return fuente["url"][0] if isinstance(fuente["url"], list) else fuente["url"]


def recortar_capitulos(texto: str, clave: str) -> str:
    """Conserva solo los capítulos pedidos (por ejemplo, 25 y 26 del Decreto 1074)."""
    marcas = list(_CAPITULO.finditer(texto))
    trozos = []
    for i, marca in enumerate(marcas):
        fin = marcas[i + 1].start() if i + 1 < len(marcas) else len(texto)
        if marca.group(1).upper() in _CAPITULOS[clave]:
            trozos.append(texto[marca.start() : fin])
    return "\n".join(trozos)


def convertir() -> dict[str, dict]:
    catalogo = cargar_catalogo()
    mes = catalogo["mes_consulta"]
    resultado: dict[str, dict] = {}
    por_coleccion: dict[str, list[dict]] = {}
    for fuente in catalogo["fuentes"]:
        partes = textos_de(fuente)
        if not partes:
            resultado[fuente["id"]] = {"estado": "sin_archivo", "articulos": 0}
            continue
        seleccion = fuente["articulos"]
        cortes: list[tuple[str, str]] = []
        for texto in partes:  # cada parte se corta aparte: las páginas no vienen en orden
            texto = limpiar(texto)
            if isinstance(seleccion, str) and seleccion in _CAPITULOS:
                texto = recortar_capitulos(texto, seleccion)
            nuevos = cortar_por_articulo(texto)
            if isinstance(seleccion, list):
                nuevos = filtrar_articulos(nuevos, seleccion)
            vistos = {n for n, _ in cortes}
            cortes += [(n, t) for n, t in nuevos if n not in vistos]
        if not cortes:
            resultado[fuente["id"]] = {"estado": "sin_articulos", "articulos": 0}
            continue
        cortes = [(n, sin_titulos_finales(t)) for n, t in cortes]
        destino = KNOWLEDGE_BASE / fuente["coleccion"]
        destino.mkdir(parents=True, exist_ok=True)
        cuerpo = [
            f"# {fuente['norma']}",
            "",
            f"Fuente: {_principal(fuente)} (consultada en {mes})",
            "",
        ]
        anteriores = fuente.get("texto_anterior", {})
        inserciones = fuente.get("insertar", {})
        for numero, contenido in cortes:
            cuerpo += [f"## Artículo {numero}", ""]
            if numero in anteriores:
                cuerpo += [
                    f"> **Texto anterior, no vigente.** Este artículo {anteriores[numero]}; el "
                    "texto vigente está en esa norma, cargada en la base de conocimiento.",
                    "",
                ]
            cuerpo += [contenido, ""]
            if numero in inserciones:
                tabla = (INSERCIONES / inserciones[numero]).read_text(encoding="utf-8")
                cuerpo += [
                    "> **Tabla en imagen en la fuente, transcrita.** Las fechas de este artículo "
                    "están en imágenes de la página y no salen en el texto; se transcribieron y "
                    "se verificaron contra la imagen.",
                    "",
                    tabla.strip(),
                    "",
                ]
        lineas = "\n".join(cuerpo).splitlines()
        contenido = "\n".join(linea.rstrip() for linea in lineas).rstrip("\n") + "\n"
        (destino / f"{fuente['id']}.md").write_text(contenido, encoding="utf-8")
        resultado[fuente["id"]] = {"estado": "ok", "articulos": len(cortes)}
        por_coleccion.setdefault(fuente["coleccion"], []).append(
            {
                "archivo": f"{fuente['id']}.md",
                "norma": fuente["norma"],
                "url": fuente["url"],
                "mes_consulta": mes,
            }
        )
    for coleccion, entradas in por_coleccion.items():
        ruta = KNOWLEDGE_BASE / coleccion / "fuentes.yaml"
        ruta.write_text(
            yaml.safe_dump({"fuentes": entradas}, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
    return resultado


if __name__ == "__main__":
    for id_fuente, datos in convertir().items():
        print(f"{id_fuente}: {datos['estado']} ({datos['articulos']} artículos)")
