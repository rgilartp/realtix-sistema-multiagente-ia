"""Límite de peticiones por IP en chat y documento (seguridad y gasto; src/api/limite.py)."""

import pytest

from src.api.limite import MENSAJE_POR_DIA, MENSAJE_POR_MINUTO, LimitadorPorIP
from tests.test_api import armar, configuracion

REQ = ("RNF-08 · Tiempos de espera y degradación", "RNF-14 · Configuración por entorno")


def _mensaje(cliente, conv: str = "conv-limite", **cabeceras: str):
    return cliente.post(
        "/api/v1/chat/mensaje", json={"id_conversacion": conv, "mensaje": "Hola"}, headers=cabeceras
    )


@pytest.mark.unit
@pytest.mark.req(*REQ)
def test_ventanas_de_un_minuto_y_de_un_dia_por_ip() -> None:
    ahora = [0.0]
    limitador = LimitadorPorIP(2, 3, reloj=lambda: ahora[0])
    assert limitador.registrar("203.0.113.7") is None and limitador.registrar("203.0.113.7") is None
    mensaje, espera = limitador.registrar("203.0.113.7")
    assert mensaje == MENSAJE_POR_MINUTO and 1 <= espera <= 61
    assert limitador.registrar("198.51.100.1") is None  # cada IP lleva su cuenta
    ahora[0] = 61.0
    assert limitador.registrar("203.0.113.7") is None  # la tercera del día
    ahora[0] = 200.0
    mensaje, espera = limitador.registrar("203.0.113.7")
    assert mensaje == MENSAJE_POR_DIA and espera > 60
    ahora[0] = 86_401.0
    assert limitador.registrar("203.0.113.7") is None  # pasó el día
    # Las IP sin peticiones en el último día se olvidan (la limpieza corre a lo más cada minuto).
    assert set(limitador._marcas) == {"203.0.113.7"}


@pytest.mark.unit
@pytest.mark.req(*REQ)
def test_los_limites_deben_ser_positivos() -> None:
    with pytest.raises(ValueError):
        configuracion(limite_peticiones_por_minuto=0)


@pytest.mark.unit
@pytest.mark.req(*REQ)
def test_chat_y_documento_responden_429_con_un_mensaje_claro(datos_sinteticos) -> None:
    cliente, _ = armar(datos_sinteticos, settings=configuracion(limite_peticiones_por_minuto=2))
    ip = {"X-Forwarded-For": "203.0.113.7"}
    assert [_mensaje(cliente, **ip).status_code for _ in range(2)] == [200, 200]
    r = _mensaje(cliente, **ip)
    assert r.status_code == 429 and r.json() == {"detalle": MENSAJE_POR_MINUTO}
    assert int(r.headers["Retry-After"]) >= 1
    documento = cliente.post(
        "/api/v1/chat/documento",
        data={"id_conversacion": "conv-limite"},
        files={"archivo": ("recibo.png", b"\x89PNG", "image/png")},
        headers=ip,
    )
    assert documento.status_code == 429  # el documento cuenta en la misma ventana
    # La IP es la última de X-Forwarded-For, la que pone Caddy: otra persona sigue atendida.
    assert (
        _mensaje(
            cliente, "conv-otra", **{"X-Forwarded-For": "203.0.113.7, 198.51.100.1"}
        ).status_code
        == 200
    )
    # El botón del funcionario y la salud no llaman modelos: no tienen límite.
    boton = cliente.post(
        "/api/v1/escalamiento", json={"id_conversacion": "conv-limite"}, headers=ip
    )
    assert boton.status_code != 429 and cliente.get("/health").status_code != 429


@pytest.mark.unit
@pytest.mark.req(*REQ)
def test_el_modo_de_evaluacion_con_escenario_no_cuenta(datos_sinteticos) -> None:
    cliente, _ = armar(datos_sinteticos, settings=configuracion(limite_peticiones_por_minuto=1))
    assert {_mensaje(cliente, **{"X-Escenario-Id": "GEN-01"}).status_code for _ in range(3)} == {
        200
    }
    # Sin el modo de evaluación, la cabecera se ignora y la petición cuenta.
    sin_modo = configuracion(limite_peticiones_por_minuto=1, modo_evaluacion=False)
    cliente, _ = armar(datos_sinteticos, settings=sin_modo)
    codigos = [_mensaje(cliente, **{"X-Escenario-Id": "GEN-01"}).status_code for _ in range(2)]
    assert codigos == [200, 429]
