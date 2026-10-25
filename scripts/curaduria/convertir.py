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


_POR_MIL = re.compile(r"\d+(?:[.,]\d+)?\s*%o\b")  # «16%o»: tarifa de tablas sin encabezado
_FORMATO = re.compile(r"[\u200b-\u200f\u202a-\u202e\u2060\ufeff\u00ad]")


def _limpiar_celda(texto: str) -> str:
    texto = _FORMATO.sub("", texto).replace(_SEPARADOR, " ")
    texto = re.sub(r"\s+", " ", texto).strip().replace("|", "/")
    if re.fullmatch(r"\d[\d ]* ?, ?\d+|\d+ \d+", texto) and " " in texto:
        texto = texto.replace(" ", "")  # «1 1,04» y «6 ,9»: la fuente parte las cifras
    return re.sub(r"^,(\d+,\d+)$", r"\1", texto)  # «,9,66»


_SEPARADOR = "\u2063"  # marca de la fuente: dos cifras separadas por espacios duros en una celda
_SEPARADAS = re.compile(rf"\s*{_SEPARADOR}\s*")


class _Grilla:
    """Filas de una tabla con rowspan y colspan expandidos.

    `filas` repite el texto de cada celda combinada; `continuacion` marca las posiciones que solo
    existen porque una celda ocupa varias columnas; `cabecera[i]` guarda el rowspan más alto de la
    fila i y si trae una celda combinada entre columnas que no sea un subtítulo.
    """

    def __init__(self, tabla) -> None:
        ocupadas: dict[tuple[int, int], tuple[str, bool]] = {}
        info: dict[int, tuple[int, bool]] = {}
        for fila, tr in enumerate(tabla.find_all("tr")):
            columna, alto, combinada = 0, 1, False
            celdas = tr.find_all(["td", "th"])
            textos = {_limpiar_celda(c.get_text(" ", strip=True)) for c in celdas} - {""}
            for celda in celdas:
                while (fila, columna) in ocupadas:
                    columna += 1
                texto = _limpiar_celda(celda.get_text(" ", strip=True))
                filas_ocupadas = max(int(celda.get("rowspan") or 1), 1)
                columnas_ocupadas = max(int(celda.get("colspan") or 1), 1)
                partes = _SEPARADAS.split(celda.get_text(" ", strip=True))
                if len(partes) == columnas_ocupadas > 1:  # dos valores en una celda combinada
                    for dc, parte in enumerate(partes):
                        ocupadas.setdefault((fila, columna + dc), (_limpiar_celda(parte), False))
                    columna += columnas_ocupadas
                    continue
                alto = max(alto, filas_ocupadas)
                combinada = combinada or (columnas_ocupadas > 1 and len(textos) > 1)
                for df in range(filas_ocupadas):
                    for dc in range(columnas_ocupadas):
                        ocupadas.setdefault((fila + df, columna + dc), (texto, dc > 0))
                columna += columnas_ocupadas
            info[fila] = (alto, combinada)
        self.filas: list[list[str]] = []
        self.continuacion: list[list[bool]] = []
        self.cabecera: list[tuple[int, bool]] = []
        if not ocupadas:
            return
        largo, ancho = max(f for f, _ in ocupadas) + 1, max(c for _, c in ocupadas) + 1
        for f in range(largo):
            fila = [ocupadas.get((f, c), ("", False)) for c in range(ancho)]
            if any(texto for texto, _ in fila):
                self.filas.append([texto for texto, _ in fila])
                self.continuacion.append([cont for _, cont in fila])
                self.cabecera.append(info.get(f, (1, False)))
        self._unir_filas_partidas()

    def _unir_filas_partidas(self) -> None:
        """Une «…constructores y» con «urbanizadores; …»: la fuente parte el rótulo en dos filas."""
        i = 0
        while i < len(self.filas) - 1:
            fila, siguiente = self.filas[i], self.filas[i + 1]
            sola = fila[0] and not any(fila[1:])
            if sola and siguiente[0][:1].islower() and any(siguiente[1:]):
                siguiente[0] = f"{fila[0]} {siguiente[0]}"
                for lista in (self.filas, self.continuacion, self.cabecera):
                    del lista[i]
            else:
                i += 1


