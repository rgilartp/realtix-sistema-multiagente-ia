"""Volumen, estados, unicidad, reproducibilidad y solo lectura de la base sintética (B3)."""

import sqlite3
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import date

import pytest

from src.data.adapter import MockRealSitAdapter
from src.data.database import TABLAS, abrir_solo_lectura, conexion
from src.data.generar.generate_synthetic_data import (
    generar_datos,
    poblar_base,
    primer_dia_habil,
)
from src.data.huella import RUTA_HUELLA, calcular_huella
from src.services.datos_anuales import smmlv, umbral_ica_pesos
from src.services.ica import PeriodoICA, buscar_tarifa_ica
from src.services.predial import buscar_tarifa_ipu, valor_impuesto

REFERENCIA = date(2026, 10, 1)


@pytest.mark.unit
def test_fecha_de_referencia_es_el_primer_dia_habil_de_octubre_de_2026(datos_sinteticos) -> None:
    assert primer_dia_habil(2026, 10) == REFERENCIA  # jueves, no festivo
    assert datos_sinteticos.fecha_referencia == REFERENCIA


@pytest.mark.unit
@pytest.mark.req("RF-IPU-02 · Estado de cuenta e historial")
def test_volumen_500_predios_y_2000_obligaciones_de_ipu(base_sintetica) -> None:
    with conexion(base_sintetica) as c:
        assert c.execute("SELECT COUNT(*) FROM predio").fetchone()[0] == 500
        assert (
            c.execute(
                "SELECT COUNT(*) FROM obligacion_tributaria WHERE tipo_tributo = 'IPU'"
            ).fetchone()[0]
            == 2000
        )
        por_vigencia = Counter(
            r[0]
            for r in c.execute(
                "SELECT vigencia_fiscal FROM obligacion_tributaria WHERE tipo_tributo = 'IPU'"
            )
        )
        assert por_vigencia == {2023: 500, 2024: 500, 2025: 500, 2026: 500}
        assert c.execute("SELECT COUNT(*) FROM avaluo_vigencia").fetchone()[0] == 2000


@pytest.mark.unit
@pytest.mark.req("RNF-04 · Uso exclusivo de datos sintéticos")
def test_identificadores_unicos_y_derivados_de_la_semilla(datos_sinteticos) -> None:
    listas = {
        "contribuyente": [c.id_contribuyente for c in datos_sinteticos.contribuyentes],
        "matrícula": [p.matricula_catastral for p in datos_sinteticos.predios],
        "chip": [p.chip for p in datos_sinteticos.predios],
        "obligación": [o.id_obligacion for o in datos_sinteticos.obligaciones],
        "pago": [p.id_pago for p in datos_sinteticos.pagos],
    }
    for nombre, ids in listas.items():
        assert len(ids) == len(set(ids)), f"{nombre} repetido"
    # La unicidad se sostiene con otras semillas (OC-02: 2 de 200 semillas repetían antes).
    for semilla in range(1, 21):
        d = generar_datos(semilla)
        assert len({p.matricula_catastral for p in d.predios}) == 500
        assert len({o.id_obligacion for o in d.obligaciones}) == len(d.obligaciones)


@pytest.mark.unit
@pytest.mark.req("RF-OBS-05 · Ejecución repetible de pruebas")
def test_misma_semilla_misma_huella(tmp_path, base_sintetica) -> None:
    otra = tmp_path / "otra.db"
    poblar_base(otra, generar_datos(42))
    assert calcular_huella(otra) == calcular_huella(base_sintetica)
    distinta = tmp_path / "distinta.db"
    poblar_base(distinta, generar_datos(7))
    assert calcular_huella(distinta) != calcular_huella(base_sintetica)


@pytest.mark.unit
@pytest.mark.req("RF-OBS-05 · Ejecución repetible de pruebas")
def test_la_huella_registrada_es_la_de_la_semilla_42(base_sintetica) -> None:
    registrada = RUTA_HUELLA.read_text(encoding="utf-8").strip()
    assert calcular_huella(base_sintetica) == registrada


