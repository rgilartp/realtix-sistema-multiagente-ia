"""Exactitud del agente OCR sobre los recibos sintéticos (B10, RF-OCR-02 y RF-OCR-04).

Lee los 10 recibos legibles en PNG y en PDF con el modelo de visión real y compara cada campo con
su JSON de referencia; pasa también las variantes degradadas y el documento de otro tipo, que
deben rechazarse con su motivo. Guarda los tokens y el costo.
"""

from typing import Any

from langchain_core.language_models import BaseChatModel

from src.agents.nodes.ocr import leer_recibo
from src.agents.vision import abrir_documento
from src.data.generar.recibos import CAMPOS_EXTRAIBLES, Recibo, imagen_de
from src.services.documentos import validar_campos

ESPERADOS = {
    "desenfocado": {"desenfocado"},
    "baja_resolucion": {"baja_resolucion"},
    "recortado": {"recortado"},
    "recortado_baja_resolucion": {"recortado", "baja_resolucion"},
}


def evaluar_ocr(
    modelo: BaseChatModel,
    recibos: list[Recibo],
    archivos: dict[str, dict[str, Any]],
    timeout_s: float,
) -> dict[str, Any]:
    """Resultados por documento y resumen: exactitud por campo y rechazos correctos."""
    resultados = []
    for recibo in recibos:
        formatos = ("png", "pdf") if recibo.calidad == "legible" else ("png",)
        for formato in formatos:
            ruta = archivos[recibo.nombre][formato]
            tipo = "application/pdf" if formato == "pdf" else "image/png"
            imagen = abrir_documento(ruta, tipo) if formato == "pdf" else imagen_de(recibo)
            campos, problemas = leer_recibo(modelo, imagen, timeout_s)
            fila: dict[str, Any] = {"documento": recibo.nombre, "formato": formato,
                                    "calidad": recibo.calidad, "tipo": recibo.tipo,
                                    "problemas": problemas}  # fmt: skip
            if recibo.tipo == "recibo_predial" and recibo.calidad == "legible":
                referencia, _ = validar_campos(recibo.extraibles())
                assert referencia is not None
                leidos = campos.como_texto() if campos else {}
                fila["aciertos"] = {
                    c: leidos.get(c) == referencia.como_texto()[c] for c in CAMPOS_EXTRAIBLES
                }
                fila["leidos"] = leidos
            else:
                esperados = ESPERADOS.get(recibo.calidad, {"no_es_recibo"})
                fila["rechazo_correcto"] = campos is None and esperados <= set(problemas)
            resultados.append(fila)
    return {"resultados": resultados, "resumen": resumir(resultados)}


def resumir(resultados: list[dict[str, Any]]) -> dict[str, Any]:
    legibles = [r for r in resultados if "aciertos" in r]
    por_campo = {
        c: round(sum(r["aciertos"][c] for r in legibles) / len(legibles), 3) if legibles else None
        for c in CAMPOS_EXTRAIBLES
    }
    total = [v for r in legibles for v in r["aciertos"].values()]
    rechazos = [r for r in resultados if "rechazo_correcto" in r]
    return {
        "documentos_legibles": len(legibles),
        "exactitud_por_campo": por_campo,
        "exactitud_total": round(sum(total) / len(total), 3) if total else None,
        "documentos_completos": sum(all(r["aciertos"].values()) for r in legibles),
        "rechazos": len(rechazos),
        "rechazos_correctos": sum(r["rechazo_correcto"] for r in rechazos),
    }
