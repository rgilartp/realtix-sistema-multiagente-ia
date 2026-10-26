"""B10: recibos sintéticos, legibilidad, lectura con el modelo falso, confirmación y contraste.

Sin red: el modelo de visión sigue un guion. Las cifras salen de las referencias aprobadas de
OCR-01 a OCR-07 y del conjunto sintético (U03: $350.000.000, 6,1 por mil, $2.135.000).
"""

import json
import os
from pathlib import Path
from typing import Any

import pytest
from PIL import Image

from src.agents.vision import FORMATO_OCR, SalidaOCR, abrir_documento
from src.api.esquemas import AVISO_IA
from src.data.adapter import MENSAJE_PREDIO_INACCESIBLE
from src.data.generar.recibos import (
    LEYENDA,
    Recibo,
    guardar,
    imagen_de,
    recibos_del_conjunto,
    textos_del_documento,
)
from src.services.documentos import (
    CamposRecibo,
    a_fecha,
    a_pesos,
    problemas_de_legibilidad,
    validar_campos,
)
from tests.modelo_falso import ModeloFalso, salida
from tests.test_api import U03, armar, chat, token

MARCAS_PROHIBIDAS = ("bogota", "secretaria", "hacienda", "alcaldia", "distrital", "realtix",
                     "realsit", "escudo", "shd")  # fmt: skip
CAMPOS_U03 = {"matricula": "50C-9000301", "vigencia": "2026", "avaluo": "$350.000.000",
              "valor_liquidado": "$2.135.000", "descuento": "$213.500",
              "fecha_limite": "10/07/2026"}  # fmt: skip


@pytest.fixture(scope="module")
def recibos(datos_sinteticos) -> dict[str, Recibo]:
    return {r.nombre: r for r in recibos_del_conjunto(datos_sinteticos)}


@pytest.fixture(scope="module")
def archivos(recibos, tmp_path_factory) -> dict[str, dict[str, Path]]:
    destino = tmp_path_factory.mktemp("recibos")
    return {nombre: guardar(r, destino) for nombre, r in recibos.items()}


def lectura(campos: dict[str, str | None] | None = None, **cambios: Any) -> Any:
    """Salida del modelo de visión con valores por defecto (el recibo de U03)."""
    return salida(**{"es_recibo_predial": True, "legible": True, "problemas": [],
                     "campos": campos or CAMPOS_U03, **cambios})  # fmt: skip


def _normalizado(texto: str) -> str:
    from src.agents.nodes._comun import normalizar

    return normalizar(texto)


# -- Generador (sección 4.5) -----------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.req(
    "RF-OCR-06 · Plantilla sintética de recibo", "RNF-04 · Uso exclusivo de datos sintéticos"
)
def test_diez_recibos_con_ocho_campos_leyenda_y_json_de_referencia(recibos, archivos) -> None:
    validos = [r for r in recibos.values() if r.calidad == "legible" and r.tipo == "recibo_predial"]
    assert len(validos) == 10
    u03 = recibos["recibo_valido_U03"]
    assert u03.extraibles() == CAMPOS_U03 and u03.tarifa == "6,1 por mil"
    assert recibos["recibo_valido_U01"].extraibles()["valor_liquidado"] == "$1.652.000"  # OCR-02
    assert recibos["recibo_valido_U06"].extraibles()["valor_liquidado"] == "$600.000"  # OCR-03
    referencia = json.loads(archivos["recibo_valido_U03"]["json"].read_text(encoding="utf-8"))
    assert referencia["extraibles"] == CAMPOS_U03 and referencia["leyenda"] == LEYENDA
    assert "propietario" not in referencia["extraibles"]
    for rutas in archivos.values():
        assert rutas["png"].stat().st_size > 0 and rutas["pdf"].read_bytes().startswith(b"%PDF-")
    for recibo in recibos.values():
        textos = textos_del_documento(recibo)
        assert textos.count(LEYENDA) == 2
        if recibo.tipo == "recibo_predial":
            assert len([t for t in textos if ": " in t]) == 9  # 8 campos (propietario y dirección)


