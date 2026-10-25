"""Arma `datos/tarifas/ica_2026.yaml`: las tarifas del ICA vigentes en 2026.

El art. 3 del Acuerdo 65 de 2002 vigente en 2026 se arma con estas fuentes, en este orden:
1. la Resolución SDH-000265 de 2021, art. 1, que da a cada CIIU su grupo y sus tarifas de 2021 a
   2024 (se usa la columna de 2024);
2. el Acuerdo 816 de 2021, art. 4: 14 por mil para las actividades financieras;
3. el Acuerdo 780 de 2020, art. 7: tarifa de los domicilios por plataformas;
4. el Acuerdo 98 de 2003: tarifa condicionada de la edición y publicación de libros.
Cada tarifa se contrasta con el texto de los acuerdos: la tarifa de grupo, con el texto original
del art. 3 del Acuerdo 65; las que cambian, con el art. 6 del Acuerdo 780. Lo que no se puede
verificar queda `pendiente` en su fila, con el valor de la resolución como referencia.
Uso: uv run python scripts/curaduria/construir_ica_2026.py
"""

import re
from collections import Counter
from decimal import Decimal

import yaml
from bs4 import BeautifulSoup
from comun import DESCARGAS, RAIZ

SALIDA = RAIZ / "datos" / "tarifas" / "ica_2026.yaml"

# Categorías que el art. 6 del Acuerdo 780 cambia desde 2022 (columna «2024 y siguientes»): tarifa,
# nombre y palabras que la identifican en la descripción del CIIU de la resolución.
CATEGORIAS_780 = [
    ("12.14", "fabricación de productos farmacéuticos", ["farmacéuticos, sustancias químicas"]),
    ("8.66", "consultoría profesional", ["consultoría profesional"]),
    ("7.66", "consultoría en el ejercicio de una profesión liberal", ["profesión liberal"]),
    (
        "7.6",
        "carreteras, proyectos de servicio público y otras obras de ingeniería civil",
        [
            "construcción de carreteras",
            "proyectos de servicio público",
            "obras de ingeniería civil",
        ],
    ),
    (
        "10.62",
        "telecomunicaciones alámbricas e inalámbricas",
        ["telecomunicaciones alámbricas", "telecomunicaciones inalámbricas"],
    ),
]
FRASES_780 = {
    "12.14": "productos farmacéuticos",
    "8.66": "Consultoría profesional",
    "7.66": "profesión liberal",
    "7.6": "Construcción de carreteras",
    "10.62": "telecomunicaciones alámbricas",
}
# La resolución deja en 6,9 a quienes el art. 6 del Acuerdo 780 sube a 8,66 («servicios prestados
# por contratistas de construcción, constructores y urbanizadores») y da 7,6 a dos CIIU que ese
# artículo no nombra. Esas filas quedan pendientes hasta que Rodolfo decida qué prevalece.
CONTRATISTAS = {"4111", "4112", "4311", "4312", "4321", "4322", "4329", "39002"}
SIN_APOYO_780 = {"4330", "4390"}
MOTIVO_CONTRATISTAS = (
    "el art. 6 del Acuerdo 780 sube a 8,66 a los contratistas de construcción, constructores y "
    "urbanizadores, y la resolución deja 6,9"
)
MOTIVO_SIN_APOYO = (
    "la resolución da 7,6, pero el art. 6 del Acuerdo 780 solo nombra carreteras, proyectos de "
    "servicio público y otras obras de ingeniería civil"
)
FUENTE_ORIGINAL = (
    "Acuerdo 65 de 2002, art. 3, texto original (tarifa del grupo, columna de 2003 y siguientes)"
)
FUENTE_816 = (
    "Acuerdo 816 de 2021, art. 4 (la resolución trae 13,1 de 2024, del Acuerdo 780, art. 6)"
)
FUENTE_780_7 = "Acuerdo 780 de 2020, art. 7 (2022: 10,14; 2023: 10,63; 2024 y siguientes: 11,04)"
HASTA_1084 = "la publicación del Acuerdo 1084 de 2026 (su art. 52 lo deroga)"


def _texto(ruta) -> str:
    texto = BeautifulSoup(ruta.read_bytes(), "html.parser").get_text("\n").replace("\xa0", " ")
    texto = re.sub(r"(Art[íi]culo)\s*\n+\s*(?=\d)", r"\1 ", texto, flags=re.IGNORECASE)
    texto = re.sub(r"[ \t]+", " ", texto)
    return re.sub(r"\n\s*\n+", "\n", texto)


