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
from src.data.generar.recibos_apaisados import dibujar_apaisado, foto_que_no_es_recibo, recortar
from src.services import notas
from src.services.documentos import (
    CamposRecibo,
    a_fecha,
    a_pesos,
    fuera_de_proporcion,
    problemas_de_calidad,
    problemas_del_documento,
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
    ("nombre", "calidad", "fuera"),
    [
        ("recibo_valido_U03", [], False),
        ("documento_otro_tipo", [], False),  # legible: el tipo lo decide el modelo
        ("recibo_desenfocado_U03", ["desenfocado"], False),
        ("recibo_baja_resolucion_U03", ["baja_resolucion"], False),
        ("recibo_solo_recortado_U03", [], True),
        ("recibo_recortado_U03", ["baja_resolucion"], True),
    ],
)
def test_calidad_y_proporcion_por_codigo(recibos, archivos, nombre, calidad, fuera) -> None:
    imagen = imagen_de(recibos[nombre])
    assert problemas_de_calidad(imagen) == calidad and fuera_de_proporcion(imagen) is fuera
    # El PDF se lee como imagen y da lo mismo.
    pdf = abrir_documento(archivos[nombre]["pdf"], "application/pdf")
    assert problemas_de_calidad(pdf) == calidad and fuera_de_proporcion(pdf) is fuera


@pytest.fixture(scope="module")
def apaisados(recibos, tmp_path_factory) -> dict[str, Path]:
    """Recibos con un formato más realista (apaisados y por secciones) y una foto sin recibo."""
    completo = dibujar_apaisado(recibos["recibo_valido_U03"])
    destino = tmp_path_factory.mktemp("apaisados")
    rutas = {}
    for nombre, imagen in (("completo", completo), ("recortado", recortar(completo)),
                           ("foto", foto_que_no_es_recibo())):  # fmt: skip
        rutas[nombre] = destino / f"{nombre}.png"
        imagen.save(rutas[nombre])
    return rutas


@pytest.mark.unit
@pytest.mark.req("RF-OCR-04 · Rechazo de documentos ilegibles")
def test_primero_el_tipo_y_la_proporcion_solo_con_campos_faltantes(recibos, apaisados) -> None:
    completo, recortado, foto = (Image.open(apaisados[n]).convert("RGB")
                                 for n in ("completo", "recortado", "foto"))  # fmt: skip
    # Un recibo apaisado completo no está recortado, aunque no sea un A4 vertical.
    assert fuera_de_proporcion(completo) and problemas_del_documento(completo, True, False) == []
    assert problemas_del_documento(recortado, True, True) == ["recortado"]
    # Una foto que no es un recibo lo dice, aunque por código parezca desenfocada.
    assert problemas_de_calidad(foto) and problemas_del_documento(foto, False, True) == [
        "no_es_recibo"
    ]
    # En un A4 vertical, que falten campos no es un recorte.
    vertical = imagen_de(recibos["recibo_valido_U03"])
    assert problemas_del_documento(vertical, True, True) == []


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
    "RF-OCR-05 · Modelo de visión", "RNF-03 · Protección de datos personales",
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
@pytest.mark.req("RNF-16 · Tasa de respuestas correctas")
def test_en_el_modo_de_evaluacion_el_contraste_reporta_sus_datos_y_notas(
    datos_sinteticos, archivos
) -> None:
    """F1 de la corrida 1 (ADR-25): el juez ve el estado de cuenta del contraste y las notas que
    agregó el sistema, como en los agentes con herramientas."""
    modelo = ModeloFalso([lectura()])
    deps = {"modelos": lambda _n: modelo, "modo_evaluacion": True}
    cliente, _ = armar(datos_sinteticos, deps_extra=deps)
    subir(cliente, archivos["recibo_valido_U03"]["png"], "conv-ocr-eval")
    meta = chat(cliente, "conv-ocr-eval", "Sí, los datos son correctos", **token(U03))["meta"]
    (visto,) = meta["herramientas"]
    assert visto["resultado"]["obligaciones_vencidas"] >= 1
    assert (
        visto["resultado"]["avaluo_registrado"] and visto["resultado"]["valor_liquidado_registrado"]
    )
    assert visto["resultado"]["fuentes_de_la_herramienta"]
    assert notas.NOTA_INTERESES_MORA in meta["notas"]


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
def test_ocr_04_y_05_rechazo_con_el_motivo_despues_del_tipo(
    api_ocr, archivos, nombre, debe_decir
) -> None:
    cliente, _, modelo = api_ocr
    # El modelo reconoce el recibo, aunque le falten datos (el recorte quita los de abajo).
    modelo.respuestas = [lectura({**CAMPOS_U03, "fecha_limite": None, "descuento": None})]
    r = subir(cliente, archivos[nombre]["png"], f"conv-{nombre}").json()
    assert (
        r["estado"] == "aclaracion" and debe_decir in r["respuesta"] and "nuevo" in r["respuesta"]
    )
    assert "2.135.000" not in r["respuesta"] and len(modelo.llamadas) == 1