@pytest.mark.unit
@pytest.mark.req("RF-IPU-02 · Estado de cuenta e historial")
def test_estados_de_las_obligaciones_al_corte(base_sintetica) -> None:
    with conexion(base_sintetica) as c:
        estados = Counter(
            (r["tipo_tributo"], r["estado_pago"])
            for r in c.execute("SELECT tipo_tributo, estado_pago FROM obligacion_tributaria")
        )
        assert {"AL_DIA", "PENDIENTE", "VENCIDO", "NO_OBLIGADO"} == {e for _, e in estados}
        assert estados[("ICA", "PENDIENTE")] > 0
        filas = c.execute("SELECT * FROM obligacion_tributaria").fetchall()
    for o in filas:
        limite = date.fromisoformat(o["fecha_limite_pago"])
        if o["estado_pago"] == "VENCIDO":
            assert limite < REFERENCIA, o["id_obligacion"]
        if o["estado_pago"] == "PENDIENTE":
            assert limite >= REFERENCIA, o["id_obligacion"]
        if o["estado_pago"] == "NO_OBLIGADO":
            assert o["valor_liquidado"] == 0 and o["tarifa_por_mil"] == "0"
        assert (o["origen_tarifa"] == "oficial") == (o["vigencia_fiscal"] == 2026)


@pytest.mark.unit
@pytest.mark.req("RF-IPU-03 · Liquidación estimada")
def test_toda_obligacion_de_ipu_sale_de_las_reglas_de_datos(datos_sinteticos) -> None:
    predios = {p.matricula_catastral: p for p in datos_sinteticos.predios}
    avaluos = {(m, v): a for m, v, a in datos_sinteticos.avaluos}
    ipu = [o for o in datos_sinteticos.obligaciones if o.tipo_tributo == "IPU"]
    assert len(ipu) == 2000
    for o in ipu:
        predio = predios[o.matricula_catastral]
        avaluo = avaluos[(o.matricula_catastral, o.vigencia_fiscal)]
        regla = buscar_tarifa_ipu(2026, predio.destino, predio.estrato, avaluo)
        assert o.base_gravable == avaluo
        assert o.tarifa_por_mil == regla.tarifa_por_mil
        assert o.valor_liquidado == (
            valor_impuesto(avaluo, regla.tarifa_por_mil) if regla.obligado else 0
        )
        assert (o.estado_pago == "NO_OBLIGADO") == (not regla.obligado)
        if o.vigencia_fiscal == 2026 and o.estado_pago != "NO_OBLIGADO":
            assert o.fecha_limite_descuento == date(2026, 4, 17)


@pytest.mark.unit
@pytest.mark.req("RF-IPU-03 · Liquidación estimada")
def test_solo_u11_queda_no_obligado_y_los_aleatorios_estan_sobre_16_smmlv(datos_sinteticos) -> None:
    limite = 16 * smmlv(2026)
    no_obligados = {
        o.matricula_catastral
        for o in datos_sinteticos.obligaciones
        if o.estado_pago == "NO_OBLIGADO"
    }
    assert no_obligados == {"50C-9001101"}
    for p in datos_sinteticos.predios:
        if p.estrato in (1, 2) and p.matricula_catastral != "50C-9001101":
            assert (
                min(a for m, _, a in datos_sinteticos.avaluos if m == p.matricula_catastral)
                > limite
            )


@pytest.mark.unit
@pytest.mark.req("RF-ICA-02 · Estimación por actividad")
def test_ica_una_obligacion_por_contribuyente_y_vigencia_en_su_predio(datos_sinteticos) -> None:
    predios = {p.matricula_catastral: p for p in datos_sinteticos.predios}
    con_actividad = {
        c.id_contribuyente: c for c in datos_sinteticos.contribuyentes if c.codigo_ciiu
    }
    cuentas: Counter[tuple[str, int]] = Counter()
    for o in datos_sinteticos.obligaciones:
        if o.tipo_tributo != "ICA":
            continue
        dueno = predios[o.matricula_catastral].id_contribuyente
        assert dueno in con_actividad
        cuentas[(dueno, o.vigencia_fiscal)] += 1
    assert set(cuentas.values()) == {1}
    assert len(cuentas) == 4 * len(con_actividad)
    for c in con_actividad.values():
        assert c.regimen_ica in ("comun_bimestral", "comun_anual", "preferencial")
        assert c.actividad_economica


