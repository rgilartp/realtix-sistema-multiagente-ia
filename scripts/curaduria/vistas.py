"""Genera las vistas lado a lado de `docs/verificacion/`: la fuente a la izquierda y la tabla
transcrita a la derecha, con las diferencias resaltadas.

Las imágenes salen del PDF del Acuerdo 1084 (páginas del OCR), del PDF de la resolución de rangos
y de las tablas incrustadas en la página de la Resolución SDH-000195, y se guardan reducidas en
`docs/verificacion/img/`. Antes hay que correr `ocr_1084.py`, `doble_lectura.py` y
`contrastar_rangos.py`.
Uso: uv run python scripts/curaduria/vistas.py
"""

import html
import json
import re
from collections.abc import Callable
from decimal import Decimal

import construir_ica_2026
import contrastar_rangos
import doble_lectura
import pypdfium2
import yaml
from comun import DESCARGAS, RAIZ
from PIL import Image

DATOS = RAIZ / "datos"
SALIDA = RAIZ / "docs" / "verificacion"
IMAGENES = SALIDA / "img"
_ESTILO = """
body{font:14px/1.4 system-ui,sans-serif;margin:16px;color:#1a1a1a}
h1{font-size:20px}h2{font-size:16px;margin:24px 0 8px}
.par{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:16px;margin:12px 0;
 padding-bottom:12px;border-bottom:1px solid #ccc}
.par>div{min-width:0;overflow-x:auto}
.par img{max-width:100%;border:1px solid #bbb}
pre{white-space:pre-wrap;overflow-wrap:anywhere;margin:0}
table{border-collapse:collapse;width:100%;font-size:13px}
td,th{border:1px solid #bbb;padding:3px 6px;text-align:left;overflow-wrap:break-word;
 word-break:normal}
.n{white-space:nowrap}
th.n{white-space:nowrap}
p{margin:6px 0}
th{background:#eee}.dif{background:#ffe08a}.ok{background:#d9f2d9}.sin{background:#f6d5d5}
.nota{background:#fff6d6;padding:6px 10px;border-left:4px solid #e0a800;margin:8px 0}
@media (max-width:800px){.par{grid-template-columns:1fr}}
"""


def _jpeg(origen: Image.Image, nombre: str) -> str:
    IMAGENES.mkdir(parents=True, exist_ok=True)
    imagen = origen.convert("L")
    imagen.thumbnail((1000, 1400))
    imagen.save(IMAGENES / nombre, quality=70, optimize=True)
    return f"img/{nombre}"


def imagen_ocr(pagina: int) -> str:
    """Página del Acuerdo 1084 tal como la leyó el OCR."""
    ruta = DESCARGAS / "ocr_1084" / f"pagina_{pagina:03d}.png"
    return _jpeg(Image.open(ruta), f"acuerdo_1084_p{pagina:02d}.jpg")


def imagen_pdf(pdf: str, pagina: int, nombre: str) -> str:
    documento = pypdfium2.PdfDocument(DESCARGAS / pdf)
    return _jpeg(documento[pagina - 1].render(scale=1.5).to_pil(), f"{nombre}_p{pagina:02d}.jpg")


def imagen_incrustada(numero: int) -> str:
    """Tabla incrustada como imagen en la página de la Resolución SDH-000195."""
    ruta = DESCARGAS / "img_sdh195" / f"imagen_{numero}.png"
    return _jpeg(Image.open(ruta), f"sdh_000195_tabla{numero}.jpg")


class Html(str):
    """Contenido de una celda que ya es HTML (por ejemplo, un enlace) y no se vuelve a escapar."""


def enlace(etiqueta: str, url: str | None) -> Html:
    if not url:
        return Html(html.escape(etiqueta))
    return Html(f'<a href="{html.escape(url, quote=True)}">{html.escape(etiqueta)}</a>')


_NUMERICA = re.compile(
    r"^([\d$.,\s%+-]+(SMMLV|UVT|smlmv)?|\d{1,2} de \w+ de \d{4}|[\d·\- ]+)$", re.IGNORECASE
)


def formato(valor) -> str:
    """Tarifas con coma decimal (12,3), y miles con punto en las cifras grandes (49.799)."""
    if isinstance(valor, bool) or valor is None:
        return str(valor)
    if isinstance(valor, int):
        return f"{valor:,}".replace(",", ".") if valor >= 10000 else str(valor)
    texto = str(valor)
    return texto.replace(".", ",") if re.fullmatch(r"\d+\.\d{1,2}", texto) else texto


