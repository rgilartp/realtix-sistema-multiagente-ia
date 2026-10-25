"""Convierte las fuentes descargadas a Markdown, corta por artículo y arma `knowledge_base/`.

Escribe un `.md` por norma en `knowledge_base/<colección>/` y el `fuentes.yaml` de cada colección.
Uso: uv run python scripts/curaduria/convertir.py
"""

import re

import pypdfium2
import yaml
from bs4 import BeautifulSoup
from comun import (
    DESCARGAS,
    KNOWLEDGE_BASE,
    cargar_catalogo,
    cortar_por_articulo,
    filtrar_articulos,
)
from markdownify import markdownify

_CAPITULO = re.compile(r"^\s*(?:#+\s*)?CAP[ÍI]TULO\s+([IVXLC\d]+)\b", re.IGNORECASE | re.MULTILINE)
_CAPITULOS = {
    "capitulos_25_26": {"25", "26", "XXV", "XXVI"},
    "capitulo_1": {"I", "1"},
    "capitulo_2": {"II", "2"},
}


def textos_de(fuente: dict) -> list[str]:
    """Devuelve el texto de cada parte descargada de la fuente (vacío si no hay archivo)."""
    if fuente["formato"] == "pdf_escaneado":  # el texto sale del OCR de ocr_1084.py
        paginas = sorted((DESCARGAS / "ocr_1084").glob("pagina_*.txt"))
        return ["\n".join(p.read_text(encoding="utf-8") for p in paginas)] if paginas else []
    ext = "html" if fuente["formato"] == "html" else "pdf"
    nombre = fuente.get("archivo", fuente["id"])
    rutas = sorted(DESCARGAS.glob(f"{nombre}.{ext}")) + sorted(DESCARGAS.glob(f"{nombre}__*.{ext}"))
    return [_leer(ruta, fuente) for ruta in rutas]


def _leer(ruta, fuente: dict) -> str:
    if ruta.suffix == ".html":
        sopa = BeautifulSoup(ruta.read_bytes(), "html.parser")
        for etiqueta in sopa(["script", "style", "nav", "header", "footer"]):
            etiqueta.decompose()
        if "alcaldiabogota.gov.co" in str(fuente["url"]):  # el Régimen Legal pone todo en una tabla
            texto = sopa.get_text("\n").replace("\xa0", " ")
            return re.sub(r"(Art[íi]culo)\s*\n+\s*(?=\d)", r"\1 ", texto, flags=re.IGNORECASE)
        return markdownify(str(sopa), heading_style="ATX")
    pdf = pypdfium2.PdfDocument(ruta)
    return "\n".join(pdf[i].get_textpage().get_text_range() for i in range(len(pdf)))


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
        for (
            texto
        ) in partes:  # cada parte se corta aparte: las páginas de una norma no vienen en orden
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
        destino = KNOWLEDGE_BASE / fuente["coleccion"]
        destino.mkdir(parents=True, exist_ok=True)
        cuerpo = [
            f"# {fuente['norma']}",
            "",
            f"Fuente: {_principal(fuente)} (consultada en {mes})",
            "",
        ]
        for numero, contenido in cortes:
            cuerpo += [f"## Artículo {numero}", "", contenido, ""]
        (destino / f"{fuente['id']}.md").write_text("\n".join(cuerpo), encoding="utf-8")
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