@pytest.mark.unit
@pytest.mark.req("RF-OCR-06 · Plantilla sintética de recibo")
def test_sin_logos_ni_marcas_reales(recibos) -> None:
    """Ni de Bogotá ni de la Secretaría de Hacienda (ni de Realtix o RealSit): no hay imágenes
    incrustadas y ningún texto dibujado las nombra."""
    for recibo in recibos.values():
        texto = _normalizado(" ".join(textos_del_documento(recibo)))
        for marca in MARCAS_PROHIBIDAS:
            assert marca not in texto, (recibo.nombre, marca)
    # La imagen solo tiene los colores de la plantilla (texto, líneas y bandas): sin logos.
    colores = imagen_de(recibos["recibo_valido_U03"]).convert("RGB").getcolors(maxcolors=4096)
    assert colores is not None and len(colores) < 4096


# -- Legibilidad y campos --------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.req("RF-OCR-04 · Rechazo de documentos ilegibles")
@pytest.mark.parametrize(
    ("nombre", "problemas"),
    [
        ("recibo_valido_U03", []),
        ("documento_otro_tipo", []),  # legible: el tipo lo decide el modelo
        ("recibo_desenfocado_U03", ["desenfocado"]),
        ("recibo_baja_resolucion_U03", ["baja_resolucion"]),
        ("recibo_solo_recortado_U03", ["recortado"]),
        ("recibo_recortado_U03", ["recortado", "baja_resolucion"]),
    ],
)
def test_legibilidad_por_codigo(recibos, archivos, nombre, problemas) -> None:
    assert problemas_de_legibilidad(imagen_de(recibos[nombre])) == problemas
    # El PDF se lee como imagen y da lo mismo.
    pdf = abrir_documento(archivos[nombre]["pdf"], "application/pdf")
    assert problemas_de_legibilidad(pdf) == problemas


@pytest.mark.unit
@pytest.mark.req("RF-OCR-02 · Extracción de campos")
def test_campos_normalizados_y_validados() -> None:
    campos, invalidos = validar_campos({**CAMPOS_U03, "matricula": "50c-9000301 "})
    assert invalidos == [] and campos is not None
    assert campos.avaluo == 350_000_000 and campos.fecha_limite.isoformat() == "2026-07-10"
    assert campos.como_texto() == CAMPOS_U03
    assert a_pesos("2135000") == 2_135_000 and a_pesos("$ 2.135.000,50") is None
    assert a_fecha("2026-07-10") == a_fecha("10-07-2026")
    _, invalidos = validar_campos({**CAMPOS_U03, "avaluo": None, "matricula": "123"})
    assert invalidos == ["matricula", "avaluo"]
    assert CamposRecibo.__dataclass_fields__.keys() == CAMPOS_U03.keys()


# -- Flujo por la API con el modelo falso (OCR-01 a OCR-07) ----------------------------------------


def subir(cliente, ruta: Path, conv: str, tipo: str = "image/png", **cabeceras: str) -> Any:
    return cliente.post(
        "/api/v1/chat/documento",
        data={"id_conversacion": conv, "mensaje": "Te envío mi recibo"},
        files={"archivo": (ruta.name, ruta.read_bytes(), tipo)},
        headers={**token(U03), **cabeceras},
    )


@pytest.fixture
def api_ocr(datos_sinteticos):
    modelo = ModeloFalso()
    cliente, servicios = armar(datos_sinteticos, deps_extra={"modelos": lambda _n: modelo})
    return cliente, servicios, modelo


