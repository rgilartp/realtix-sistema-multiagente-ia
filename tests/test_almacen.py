"""Almacén propio: SQLite en las unitarias y PostgreSQL en la prueba de integración."""

import os
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime

import pytest
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from src.data.adapter import MockRealSitAdapter
from src.data.models import CasoEscalado
from src.store.almacen import Almacen, crear_motor

URL_COMPOSE = "postgresql://realtix:realtix_dev@localhost:5432/realtix"  # docker-compose.yml


@pytest.fixture
def almacen() -> Almacen:
    almacen = Almacen(
        crear_motor("sqlite+pysqlite:///:memory:"),
        reloj=lambda: datetime(2026, 10, 1, 15, 0, tzinfo=UTC),
    )
    almacen.crear_esquema()
    return almacen


def _caso(id_caso: str = "CASO-1", conversacion: str = "CONV-1", **extra) -> CasoEscalado:
    return CasoEscalado(id_caso, conversacion, "Resumen del caso", 0.0, **extra)


@pytest.mark.unit
@pytest.mark.req("RF-SYS-02 · Alcance de solo lectura")
def test_registrar_un_caso_sin_conversacion_previa_la_crea(almacen: Almacen) -> None:
    # H-02: antes fallaba con IntegrityError.
    assert almacen.estado_conversacion("CONV-1") is None
    almacen.registrar_caso(_caso(motivo="solicitud explícita", resumen_json={"intentos": 0}))
    assert almacen.estado_conversacion("CONV-1") == "escalada"
    caso = almacen.obtener_caso("CASO-1")
    assert caso["motivo"] == "solicitud explícita"
    assert caso["resumen_json"] == {"intentos": 0}


@pytest.mark.unit
@pytest.mark.req("RF-ESC-03 · Resumen estructurado del caso")
def test_el_caso_que_escala_antes_de_la_confianza_guarda_cero_con_su_motivo(
    almacen: Almacen,
) -> None:
    almacen.registrar_caso(_caso(motivo="tope de reclasificaciones"))
    caso = almacen.obtener_caso("CASO-1")
    assert caso["nivel_confianza"] == 0.0
    assert caso["motivo"] == "tope de reclasificaciones"


@pytest.mark.unit
def test_estados_de_la_conversacion(almacen: Almacen) -> None:
    almacen.asegurar_conversacion("CONV-2", "CC-1000000001")
    almacen.asegurar_conversacion("CONV-2", "OTRO")  # no pisa la existente
    assert almacen.estado_conversacion("CONV-2") == "activa"
    almacen.cambiar_estado("CONV-2", "cerrada")
    assert almacen.estado_conversacion("CONV-2") == "cerrada"
    with pytest.raises(ValueError):
        almacen.cambiar_estado("CONV-2", "inventada")


@pytest.mark.unit
def test_mensajes_del_funcionario_e_interacciones_sin_texto_del_contribuyente(
    almacen: Almacen,
) -> None:
    almacen.registrar_caso(_caso())
    almacen.guardar_mensaje("CASO-1", "contribuyente", "¿Y mi predio?")
    almacen.guardar_mensaje("CASO-1", "funcionario", "Ya lo reviso")
    assert [m["autor"] for m in almacen.mensajes_del_caso("CASO-1")] == [
        "contribuyente",
        "funcionario",
    ]
    almacen.registrar_interaccion("CONV-1", 850, "ipu", 0.82, False)
    fila = almacen.interacciones("CONV-1")[0]
    assert set(fila) == {
        "id_interaccion", "id_conversacion", "categoria", "nivel_confianza",
        "escalada", "duracion_ms", "fecha",
    }  # fmt: skip


@pytest.mark.unit
@pytest.mark.req("RNF-02 · Escalamiento horizontal")
def test_registro_concurrente_de_casos(tmp_path) -> None:
    almacen = Almacen(crear_motor(f"sqlite+pysqlite:///{tmp_path / 'almacen.db'}"))
    almacen.crear_esquema()

    def registrar(n: int) -> None:
        almacen.registrar_caso(_caso(f"CASO-{n}", f"CONV-{n}"))

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(registrar, range(40)))
    assert len(almacen.listar_casos()) == 40


@pytest.mark.unit
@pytest.mark.req("RF-SYS-02 · Alcance de solo lectura")
def test_el_adaptador_registra_en_el_almacen_y_no_en_realsit(
    almacen: Almacen, base_sintetica
) -> None:
    from src.data.huella import calcular_huella

    antes = calcular_huella(base_sintetica)
    adaptador = MockRealSitAdapter(base_sintetica, registro_casos=almacen)
    assert adaptador.registrar_caso_escalado(_caso(motivo="fuera de alcance")).ok
    assert almacen.obtener_caso("CASO-1")["motivo"] == "fuera de alcance"
    assert calcular_huella(base_sintetica) == antes


@pytest.mark.integration
@pytest.mark.req("RF-ORQ-04 · Implementación en LangGraph")
def test_almacen_en_postgresql() -> None:
    url = os.environ.get("DATABASE_URL_PRUEBAS", URL_COMPOSE)
    motor = crear_motor(url)
    try:
        with motor.connect() as c:
            c.execute(text("SELECT 1"))
    except OperationalError:
        pytest.skip("PostgreSQL no responde: levanta `docker compose up -d postgres`.")
    almacen = Almacen(motor)
    almacen.crear_esquema()
    try:
        almacen.registrar_caso(_caso("PG-1", "PG-CONV-1", resumen_json={"a": 1}))
        assert almacen.obtener_caso("PG-1")["resumen_json"] == {"a": 1}
        assert almacen.estado_conversacion("PG-CONV-1") == "escalada"
    finally:
        with motor.begin() as c:
            for tabla in ("mensaje_funcionario", "caso_escalado", "conversacion", "interaccion"):
                c.execute(text(f"DELETE FROM {tabla}"))  # noqa: S608


@pytest.mark.unit
@pytest.mark.req("RF-SYS-05 · Adaptador equivalente a RealSit")
def test_el_contenedor_arma_el_adaptador_con_el_almacen(entorno_valido, base_sintetica) -> None:
    from src.container import Contenedor

    entorno_valido.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    entorno_valido.setenv("REALSIT_DB_PATH", str(base_sintetica))
    contenedor = Contenedor()
    assert contenedor.settings.vigencia_actual == 2026
    assert contenedor.adaptador.get_predios_contribuyente("CC-1000000003")
    assert contenedor.adaptador.registrar_caso_escalado(_caso(motivo="prueba")).ok
    assert contenedor.almacen.obtener_caso("CASO-1")["nivel_confianza"] == 0.0