def _celda(valor, etiqueta: str = "td") -> str:
    if isinstance(valor, Html):
        return f"<{etiqueta}>{valor}</{etiqueta}>"
    texto = formato(valor)
    sin_corte = _NUMERICA.match(texto) or (etiqueta == "th" and len(texto) <= 14)
    clase = ' class="n"' if sin_corte else ""
    return f"<{etiqueta}{clase}>{html.escape(texto)}</{etiqueta}>"


def tabla(
    columnas: list[str], filas: list[list], marca: Callable[[list], str] = lambda _: ""
) -> str:
    cabecera = "".join(_celda(c, "th") for c in columnas)
    cuerpo = "".join(
        f'<tr class="{marca(f)}">' + "".join(_celda(c) for c in f) + "</tr>" for f in filas
    )
    return f"<table><tr>{cabecera}</tr>{cuerpo}</table>"


def md_a_html(texto: str) -> str:
    """Párrafos y tablas Markdown de un extracto de la fuente, como párrafos y tablas HTML."""
    partes = []
    for bloque in re.split(r"\n\s*\n", texto.strip()):
        lineas = [linea for linea in bloque.splitlines() if linea.strip()]
        if lineas and all(linea.startswith("|") for linea in lineas):
            filas = [
                [c.strip() for c in linea.strip().strip("|").split("|")]
                for linea in lineas
                if not re.fullmatch(r"\|[-| ]+\|", linea.strip())
            ]
            partes.append(tabla(filas[0], filas[1:]))
        elif lineas:
            parrafo = html.escape(" ".join(linea.strip() for linea in lineas))
            partes.append(
                "<p>" + re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", parrafo) + "</p>"
            )
    return "".join(partes)


def par(imagenes: list[str], derecha: str) -> str:
    izquierda = "".join(f'<img src="{i}" alt="Fuente">' for i in imagenes)
    return f'<div class="par"><div>{izquierda}</div><div>{derecha}</div></div>'


def nota(texto: str) -> str:
    return f'<p class="nota">{html.escape(texto)}</p>'


def pagina(archivo: str, titulo: str, cuerpo: str) -> None:
    SALIDA.mkdir(parents=True, exist_ok=True)
    (SALIDA / archivo).write_text(
        f'<!doctype html><html lang="es"><meta charset="utf-8">'
        f'<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{html.escape(titulo)}</title><style>{_ESTILO}</style>"
        f'<h1>{html.escape(titulo)}</h1><p><a href="index.html">Índice de vistas</a></p>{cuerpo}\n',
        encoding="utf-8",
    )


def _yaml(ruta: str) -> dict:
    return yaml.safe_load((DATOS / ruta).read_text(encoding="utf-8"))


def _valor(v) -> str:
    return (
        "en adelante" if v is None else f"{v:,}".replace(",", ".") if isinstance(v, int) else str(v)
    )


def _diferencias(datos: dict) -> str:
    filas = [[d["pagina"], d["ocr"], d["imagen"], d["se_usa"]] for d in datos["diferencias_ocr"]]
    return tabla(
        ["Página del PDF", "El OCR leyó", "La imagen dice", "Se usa"], filas, lambda _: "dif"
    )


def _contraste_1084(*prefijos: str) -> str:
    """Tabla con el resultado del contraste de los YAML con el texto digital del Acuerdo 1084."""
    resultados = json.loads((SALIDA / "acuerdo_1084_contraste.json").read_text(encoding="utf-8"))
    filas = [
        [r["tabla"], r["filas_en_el_texto"], r["filas_en_el_yaml"], len(r["diferencias"])]
        for r in resultados
        if r["tabla"].startswith(prefijos)
    ]
    return tabla(
        ["Tabla", "Filas en el texto digital", "Filas en el YAML", "Diferencias"],
        filas,
        lambda f: "ok" if f[3] == 0 else "dif",
    )


def _reglas(reglas: list[dict]) -> str:
    return tabla(["Artículo", "Regla"], [[r["articulo"], r["regla"]] for r in reglas])