def _grilla(tabla) -> list[list[str]]:
    """Filas de la tabla con rowspan y colspan expandidos, repitiendo el valor de la celda."""
    return _Grilla(tabla).filas


def _columnas_utiles(filas: list[list[str]]) -> list[int]:
    """Columnas que no están vacías ni son idénticas a la anterior en todas las filas."""
    ancho = max(len(f) for f in filas)
    filas = [f + [""] * (ancho - len(f)) for f in filas]
    return [
        c
        for c in range(ancho)
        if any(f[c] for f in filas) and (c == 0 or any(f[c] != f[c - 1] for f in filas))
    ]


def _colapsar_columnas_gemelas(filas: list[list[str]]) -> list[list[str]]:
    """Quita las columnas vacías y las idénticas a la anterior en todas las filas (maquetación)."""
    conservar = _columnas_utiles(filas)
    ancho = max(len(f) for f in filas)
    return [[(f + [""] * (ancho - len(f)))[c] for c in conservar] for f in filas]


def _alinear_fila_corta(fila: list[str], ancho: int) -> list[str]:
    """Una fila con una celda menos que el encabezado deja vacía la primera columna de tarifas."""
    if len(fila) != ancho - 1:
        return fila
    primero = next((i for i, c in enumerate(fila) if i >= 2 and _es_valor(c)), None)
    return fila if primero is None else [*fila[:primero], "", *fila[primero:]]


def _unir_celdas(rotulo: str, sub: str) -> str:
    if re.fullmatch(r"\d+", sub) and re.match(r"(?i)años\b", rotulo):
        return f"Año {sub}"  # «Años de la exención» sobre «1»…«10»
    return f"{rotulo} {sub}"


def _unir_encabezados(encabezados: list[list[str]]) -> list[str]:
    """Une las filas de encabezado en una: «BASE GRAVABLE» y «DESDE» dan «BASE GRAVABLE DESDE»."""
    unidos = []
    for columna in zip(*encabezados, strict=True):
        partes: list[str] = []
        texto = ""
        for parte in columna:
            if parte and parte not in partes:
                texto = _unir_celdas(texto, parte) if texto else parte
                partes.append(parte)
        unidos.append(texto)
    return unidos


def _tabla_a_lineas(encabezado: list[str], filas: list[list[str]]) -> list[str]:
    lineas = ["| " + " | ".join(encabezado) + " |", "|" + "---|" * len(encabezado)]
    return lineas + ["| " + " | ".join(f) + " |" for f in filas]


def _filas_de_encabezado(info: list[tuple[int, bool]], filas: list[list[str]]) -> int:
    """Filas del encabezado según la estructura: rowspan y celdas combinadas en la primera fila.

    Una celda combinada entre columnas solo anuncia un segundo nivel si la fila siguiente no trae
    valores: si los trae, es una fila de datos y la fuente armó mal el encabezado.
    """
    total = len(filas)
    n, i = 1, 0
    while i < n and i < total:
        alto, combinada = info[i]
        segundo_nivel = i == 0 and combinada and total > 1
        if segundo_nivel and not any(_es_valor(c) for c in filas[1]):
            n = max(n, 2)
        n = max(n, i + alto)
        i += 1
    return min(n, max(total - 1, 1))


