"""Lectura del recibo con el modelo de visión (RF-OCR-02 y RF-OCR-05).

Una sola llamada a Haiku 5.5 (`MODELO_OCR`) con la imagen y la salida en `json_schema`: si es un
recibo predial, si se puede leer y los seis campos de RF-OCR-02 tal como aparecen (nunca el nombre
del propietario). Un PDF se convierte en imagen (primera página) con pypdfium2. La imagen se envía
con un ancho máximo de 1.000 px, que basta para leer la plantilla y gasta menos tokens, y un alto
máximo de 2.000 px; en PNG o, si así pesa demasiado (una foto), en JPEG. Una imagen de más de
`PIXELES_MAXIMOS` se rechaza antes de decodificarla (auditoría de seguridad: una imagen pequeña en
bytes puede ocupar cientos de MB al abrirse).
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
ALTO_MAXIMO = 2000
BYTES_MAXIMOS_PNG = 3_500_000  # en base64 queda por debajo de los 5 MB por imagen de la API
ESCALA_PDF = 150 / 72  # unos 150 ppp, como la plantilla
LADO_MAXIMO_PDF = 2500
PIXELES_MAXIMOS = 25_000_000  # unos 5.000 × 5.000 px: muy por encima de un recibo escaneado
Image.MAX_IMAGE_PIXELS = PIXELES_MAXIMOS  # Pillow avisa por encima y falla desde el doble


class ImagenDemasiadoGrandeError(ValueError):
    """La imagen declara más píxeles de los que se aceptan; el nodo OCR la rechaza como ilegible."""


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
    """La imagen del documento; de un PDF, la primera página. Falla si el archivo está dañado o si
    la imagen tiene más de `PIXELES_MAXIMOS`."""
    if tipo == "application/pdf":
        import pypdfium2

        pdf = pypdfium2.PdfDocument(str(ruta))
        try:
            pagina = pdf[0]
            ancho, alto = pagina.get_size()  # en puntos
            # Una página enorme no se convierte a más de LADO_MAXIMO_PDF píxeles por lado.
            escala = min(ESCALA_PDF, LADO_MAXIMO_PDF / max(ancho, alto, 1))
            return pagina.render(scale=escala).to_pil().convert("RGB")
        finally:
            pdf.close()
    with Image.open(ruta) as imagen:
        ancho, alto = imagen.size  # sale del encabezado, sin decodificar la imagen
        if ancho * alto > PIXELES_MAXIMOS:
            raise ImagenDemasiadoGrandeError(f"{ancho} × {alto} píxeles")
        return imagen.convert("RGB")


def imagen_para_el_modelo(imagen: Image.Image) -> tuple[str, str]:
    """El tipo y la imagen en base64, reducida si hace falta: ancho de 1.000 px y alto de 2.000 px
    como máximo; en PNG, o en JPEG si el PNG pesa demasiado (una foto)."""
    escala = min(1.0, ANCHO_MAXIMO / imagen.width, ALTO_MAXIMO / imagen.height)
    if escala < 1:
        tamano = (max(1, round(imagen.width * escala)), max(1, round(imagen.height * escala)))
        imagen = imagen.resize(tamano, Image.Resampling.LANCZOS)
    salida = io.BytesIO()
    imagen.save(salida, "PNG", optimize=True)
    tipo = "image/png"
    if salida.tell() > BYTES_MAXIMOS_PNG:
        salida = io.BytesIO()
        imagen.convert("RGB").save(salida, "JPEG", quality=85)
        tipo = "image/jpeg"
    return tipo, base64.b64encode(salida.getvalue()).decode("ascii")


def leer_documento(modelo: BaseChatModel, imagen: Image.Image, timeout_s: float) -> SalidaOCR:
    """Lectura estructurada del documento (con tiempo máximo y un reintento)."""
    tipo, datos = imagen_para_el_modelo(imagen)
    mensajes = [
        SystemMessage(cargar_prompt("ocr").texto),
        HumanMessage(
            content=[
                {"type": "text", "text": "Lee este documento y entrega el JSON pedido."},
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": tipo,
                        "data": datos,
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