def _decimales(texto: str) -> set[Decimal]:
    numeros = re.findall(r"(?<![\d.,])\d{1,2}(?:,\d{1,2})?(?![\d.,])", texto)
    return {Decimal(n.replace(",", ".")).normalize() for n in numeros}


def _tarifa(texto: str) -> str:
    """'11,04' o '1 1,04' pasa a '11.04' (la resolución parte algunas cifras con espacios)."""
    limpio = re.sub(r"\s+", "", texto).lstrip(",")  # una celda trae «,9,66»
    return str(Decimal(limpio.replace(",", ".")).normalize())


def _filas_resolucion() -> tuple[dict[str, str], list[list[str]]]:
    ruta = DESCARGAS / "resolucion_sdh_000265_2021.html"
    sopa = BeautifulSoup(ruta.read_bytes(), "html.parser")
    tablas = [t for t in sopa.find_all("table") if t.find_all("tr")]

    def celdas(fila) -> list[str]:
        return [
            re.sub(r"\s+", " ", c.get_text(" ", strip=True)) for c in fila.find_all(["td", "th"])
        ]

    grupos: dict[str, str] = {}
    for fila in tablas[0].find_all("tr")[1:]:
        c = celdas(fila)
        if len(c) >= 2:
            grupos[c[-2]] = c[-1].rstrip("*")
    return grupos, [celdas(f) for f in tablas[1].find_all("tr")[1:]]


def _verificar_textos() -> dict:
    """Comprueba en los textos de los acuerdos las cifras que usan las reglas."""
    original = _texto(DESCARGAS / "acuerdo_65_2002.html")
    original = original[original.index("El texto original del artículo era el") :]
    original = original[: re.search(r"\nArt[íi]culo 4\b", original).start()]
    en_780 = _texto(DESCARGAS / "acuerdo_780_2020.html")
    art_6 = en_780[en_780.index("ARTÍCULO 6") : en_780.index("ARTÍCULO 7")]
    art_7 = en_780[en_780.index("ARTÍCULO 7") : en_780.index("ARTÍCULO 8")]
    en_816 = _texto(DESCARGAS / "acuerdo_816_2021.html")
    art_4 = en_816[en_816.index("ARTÍCULO 4") : en_816.index("ARTÍCULO 5")]
    en_98 = _texto(DESCARGAS / "acuerdo_98_2003.html")
    return {
        "original": _decimales(original),
        "frases_780": {t: f in art_6 for t, f in FRASES_780.items()},
        "art7_780": "11.04" in art_7,
        "financiero_816": bool(re.search(r"d\. Actividades financieras\s+14\b", art_4)),
        "libros_98": "4,14 por mil" in en_98 and "8 por mil" in en_98,
    }


def _fila(ciiu: str, descripcion: str, grupo: str, t2024: str, contexto: dict) -> dict:
    """Arma la fila de un CIIU: elige la regla que fija su tarifa y la verifica en los textos."""
    grupos, texto, por_codigo = contexto["grupos"], contexto["texto"], contexto["por_codigo"]
    nota, por_tarifa = None, False
    if grupo not in grupos:  # la fuente digital deja incompleto el código de grupo de algunas filas
        candidatos = [g for g in grupos if g.endswith(grupo) and _tarifa(grupos[g]) == t2024]
        if candidatos and Decimal(t2024).normalize() in texto["original"]:
            nota = (
                f"el código de grupo viene como «{grupo}» en la fuente; "
                f"la tarifa coincide con la de {', '.join(candidatos)}"
            )
            por_tarifa = True
            if len(candidatos) == 1:
                grupo = candidatos[0]
    base = _tarifa(grupos[grupo]) if grupo in grupos else None
    base_en_texto = base is not None and Decimal(base).normalize() in texto["original"]
    registro = {"ciiu": ciiu, "actividad": descripcion, "grupo_resolucion_265": grupo}
    if nota:
        registro["nota"] = nota
    minuscula = descripcion.lower()
    if ciiu in CONTRATISTAS | SIN_APOYO_780:
        registro |= {
            "tarifa_por_mil": "pendiente",
            "tarifa_resolucion_265": t2024,
            "motivo": MOTIVO_CONTRATISTAS if ciiu in CONTRATISTAS else MOTIVO_SIN_APOYO,
        }
    elif ciiu == "5330":
        ok = texto["art7_780"] and t2024 == "11.04"
        registro |= {
            "tarifa_por_mil": "11.04" if ok else "pendiente",
            "fuente_tarifa": FUENTE_780_7,
            "rige_hasta": HASTA_1084,
        }
    elif grupo == "401":
        registro |= {
            "tarifa_por_mil": "14" if texto["financiero_816"] else "pendiente",
            "fuente_tarifa": FUENTE_816,
        }
    elif por_tarifa or (t2024 == base and base_en_texto):
        registro |= {"tarifa_por_mil": t2024, "fuente_tarifa": FUENTE_ORIGINAL}
    else:
        categoria = next(
            (c for c in CATEGORIAS_780 if c[0] == t2024 and any(p in minuscula for p in c[2])),
            None,
        )
        hermana = por_codigo.get(ciiu[:-1] + "2")
        if (
            categoria is None
            and t2024 == "8.66"
            and hermana
            and "profesión liberal" in hermana[2].lower()
            and _tarifa(hermana[-1]) == "7.66"
        ):  # la resolución parte cada actividad profesional en X1 (consultoría) y X2 (liberal)
            categoria = CATEGORIAS_780[1]
        if categoria:
            registro |= {
                "tarifa_por_mil": t2024,
                "fuente_tarifa": (
                    f"Acuerdo 780 de 2020, art. 6, columna «2024 y siguientes» ({categoria[1]})"
                ),
            }
        else:
            registro |= {
                "tarifa_por_mil": "pendiente",
                "tarifa_resolucion_265": t2024,
                "motivo": (
                    "la tarifa de 2024 de la resolución no coincide con la de su grupo ni con una "
                    "categoría del art. 6 del Acuerdo 780"
                ),
            }
    if ciiu == "58112":
        registro["tarifa_condicionada"] = {
            "tarifa_por_mil": "4.14",
            "condicion": (
                "donar tres ejemplares de cada nueva publicación y dar a la Secretaría de "
                "Educación los descuentos del parágrafo primero"
            ),
            "fuente": "Acuerdo 98 de 2003, art. 1 y parágrafos (si no se cumple, 8 por mil)",
            "rige_hasta": HASTA_1084,
        }
    return registro