@pytest.mark.unit
@pytest.mark.req(
    "RF-OCR-02 · Extracción de campos", "RF-OCR-03 · Confirmación de datos extraídos",
    "RF-OCR-05 · Modelo de visión",
)  # fmt: skip
def test_ocr_01_y_ocr_07_lectura_confirmacion_y_contraste(api_ocr, archivos) -> None:
    cliente, servicios, modelo = api_ocr
    modelo.respuestas = [lectura()]
    r = subir(cliente, archivos["recibo_valido_U03"]["png"], "conv-ocr")
    datos = r.json()
    assert (
        r.status_code == 200 and datos["estado"] == "aclaracion" and datos["aviso_ia"] == AVISO_IA
    )
    for valor in CAMPOS_U03.values():
        assert valor in datos["respuesta"]
    assert (
        "¿Es correcto?" in datos["respuesta"] and "Usuario de Prueba 03" not in datos["respuesta"]
    )
    assert datos["meta"]["datos_extraidos"]["campos"] == CAMPOS_U03
    assert datos["meta"]["agentes_invocados"][1] == "nodo_ocr"
    # El modelo recibió la imagen con su formato de salida, y el estado no guarda la imagen.
    mensajes, parametros = modelo.llamadas[0]
    assert parametros["output_config"] == FORMATO_OCR
    assert mensajes[1].content[1]["type"] == "image"
    estado = servicios.grafo.get_state({"configurable": {"thread_id": "conv-ocr"}}).values
    assert "iVBOR" not in str(estado)  # el comienzo de un PNG en base64
    # OCR-07: confirma y el sistema contrasta con el adaptador, sin modificarlo.
    antes = servicios.adaptador.get_estado_cuenta("50C-9000301", U03)
    segundo = chat(cliente, "conv-ocr", "Sí, los datos son correctos", **token(U03))
    assert (
        segundo["estado"] == "respondida" and segundo["meta"]["agentes_invocados"][1] == "nodo_ocr"
    )
    texto = segundo["respuesta"]
    assert "coinciden" in texto and "$350.000.000" in texto and "$2.135.000" in texto
    assert "1 obligación vencida con un saldo de $2.135.000" in texto
    assert servicios.adaptador.get_estado_cuenta("50C-9000301", U03) == antes
    assert len(modelo.llamadas) == 1  # la confirmación no llama al modelo


@pytest.mark.unit
@pytest.mark.req("RF-OCR-04 · Rechazo de documentos ilegibles")
@pytest.mark.parametrize(
    ("nombre", "debe_decir"),
    [
        ("recibo_desenfocado_U03", "desenfocada"),  # OCR-04
        ("recibo_recortado_U03", "recortado"),  # OCR-05
        ("recibo_baja_resolucion_U03", "baja resolución"),
    ],
)
def test_ocr_04_y_05_rechazo_por_codigo_sin_llamar_al_modelo(
    api_ocr, archivos, nombre, debe_decir
) -> None:
    cliente, _, modelo = api_ocr
    r = subir(cliente, archivos[nombre]["png"], f"conv-{nombre}").json()
    assert (
        r["estado"] == "aclaracion" and debe_decir in r["respuesta"] and "nuevo" in r["respuesta"]
    )
    assert "2.135.000" not in r["respuesta"] and modelo.llamadas == []


@pytest.mark.unit
@pytest.mark.req("RF-OCR-04 · Rechazo de documentos ilegibles")
def test_ocr_06_documento_de_otro_tipo_y_campos_faltantes(api_ocr, archivos) -> None:
    cliente, _, modelo = api_ocr
    modelo.respuestas = [
        lectura({k: None for k in CAMPOS_U03}, es_recibo_predial=False),
        lectura({**CAMPOS_U03, "avaluo": None}),
    ]
    otro = subir(cliente, archivos["documento_otro_tipo"]["png"], "conv-otro").json()
    assert "no es un recibo" in otro["respuesta"] and "nuevo" in otro["respuesta"]
    incompleto = subir(cliente, archivos["recibo_valido_U03"]["png"], "conv-incompleto").json()
    assert "faltan datos del recibo" in incompleto["respuesta"]
    assert incompleto["meta"]["datos_extraidos"] is None


