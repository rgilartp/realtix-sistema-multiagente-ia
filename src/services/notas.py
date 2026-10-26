"""Notas que acompañan toda liquidación o estimación (sin modelo; el texto no se reescribe).

La aproximación al múltiplo de mil es una decisión de Rodolfo (B5): la estimación calcula y muestra
los valores exactos y solo advierte que la factura o la declaración los aproximan.
"""

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
NOTA_PROYECCION_ICA_ANUAL = (
    "El ICA anual de 2026 se estima como una proyección del año completo a partir de los ingresos "
    "que se indican; el impuesto definitivo depende de los ingresos reales del año."
)
NOTA_COMPLEMENTARIOS_ICA = (
    "La estimación no incluye el complementario de avisos y tableros (15 % del impuesto, "
    "Decreto 352 de 2002, art. 59) ni la sobretasa bomberil (Resolución SDH-000195 de 2025, "
    "art. 2), que se suman cuando aplican."
)