def vista_sobretasa() -> None:
    d = _yaml("tarifas/sobretasa_alumbrado_2027.yaml")
    tarifas = tabla(
        ["Categoría (texto del art. 14)", "2027 a 2041", "Desde 2042"],
        [[t["descripcion"], t["de_2027_a_2041"], t["desde_2042"]] for t in d["tarifas_por_mil"]],
    )
    topes = tabla(
        ["Categoría (texto del art. 15)", "Límite (UVT)"],
        [[t["descripcion"], t["valor_limite_uvt"]] for t in d["topes_uvt"]],
        lambda f: "dif" if f[1] == 600 else "",
    )
    cuerpo = nota(
        "Art. 14 (tarifas por mil) en la página 19 del PDF y art. 15 (topes) en la página 20. El "
        "texto digital del Régimen Legal coincide con el YAML fila por fila."
    ) + par(
        [imagen_ocr(19), imagen_ocr(20)],
        "<h2>Art. 14, tarifas por mil</h2>"
        + tarifas
        + "<h2>Art. 15, topes</h2>"
        + topes
        + "<h2>Reglas (arts. 11, 13, 14 y 15)</h2>"
        + _reglas(d["reglas"])
        + "<h2>Contraste con el texto digital</h2>"
        + _contraste_1084("sobretasa")
        + "<h2>Diferencias entre el OCR y la imagen</h2>"
        + _diferencias(d),
    )
    pagina("sobretasa_alumbrado_2027.html", "Sobretasa de alumbrado público 2027", cuerpo)


def _categorias_no_residenciales() -> list[str]:
    """Categoría de cada fila de los no residenciales, tal como la escribe el art. 20."""
    texto = (RAIZ / "knowledge_base" / "normativa_ipu" / "acuerdo_1084_2026.md").read_text("utf-8")
    inicio = texto.index("| CATEGORÍA DEL PREDIO | TARIFA X MIL | DESDE | HASTA |")
    filas = []
    for linea in texto[inicio:].splitlines()[2:]:
        if not linea.startswith("|"):
            break
        filas.append(linea.strip("|").split("|")[0].strip())
    return filas


def _limite(fila: dict, campo: str) -> str:
    """Desde o Hasta con su unidad: «135 SMMLV» y no «135» cuando el límite va en salarios."""
    valor = fila[campo]
    if valor is None:
        return "en adelante"
    if fila.get("unidad") == "SMMLV" and not (campo == "desde" and valor == 1):
        previo = "Más de " if campo == "desde" and fila.get("desde_exclusivo") else ""
        return f"{previo}{valor} SMMLV"
    return f"$ {_valor(valor)}"


def vista_ipu_2027() -> None:
    d = _yaml("tarifas/ipu_2027.yaml")
    pref = d["preferenciales"]
    cuerpo = nota(
        "Art. 20 del Acuerdo 1084 en las páginas 21 a 25 del PDF. Las tablas se contrastaron, "
        "fila por fila, con el texto digital del Régimen Legal; el resultado está al final de la "
        "primera sección."
    )
    residencial = tabla(
        ["Desde ($)", "Hasta ($)", "Tarifa por mil"],
        [
            [_valor(f["desde"]), _valor(f["hasta"]), f["tarifa_por_mil"]]
            for f in d["generales"]["residencial"]
        ],
    )
    no_res = tabla(
        ["Categoría del predio (como está en la norma)", "Tarifa por mil", "Desde", "Hasta"],
        [
            [literal, f["tarifa_por_mil"], _limite(f, "desde"), _limite(f, "hasta")]
            for literal, f in zip(
                _categorias_no_residenciales(), d["generales"]["no_residencial"], strict=True
            )
        ],
    )
    preferenciales = tabla(
        ["Estratos", "Desde", "Hasta", "Tarifa por mil"],
        [
            [
                ",".join(map(str, f.get("estratos", ["rural"]))),
                _valor(f["desde"]),
                _valor(f["hasta"]),
                f["tarifa_por_mil"],
            ]
            for f in pref["residencial_urbano_y_rural_agropecuario"] + pref["residencial_rural"]
        ],
    )
    clubes = tabla(
        ["Desde ($)", "Hasta ($)", "2027", "2028 y siguientes"],
        [
            [
                _valor(f["desde"]),
                _valor(f["hasta"]),
                f["tarifa_por_mil_2027"],
                f["tarifa_por_mil_desde_2028"],
            ]
            for f in d["generales"]["dotacional_clubes_de_particulares"]["rangos"]
        ],
    )
    cuerpo += par(
        [imagen_ocr(21), imagen_ocr(22)],
        "<h2>Preferenciales (SMMLV)</h2>"
        + preferenciales
        + f"<p>Excluidos: {html.escape(pref['excluidos'])}</p>"
        + "<h2>Reglas del art. 20</h2>"
        + _reglas(d["reglas"])
        + "<h2>Contraste con el texto digital</h2>"
        + _contraste_1084("predial")
        + "<h2>Diferencias entre el OCR y la imagen</h2>"
        + _diferencias(d),
    )
    cuerpo += par(
        [imagen_ocr(22), imagen_ocr(23)], "<h2>Residenciales (generales)</h2>" + residencial
    )
    cuerpo += par([imagen_ocr(23), imagen_ocr(24)], "<h2>No residenciales</h2>" + no_res)
    cuerpo += par([imagen_ocr(25)], "<h2>Clubes campestres, sociales y deportivos</h2>" + clubes)
    pagina("ipu_2027.html", "Predial 2027, Acuerdo 1084, art. 20", cuerpo)


