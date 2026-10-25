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
from collections.abc import Callable

import construir_ica_2026
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
.par img{max-width:100%;border:1px solid #bbb}
table{border-collapse:collapse;width:100%;font-size:13px}
td,th{border:1px solid #bbb;padding:3px 6px;text-align:left}
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


def tabla(
    columnas: list[str], filas: list[list], marca: Callable[[list], str] = lambda _: ""
) -> str:
    cabecera = "".join(f"<th>{html.escape(c)}</th>" for c in columnas)
    cuerpo = "".join(
        f'<tr class="{marca(f)}">' + "".join(f"<td>{html.escape(str(c))}</td>" for c in f) + "</tr>"
        for f in filas
    )
    return f"<table><tr>{cabecera}</tr>{cuerpo}</table>"


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


def vista_sobretasa() -> None:
    d = _yaml("tarifas/sobretasa_alumbrado_2027.yaml")
    tarifas = tabla(
        ["Categoría", "2027 a 2041", "Desde 2042"],
        [[t["categoria"], t["de_2027_a_2041"], t["desde_2042"]] for t in d["tarifas_por_mil"]],
    )
    topes = tabla(
        ["Categoría", "Límite (UVT)"],
        [[t["categoria"], t["valor_limite_uvt"]] for t in d["topes_uvt"]],
        lambda f: "dif" if f[1] == 600 else "",
    )
    cuerpo = nota(
        "Art. 14 (tarifas por mil) en la página 19 del PDF y art. 15 (topes) en la página 20."
    ) + par(
        [imagen_ocr(19), imagen_ocr(20)],
        "<h2>Art. 14, tarifas por mil</h2>"
        + tarifas
        + "<h2>Art. 15, topes</h2>"
        + topes
        + "<h2>Diferencias entre el OCR y la imagen</h2>"
        + _diferencias(d),
    )
    pagina("sobretasa_alumbrado_2027.html", "Sobretasa de alumbrado público 2027", cuerpo)


def vista_ipu_2027() -> None:
    d = _yaml("tarifas/ipu_2027.yaml")
    pref = d["preferenciales"]
    cuerpo = nota(
        "Art. 20 del Acuerdo 1084 en las páginas 21 a 25 del PDF. El texto digital del "
        "Régimen Legal "
        "(Acuerdo 105 de 2003, art. 2) coincide con las categorías no residenciales, las "
        "preferenciales y los clubes."
    )
    residencial = tabla(
        ["Desde ($)", "Hasta ($)", "Tarifa por mil"],
        [
            [_valor(f["desde"]), _valor(f["hasta"]), f["tarifa_por_mil"]]
            for f in d["generales"]["residencial"]
        ],
    )
    no_res = tabla(
        ["Destino", "Tarifa por mil", "Desde", "Hasta"],
        [
            [f["destino"], f["tarifa_por_mil"], _valor(f["desde"]), _valor(f["hasta"])]
            for f in d["generales"]["no_residencial"]
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
    pagina("ica_2027.html", "ICA 2027, Acuerdo 1084, art. 21", cuerpo)


def _extracto(archivo: str, desde: str, hasta: str | None = None, largo: int = 3000) -> str:
    texto = construir_ica_2026._texto(DESCARGAS / archivo)
    inicio = texto.index(desde)
    fin = texto.index(hasta, inicio) if hasta else inicio + largo
    lineas = texto[inicio:fin].strip().replace("\r", "").splitlines()
    return f"<pre>{html.escape(chr(10).join(linea.rstrip() for linea in lineas))}</pre>"


def vista_ica_2026() -> None:
    d = _yaml("tarifas/ica_2026.yaml")
    lecturas = {
        r["ciiu"]: r["estado"]
        for r in json.loads((SALIDA / "ica_2026_doble_lectura.json").read_text(encoding="utf-8"))
    }
    filas = d["por_actividad"]
    pendientes = [f for f in filas if f["tarifa_por_mil"] == "pendiente"]
    decididas = [f for f in filas if "decision" in f]
    resaltadas = {f["ciiu"] for f in pendientes + decididas}
    por_fuente = d["contraste"]["filas_por_fuente_de_la_tarifa"]
    coinciden = sum(1 for f in filas if lecturas.get(f["ciiu"]) == "coincide")
    cuerpo = nota(
        f"{len(filas)} actividades, {len(pendientes)} pendientes y {len(decididas)} decididas por "
        "Rodolfo. Segunda lectura de la resolución: "
        f"el Registro Distrital 7103 coincide en la tarifa de 2024 de {coinciden} filas. Verde: "
        "coinciden las dos lecturas; amarillo: fila pendiente o decidida por Rodolfo; sin color: "
        "la segunda lectura no pudo leer la fila."
    )
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
    texto_derogadas += f"</ul><p>{html.escape(derogadas['rigen_desde_y_hasta'])}</p>"
    texto_derogadas += (
        f"<p>No fijan tarifas: {html.escape(derogadas['no_fijan_tarifas_del_ica'])}</p>"
    )
    tabla_filas = tabla(
        ["CIIU", "Actividad", "Grupo", "Tarifa por mil", "Fuente de la tarifa"],
        [
            [
                f["ciiu"],
                f["actividad"],
                f["grupo_resolucion_265"],
                f["tarifa_por_mil"],
                f.get("fuente_tarifa", ""),
            ]
            for f in filas
        ],
        lambda f: (
            "dif" if f[0] in resaltadas else ("ok" if lecturas.get(f[0]) == "coincide" else "")
        ),
    )
    izquierda = (
        "<h2>Art. 3 del Acuerdo 65, texto original</h2>"
        + _extracto("acuerdo_65_2002.html", "El texto original del artículo era el", None, 3300)
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
    pdf = "resolucion_000194_2025_rangos.pdf"
    paginas = [imagen_pdf(pdf, n, "resolucion_000194") for n in (1, 2)]
    cuerpo = nota(
        f"Contraste automático con el texto del PDF: {len(contraste['diferencias'])} diferencias "
        f"en {contraste['rangos_en_el_pdf']} rangos. La resolución del PDF lleva el número "
        "SDH-000194 "
        "de 2025."
    )
    cuerpo += par(
        paginas,
        "<h2>Residenciales urbanos</h2>" + residencial + "<h2>No residenciales</h2>" + no_res,
    )
    pagina("ipu_2026.html", "Predial 2026, resolución de rangos", cuerpo)


def vista_calendario() -> None:
    d = _yaml("calendario/2026.yaml")
    filas = [[p["concepto"], " · ".join(p["fechas"]), p["articulo"] or "—"] for p in d["plazos"]]
    cuerpo = nota(
        "Las tablas de fechas del ICA bimestral y de las cuotas del SPAC están como imagen en la "
        "página del Régimen Legal; se leyeron de la imagen. Las demás fechas salen del texto."
    )
    cuerpo += par(
        [imagen_incrustada(1), imagen_incrustada(4)],
        tabla(["Concepto", "Fechas", "Artículo"], filas),
    )
    pagina("calendario_2026.html", "Calendario 2026, Resolución SDH-000195", cuerpo)


def vista_regimenes() -> None:
    r = _yaml("regimenes_ica.yaml")
    u = _yaml("uvt_smmlv.yaml")
    filas = [
        [a["anio_gravable"], a["fuente"], a["umbral_uvt"], a["base_del_umbral"]] for a in r["anios"]
    ]
    uvt = tabla(
        ["Año", "UVT", "SMMLV", "Fuente"],
        [
            [
                x["anio"],
                x["valor"],
                next(s["valor"] for s in u["smmlv"] if s["anio"] == x["anio"]),
                x["fuente"],
            ]
            for x in u["uvt"]
        ],
        lambda f: "sin" if "pendiente" in str(f[1]) or "pendiente" in str(f[2]) else "",
    )
    cuerpo = nota(
        "Regímenes del ICA: art. 1 de la Resolución SDH-000195 (2026) y art. 26 del Acuerdo 1084 "
        "(desde 2027, página 48 del PDF). UVT y SMMLV salen de fuentes secundarias y hay que "
        "contrastarlos con la DIAN y el decreto."
    )
    cuerpo += par(
        [imagen_ocr(48)],
        "<h2>Regímenes</h2>"
        + tabla(["Año gravable", "Fuente", "Umbral (UVT)", "Base del umbral"], filas)
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
