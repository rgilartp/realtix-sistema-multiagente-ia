"""Lectura del recibo con el modelo de visión (RF-OCR-02 y RF-OCR-05).

Una sola llamada a Haiku 5.5 (`MODELO_OCR`) con la imagen y la salida en `json_schema`: si es un
recibo predial, si se puede leer y los seis campos de RF-OCR-02 tal como aparecen (nunca el nombre
del propietario). Un PDF se convierte en imagen (primera página) con pypdfium2. La imagen se envía
con un ancho máximo de 1.000 px, que basta para leer la plantilla y gasta menos tokens.
"""

import base64
import io
from pathlib import Path
from typing import Literal

from anthropic import transform_schema
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from PIL import Image
from pydantic import BaseModel, ConfigDict

from src.agents.prompts import cargar_prompt
from src.integrations.modelos import texto_de_respuesta
from src.integrations.robustez import con_tiempo_y_reintento

ANCHO_MAXIMO = 1000
ESCALA_PDF = 150 / 72  # unos 150 ppp, como la plantilla


class CamposOCR(BaseModel):
    model_config = ConfigDict(extra="forbid")
    matricula: str | None
    vigencia: str | None
    avaluo: str | None
    valor_liquidado: str | None
    descuento: str | None
    fecha_limite: str | None


class SalidaOCR(BaseModel):
    """Esquema de la lectura; no pide razonamiento (sección 3.2)."""

    model_config = ConfigDict(extra="forbid")
    es_recibo_predial: bool
    legible: bool
    problemas: list[Literal["desenfocado", "baja_resolucion", "recortado", "ilegible"]]
    campos: CamposOCR


FORMATO_OCR = {"format": {"type": "json_schema", "schema": transform_schema(SalidaOCR)}}


def abrir_documento(ruta: str | Path, tipo: str) -> Image.Image:
    """La imagen del documento; de un PDF, la primera página. Falla si el archivo está dañado."""
    if tipo == "application/pdf":
        import pypdfium2

        pdf = pypdfium2.PdfDocument(str(ruta))
        try:
            return pdf[0].render(scale=ESCALA_PDF).to_pil().convert("RGB")
        finally:
            pdf.close()
    with Image.open(ruta) as imagen:
        return imagen.convert("RGB")


def png_base64(imagen: Image.Image, ancho_maximo: int = ANCHO_MAXIMO) -> str:
    if imagen.width > ancho_maximo:
        alto = round(imagen.height * ancho_maximo / imagen.width)
        imagen = imagen.resize((ancho_maximo, alto), Image.Resampling.LANCZOS)
    salida = io.BytesIO()
    imagen.save(salida, "PNG", optimize=True)
    return base64.b64encode(salida.getvalue()).decode("ascii")


def leer_documento(modelo: BaseChatModel, imagen: Image.Image, timeout_s: float) -> SalidaOCR:
    """Lectura estructurada del documento (con tiempo máximo y un reintento)."""
    mensajes = [
        SystemMessage(cargar_prompt("ocr").texto),
        HumanMessage(
            content=[
                {"type": "text", "text": "Lee este documento y entrega el JSON pedido."},
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": png_base64(imagen),
                    },
                },  # fmt: skip
            ]
        ),
    ]
    enlazado = modelo.bind(output_config=FORMATO_OCR)
    respuesta = con_tiempo_y_reintento(
        lambda: enlazado.invoke(mensajes), timeout_s, servicio="modelo"
    )
    return SalidaOCR.model_validate_json(texto_de_respuesta(respuesta))