def vista_ica_2027() -> None:
    d = _yaml("tarifas/ica_2027.yaml")
    lecturas = {
        r["ciiu"]: r
        for r in json.loads((SALIDA / "ica_2027_doble_lectura.json").read_text(encoding="utf-8"))
    }
    por_pagina: dict[int, list[dict]] = {}
    for fila in d["por_actividad"]:
        por_pagina.setdefault(fila["pagina_pdf"], []).append(fila)
    total = len(d["por_actividad"])
    legal = sum(lecturas[f["ciiu"]]["regimen_legal"] == "coincide" for f in d["por_actividad"])
    digital = doble_lectura.progresivas_regimen_legal()
    progresivas = d["progresiva_financiera"]
    legal_prog = sum(
        digital.get(f["ciiu"]) == (f["hasta_2027"], f["en_2028"], f["desde_2029"])
        for f in progresivas
    )
    aplicacion = d["aplicacion"]["periodos_que_cubre"]
    cuerpo = nota(
        f"{total} actividades de tarifa fija y {len(progresivas)} de tarifa progresiva "
        f"({total + len(progresivas)} en total). Segunda lectura: el texto digital del Régimen "
        f"Legal coincide en {legal} de {total} fijas y en {legal_prog} de {len(progresivas)} "
        "progresivas, y no tiene más. Verde: el OCR leyó el código y la tarifa; amarillo: el OCR "
        "leyó otra tarifa (error del OCR, se confirma con la imagen); sin color: el OCR no leyó "
        "la tarifa."
    )
    cuerpo += nota(
        "Periodos que cubre esta tabla. Anuales: "
        + aplicacion["declarantes_anuales"]
        + ". Bimestrales: "
        + aplicacion["declarantes_bimestrales"]
        + "."
    )

    def marca(fila: list) -> str:
        estado = lecturas[fila[0]]["estado"]
        return {"coincide": "ok", "tarifa_distinta": "dif"}.get(estado, "")

    def marca_progresiva(fila: list) -> str:
        return "ok" if digital.get(fila[0]) == tuple(fila[2:]) else "dif"

    for numero in sorted(set(por_pagina) | {45}):
        derecha = f"<h2>Página {numero} del PDF</h2>"
        if numero in por_pagina:
            filas = [[f["ciiu"], f["actividad"], f["tarifa_por_mil"]] for f in por_pagina[numero]]
            derecha += tabla(["CIIU", "Actividad", "Tarifa por mil"], filas, marca)
        if numero == 44:
            derecha += "<h2>Demás actividades</h2>" + tabla(
                ["Clase", "Tarifa por mil"],
                [[f["clase"], f["tarifa_por_mil"]] for f in d["demas_actividades"]],
            )
        progresivas_pagina = [f for f in progresivas if f["pagina_pdf"] == numero]
        if progresivas_pagina:
            derecha += "<h2>Tarifa progresiva (actividades financieras)</h2>" + tabla(
                ["CIIU", "Actividad", "Hasta 2027", "2028", "Desde 2029"],
                [
                    [f["ciiu"], f["actividad"], f["hasta_2027"], f["en_2028"], f["desde_2029"]]
                    for f in progresivas_pagina
                ],
                marca_progresiva,
            )
        cuerpo += par([imagen_ocr(numero)], derecha)
    simple = d["regimen_simple_2027"]
    cuerpo += par(
        [imagen_ocr(simple["pagina_pdf"])],
        "<h2>ICA consolidado del régimen SIMPLE desde 2027 (art. 24)</h2>"
        + nota(simple["lectura"])
        + tabla(
            ["Numeral del art. 908 del ET", "Tarifa por mil"],
            [[t["numeral"], t["tarifa_por_mil"]] for t in simple["tarifas_por_mil"]],
        )
        + "<h2>Contraste con el texto digital</h2>"
        + _contraste_1084("ICA consolidado"),
    )
    pagina("ica_2027.html", "ICA 2027, Acuerdo 1084, arts. 21 y 24", cuerpo)