@pytest.mark.unit
@pytest.mark.req("RF-ICA-03 · Fechas de declaración")
def test_regimen_de_ica_segun_el_umbral_de_391_uvt(datos_sinteticos) -> None:
    umbral = umbral_ica_pesos(2026)
    assert umbral == 19_471_409
    contribuyentes = {c.id_contribuyente: c for c in datos_sinteticos.contribuyentes}
    predios = {p.matricula_catastral: p for p in datos_sinteticos.predios}
    for o in datos_sinteticos.obligaciones:
        if o.tipo_tributo == "ICA" and o.vigencia_fiscal == 2025:
            c = contribuyentes[predios[o.matricula_catastral].id_contribuyente]
            assert (c.regimen_ica == "comun_bimestral") == (o.valor_liquidado > umbral)
    assert {c.regimen_ica for c in contribuyentes.values()} >= {
        "comun_bimestral",
        "comun_anual",
        "preferencial",
    }


@pytest.mark.unit
@pytest.mark.req("RF-ICA-02 · Estimación por actividad")
def test_tarifas_del_ica_cargadas_de_datos_sin_provisionales(base_sintetica) -> None:
    with conexion(base_sintetica) as c:
        filas = c.execute("SELECT * FROM tarifa_ica").fetchall()
    assert len(filas) == 486
    assert all(f["fuente"] and f["vigencia"] == 2026 for f in filas)
    for f in filas[::40]:
        esperado = buscar_tarifa_ica(f["codigo_ciiu"], PeriodoICA(2026))
        assert f["tarifa_por_mil"] == format(esperado.tarifa_por_mil, "f")


@pytest.mark.unit
@pytest.mark.req("RF-SYS-02 · Alcance de solo lectura")
def test_una_escritura_sobre_la_base_de_realsit_falla(base_sintetica) -> None:
    antes = calcular_huella(base_sintetica)
    conn = abrir_solo_lectura(base_sintetica)
    try:
        for sentencia in (
            "INSERT INTO pago VALUES ('X', 'Y', '2026-01-01', 1, 'PSE')",
            "UPDATE predio SET avaluo_catastral = 1",
            "DELETE FROM obligacion_tributaria",
            "DROP TABLE pago",
        ):
            with pytest.raises(sqlite3.OperationalError, match="readonly"):
                conn.execute(sentencia)
    finally:
        conn.close()
    assert calcular_huella(base_sintetica) == antes
    assert set(TABLAS) >= {"contribuyente", "predio", "obligacion_tributaria", "pago"}


@pytest.mark.unit
@pytest.mark.req("RF-SYS-02 · Alcance de solo lectura")
def test_el_adaptador_no_tiene_metodos_de_escritura_sobre_realsit() -> None:
    publicos = {n for n in dir(MockRealSitAdapter) if not n.startswith("_")}
    assert publicos == {
        "get_predios_contribuyente",
        "get_estado_cuenta",
        "get_historial_pagos",
        "get_avaluo_catastral",
        "get_tarifa_ica",
        "get_obligaciones_vigentes",
        "registrar_caso_escalado",
    }


@pytest.mark.unit
def test_ruta_como_texto_o_path_y_uso_desde_varios_hilos(base_sintetica) -> None:
    como_texto = MockRealSitAdapter(str(base_sintetica))
    como_path = MockRealSitAdapter(base_sintetica)
    assert como_texto.get_predios_contribuyente("CC-1000000003") == (
        como_path.get_predios_contribuyente("CC-1000000003")
    )

    def consulta(_: int) -> int:
        return como_texto.get_estado_cuenta("50C-9000301", "CC-1000000003").saldo_total_pendiente

    with ThreadPoolExecutor(max_workers=8) as pool:
        assert set(pool.map(consulta, range(64))) == {2_135_000}