def construir() -> dict:
    grupos, filas = _filas_resolucion()
    texto = _verificar_textos()
    assert texto["financiero_816"] and texto["art7_780"] and texto["libros_98"], texto
    assert all(texto["frases_780"].values()), texto["frases_780"]
    # los encabezados que se repiten en los cortes de página no traen tarifas numéricas
    datos = [f for f in filas if len(f) >= 6 and all(re.fullmatch(r"[\d ,]+", x) for x in f[3:])]
    contexto = {"grupos": grupos, "texto": texto, "por_codigo": {f[1]: f for f in datos}}
    resultado = [_fila(f[1], f[2], f[0], _tarifa(f[-1]), contexto) for f in datos]
    return {"filas": resultado, "grupos": grupos, "texto": texto}


def _encabezado(datos: dict) -> dict:
    texto = datos["texto"]
    por_fuente = Counter(
        f["fuente_tarifa"].split(" (")[0].split(", texto")[0].split(", columna")[0]
        if "fuente_tarifa" in f
        else "pendiente"
        for f in datos["filas"]
    )
    tarifas_de_grupo = {
        g: Decimal(_tarifa(t)).normalize() in texto["original"] for g, t in datos["grupos"].items()
    }
    return {
        "fuente": (
            "Acuerdo 65 de 2002, art. 3, en su texto vigente en 2026: el original, modificado por "
            "el art. 6 del Acuerdo 780 de 2020 y el art. 4 del Acuerdo 816 de 2021"
        ),
        "url": "https://www.alcaldiabogota.gov.co/sisjur/normas/Norma1.jsp?i=5156",
        "mes_consulta": "octubre de 2026",
        "vigencia_desde": 2026,
        "vigencia_hasta": 2026,
        "verificado_por": "",
        "estado": "parcial",
        "nota_de_estado": (
            "Las filas pendientes no se completan con valores supuestos; cada una trae el valor de "
            "la resolución como referencia y el motivo."
        ),
        "periodos_que_cubre": {
            "declarantes_anuales": "año gravable 2026 (se declara en febrero de 2027)",
            "declarantes_bimestrales": (
                "bimestres 1 a 5 de 2026 (enero-octubre); desde el bimestre 6 de 2026 aplica "
                "ica_2027.yaml, porque el Acuerdo 1084 se aprobó en plenaria el 28 de septiembre "
                "de 2026 y se firmó el 8 de octubre de 2026, ambas fechas dentro del bimestre 5"
            ),
            "tarifas_de_2024_y_siguientes": (
                "las de la columna de 2024 de la resolución rigen desde el año gravable 2024"
            ),
        },
        "fuentes": [
            "Acuerdo 65 de 2002, art. 3, texto original (Régimen Legal de Bogotá, i=5156)",
            "Acuerdo 780 de 2020, arts. 6 y 7 (Régimen Legal, i=100965)",
            "Acuerdo 816 de 2021, art. 4 (Régimen Legal, i=116160)",
            "Resolución SDH-000265 de 2021, art. 1 (compilación de la Secretaría de Hacienda; "
            "el PDF de bogota.gov.co trae el mismo texto)",
            "Acuerdo 98 de 2003 (Régimen Legal, i=10597)",
            "Acuerdo 1019 de 2025, art. 44 (Régimen Legal, i=191818)",
        ],
        "contraste": {
            "pagina_de_hacienda": (
                "La página del ICA de la Secretaría de Hacienda dice que las tarifas vigentes son "
                "las del art. 3 modificado por el art. 6 del Acuerdo 780 de 2020 y el art. 4 del "
                "Acuerdo 816 de 2021, con 14 por mil para las actividades financieras. La página "
                "no se descarga como texto, así que cada tarifa se contrastó con los acuerdos."
            ),
            "filas_por_fuente_de_la_tarifa": dict(por_fuente),
            "tarifas_de_grupo_que_aparecen_en_el_texto_original": tarifas_de_grupo,
            "cifras_del_art_6_del_acuerdo_780_en_el_texto": texto["frases_780"],
            "art_7_del_acuerdo_780_11_04_en_el_texto": texto["art7_780"],
            "art_4_del_acuerdo_816_14_en_el_texto": texto["financiero_816"],
            "acuerdo_98_4_14_y_8_en_el_texto": texto["libros_98"],
            "resolucion_265_modificada": (
                "Sin nota de modificación en la compilación de la Secretaría de Hacienda ni "
                "resolución posterior en el Régimen Legal o en la búsqueda web."
            ),
        },
        "normas_derogadas_por_el_art_52_del_acuerdo_1084": {
            "fijaban_tarifas_del_ica_y_se_aplican_aqui": [
                "Acuerdo 98 de 2003 (edición y publicación de libros: 4,14 por mil, u 8 si no se "
                "cumplen las condiciones); fila 58112",
                "Acuerdo 780 de 2020, art. 7 (domicilios por plataformas: 11,04 por mil desde "
                "2024); fila 5330",
                "Acuerdo 1019 de 2025, art. 44 (ICA consolidado del régimen SIMPLE en 2026); "
                "sección regimen_simple_2026",
            ],
            "rigen_desde_y_hasta": (
                "Cada una rige hasta la publicación del Acuerdo 1084 (art. 52); la tarifa del "
                "art. 21 de ese acuerdo la reemplaza desde el bimestre 6 de 2026 y, en los "
                "anuales, desde 2027"
            ),
            "no_fijan_tarifas_del_ica": (
                "arts. 7 y 8 del Decreto 807 de 1993; art. 27 del Acuerdo 65 de 2002 "
                "(exenciones); Acuerdo 77 de 2002 y Acuerdo 185 de 2005 (predial); arts. 12 a 14 "
                "del Acuerdo 469 de 2011 y art. 9 del Acuerdo 671 de 2017 (notificaciones); "
                "art. 10 del Acuerdo 756 de 2019 (regímenes); Acuerdo 111 de 2003 (publicidad "
                "exterior) y Acuerdo 399 de 2009 (azar y espectáculos), estos dos derogados "
                "desde el 1 de enero de 2027"
            ),
        },
        "regimen_simple_2026": {
            "fuente": "Acuerdo 1019 de 2025, art. 44 (derogado por el art. 52 del Acuerdo 1084)",
            "descripcion": (
                "Tarifas del ICA consolidado del régimen SIMPLE, por numeral del art. 908 del "
                "Estatuto Tributario Nacional"
            ),
            "tarifas_por_mil": [
                {"numeral": "1", "tarifa_por_mil": "12"},
                {"numeral": "2", "tarifa_por_mil": "16"},
                {"numeral": "3", "tarifa_por_mil": "30"},
                {"numeral": "3 (sic)", "tarifa_por_mil": "30"},
                {"numeral": "6", "tarifa_por_mil": "16"},
            ],
        },
    }


def main() -> None:
    datos = construir()
    filas = datos["filas"]
    contenido = _encabezado(datos) | {"por_actividad": filas}
    SALIDA.write_text(
        yaml.safe_dump(contenido, allow_unicode=True, sort_keys=False, width=110),
        encoding="utf-8",
    )
    pendientes = [f["ciiu"] for f in filas if f["tarifa_por_mil"] == "pendiente"]
    print(len(filas), "filas;", len(pendientes), "pendientes:", ", ".join(pendientes))


if __name__ == "__main__":
    main()
