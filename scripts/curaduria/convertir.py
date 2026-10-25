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


_ANIO = re.compile(r"^(19|20)\d{2}\b")
_VALOR = re.compile(
    r"^\$|^más de\b|^cualquier\b|^[\d][\d.,\s]*$|^\d[\d.,]*\s*(smmlv|smlmv|uvt)$", re.IGNORECASE
)


def _es_valor(celda: str) -> bool:
    """Celda con un valor (monto, tarifa, código) y no con un rótulo de encabezado."""
    texto = celda.strip()
    return bool(texto) and not _ANIO.match(texto) and bool(_VALOR.match(texto))


def _limpiar_celda(texto: str) -> str:
    texto = re.sub(r"\s+", " ", texto).strip().replace("|", "/")
    if re.fullmatch(r"\d[\d ]* ?, ?\d+|\d+ \d+", texto) and " " in texto:
        texto = texto.replace(" ", "")  # «1 1,04» y «6 ,9»: la fuente parte las cifras
    return re.sub(r"^,(\d+,\d+)$", r"\1", texto)  # «,9,66»


def _grilla(tabla) -> list[list[str]]:
    """Filas de la tabla con rowspan y colspan expandidos, repitiendo el valor de la celda."""
    ocupadas: dict[tuple[int, int], str] = {}
    for fila, tr in enumerate(tabla.find_all("tr")):
        columna = 0
        for celda in tr.find_all(["td", "th"]):
            while (fila, columna) in ocupadas:
                columna += 1
            texto = _limpiar_celda(celda.get_text(" ", strip=True))
            filas_ocupadas = max(int(celda.get("rowspan") or 1), 1)
            columnas_ocupadas = max(int(celda.get("colspan") or 1), 1)
            for df in range(filas_ocupadas):
                for dc in range(columnas_ocupadas):
                    ocupadas.setdefault((fila + df, columna + dc), texto)
            columna += columnas_ocupadas
    if not ocupadas:
        return []
    alto, ancho = max(f for f, _ in ocupadas) + 1, max(c for _, c in ocupadas) + 1
    grilla = [[ocupadas.get((f, c), "") for c in range(ancho)] for f in range(alto)]
    return [fila for fila in grilla if any(fila)]


def _colapsar_columnas_gemelas(filas: list[list[str]]) -> list[list[str]]:
    """Quita las columnas vacías y las idénticas a la anterior en todas las filas (maquetación)."""
    ancho = max(len(f) for f in filas)
    filas = [f + [""] * (ancho - len(f)) for f in filas]
    conservar = [
        c
        for c in range(ancho)
        if any(f[c] for f in filas) and (c == 0 or any(f[c] != f[c - 1] for f in filas))
    ]
    return [[f[c] for c in conservar] for f in filas]


def _alinear_fila_corta(fila: list[str], ancho: int) -> list[str]:
    """Una fila con una celda menos que el encabezado deja vacía la primera columna de tarifas."""
    if len(fila) != ancho - 1:
        return fila
    primero = next((i for i, c in enumerate(fila) if i >= 2 and _es_valor(c)), None)
    return fila if primero is None else [*fila[:primero], "", *fila[primero:]]


def _unir_encabezados(encabezados: list[list[str]]) -> list[str]:
    """Une las filas de encabezado en una: «BASE GRAVABLE» y «DESDE» dan «BASE GRAVABLE DESDE»."""
    unidos = []
    for columna in zip(*encabezados, strict=True):
        partes: list[str] = []
        for parte in columna:
            if parte and parte not in partes:
                partes.append(parte)
        unidos.append(" ".join(partes))
    return unidos


def _tabla_a_lineas(encabezado: list[str], filas: list[list[str]]) -> list[str]:
    lineas = ["| " + " | ".join(encabezado) + " |", "|" + "---|" * len(encabezado)]
    return lineas + ["| " + " | ".join(f) + " |" for f in filas]