@pytest.mark.unit
@pytest.mark.req("RF-OCR-04 · Rechazo de documentos ilegibles", "RF-OCR-02 · Extracción de campos")
def test_recibo_apaisado_completo_recortado_y_foto_que_no_es_recibo(api_ocr, apaisados) -> None:
    cliente, _, modelo = api_ocr
    modelo.respuestas = [
        lectura(),
        lectura({**CAMPOS_U03, "fecha_limite": None}),
        lectura({k: None for k in CAMPOS_U03}, es_recibo_predial=False, legible=False),
    ]
    completo = subir(cliente, apaisados["completo"], "conv-apaisado").json()
    assert "Estos son los datos que leí" in completo["respuesta"]
    assert "recortado" not in completo["respuesta"]
    recortado = subir(cliente, apaisados["recortado"], "conv-apaisado-recortado").json()
    assert "recortado" in recortado["respuesta"] and "no es un recibo" not in recortado["respuesta"]
    foto = subir(cliente, apaisados["foto"], "conv-foto").json()
    assert "no es un recibo" in foto["respuesta"]
    assert "recortado" not in foto["respuesta"] and "desenfocad" not in foto["respuesta"]


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


def _general(texto: str = "Hola, ¿en qué te ayudo?") -> Any:
    return salida(respuesta=texto, suficiencia="completa", cobertura=1.0, fuera_del_mvp=False,
                  fragmentos_citados=[])  # fmt: skip


@pytest.mark.unit
@pytest.mark.req(
    "RF-OCR-03 · Confirmación de datos extraídos", "RF-AUT-02 · Restricción a predios propios"
)
def test_negacion_y_predio_ajeno(api_ocr, archivos) -> None:
    cliente, _, modelo = api_ocr
    u01 = {**CAMPOS_U03, "matricula": "50C-9000101", "avaluo": "$280.000.000",
           "valor_liquidado": "$1.652.000", "descuento": "$165.200"}  # fmt: skip
    modelo.respuestas = [lectura(), lectura(u01)]
    subir(cliente, archivos["recibo_valido_U03"]["png"], "conv-neg")
    no = chat(cliente, "conv-neg", "No, están mal", **token(U03))
    assert "no usaré esos datos" in no["respuesta"] and no["meta"]["datos_extraidos"] is None
    # Recibo de un predio ajeno (el de U01 con la sesión de U03): mismo mensaje único (OC-06).
    subir(cliente, archivos["recibo_valido_U01"]["pdf"], "conv-ajeno", tipo="application/pdf")
    ajeno = chat(cliente, "conv-ajeno", "Sí, correcto", **token(U03))
    assert ajeno["estado"] == "rechazo_acceso" and ajeno["respuesta"] == MENSAJE_PREDIO_INACCESIBLE