def _extracto(archivo: str, desde: str, hasta: str | None = None, largo: int = 3000) -> str:
    texto = construir_ica_2026._texto(DESCARGAS / archivo)
    inicio = texto.index(desde)
    fin = texto.index(hasta, inicio) if hasta else inicio + largo
    return md_a_html(texto[inicio:fin])


def _extracto_kb(coleccion: str, archivo: str, numero: int, hasta: str | None = None) -> str:
    """Un artículo de la base de conocimiento (con sus tablas) como HTML."""
    texto = (RAIZ / "knowledge_base" / coleccion / archivo).read_text(encoding="utf-8")
    inicio = texto.index(f"\n## Artículo {numero}\n")
    fin = texto.find("\n## Artículo ", inicio + 1)
    articulo = texto[inicio + len(f"\n## Artículo {numero}\n") : fin if fin != -1 else len(texto)]
    if hasta:
        articulo = articulo[: articulo.index(hasta)]
    return md_a_html(articulo)


def vista_ica_2026() -> None:
    d = _yaml("tarifas/ica_2026.yaml")
    lecturas = {
        r["ciiu"]: r["estado"]
        for r in json.loads((SALIDA / "ica_2026_doble_lectura.json").read_text(encoding="utf-8"))
    }
    filas = d["por_actividad"]
    pendientes = [f for f in filas if f["tarifa_por_mil"] == "pendiente"]
    decididas = [f for f in filas if "decision" in f]
    _, filas_resolucion = construir_ica_2026._filas_resolucion()
    res_2024 = {
        construir_ica_2026.CIIU_CORREGIDO.get(f[1], (f[1],))[0]: construir_ica_2026._tarifa(f[-1])
        for f in filas_resolucion
        if len(f) >= 6 and all(re.fullmatch(r"[\d ,]+", x) for x in f[3:])
    }

    def distinta(f: dict) -> bool:
        return f["tarifa_por_mil"] != "pendiente" and Decimal(f["tarifa_por_mil"]) != Decimal(
            res_2024[f["ciiu"]]
        )

    cambiadas = [f for f in filas if distinta(f)]
    resaltadas = {f["ciiu"] for f in pendientes + decididas + cambiadas}
    por_fuente = d["contraste"]["filas_por_fuente_de_la_tarifa"]
    coinciden = sum(1 for f in filas if lecturas.get(f["ciiu"]) == "coincide")
    cuerpo = nota(
        f"{len(filas)} actividades, {len(pendientes)} pendientes y {len(decididas)} decididas por "
        "Rodolfo. Segunda lectura de la resolución: "
        f"el Registro Distrital 7103 coincide en la tarifa de 2024 de {coinciden} filas. Verde: "
        "coinciden las dos lecturas; amarillo: la tarifa de 2026 es distinta de la columna de 2024 "
        "de la resolución, o la fila quedó pendiente o la decidió Rodolfo; sin color: la segunda "
        "lectura no pudo leer la fila."
    )
    cuerpo += nota(d["criterio_de_la_resolucion_265"])
    cuerpo += nota(d["decision_de_rodolfo"]["decision"] + ".")
    cuerpo += nota(
        "Periodos que cubre esta tabla. Anuales: "
        + d["periodos_que_cubre"]["declarantes_anuales"]
        + ". Bimestrales: "
        + d["periodos_que_cubre"]["declarantes_bimestrales"]
        + "."
    )
    resumen = tabla(["Fuente de la tarifa", "Filas"], [[k, v] for k, v in por_fuente.items()])
    pend = tabla(
        ["CIIU", "Actividad", "Tarifa por mil", "Nota para el agente"],
        [
            [f["ciiu"], f["actividad"], f["tarifa_por_mil"], f["nota_para_el_agente"]]
            for f in decididas
        ],
        lambda _: "dif",
    )
    simple = d["regimen_simple_2026"]
    tabla_simple = tabla(
        ["Numeral del art. 908 del ET", "Tarifa por mil"],
        [[t["numeral"], t["tarifa_por_mil"]] for t in simple["tarifas_por_mil"]],
    )
    derogadas = d["normas_derogadas_por_el_art_52_del_acuerdo_1084"]
    texto_derogadas = "<ul>" + "".join(
        f"<li>{html.escape(x)}</li>" for x in derogadas["fijaban_tarifas_del_ica_y_se_aplican_aqui"]
    )
    texto_derogadas += f"</ul><p>{html.escape(derogadas['rigen_para'])}</p>"
    texto_derogadas += (
        f"<p>No fijan tarifas: {html.escape(derogadas['no_fijan_tarifas_del_ica'])}</p>"
    )
    tabla_filas = tabla(
        [
            "CIIU",
            "Actividad",
            "Grupo",
            "Resolución 265, 2024",
            "Tarifa 2026",
            "Fuente de la tarifa",
        ],
        [
            [
                f["ciiu"],
                f["actividad"],
                f["grupo_resolucion_265"],
                res_2024[f["ciiu"]],
                f["tarifa_por_mil"],
                f.get("fuente_tarifa", ""),
            ]
            for f in filas
        ],
        lambda f: (
            "dif" if f[0] in resaltadas else ("ok" if lecturas.get(f[0]) == "coincide" else "")
        ),
    )
    demas = (
        tabla(
            ["Clase", "Tarifa por mil"],
            [[f["clase"], f["tarifa_por_mil"]] for f in d["demas_actividades"]],
        )
        + f"<p>{html.escape(d['demas_actividades_fuente'])}</p>"
    )
    izquierda = (
        "<h2>Art. 3 del Acuerdo 65, texto original</h2>"
        + _extracto("acuerdo_65_2002.html", "El texto original del artículo era el", "\nArtículo 4")
        + "<h2>Acuerdo 780 de 2020, arts. 6 y 7</h2>"
        + _extracto("acuerdo_780_2020.html", "ARTÍCULO 6", "ARTÍCULO 8")
        + "<h2>Acuerdo 816 de 2021, art. 4</h2>"
        + _extracto("acuerdo_816_2021.html", "ARTÍCULO 4", "ARTÍCULO 5")
        + "<h2>Acuerdo 98 de 2003, art. 1</h2>"
        + _extracto("acuerdo_98_2003.html", "Artículo 1.", "Artículo 2.", 2600)
    )
    cuerpo += (
        f'<div class="par"><div>{izquierda}</div><div><h2>Fuente de cada tarifa</h2>{resumen}'
        f"<h2>Filas que decidió Rodolfo</h2>{pend}"
        f"<h2>Demás actividades</h2>{demas}"
        "<h2>Normas derogadas por el art. 52 del Acuerdo 1084</h2>"
        f"{texto_derogadas}<h2>ICA consolidado del régimen SIMPLE en 2026</h2>{tabla_simple}"
        "</div></div>"
    )
    cuerpo += f"<h2>Las {len(filas)} actividades</h2>{tabla_filas}"
    pagina("ica_2026.html", "ICA 2026, texto vigente del art. 3 del Acuerdo 65", cuerpo)