@pytest.mark.unit
@pytest.mark.req(
    "RF-OCR-03 · Confirmación de datos extraídos", "RF-AUT-02 · Restricción a predios propios"
)
def test_negacion_otra_pregunta_y_predio_ajeno(api_ocr, archivos) -> None:
    cliente, _, modelo = api_ocr
    u01 = {**CAMPOS_U03, "matricula": "50C-9000101", "avaluo": "$280.000.000",
           "valor_liquidado": "$1.652.000", "descuento": "$165.200"}  # fmt: skip
    # Pregunta otra cosa: el OCR la devuelve y el orquestador la reclasifica (agente general).
    modelo.respuestas = [lectura(), salida(respuesta="Hola, ¿en qué te ayudo?",
                                           suficiencia="completa", cobertura=1.0,
                                           fuera_del_mvp=False, fragmentos_citados=[]),
                         lectura(u01)]  # fmt: skip
    subir(cliente, archivos["recibo_valido_U03"]["png"], "conv-neg")
    otra = chat(cliente, "conv-neg", "Hola, buenas tardes", **token(U03))
    assert "nodo_general" in otra["meta"]["agentes_invocados"]
    no = chat(cliente, "conv-neg", "No, están mal", **token(U03))
    assert "no usaré esos datos" in no["respuesta"] and no["meta"]["datos_extraidos"] is None
    # Recibo de un predio ajeno (el de U01 con la sesión de U03): mismo mensaje único (OC-06).
    subir(cliente, archivos["recibo_valido_U01"]["pdf"], "conv-ajeno", tipo="application/pdf")
    ajeno = chat(cliente, "conv-ajeno", "Sí, correcto", **token(U03))
    assert ajeno["estado"] == "rechazo_acceso" and ajeno["respuesta"] == MENSAJE_PREDIO_INACCESIBLE


@pytest.mark.unit
@pytest.mark.req("RNF-08 · Tiempos de espera y degradación", "RF-OCR-05 · Modelo de visión")
def test_falla_del_modelo_de_vision_escala_sin_error_tecnico(api_ocr, archivos) -> None:
    cliente, _, modelo = api_ocr
    modelo.respuestas = [ConnectionError("api caída"), ConnectionError("api caída")]
    r = subir(cliente, archivos["recibo_valido_U03"]["png"], "conv-caida").json()
    assert r["estado"] == "escalada" and r["meta"]["motivo_escalamiento"] == "fallo de servicio"
    assert "api" not in r["respuesta"].lower()


@pytest.mark.unit
@pytest.mark.req("RF-OCR-02 · Extracción de campos")
def test_el_esquema_no_pide_el_nombre_del_propietario_ni_razonamiento() -> None:
    esquema = SalidaOCR.model_json_schema()
    nombres = [*esquema["properties"], *esquema["$defs"]["CamposOCR"]["properties"]]
    for prohibido in ("propietario", "nombre", "razon", "reasoning"):
        assert not any(prohibido in n for n in nombres)
    assert problemas_de_legibilidad(Image.new("RGB", (400, 566), "white")) == ["baja_resolucion"]


# -- Con el modelo de visión real (REALTIX_PRUEBAS_REALES=1) -------------------------------------


@pytest.mark.integration
@pytest.mark.skipif(
    os.environ.get("REALTIX_PRUEBAS_REALES") != "1",
    reason="Usa el modelo de visión real: REALTIX_PRUEBAS_REALES=1",
)
@pytest.mark.req(
    "RF-OCR-02 · Extracción de campos", "RF-OCR-04 · Rechazo de documentos ilegibles",
    "RF-OCR-05 · Modelo de visión",
)  # fmt: skip
def test_exactitud_por_campo_y_rechazos_con_el_modelo_real(recibos, archivos) -> None:
    from src.container import Contenedor
    from src.evaluacion.ocr import evaluar_ocr

    contenedor = Contenedor()
    reporte = evaluar_ocr(
        contenedor.modelo("ocr"), list(recibos.values()), archivos,
        contenedor.settings.timeout_modelo_s,
    )  # fmt: skip
    resumen = reporte["resumen"]
    assert resumen["exactitud_total"] >= 0.95, resumen
    assert resumen["rechazos_correctos"] == resumen["rechazos"], resumen