def tabla_markdown(tabla) -> str | None:
    """Pasa una tabla de datos de HTML a Markdown; devuelve None si es de maquetación.

    El encabezado es la primera fila; solo suma filas cuando la primera trae celdas combinadas
    (rowspan, o colspan sobre un segundo nivel). Las filas de subtítulo («Predios residenciales
    rurales») parten la tabla y cada subtítulo vuelve a ponerse sobre su tabla. En las filas de
    datos, la celda que ocupa varias columnas lleva el texto en la primera y «—» en las demás.
    """
    grilla = _Grilla(tabla)
    filas = grilla.filas
    if not filas:
        return None
    if len(filas) < 2 or max(sum(bool(c) for c in f) for f in filas) < 2:
        return None
    ancho = max(len(f) for f in filas)
    segmentos: list[tuple[str | None, list[int]]] = []
    for i, fila in enumerate(filas):
        if len({c for c in fila if c}) == 1 and sum(bool(c) for c in fila) > 1:
            segmentos.append((fila[0], []))  # fila de subtítulo: todas las celdas iguales
        elif fila == [fila[0]] + [""] * (ancho - 1) and not segmentos:
            segmentos.append((fila[0], []))
        else:
            if not segmentos:
                segmentos.append((None, []))
            segmentos[-1][1].append(i)
    bloques: list[str] = []
    encabezado_previo: list[str] | None = None
    for posicion, (subtitulo, indices) in enumerate(segmentos):
        if not indices:
            if subtitulo:
                bloques.append(f"**{subtitulo}**")
            continue
        cuerpo = [filas[i] for i in indices]
        conservar = _columnas_utiles(cuerpo)
        cuerpo = [[(f + [""] * (ancho - len(f)))[c] for c in conservar] for f in cuerpo]
        guiones = [
            [(grilla.continuacion[i] + [False] * ancho)[c] for c in conservar] for i in indices
        ]
        info = [grilla.cabecera[i] for i in indices]
        con_valores = any(_es_valor(c) for f in cuerpo for c in f)
        nuevo = encabezado_previo is None or (
            not any(_es_valor(c) for c in cuerpo[0]) and con_valores
        )
        sin_encabezado = nuevo and any(_POR_MIL.search(c) for c in cuerpo[0])
        n = _filas_de_encabezado(info, cuerpo) if nuevo and not sin_encabezado else 0
        if sin_encabezado:
            encabezado = [""] * len(cuerpo[0])
        elif n:
            encabezado = _unir_encabezados(cuerpo[:n])
            if len(cuerpo) == n and any(s[1] for s in segmentos[posicion + 1 :]):
                encabezado_previo = (
                    encabezado  # solo el encabezado: los datos vienen tras el subtítulo
                )
                continue
        else:
            encabezado = encabezado_previo or []
        encabezado_previo = encabezado
        etiquetas = {p for c in encabezado for p in c.split()}
        datos = []
        for fila, marca in zip(cuerpo[n:], guiones[n:], strict=True):
            fila = [("—" if cont and c else c) for c, cont in zip(fila, marca, strict=True)]
            if any(_es_valor(c) for c in fila) or not all(
                p in etiquetas for c in fila for p in c.split()
            ):  # fuera las filas de encabezado repetidas en los cortes de página
                datos.append(_alinear_fila_corta(fila, len(encabezado)))
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
            texto = str(nodo)
            if nodo.find_parent("td"):
                texto = re.sub(r"\xa0{4,}", _SEPARADOR, texto)
            nodo.replace_with(re.sub(r"\s+", " ", texto.replace("\xa0", " ")))
    for tabla in hojas:
        markdown = tabla_markdown(tabla)
        if markdown:
            tabla.replace_with(NavigableString(f"\n\n{markdown}\n\n"))
        elif not tabla.get_text(strip=True):
            tabla.decompose()
    for etiqueta in sopa.find_all(_BLOQUES):
        etiqueta.insert_before(NavigableString("\n"))
        etiqueta.insert_after(NavigableString("\n"))
    return sopa.get_text("").replace(_SEPARADOR, " ")


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
_ROTULO = re.compile(r"^(PAR[ÁA]GRAFO|ART[ÍI]CULO|T[ÍI]TULO|CAP[ÍI]TULO|SECCI[ÓO]N|TRANSITORIO)\b")
_FECHA_DE_EXPEDICION = re.compile(r"^Dad[oa]\s+en\b")
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
        or (_NOMBRE.match(texto) and len(texto.split()) >= 2 and not _ROTULO.match(texto))
    )


def _marca_el_cierre(linea: str) -> bool:
    """Fórmula de cierre, fecha de expedición, cargo o pie: desde ahí puede haber firmas."""
    texto = linea.strip()
    return not texto.startswith("|") and bool(
        _FORMULA.match(texto)
        or _FECHA_DE_EXPEDICION.match(texto)
        or _CARGO.match(texto)
        or _PIE.match(texto)
    )