@pytest.mark.unit
@pytest.mark.req("RF-OCR-03 · Confirmación de datos extraídos", "RF-ORQ-06 · Prevención de bucles")
def test_otros_mensajes_no_confirman_ni_escalan(api_ocr, archivos) -> None:
    """Revisión independiente: un recibo sin confirmar no escala la conversación por el tope de
    reclasificaciones, y una pregunta que empieza con «Si…» o «inexactos» no confirma."""
    cliente, servicios, modelo = api_ocr
    modelo.respuestas = [lectura(), *[_general() for _ in range(3)]]
    subir(cliente, archivos["recibo_valido_U03"]["png"], "conv-otros")
    for mensaje in ("Hola, buenas tardes", "Hola otra vez", "Hola de nuevo"):
        r = chat(cliente, "conv-otros", mensaje, **token(U03))
        assert r["estado"] == "respondida" and "nodo_general" in r["meta"]["agentes_invocados"]
    assert servicios.almacen.estado_conversacion("conv-otros") == "activa"
    # Los datos vencieron con el primer mensaje: un «sí» posterior ya no los usa.
    modelo.respuestas = [_general("¿Sobre qué quieres que te confirme?")]
    tarde = chat(cliente, "conv-otros", "Sí", **token(U03))
    assert "coinciden" not in tarde["respuesta"]
    for conversacion, mensaje in (
        ("conv-si", "Si pago después de la fecha, ¿cuánto me cobran de intereses?"),
        ("conv-inexactos", "Los datos son inexactos"),
    ):
        modelo.respuestas = [lectura(), _general()]
        subir(cliente, archivos["recibo_valido_U03"]["png"], conversacion)
        r = chat(cliente, conversacion, mensaje, **token(U03))
        assert "Gracias por confirmar" not in r["respuesta"], mensaje


@pytest.mark.unit
@pytest.mark.req(
    "RF-OCR-03 · Confirmación de datos extraídos", "RF-ESC-02 · Activación del escalamiento"
)
def test_peticion_de_funcionario_y_oferta_de_transferencia_no_confirman(api_ocr, archivos) -> None:
    cliente, _, modelo = api_ocr
    modelo.respuestas = [lectura()]
    subir(cliente, archivos["recibo_valido_U03"]["png"], "conv-func")
    r = chat(cliente, "conv-func", "No, quiero hablar con un funcionario", **token(U03))
    assert r["estado"] == "escalada" and r["meta"]["motivo_escalamiento"] == "solicitud explícita"
    # Con un recibo pendiente, «¿Eres un robot?» ofrece la transferencia; el «Sí» la acepta.
    modelo.respuestas = [lectura()]
    subir(cliente, archivos["recibo_valido_U03"]["png"], "conv-robot")
    robot = chat(cliente, "conv-robot", "¿Eres un robot?", **token(U03))
    assert "inteligencia artificial" in robot["respuesta"]
    acepta = chat(cliente, "conv-robot", "Sí", **token(U03))
    assert acepta["estado"] == "escalada" and "coinciden" not in acepta["respuesta"]


@pytest.mark.unit
@pytest.mark.req(
    "RF-AUT-04 · Aviso de sesión requerida", "RF-OCR-03 · Confirmación de datos extraídos"
)
def test_sin_sesion_el_recibo_pendiente_da_el_aviso_de_sesion(datos_sinteticos) -> None:
    from src.agents.dependencias import Dependencias
    from src.agents.graph import configuracion_de_hilo, construir_grafo
    from src.agents.nodes.general import AVISO_SESION
    from src.agents.state import entrada_de_turno
    from src.data.memoria import RealSitEnMemoria

    grafo = construir_grafo(
        Dependencias(RealSitEnMemoria(datos_sinteticos), modelos=lambda _n: ModeloFalso())
    )
    config = configuracion_de_hilo("conv-vencida", "2026-10-01T10:00:00-05:00")
    pendiente = {"ocr": {"campos": CAMPOS_U03, "pendiente": True, "confirmado": False}}
    grafo.update_state(config, {"datos_extraidos": pendiente})
    final = grafo.invoke(entrada_de_turno("Sí, correcto", "conv-vencida"), config)
    assert final["respuesta_final"] == AVISO_SESION and "ocr" not in final["datos_extraidos"]


