"""Reglas de acceso, resumen del caso y minimización de lo que se envía a los modelos."""

import json
from dataclasses import asdict

import pytest

from src.agents.dependencias import Dependencias
from src.agents.graph import configuracion_de_hilo, construir_grafo
from src.agents.state import entrada_de_turno
from src.data.adapter import (
    PredioNoAutorizadoError,
    PredioNoEncontradoError,
    verificar_predio_propio,
)
from src.data.memoria import RealSitEnMemoria
from src.data.models import Predio
from src.services.acceso import decidir_acceso
from src.services.minimizacion import PROHIBIDOS, minimizar
from src.services.resumen import construir_resumen
from src.store.almacen import Almacen, crear_motor

U03, P03 = "CC-1000000003", "50C-9000301"


def _predio(dueno: str = U03) -> Predio:
    return Predio(
        P03, "AAA0000AAAA", dueno, "Calle 1 # 2-3", "Usaquén", 4, "residencial", 350_000_000
    )


# -- Acceso ---------------------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.req("RF-AUT-03 · Consultas sin autenticación")
def test_la_consulta_general_se_atiende_sin_sesion() -> None:
    assert decidir_acceso(False, None).permitido
    assert decidir_acceso(False, None).razon == "permitido"


@pytest.mark.unit
@pytest.mark.req("RF-AUT-04 · Aviso de sesión requerida")
def test_la_consulta_personal_sin_sesion_pide_iniciar_sesion() -> None:
    d = decidir_acceso(True, None)
    assert not d.permitido and d.razon == "sesion_requerida"
    assert decidir_acceso(True, "").razon == "sesion_requerida"


@pytest.mark.unit
@pytest.mark.req("RF-AUT-02 · Restricción a predios propios")
def test_predio_propio_ajeno_e_inexistente_con_la_regla_unica_del_adaptador() -> None:
    assert decidir_acceso(True, U03, pidio_predio=True, predio=_predio()).permitido
    ajeno = decidir_acceso(True, U03, pidio_predio=True, predio=_predio("CC-1000000002"))
    inexistente = decidir_acceso(True, U03, pidio_predio=True, predio=None)
    assert ajeno == inexistente and ajeno.razon == "predio_inaccesible" and not ajeno.permitido
    assert decidir_acceso(True, U03).permitido  # sin predio pedido todavía


@pytest.mark.unit
@pytest.mark.req("RF-AUT-02 · Restricción a predios propios")
def test_no_hay_dos_implementaciones_de_la_restriccion(datos_sinteticos) -> None:
    with pytest.raises(PredioNoEncontradoError):
        verificar_predio_propio(None, U03)
    with pytest.raises(PredioNoAutorizadoError):
        verificar_predio_propio(_predio("CC-1000000002"), U03)
    adaptador = RealSitEnMemoria(datos_sinteticos)
    ajeno = next(p for p in datos_sinteticos.predios if p.id_contribuyente != U03)
    with pytest.raises(PredioNoAutorizadoError):  # el adaptador usa la misma función
        adaptador.get_estado_cuenta(ajeno.matricula_catastral, U03)


# -- Resumen --------------------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.req("RF-ESC-03 · Resumen del caso")
def test_resumen_en_texto_y_en_json_con_las_mismas_cifras() -> None:
    resueltas = [{"categoria": "ipu", "texto": "Predial resuelto"}]
    rechazadas = [{"categoria": "ica", "texto": "Dudosa", "nivel": 0.48}]
    texto, datos = construir_resumen(
        motivo="confianza insuficiente",
        categoria="ica",
        nivel_confianza=0.48,
        intentos=1,
        resueltas=resueltas,
        rechazadas=rechazadas,
    )
    assert texto.startswith("Motivo: confianza insuficiente. Categoría: ica.")
    assert "Nivel de confianza: 0,48" in texto and "Partes ya resueltas: 1" in texto
    assert datos["partes_resueltas"] == ["Predial resuelto"]
    assert datos["partes_rechazadas"] == [{"categoria": "ica", "texto": "Dudosa", "nivel": 0.48}]
    assert datos["intentos"] == 1 and "motivo_original" not in datos
    json.dumps(datos)  # serializable para la bandeja de B9