def recortar_cierre(contenido: str) -> str:
    """Conserva la fórmula de cierre y la fecha de expedición; quita las firmas y lo que sigue.

    Solo busca firmas desde la fórmula de cierre, la fecha de expedición o la línea de un cargo:
    antes de eso, una tabla o un rótulo en mayúsculas es texto de la norma.
    """
    lineas = contenido.splitlines()
    cierre = next((i for i, linea in enumerate(lineas) if _marca_el_cierre(linea)), None)
    if cierre is None:
        return contenido
    for i in range(max(cierre, 1), len(lineas)):
        if _es_firma(lineas[i]):
            return "\n".join(lineas[:i]).rstrip()
    return contenido


def mover_divisiones(cortes: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Pasa «CAPÍTULO II / Impuesto de Industria y Comercio» del final de un artículo al inicio del
    siguiente cuando es el que sigue en la numeración; en el último, lo quita.

    Solo toca los encabezados en minúsculas: los de todo en mayúsculas los quita
    `sin_titulos_finales`.
    """
    resultado = list(cortes)
    for i, (numero, texto) in enumerate(resultado):
        if sin_titulos_finales(texto) != texto.rstrip():
            continue
        lineas = texto.rstrip().splitlines()
        con_texto = [j for j, linea in enumerate(lineas) if linea.strip()]
        inicio = next((j for j in con_texto[-3:] if _DIVISION.match(lineas[j].strip())), None)
        if not inicio:
            continue
        division = "\n".join(lineas[inicio:]).strip()
        resultado[i] = (numero, "\n".join(lineas[:inicio]).rstrip())
        siguiente = resultado[i + 1] if i + 1 < len(resultado) else None
        if siguiente and siguiente[0].isdigit() and int(siguiente[0]) == int(numero) + 1:
            resultado[i + 1] = (siguiente[0], f"{division}\n\n{siguiente[1]}")
    return resultado


def sin_titulos_finales(contenido: str) -> str:
    """Quita del final de un artículo los títulos de la sección que sigue (TÍTULO, CAPÍTULO…)."""
    lineas = contenido.rstrip().splitlines()
    while len(lineas) > 1:
        ultima = lineas[-1].strip()
        es_titulo = not _FORMULA.match(ultima) and (
            _DIVISION.match(ultima)
            or (_TITULO_FINAL.match(ultima) and re.search(r"[A-ZÁÉÍÓÚÑ]{3}", ultima))
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
    texto = re.sub(r"(?m)^\d{1,2} https?://\S+[ \t]*$\n?", "", texto)  # nota al pie con un enlace
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


_LISTA_SIGUE = re.compile(r"(?:son|serán) los siguientes:\s*$", re.MULTILINE)


def _con_tabla_transcrita(contenido: str, archivo: str) -> str:
    """Cambia la tabla en texto suelto del PDF por la tabla transcrita de `datos/`."""
    corte = _LISTA_SIGUE.search(contenido)
    if corte is None:
        raise ValueError(f"no se encontró dónde empieza la tabla: {contenido[:60]!r}")
    tabla = (INSERCIONES / archivo).read_text(encoding="utf-8").strip()
    return (
        f"{contenido[: corte.end()].rstrip()}\n\n"
        "> **Tabla transcrita.** El PDF trae esta tabla como texto suelto; se transcribió desde "
        "`datos/tarifas/ipu_2026.yaml`, que se contrastó con el PDF fila por fila "
        "(`scripts/curaduria/contrastar_rangos.py`).\n\n"
        f"{tabla}"
    )


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
        cortes = mover_divisiones(cortes)
        for cambio in fuente.get("reemplazos", []):
            cortes = [(n, x.replace(cambio["de"], cambio["a"])) for n, x in cortes]
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
        transcritas = fuente.get("tablas_transcritas", {})
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
            if numero in transcritas:
                cuerpo += [_con_tabla_transcrita(contenido, transcritas[numero]), ""]
            else:
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