def tabla_markdown(tabla) -> str | None:
    """Pasa una tabla de datos de HTML a Markdown; devuelve None si es de maquetación.

    Expande rowspan y colspan, une las filas de encabezado en una, parte la tabla en las filas de
    subtítulo («Predios residenciales rurales») y vuelve a poner cada subtítulo sobre su tabla.
    """
    filas = _grilla(tabla)
    if not filas:
        return None
    if len(filas) < 2 or max(sum(bool(c) for c in f) for f in filas) < 2:
        return None
    ancho = max(len(f) for f in filas)
    segmentos: list[tuple[str | None, list[list[str]]]] = []
    for fila in filas:
        if len({c for c in fila if c}) == 1 and sum(bool(c) for c in fila) > 1:
            segmentos.append((fila[0], []))  # fila de subtítulo: todas las celdas iguales
        elif fila == [fila[0]] + [""] * (ancho - 1) and not segmentos:
            segmentos.append((fila[0], []))
        else:
            if not segmentos:
                segmentos.append((None, []))
            segmentos[-1][1].append(fila)
    bloques: list[str] = []
    encabezado_previo: list[str] | None = None
    for subtitulo, cuerpo in segmentos:
        if not cuerpo:
            if subtitulo:
                bloques.append(f"**{subtitulo}**")
            continue
        cuerpo = _colapsar_columnas_gemelas(cuerpo)
        n = next((i for i, f in enumerate(cuerpo) if any(_es_valor(c) for c in f)), len(cuerpo))
        if n == 0 and encabezado_previo is not None:
            encabezado, datos = encabezado_previo, cuerpo
        else:
            n = max(n, 1)
            encabezado, datos = _unir_encabezados(cuerpo[:n]), cuerpo[n:]
            encabezado_previo = encabezado
        etiquetas = {parte for parte in encabezado for parte in parte.split()}
        datos = [
            _alinear_fila_corta(f, len(encabezado))
            for f in datos
            if any(_es_valor(c) for c in f) or not all(p in etiquetas for c in f for p in c.split())
        ]  # fuera las filas de encabezado repetidas en los cortes de página
        bloque = "\n".join(_tabla_a_lineas(encabezado, datos))
        bloques.append(f"**{subtitulo}**\n\n{bloque}" if subtitulo else bloque)
    return "\n\n".join(bloques)


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


_TITULO_FINAL = re.compile(r"^[A-ZÁÉÍÓÚÑÜ0-9 .,;:()ºª°\-<>“”\"'/¿?]{6,}$")
_DIVISION = re.compile(r"^(T[ÍI]TULO|CAP[ÍI]TULO|SECCI[ÓO]N|LIBRO|PARTE)\b", re.IGNORECASE)
_FORMULA = re.compile(
    r"^(PUBL[ÍI]QUESE|COMUN[ÍI]QUESE|C[ÚU]MPLASE|EJ[ÉE]CUTESE|NOTIF[ÍI]QUESE)\b", re.I
)
_CARGO = re.compile(
    r"^(El|La|Los|Las)\s+(Presidente|Presidenta|Secretari[oa]|Ministro|Ministra|Alcalde|Alcaldesa|"
    r"Director|Directora|Subsecretari[oa]|Vicepresidente|Superintendente)\b"
)
_CARGO_SUELTO = re.compile(r"^(Presidente|Presidenta|Secretari[oa]|Alcalde|Alcaldesa|Director)\b")
_NOMBRE = re.compile(r"^[A-ZÁÉÍÓÚÑÜ][A-ZÁÉÍÓÚÑÜ.'\- ]{5,}$")
_PIE = re.compile(
    r"^(NOTA:|Aprobado por|Revisado por|Proyectado por|Disposiciones analizadas|ISSN|"
    r"Última actualización)",
    re.IGNORECASE,
)