@pytest.mark.unit
@pytest.mark.req("RF-OCR-03 · Confirmación de datos extraídos")
@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ("Sí, los datos son correctos", "si"), ("Sí", "si"), ("ok", "si"),
        ("sí los datos son correctos", "si"), ("Todo bien", "si"),
        ("correcto, no hay problema", "si"), ("No", "no"), ("No, están mal", "no"),
        ("Los datos son inexactos", "no"), ("Están incorrectos", "no"),
        ("Si pago después de la fecha, ¿cuánto me cobran?", None),
        ("Si pago después de la fecha cuánto me cobran", None),
        ("No entiendo qué es el avalúo", None), ("No, quiero hablar con un funcionario", None),
        ("Hola, buenas tardes", None),
    ],
)  # fmt: skip
def test_interpretar_la_confirmacion(texto, esperado) -> None:
    from src.services.documentos import interpretar_confirmacion

    assert interpretar_confirmacion(texto) == esperado


@pytest.mark.unit
@pytest.mark.req("RNF-08 · Tiempos de espera y degradación", "RF-OCR-05 · Modelo de visión")
def test_falla_del_modelo_de_vision_escala_sin_error_tecnico(api_ocr, archivos) -> None:
    cliente, _, modelo = api_ocr
    modelo.respuestas = [ConnectionError("api caída"), ConnectionError("api caída")]
    r = subir(cliente, archivos["recibo_valido_U03"]["png"], "conv-caida").json()
    assert r["estado"] == "escalada" and r["meta"]["motivo_escalamiento"] == "fallo de servicio"
    assert "api" not in r["respuesta"].lower()


@pytest.mark.unit
@pytest.mark.req("RF-OCR-02 · Extracción de campos", "RNF-03 · Protección de datos personales")
def test_el_esquema_no_pide_el_nombre_del_propietario_ni_razonamiento() -> None:
    esquema = SalidaOCR.model_json_schema()
    nombres = [*esquema["properties"], *esquema["$defs"]["CamposOCR"]["properties"]]
    for prohibido in ("propietario", "nombre", "razon", "reasoning"):
        assert not any(prohibido in n for n in nombres)
    assert problemas_de_calidad(Image.new("RGB", (400, 566), "white")) == ["baja_resolucion"]


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


@pytest.mark.integration
@pytest.mark.skipif(
    os.environ.get("REALTIX_PRUEBAS_REALES") != "1",
    reason="Usa el modelo de visión real: REALTIX_PRUEBAS_REALES=1",
)
@pytest.mark.req("RF-OCR-04 · Rechazo de documentos ilegibles", "RF-OCR-05 · Modelo de visión")
def test_recibos_apaisados_y_foto_con_el_modelo_real(apaisados) -> None:
    from src.agents.nodes.ocr import leer_recibo
    from src.container import Contenedor

    contenedor = Contenedor()
    leidos = {
        nombre: leer_recibo(
            contenedor.modelo("ocr"),
            abrir_documento(ruta, "image/png"),
            contenedor.settings.timeout_modelo_s,
        )  # fmt: skip
        for nombre, ruta in apaisados.items()
    }
    campos, problemas = leidos["completo"]
    assert campos is not None and campos.como_texto()["matricula"] == "50C-9000301", problemas
    assert leidos["recortado"][0] is None and "recortado" in leidos["recortado"][1]
    assert leidos["foto"] == (None, ["no_es_recibo"])