def vista_ipu_2026() -> None:
    d = _yaml("tarifas/ipu_2026.yaml")
    contraste = json.loads((SALIDA / "ipu_2026_contraste.json").read_text(encoding="utf-8"))
    residencial = tabla(
        ["Desde ($)", "Hasta ($)", "Tarifa por mil"],
        [
            [_valor(f["desde"]), _valor(f["hasta"]), f["tarifa_por_mil"]]
            for f in d["residencial_urbano"]
        ],
        lambda _: "ok" if not contraste["diferencias"] else "dif",
    )
    no_res = tabla(
        ["Destino", "Desde", "Hasta", "Tarifa por mil"],
        [
            [f["destino"], _valor(f["desde"]), _valor(f["hasta"]), f["tarifa_por_mil"]]
            for f in d["no_residencial"]
        ],
    )
    clubes = tabla(
        ["Desde ($)", "Hasta ($)", "Tarifa por mil"],
        [
            [_valor(f["desde"]), _valor(f["hasta"]), f["tarifa_por_mil"]]
            for f in d["clubes_destino_66"]
        ],
        lambda _: "ok" if not contraste["diferencias"] else "dif",
    )
    pdf = "resolucion_000194_2025_rangos.pdf"
    paginas = [
        imagen_pdf(pdf, n, "resolucion_000194") for n in contrastar_rangos.paginas_con_tablas()
    ]
    filas_pdf = contraste["filas_en_el_pdf"]
    cuerpo = nota(
        "Contraste automático con el texto del PDF, fila por fila: "
        f"{len(contraste['diferencias'])} diferencias en {filas_pdf['art_1']} rangos del art. 1, "
        f"{filas_pdf['art_2']} del art. 2 y "
        f"{filas_pdf['art_3']} del art. 3. La resolución del PDF lleva el número SDH-000194 de "
        "2025. Se muestran las páginas del PDF que traen las tablas."
    )
    cuerpo += nota(d["otras_categorias_no_transcritas"])
    pref = d["preferenciales"]
    tabla_pref = tabla(
        [
            "Estratos",
            "Desde (texto)",
            "Hasta (texto)",
            "Tarifa por mil",
            "Desde (número)",
            "Hasta (número)",
        ],
        [
            [
                ",".join(map(str, f["estratos"])),
                f["desde"],
                f["hasta"],
                f["tarifa_por_mil"],
                f"{f['desde_valor']} {f['unidad_desde']}"
                + (" (exclusivo)" if f["desde_exclusivo"] else ""),
                f"{f['hasta_valor']} {f['unidad_hasta']}",
            ]
            for f in pref["residencial"]
        ],
    )
    pesos = tabla(
        ["Límite", "En pesos de 2026"],
        [[k.replace("_smmlv", " SMMLV"), v] for k, v in pref["limites_en_pesos"].items()],
    )
    texto_normas = (
        "<h2>Acuerdo 648 de 2016, art. 1</h2>"
        + _extracto_kb("normativa_ipu", "acuerdo_648_2016.md", 1, "Los demás predios")
        + "<h2>Acuerdo 780 de 2020, art. 3, parágrafo 2</h2>"
        + "<p>Se mantienen las tarifas preferenciales del 1 y 3 por mil, del Acuerdo 648 de 2016, "
        "para los predios residenciales de los estratos 1, 2 y 3 según los valores de los avalúos "
        "catastrales allí señalados.</p>"
        + "<h2>Decreto 639 de 2025, art. 207</h2>"
        + _extracto_kb("normativa_ipu", "decreto_639_2025.md", 207)
    )
    cuerpo += (
        '<h2 id="preferenciales">Tarifas preferenciales de 2026</h2>'
        f'<div class="par"><div>{texto_normas}</div><div>{tabla_pref}'
        f"<p>SMMLV de 2026: {formato(pref['smmlv_del_anio_gravable']['valor'])}.</p>{pesos}"
        f"<p>{html.escape(pref['limite_de_16_smmlv'])}</p>"
        f"<p>{html.escape(pref['excluidos'])}</p></div></div>"
    )
    cuerpo += par(
        paginas,
        "<h2>Art. 1, residenciales urbanos</h2>"
        + residencial
        + "<h2>Art. 2, no residenciales</h2>"
        + no_res
        + "<h2>Art. 3, clubes (destino 66)</h2>"
        + clubes,
    )
    pagina("ipu_2026.html", "Predial 2026, resolución de rangos", cuerpo)