def _es_firma(linea: str) -> bool:
    """Línea con nombres o cargos de quienes firman (no la fórmula de cierre ni la fecha)."""
    texto = linea.strip()
    if not texto:
        return False
    if texto.startswith("|"):
        celdas = [c.strip() for c in texto.strip("|").split("|") if c.strip(" -:")]
        return bool(celdas) and all(_NOMBRE.match(c) or _CARGO_SUELTO.match(c) for c in celdas)
    if _FORMULA.match(texto):
        return False
    return bool(
        _CARGO.match(texto)
        or _PIE.match(texto)
        or (_NOMBRE.match(texto) and len(texto.split()) >= 2)
    )


def recortar_cierre(contenido: str) -> str:
    """Conserva la fórmula de cierre y la fecha de expedición; quita las firmas y lo que sigue."""
    lineas = contenido.splitlines()
    for i, linea in enumerate(lineas):
        if i > 0 and _es_firma(linea):
            return "\n".join(lineas[:i]).rstrip()
    return contenido


def sin_titulos_finales(contenido: str) -> str:
    """Quita del final de un artículo los títulos de la sección que sigue (TÍTULO, CAPÍTULO…)."""
    lineas = contenido.rstrip().splitlines()
    while len(lineas) > 1:
        ultima = lineas[-1].strip()
        es_titulo = _DIVISION.match(ultima) or (
            _TITULO_FINAL.match(ultima) and re.search(r"[A-ZÁÉÍÓÚÑ]{3}", ultima)
        )
        if ultima and not es_titulo:
            break
        lineas.pop()
    return "\n".join(lineas)


def limpiar(texto: str) -> str:
    """Quita el ruido web que quede: enlaces en texto plano, imágenes y anclas de javascript."""
    texto = texto.replace("\r\n", "\n").replace("\r", "\n")
    texto = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", texto)
    texto = re.sub(r"\[([^\]]*)\]\((?:[^()]|\([^)]*\))*\)", r"\1", texto)
    texto = re.sub(r"(?m)^.*(?:javascript:|Ir al inicio).*$\n?", "", texto)
    texto = re.sub(r"(?m)^[ \t]*Jurisprudencia Vigencia[ \t]*$\n?", "", texto)
    texto = re.sub(r"<Ver en Jurisprudencia Vigencia[^>]*>[ \t]*", "", texto)
    texto = re.sub(r"[\u200b-\u200f\u202a-\u202e\u2060\ufeff\u00ad]", "", texto)  # formato Unicode
    texto = re.sub(  # encabezado y pie de página de las resoluciones de la Secretaría de Hacienda
        r"(?m)^(Pública|“Por la cual se ajustan para el año gravable 2026 los rangos del avalúo "
        r"catastral determinantes de|la tarifa del impuesto predial unificado”|www\.haciendabogota"
        r"\.gov\.co|Carrera 30 N\.° 25-90.*|PBX: \(\+57\).*|NIT\. 899\.999\.061-9)[ \t]*$\n?",
        "",
        texto,
    )
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
        cortes[-1] = (cortes[-1][0], recortar_cierre(cortes[-1][1]))
        cortes = [(n, sin_titulos_finales(t)) for n, t in cortes]
        destino = KNOWLEDGE_BASE / fuente["coleccion"]
        destino.mkdir(parents=True, exist_ok=True)
        cuerpo = [
            f"# {fuente['norma']}",
            "",
            f"Fuente: {_principal(fuente)} (consultada en {mes})",
            "",
        ]
        if fuente.get("vigencia"):
            cuerpo += [f"> **Vigencia por año gravable.** {fuente['vigencia']}", ""]
        anteriores = fuente.get("texto_anterior", {})
        inserciones = fuente.get("insertar", {})
        notas_de_articulo = fuente.get("notas_de_articulo", {})
        for numero, contenido in cortes:
            cuerpo += [f"## Artículo {numero}", ""]
            if numero in anteriores:
                cuerpo += [
                    f"> **Texto anterior, no vigente.** Este artículo {anteriores[numero]}; el "
                    "texto vigente está en esa norma, cargada en la base de conocimiento.",
                    "",
                ]
            if numero in notas_de_articulo:
                cuerpo += [f"> **Vigencia.** {notas_de_articulo[numero]}", ""]
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