@pytest.mark.unit
@pytest.mark.req("RF-ESC-04 · Tiempo de entrega del resumen")
def test_cada_escalamiento_mide_el_tiempo_del_resumen() -> None:
    almacen = Almacen(crear_motor("sqlite+pysqlite:///:memory:"))
    almacen.crear_esquema()
    from src.data.generar.generate_synthetic_data import generar_datos

    grafo = construir_grafo(
        Dependencias(RealSitEnMemoria(generar_datos(42), registro_casos=almacen))
    )
    entrada = entrada_de_turno("Quiero hablar con una persona", "tiempo-1")
    r = grafo.invoke(entrada, configuracion_de_hilo("tiempo-1"))
    caso = almacen.obtener_caso("CASO-tiempo-1")
    assert 0 <= caso["resumen_json"]["duracion_resumen_ms"] < 5000  # p95 menor a 5 s (RF-ESC-04)
    assert 0 <= r["marcas"]["duracion_escalamiento_ms"] < 5000


# -- Minimización ---------------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.req("RNF-03 · Protección de datos personales")
def test_lo_que_se_envia_al_modelo_no_lleva_nombre_documento_ni_direccion(datos_sinteticos) -> None:
    adaptador = RealSitEnMemoria(datos_sinteticos)
    contribuyente = datos_sinteticos.contribuyentes[0]
    predio = next(
        p for p in datos_sinteticos.predios if p.id_contribuyente == contribuyente.id_contribuyente
    )
    cuenta = adaptador.get_estado_cuenta(predio.matricula_catastral, contribuyente.id_contribuyente)
    enviado = minimizar(cuenta)
    texto = json.dumps(enviado, ensure_ascii=False)
    assert enviado["matricula_catastral"] == predio.matricula_catastral
    assert enviado["obligaciones"] and "estado_pago" in enviado["obligaciones"][0]
    for personal in (contribuyente.nombre, contribuyente.numero_documento, predio.direccion):
        assert personal not in texto
    assert contribuyente.id_contribuyente not in texto
    assert not (PROHIBIDOS & _claves(enviado))


@pytest.mark.unit
@pytest.mark.req("RNF-03 · Protección de datos personales")
def test_minimizar_descarta_todo_campo_que_no_este_en_la_lista_blanca() -> None:
    predio = _predio()
    assert minimizar(predio) == {
        "matricula_catastral": P03,
        "avaluo_catastral": 350_000_000,
        "destino": "residencial",
        "estrato": 4,
    }
    assert minimizar({"nombre": "Ana", "valor_pagado": 5}) == {"valor_pagado": 5}
    assert "contribuyente" not in asdict(predio)


def _claves(valor) -> set[str]:
    if isinstance(valor, dict):
        return set(valor) | {c for v in valor.values() for c in _claves(v)}
    if isinstance(valor, list):
        return {c for v in valor for c in _claves(v)}
    return set()


@pytest.mark.unit
@pytest.mark.req("RF-AUT-02 · Restricción a predios propios")
def test_las_matriculas_ajenas_del_mensaje_se_detectan_sin_modelo() -> None:
    """F9 de la corrida 1, con matrículas sintéticas inventadas."""
    from src.services.acceso import matriculas_ajenas, rechazo_previo

    propias = ["50C-9999901"]
    assert matriculas_ajenas("Dame el saldo del 50c-9999901", propias) == []
    texto = "Dame el 50C-9999977, el 50c-9999977 y el 50C-9999901"
    assert matriculas_ajenas(texto, propias) == ["50C-9999977"]
    assert matriculas_ajenas("¿Qué es el predial?", propias) == []
    assert matriculas_ajenas("El 50C-123 y el 50C-12345678 no son válidas", propias) == []
    assert matriculas_ajenas("Dame el 50C-9999977", []) == ["50C-9999977"]
    assert rechazo_previo(texto, "CC-9", propias) and not rechazo_previo(texto, None, propias)


@pytest.mark.unit
@pytest.mark.req("RF-ESC-03 · Resumen del caso")
def test_el_nivel_del_resumen_lleva_coma_decimal_y_el_json_conserva_el_numero() -> None:
    """F12 de la corrida 1, con un nivel inventado de dos decimales."""
    texto, datos = construir_resumen(
        motivo="confianza insuficiente",
        categoria="ipu",
        nivel_confianza=0.37,
        intentos=0,
        resueltas=[],
        rechazadas=[],
    )
    assert "Nivel de confianza: 0,37." in texto and "0.37" not in texto
    assert datos["nivel_confianza"] == 0.37