def vista_calendario() -> None:
    d = _yaml("calendario/2026.yaml")
    filas = [
        [
            p["concepto"],
            Html("<br>".join(f'<span class="n">{html.escape(str(f))}</span>' for f in p["fechas"])),
            p["articulo"] or "—",
        ]
        for p in d["plazos"]
    ]
    cuerpo = nota(
        "Las tablas de fechas del ICA bimestral y de las cuotas del SPAC están como imagen en la "
        "página del Régimen Legal; se leyeron de la imagen. Las demás fechas salen del texto."
    )
    insertadas = ""
    for titulo, archivo in (
        ("Art. 1: ICA bimestral y agentes de retención", "sdh_195_art_1.md"),
        ("Art. 5: cuotas del SPAC", "sdh_195_art_5.md"),
    ):
        contenido = (RAIZ / "scripts" / "curaduria" / "inserciones" / archivo).read_text(
            encoding="utf-8"
        )
        insertadas += f"<h2>Tabla insertada en la base de conocimiento, {titulo}</h2>"
        insertadas += md_a_html(contenido)
    cuerpo += par(
        [imagen_incrustada(1), imagen_incrustada(2), imagen_incrustada(4)],
        tabla(["Concepto", "Fechas", "Artículo"], filas)
        + nota(
            "A la izquierda están las imágenes de la página: la tabla del art. 1 sigue en la "
            "segunda imagen (bimestres 4 a 6 de la retención). A la derecha, las tablas que se "
            "insertaron en la base de conocimiento, para compararlas con las imágenes."
        )
        + insertadas,
    )
    textos = "".join(
        f"<h2>Art. {n}{' (ICA anual)' if c == 'normativa_ica' else ''}</h2>" + _extracto_kb(c, a, n)
        for c, a, n in (
            ("normativa_ica", "resolucion_sdh_000195_2025_ica.md", 1),
            ("normativa_ipu", "resolucion_sdh_000195_2025.md", 3),
            ("normativa_ipu", "resolucion_sdh_000195_2025.md", 4),
            ("normativa_ipu", "resolucion_sdh_000195_2025.md", 5),
            ("normativa_ipu", "resolucion_sdh_000195_2025.md", 6),
        )
    )
    cuerpo += (
        "<h2>Texto de los artículos de donde salen las fechas</h2>"
        + nota(
            "Las fechas que no están en imagen salen de estos textos (arts. 1, 3, 4, 5 y 6 de la "
            "Resolución SDH-000195 de 2025), tal como están en la base de conocimiento."
        )
        + f'<div class="texto">{textos}</div>'
    )
    pagina("calendario_2026.html", "Calendario 2026, Resolución SDH-000195", cuerpo)


