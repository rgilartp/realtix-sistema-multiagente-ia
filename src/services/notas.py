"""Notas que acompañan toda liquidación o estimación (sin modelo; el texto no se reescribe).

La aproximación al múltiplo de mil es una decisión de Rodolfo (B5): la estimación calcula y muestra
los valores exactos y solo advierte que la factura o la declaración los aproximan.
"""

import re
import unicodedata

NOTA_ESTIMACION = (
    "Esta es una estimación informativa y no vinculante: no reemplaza la factura, la declaración "
    "ni un pronunciamiento de la Secretaría Distrital de Hacienda."
)
NOTA_APROXIMACION_PREDIAL = (
    "En la factura y en la declaración los valores se aproximan al múltiplo de mil más cercano "
    "(Decreto 807 de 1993, arts. 15 y 132), así que el valor a pagar puede variar levemente; "
    "el que cuenta es el de la factura o la declaración."
)
NOTA_APROXIMACION_ICA = (
    "En la declaración los valores se aproximan al múltiplo de mil más cercano (Decreto 807 de "
    "1993, art. 15), así que el valor a pagar puede variar levemente; el que cuenta es el de la "
    "declaración."
)
NOTA_LEY_1995 = (
    "La estimación no aplica los topes al aumento anual del impuesto predial de la Ley 1995 "
    "de 2019 (art. 2, vigente por la Ley 2294 de 2023, art. 49, parágrafo 3), que dependen del "
    "impuesto del año anterior; por eso el valor de la factura puede ser menor."
)
NOTA_IVIUR_2027 = (
    "Los rangos en pesos de 2027 se actualizan cada año con el IVIUR y esa actualización aún no se "
    "publica; la estimación usa la tabla del Acuerdo 1084 de 2026 tal como está."
)
NOTA_DESCUENTO_2027 = "El descuento por pronto pago de 2027 aún no se publica; no se estima."
NOTA_TOPE_SOBRETASA = (
    "La sobretasa de alumbrado público tiene un tope de 600 UVT en los predios residenciales "
    "y de 1.200 UVT en los demás (Acuerdo 1084 de 2026, art. 15); como la UVT de 2027 aún no "
    "se publica, la estimación no aplica el tope y el valor de la factura puede ser menor."
)
NOTA_SOBRETASA_SIN_UVT = (
    "La sobretasa de alumbrado público de los estratos 1, 2 y 3 depende de la UVT de 2027 "
    "(el límite de 20.000 UVT), que aún no se publica; por eso no se estima."
)
NOTA_PROYECCION_ICA_ANUAL = (
    "El ICA anual de 2026 se estima como una proyección del año completo a partir de los ingresos "
    "que se indican; el impuesto definitivo depende de los ingresos reales del año."
)
NOTA_COMPLEMENTARIOS_ICA = (
    "La estimación no incluye el complementario de avisos y tableros (15 % del impuesto, "
    "Decreto 352 de 2002, art. 59) ni la sobretasa bomberil (Resolución SDH-000195 de 2025, "
    "art. 2), que se suman cuando aplican."
)
NOTA_INTERESES_MORA = (
    "Como hay obligaciones vencidas, el pago incluye intereses de mora (Decreto 807 de 1993, "
    "art. 66), que esta información no calcula; el valor exacto lo da la factura o la Secretaría "
    "Distrital de Hacienda."
)


def nota_avaluo_anterior(anio: int, anterior: int) -> str:
    """El avalúo del año pedido aún no se conoce y la estimación usa el del año anterior."""
    return (
        f"El avalúo catastral de {anio} aún no se conoce; la estimación usa el de {anterior}, así "
        "que el valor puede cambiar cuando se fije el nuevo avalúo."
    )


_FIN_DE_ORACION = re.compile(r"(?<=[.!?])\s+(?=[¿¡A-ZÁÉÍÓÚÑ])")
_PALABRA = re.compile(r"\w{4,}")
COINCIDENCIA_MINIMA = 0.6  # parte de las palabras de la oración que también están en la nota


def _palabras(texto: str) -> set[str]:
    sin_tildes = "".join(
        c for c in unicodedata.normalize("NFD", texto.lower()) if unicodedata.category(c) != "Mn"
    )
    return set(_PALABRA.findall(sin_tildes))


def sin_repetir_notas(texto: str, notas_que_se_agregan: list[str]) -> str:
    """Quita de la respuesta del modelo las oraciones que repiten una nota que el sistema agrega al
    final (F11 de la corrida 1): las que comparten al menos el 60 % de sus palabras (de cuatro
    letras o más, y como mínimo seis) con alguna nota. Sin modelo; las demás no cambian."""
    if not notas_que_se_agregan:
        return texto
    de_las_notas = [_palabras(n) for n in notas_que_se_agregan]

    def repite(oracion: str) -> bool:
        propias = _palabras(oracion)
        return any(
            len(propias & nota) >= max(6, COINCIDENCIA_MINIMA * len(propias))
            for nota in de_las_notas
        )

    parrafos = []
    for parrafo in texto.split("\n"):
        oraciones = [o for o in _FIN_DE_ORACION.split(parrafo) if not repite(o)]
        if oraciones or not parrafo.strip():
            parrafos.append(" ".join(oraciones))
    return re.sub(r"\n{3,}", "\n\n", "\n".join(parrafos)).strip()