def vista_regimenes() -> None:
    r = _yaml("regimenes_ica.yaml")
    u = _yaml("uvt_smmlv.yaml")
    filas = [
        [a["anio_gravable"], a["fuente"], a["umbral_uvt"], a["base_del_umbral"]] for a in r["anios"]
    ]

    def fuente(x: dict) -> Html:
        etiqueta = x["fuente"].replace("Resolución DIAN", "Res. DIAN")
        return enlace(etiqueta, x.get("url"))

    uvt = tabla(
        ["Año", "UVT", "Resolución de la DIAN", "SMMLV", "Decreto del salario mínimo"],
        [
            [
                x["anio"],
                x["valor"],
                fuente(x),
                s["valor"],
                fuente(s),
            ]
            for x in u["uvt"]
            for s in u["smmlv"]
            if s["anio"] == x["anio"]
        ],
        lambda f: "sin" if "pendiente" in str(f[1]) or "pendiente" in str(f[3]) else "",
    )
    bomberil = [
        [a["anio_gravable"], a["sobretasa_bomberil"]["umbral_uvt"], a["sobretasa_bomberil"]["base"],
         a["sobretasa_bomberil"]["fuente"]]
        for a in r["anios"]
        if a.get("sobretasa_bomberil")
    ]  # fmt: skip
    cuerpo = nota(
        "Regímenes del ICA: art. 1 de la Resolución SDH-000195 (2026) y art. 26 del Acuerdo 1084 "
        "(desde 2027, página 48 del PDF). Umbral de la sobretasa bomberil: art. 2 de la misma "
        "resolución (2026). UVT y SMMLV salen de las resoluciones de la DIAN y de "
        "los decretos del salario mínimo; los de 2027 aún no existen. "
        "El SIMPLE de 2026 (12, 16, 30, 30 y 16 por mil) se verificó con el texto del art. 44 del "
        "Acuerdo 1019 de 2025 en el Régimen Legal."
    )
    cuerpo += par(
        [imagen_ocr(48)],
        "<h2>Regímenes</h2>"
        + tabla(["Año gravable", "Fuente", "Umbral (UVT)", "Base del umbral"], filas)
        + "<h2>Sobretasa bomberil</h2>"
        + tabla(["Año gravable", "Umbral (UVT)", "Base", "Fuente"], bomberil)
        + "<h2>UVT y SMMLV</h2>"
        + uvt,
    )
    pagina("regimenes_y_uvt.html", "Regímenes del ICA, UVT y SMMLV", cuerpo)


def indice() -> None:
    enlaces = [
        ("ipu_2026.html", "Predial 2026"),
        ("ipu_2027.html", "Predial 2027"),
        ("sobretasa_alumbrado_2027.html", "Sobretasa de alumbrado 2027"),
        ("ica_2026.html", "ICA 2026"),
        ("ica_2027.html", "ICA 2027"),
        ("calendario_2026.html", "Calendario 2026"),
        ("regimenes_y_uvt.html", "Regímenes del ICA, UVT y SMMLV"),
    ]
    lista = "".join(f'<li><a href="{a}">{t}</a></li>' for a, t in enlaces)
    pagina("index.html", "Vistas de verificación", f"<ul>{lista}</ul>")


def main() -> None:
    vista_ipu_2026()
    vista_ipu_2027()
    vista_sobretasa()
    vista_ica_2026()
    vista_ica_2027()
    vista_calendario()
    vista_regimenes()
    indice()
    print("vistas escritas en", SALIDA)


if __name__ == "__main__":
    main()
