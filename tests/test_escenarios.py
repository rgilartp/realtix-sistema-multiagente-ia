"""Escenarios del nivel de sistema (60), conjunto de enrutamiento (100) y su hoja de revisión.

Los 60 YAML son el material de la evaluación del OE4: aquí se comprueba que el esquema, la
distribución de la sección 6.3 y los orígenes (adenda y CA-01 a CA-06) estén completos, que la hoja
de revisión y el índice estén al día y que los servicios de B5 coincidan con las referencias
escritas a mano. Las referencias no salen de los servicios: se comparan contra ellos.
"""

import copy
import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from src.evaluacion.escenarios import (
    DIR_ESCENARIOS,
    DISTRIBUCION,
    HOJA_REVISION,
    INDICE,
    aprobar_referencias,
    cargar_enrutamiento,
    cargar_escenarios,
    esc_con_pendientes,
    hoja_de_revision,
    indice,
    requerimientos_de_la_especificacion,
    validar_conjunto,
    validar_enrutamiento,
    validar_escenario,
)
from src.services.calendario_tributario import fechas_ica, fechas_predial
from src.services.datos_anuales import smmlv, umbral_ica_pesos
from src.services.ica import PeriodoICA, estimar_ica
from src.services.predial import liquidar_predial

RAIZ = Path(__file__).resolve().parent.parent
USUARIOS = {
    u["id"]: u
    for u in yaml.safe_load((RAIZ / "tests/fixtures/usuarios_prueba.yaml").read_text("utf-8"))[
        "usuarios"
    ]
}
MESES = [
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
]


@pytest.fixture(scope="module")
def escenarios() -> list[dict]:
    return cargar_escenarios()


@pytest.fixture(scope="module")
def por_id(escenarios) -> dict[str, dict]:
    return {e["id"]: e for e in escenarios}


def pesos(valor: int) -> str:
    """12345678 -> «12.345.678»."""
    return f"{valor:,}".replace(",", ".")


def dia_y_mes(iso: str) -> str:
    _, mes, dia = iso.split("-")
    return f"{int(dia)} de {MESES[int(mes) - 1]}"


def fecha_larga(iso: str) -> str:
    anio, mes, dia = iso.split("-")
    return f"{int(dia)} de {MESES[int(mes) - 1]} de {anio}"


# -- Esquema y distribución ----------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.req("RNF-16 · Tasa de respuestas correctas")
def test_los_60_escenarios_cumplen_el_esquema_y_la_distribucion(escenarios) -> None:
    errores = validar_conjunto(escenarios, requerimientos_de_la_especificacion())
    assert errores == []
    assert len(escenarios) == 60 and sum(DISTRIBUCION.values()) == 60


@pytest.mark.unit
@pytest.mark.req("RNF-16 · Tasa de respuestas correctas")
def test_estan_los_14_de_la_adenda_y_cada_criterio_ca(escenarios) -> None:
    origenes = [o for e in escenarios for o in e["origen"]]
    for n in range(1, 15):
        assert origenes.count(f"adenda-{n}") == (2 if n == 8 else 1), n  # el 8: 2026 y 2027
    assert "adenda-15" not in origenes  # es una revisión automática de las trazas (B12)
    for n in range(1, 7):
        assert origenes.count(f"CA-0{n}") == 1, n


@pytest.mark.unit
@pytest.mark.req("RNF-16 · Tasa de respuestas correctas")
def test_el_archivo_lleva_el_nombre_del_id_y_aprobado_por_es_texto(escenarios) -> None:
    for ruta in DIR_ESCENARIOS.glob("*.yaml"):
        assert yaml.safe_load(ruta.read_text("utf-8"))["id"] == ruta.stem
    assert all(isinstance(e["aprobado_por"], str) for e in escenarios)


@pytest.mark.unit
@pytest.mark.req("RNF-16 · Tasa de respuestas correctas")
def test_las_sesiones_son_usuarios_de_prueba_y_el_reloj_es_el_de_referencia(escenarios) -> None:
    for e in escenarios:
        assert e["sesion"] in (*USUARIOS, "TOKEN_INVALIDO", None), e["id"]
        if e["grupo"] != "horario":
            assert e["reloj"] == "2026-10-01T10:00:00-05:00", e["id"]  # primer día hábil, 10:00


@pytest.mark.unit
@pytest.mark.req("RNF-16 · Tasa de respuestas correctas")
def test_el_validador_rechaza_un_escenario_mal_formado(por_id) -> None:
    base = por_id["IPU-10"]
    assert validar_escenario(base) == []
    casos = {
        "falta un campo": lambda e: e.pop("hu"),
        "grupo desconocido": lambda e: e.update(grupo="otro"),
        "categoría desconocida": lambda e: e.update(categoria_esperada="vehiculos"),
        "reloj sin zona": lambda e: e.update(reloj="2026-10-01T10:00:00"),
        "reloj de otra zona": lambda e: e.update(reloj="2026-10-01T10:00:00+00:00"),
        "requerimiento inválido": lambda e: e.update(rf=["RF-1"]),
        "origen desconocido": lambda e: e.update(origen=["adenda-15"]),
        "verificación desconocida": lambda e: e.update(verificaciones_codigo=[{"tipo": "x"}]),
        "verificación sin valor": lambda e: e.update(
            verificaciones_codigo=[{"tipo": "contiene_texto"}]
        ),
        "referencia vacía": lambda e: e.update(respuesta_referencia=" "),
        "sin fuentes": lambda e: e.update(fuentes_esperadas=[]),
        "pendiente sin explicar": lambda e: e.update(respuesta_referencia="PENDIENTE: falta"),
        "aprobado_por nulo": lambda e: e.update(aprobado_por=None),
        "sesión desconocida": lambda e: e.update(sesion="U99"),
        "motivo ajeno": lambda e: e.update(
            verificaciones_codigo=[{"tipo": "escala", "motivo": "x"}]
        ),
    }  # fmt: skip
    for nombre, rompe in casos.items():
        malo = copy.deepcopy(base)
        rompe(malo)
        assert validar_escenario(malo), nombre
    sin_rf_del_anexo = copy.deepcopy(base)
    sin_rf_del_anexo["rf"] = ["RF-IPU-99"]
    assert validar_escenario(sin_rf_del_anexo, requerimientos_de_la_especificacion())


@pytest.mark.unit
@pytest.mark.req("RNF-16 · Tasa de respuestas correctas")
def test_el_conjunto_detecta_ids_repetidos_y_distribucion_incorrecta(escenarios) -> None:
    sobra = [*escenarios, copy.deepcopy(escenarios[0])]
    errores = validar_conjunto(sobra)
    assert any("id repetido" in e for e in errores) and any("se esperaban 60" in e for e in errores)
    sin_ipu = [e for e in escenarios if e["id"] != "IPU-04"]
    assert any("grupo ipu" in e for e in validar_conjunto(sin_ipu))


@pytest.mark.unit
@pytest.mark.req("RNF-16 · Tasa de respuestas correctas")
def test_los_multiagente_declaran_sus_categorias(escenarios) -> None:
    multi = [e for e in escenarios if e["grupo"] == "multiagente"]
    assert len(multi) == 3 and all(e["categorias_esperadas"] == ["ipu", "ica"] for e in multi)
    sin = copy.deepcopy(multi[0])
    del sin["categorias_esperadas"]
    assert validar_escenario(sin)


# -- Referencias: fuentes y pendientes -----------------------------------------------------------


@pytest.mark.unit
@pytest.mark.req("RNF-16 · Tasa de respuestas correctas")
def test_toda_referencia_con_contenido_cita_su_fuente_y_lo_pendiente_esta_marcado(
    escenarios,
) -> None:
    # Decisión de Rodolfo: en las referencias de comportamiento, sin datos tributarios, la fuente
    # puede ser el requerimiento que lo define (RF, RNF, CA o la adenda). No queda ninguna.
    assert [e["id"] for e in escenarios if esc_con_pendientes(e)] == []
    for e in escenarios:
        if not e["respuesta_referencia"].startswith("PENDIENTE"):
            assert e["fuentes_esperadas"], e["id"]


@pytest.mark.unit
@pytest.mark.req("RNF-16 · Tasa de respuestas correctas")
def test_las_referencias_no_traen_fechas_del_trabajo_ni_otro_municipio_que_medellin(
    escenarios,
) -> None:
    for e in escenarios:
        texto = " ".join(
            [e["respuesta_referencia"], *e["no_debe"], *(t["usuario"] for t in e["turnos"])]
        )
        for otro in ("Cali", "Barranquilla", "Cartagena", "Bucaramanga"):
            assert otro not in texto, (e["id"], otro)
        assert "octubre de 2026" not in e["respuesta_referencia"].replace(
            "de octubre de 2026", ""
        ), e[
            "id"
        ]  # solo fechas tributarias («2 de octubre de 2026»), nunca «octubre de 2026» a secas


# -- Las referencias escritas a mano frente a los servicios de B5 (no al revés) ------------------


@pytest.mark.unit
@pytest.mark.req("RF-IPU-03 · Liquidación estimada")
def test_los_servicios_coinciden_con_las_referencias_del_predial(por_id) -> None:
    liq = liquidar_predial(2026, "residencial", 4, 350_000_000)
    ref = por_id["IPU-10"]["respuesta_referencia"]
    for valor in (liq.impuesto, liq.total_con_descuento, liq.descuento):
        assert pesos(valor) in ref or valor == liq.descuento, valor
    assert "6,1 por mil" in ref and str(liq.tarifa.tarifa_por_mil) == "6.1"
    liq27 = liquidar_predial(2027, "residencial", 4, 350_000_000)
    ref27 = por_id["IPU-11"]["respuesta_referencia"]
    assert liq27.sobretasa is not None
    for valor in (liq27.impuesto, liq27.sobretasa.valor, liq27.impuesto + liq27.sobretasa.valor):
        assert pesos(valor) in ref27, valor
    multi = liquidar_predial(2026, "residencial", 4, 410_000_000)
    assert pesos(multi.impuesto) in por_id["MULTI-02"]["respuesta_referencia"]
    assert pesos(16 * smmlv(2026)) in por_id["IPU-06"]["respuesta_referencia"]


@pytest.mark.unit
@pytest.mark.req("RF-ICA-02 · Estimación por actividad")
def test_los_servicios_coinciden_con_las_referencias_del_ica(por_id) -> None:
    casos = {
        "ICA-04": estimar_ica("6201", 60_000_000, PeriodoICA(2026)),
        "ICA-05": estimar_ica("5611", 250_000_000, PeriodoICA(2026, "bimestral", 3)),
        "ICA-06": estimar_ica("6201", 900_000_000, PeriodoICA(2027)),
    }
    for id_, est in casos.items():
        assert pesos(est.impuesto) in por_id[id_]["respuesta_referencia"], id_
    assert (
        pesos(estimar_ica("6201", 900_000_000, PeriodoICA(2026)).impuesto)
        in (por_id["ICA-06"]["respuesta_referencia"])
    )
    acc = por_id["ACC-04"]["respuesta_referencia"]
    assert "9,66" in acc and "10 por mil" in acc
    assert pesos(umbral_ica_pesos(2026)) in por_id["ICA-03"]["respuesta_referencia"]


@pytest.mark.unit
@pytest.mark.req("RF-ICA-03 · Fechas de declaración")
def test_los_servicios_coinciden_con_las_referencias_de_fechas(por_id) -> None:
    for fecha in fechas_ica(2026, "bimestral"):
        assert dia_y_mes(fecha) in por_id["ICA-07"]["respuesta_referencia"], fecha
    assert fecha_larga(fechas_ica(2026, "anual")[0]) in por_id["ICA-08"]["respuesta_referencia"]
    predial = fechas_predial(2026)
    assert fecha_larga(predial["pronto_pago"]) in por_id["IPU-07"]["respuesta_referencia"]
    assert fecha_larga(predial["sin_descuento"]) in por_id["IPU-08"]["respuesta_referencia"]
    for cuota in predial["spac_cuotas"][2:]:
        assert dia_y_mes(cuota) in por_id["IPU-15"]["respuesta_referencia"]


@pytest.mark.unit
@pytest.mark.req("RF-IPU-02 · Estado de cuenta e historial")
def test_las_referencias_con_usuarios_coinciden_con_usuarios_prueba_yaml(por_id) -> None:
    def valor(usuario: str, predio: int = 0, clave: str = "valor") -> str:
        return pesos(USUARIOS[usuario]["predios"][predio]["ipu_2026"][clave])

    def saldo(usuario: str, predio: int = 0) -> str:
        return pesos(USUARIOS[usuario]["predios"][predio]["estado_cuenta"]["saldo"])

    def obligaciones(usuario: str, predio: int, estado: str) -> list[str]:
        return [
            pesos(o["valor"])
            for o in USUARIOS[usuario]["predios"][predio]["obligaciones"]
            if o["estado"] == estado
        ]

    pagos_u03 = USUARIOS["U03"]["predios"][0]["pagos"]
    esperados = {
        "IPU-01": [saldo("U03"), *obligaciones("U03", 0, "VENCIDO")],
        "IPU-02": [saldo("U02", 1), *obligaciones("U02", 1, "VENCIDO")],
        "IPU-03": [pesos(p["valor"]) for p in pagos_u03]
        + [fecha_larga(p["fecha"]) for p in pagos_u03],
        "IPU-14": [saldo("U02", 1)],
        "IPU-15": [saldo("U08"), pesos(845_000)],
        "MULTI-01": [pesos(USUARIOS["U04"]["predios"][0]["estado_cuenta"]["saldo"]),
                     valor("U04")],
        "AMB-02": [saldo("U02", 1), valor("U02", 1)],
        "OCR-01": [valor("U03"), valor("U03", clave="descuento"),
                   pesos(USUARIOS["U03"]["predios"][0]["avaluo_2026"])],
        "OCR-02": [valor("U01"), valor("U01", clave="descuento")],
        "OCR-03": [valor("U06"), valor("U06", clave="descuento")],
        "OCR-07": [valor("U03"), saldo("U03")],
        "ICA-05": [pesos(USUARIOS["U04"]["predios"][0]["estado_cuenta"]["saldo"])],
        "MULTI-02": [valor("U12", clave="valor_pagado")],
    }  # fmt: skip
    for id_, valores in esperados.items():
        for v in valores:
            assert v in por_id[id_]["respuesta_referencia"], (id_, v)
    referencia_pagos = por_id["IPU-03"]["respuesta_referencia"].lower()
    assert all(p["medio"].lower() in referencia_pagos for p in pagos_u03)
    assert USUARIOS["U02"]["predios"][0]["estado_cuenta"]["saldo"] == 0
    assert "al día (saldo $0)" in por_id["IPU-02"]["respuesta_referencia"]


@pytest.mark.unit
@pytest.mark.req("RF-IPU-03 · Liquidación estimada")
def test_las_verificaciones_de_valores_estan_en_la_referencia(escenarios) -> None:
    for e in escenarios:
        if e["respuesta_referencia"].startswith("PENDIENTE"):
            continue
        for v in e["verificaciones_codigo"]:
            if v["tipo"] in ("contiene_valor",) and e["grupo"] != "ocr":
                assert v["valor"] in e["respuesta_referencia"], (e["id"], v["valor"])


# -- Hoja de revisión, índice y aprobación -------------------------------------------------------


@pytest.mark.unit
@pytest.mark.req("RNF-16 · Tasa de respuestas correctas")
def test_la_hoja_y_el_indice_estan_al_dia(escenarios) -> None:
    assert HOJA_REVISION.read_text("utf-8") == hoja_de_revision(escenarios)
    assert INDICE.read_text("utf-8") == indice(escenarios)
    resultado = subprocess.run(
        [sys.executable, str(RAIZ / "scripts/generar_hoja_escenarios.py"), "--verificar"],
        capture_output=True, text=True, check=False,
    )  # fmt: skip
    assert resultado.returncode == 0, resultado.stderr


@pytest.mark.unit
@pytest.mark.req("RNF-16 · Tasa de respuestas correctas")
def test_la_hoja_empieza_por_la_adenda_y_los_ca(escenarios) -> None:
    filas = [
        f for f in hoja_de_revision(escenarios).splitlines()
        if f.startswith("| ") and not f.startswith("| ID")
    ]  # fmt: skip
    primeras = [f.split(" | ")[0].removeprefix("| ") for f in filas[:19]]
    assert primeras[:2] == ["AIA-01", "AIA-02"]
    origenes = [f.split(" | ")[2] for f in filas[:19]]
    assert all(("adenda" in o) or ("CA-" in o) for o in origenes)
    assert not any(
        ("adenda" in f.split(" | ")[2]) or ("CA-" in f.split(" | ")[2]) for f in filas[19:]
    )


@pytest.mark.unit
@pytest.mark.req("RNF-16 · Tasa de respuestas correctas")
def test_aprobar_llena_aprobado_por_sin_tocar_el_resto_ni_los_pendientes(tmp_path) -> None:
    copia = tmp_path / "escenarios"
    copia.mkdir()
    for ruta in DIR_ESCENARIOS.glob("*.yaml"):  # copia sin aprobar, como antes de la parada
        sin_aprobar = re.sub(
            r"^aprobado_por:.*$", "aprobado_por: ''", ruta.read_text("utf-8"), flags=re.M
        )
        (copia / ruta.name).write_text(sin_aprobar, encoding="utf-8")
    pendiente = copia / "OCR-04.yaml"  # se simula una referencia sin fuente
    datos = yaml.safe_load(pendiente.read_text("utf-8"))
    datos["respuesta_referencia"] = "PENDIENTE: falta la fuente"
    datos["pendiente"] = ["Falta la fuente del motivo del rechazo."]
    pendiente.write_text(yaml.safe_dump(datos, allow_unicode=True, sort_keys=False), "utf-8")
    originales = {p.name: p.read_text("utf-8") for p in copia.glob("*.yaml")}
    aprobados, excluidos, pendientes = aprobar_referencias(
        "Rodolfo Angel Gilart Pulido", frozenset({"IPU-04"}), directorio=copia
    )
    assert excluidos == ["IPU-04"] and pendientes == ["OCR-04"] and "IPU-04" not in aprobados
    assert len(aprobados) + len(excluidos) + len(pendientes) == 60
    for ruta in copia.glob("*.yaml"):
        nuevo = yaml.safe_load(ruta.read_text("utf-8"))
        id_ = nuevo["id"]
        if id_ in aprobados:
            assert nuevo["aprobado_por"] == "Rodolfo Angel Gilart Pulido"
            sin_linea = [
                linea for linea in ruta.read_text("utf-8").splitlines()
                if not linea.startswith("aprobado_por:")
            ]  # fmt: skip
            original = [
                linea for linea in originales[ruta.name].splitlines()
                if not linea.startswith("aprobado_por:")
            ]  # fmt: skip
            assert sin_linea == original, id_  # solo cambió esa línea
        else:
            assert nuevo["aprobado_por"] == "" and ruta.read_text("utf-8") == originales[ruta.name]
    with pytest.raises(ValueError):
        aprobar_referencias("", directorio=copia)
    with pytest.raises(ValueError):
        aprobar_referencias("X", frozenset({"NO-99"}), directorio=copia)


# -- Conjunto de enrutamiento --------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.req("RF-ORQ-01 · Clasificación de la consulta")
def test_el_conjunto_de_enrutamiento_son_100_consultas_20_por_categoria() -> None:
    consultas = cargar_enrutamiento()
    assert validar_enrutamiento(consultas) == []
    por_categoria = {c: sum(1 for q in consultas if q["categoria"] == c) for c in
                     ("ipu", "ica", "general", "ocr", "fuera_de_alcance")}  # fmt: skip
    assert set(por_categoria.values()) == {20}
    tipos = [q["adjunto"]["tipo"] for q in consultas if q["categoria"] == "ocr"]
    assert set(tipos) == {"recibo_sintetico", "otro_documento"}
    assert tipos.count("otro_documento") == 2


@pytest.mark.unit
@pytest.mark.req("RF-ORQ-01 · Clasificación de la consulta")
def test_el_validador_de_enrutamiento_rechaza_conjuntos_incorrectos() -> None:
    consultas = cargar_enrutamiento()
    assert validar_enrutamiento(consultas[:-1])
    repetido = copy.deepcopy(consultas)
    repetido[1]["texto"] = repetido[0]["texto"]
    assert any("texto repetido" in e for e in validar_enrutamiento(repetido))
    sin_adjunto = copy.deepcopy(consultas)
    next(c for c in sin_adjunto if c["categoria"] == "ocr").pop("adjunto")
    assert any("adjunto" in e for e in validar_enrutamiento(sin_adjunto))
    con_adjunto = copy.deepcopy(consultas)
    next(c for c in con_adjunto if c["categoria"] == "ipu")["adjunto"] = {
        "tipo": "recibo_sintetico"
    }
    assert any("adjunto" in e for e in validar_enrutamiento(con_adjunto))
    mala = copy.deepcopy(consultas)
    mala[0]["categoria"] = "vehiculos"
    assert any("categoria" in e for e in validar_enrutamiento(mala))


@pytest.mark.unit
@pytest.mark.req("RF-ORQ-01 · Clasificación de la consulta")
def test_el_clasificador_simulado_acierta_las_consultas_inequivocas() -> None:
    """Chequeo de cordura del conjunto: el clasificador por palabras de B4 no es el de B7."""
    from src.agents.nodes.orquestador import clasificar_por_palabras

    consultas = cargar_enrutamiento()
    claras = [q for q in consultas if q["categoria"] in ("ocr", "fuera_de_alcance")]
    aciertos = 0
    for q in claras:
        estado = {"documento_adjunto": q.get("adjunto"), "contribuyente_id": "CC-1"}
        partes = clasificar_por_palabras(q["texto"], estado).partes  # type: ignore[arg-type]
        aciertos += partes[0]["categoria"] == q["categoria"]
    assert aciertos / len(claras) >= 0.4  # solo detecta que las etiquetas no son absurdas


CA_LITERAL = {
    "CA-01": (
        "un contribuyente sintético autenticado, con un predio que tiene obligaciones pendientes",
        "pregunta por el estado de cuenta de ese predio",
        "el sistema informa el saldo pendiente y las obligaciones por vigencia con su estado, "
        "iguales a los que devuelve el adaptador para ese predio",
    ),
    "CA-02": (
        "un contribuyente autenticado que se identifica con su cédula o NIT",
        "pide su estado de cuenta",
        "el sistema obtiene sus predios mediante el adaptador y responde solo sobre ellos",
    ),
    "CA-03": (
        "el mismo contribuyente de CA-01",
        "pide su historial de pagos",
        "el sistema lista los pagos registrados con su fecha, valor y medio de pago, iguales a los "
        "del adaptador, sin modificar ningún dato (RF-SYS-02)",
    ),
    "CA-04": (
        "un contribuyente autenticado",
        "consulta un predio con una matrícula catastral válida que no le pertenece",
        "el sistema rechaza la consulta con un mensaje explícito, no revela ningún dato del predio "
        "y no escala el caso (RF-AUT-02)",
    ),
    "CA-05": (
        "una sesión sin autenticar",
        "se pide el estado de cuenta de un predio",
        "el sistema no entrega datos e indica que se debe iniciar sesión en la Oficina Virtual "
        "Tributaria (RF-AUT-04)",
    ),
    "CA-06": (
        "el adaptador de datos no responde dentro del tiempo máximo de espera",
        "el agente consulta el estado de cuenta",
        "el sistema no muestra un error técnico y deriva la consulta al escalamiento (RNF-08)",
    ),
}  # Tabla 11 del documento de grado, «Criterios de aceptación del requerimiento RF-IPU-02»


@pytest.mark.unit
@pytest.mark.req("RF-IPU-02 · Estado de cuenta e historial")
def test_los_criterios_ca_van_literales_en_su_escenario(escenarios) -> None:
    for e in escenarios:
        for ca in (o for o in e["origen"] if o.startswith("CA-")):
            gcd = e["dado_cuando_entonces"]
            assert (gcd["dado"], gcd["cuando"], gcd["entonces"]) == CA_LITERAL[ca], e["id"]
    texto = " ".join(str(e) for e in escenarios) + HOJA_REVISION.read_text("utf-8")
    assert "no está en el repositorio" not in texto


@pytest.mark.unit
@pytest.mark.req("RNF-07 · Aviso fuera de horario")
def test_los_de_horario_van_sin_categoria_y_dicen_cuando_se_vuelve_a_atender(por_id) -> None:
    from datetime import datetime

    from src.services.horario import DIAS, MESES, Horario

    for id_ in ("HOR-01", "HOR-02"):
        e = por_id[id_]
        assert e["categoria_esperada"] is None
        apertura = Horario().proxima_apertura(datetime.fromisoformat(e["reloj"]))
        cuando = (
            f"{DIAS[apertura.weekday()]} {apertura.day} de {MESES[apertura.month - 1]} de "
            f"{apertura.year} a las 8:00 a. m."
        )
        assert cuando in e["respuesta_referencia"], (id_, cuando)
    otro = copy.deepcopy(por_id["IPU-04"])
    otro["categoria_esperada"] = None
    assert validar_escenario(otro)  # fuera de horario, nadie más va sin categoría


@pytest.mark.unit
@pytest.mark.req("RF-ORQ-01 · Clasificación de la consulta")
def test_la_regla_de_categorias_esta_escrita_y_se_cumple() -> None:
    texto = (RAIZ / "tests/componentes/enrutamiento.yaml").read_text("utf-8")
    assert "Regla de categorías" in texto and "glosario" in texto
    consultas = {q["id"]: q for q in cargar_enrutamiento()}
    assert consultas["ENR-GEN05"]["texto"] == "¿Qué es el SPAC?"
    assert consultas["ENR-GEN05"]["categoria"] == "general"  # definición del glosario
    ipu10 = consultas["ENR-IPU10"]
    assert "sobretasa" in ipu10["texto"] and "2027" in ipu10["texto"]  # cálculo: su agente
    definiciones = [q for q in consultas.values() if q["texto"].startswith("¿Qué es la sobretasa")]
    assert all(q["categoria"] == "general" for q in definiciones)


@pytest.mark.unit
@pytest.mark.req("RNF-05 · Registro auditable")
def test_los_mensajes_del_contribuyente_no_llevan_numeros_de_documento(escenarios) -> None:
    """La identificación la da la sesión; un documento en el texto iría al modelo y a las trazas."""
    import re

    documento = re.compile(r"\b(CC|CE|NIT)[-\s]?\d{6,}|\b\d{8,10}\b", re.IGNORECASE)
    for e in escenarios:
        for turno in e["turnos"]:
            assert not documento.search(turno["usuario"]), (e["id"], turno["usuario"])
    for consulta in cargar_enrutamiento():
        assert not documento.search(consulta["texto"]), consulta["id"]


@pytest.mark.unit
@pytest.mark.req("RNF-16 · Tasa de respuestas correctas")
def test_las_verificaciones_de_texto_no_dependen_de_la_forma_de_escribir() -> None:
    from src.evaluacion.escenarios import contiene, normalizar_texto

    assert contiene("Tienes un descuento del 10% hasta el 17 de abril", "10 %")
    assert contiene("Se causa el 1 de enero", "1° de enero")
    assert contiene("SE CAUSA EL 1º DE ENERO", "1° de enero")
    assert contiene("el regimen comun", "régimen común")
    assert not contiene("el 11 de julio", "1 de julio")  # no confunde fechas parecidas
    assert normalizar_texto("  Hola\n  Mundo ") == "hola mundo"


@pytest.mark.unit
@pytest.mark.req("RNF-16 · Tasa de respuestas correctas")
def test_el_validador_cuida_la_aprobacion_las_categorias_y_los_adjuntos(por_id) -> None:
    pendiente_aprobado = copy.deepcopy(por_id["IPU-04"])
    pendiente_aprobado["respuesta_referencia"] = "PENDIENTE: falta la fuente"
    pendiente_aprobado["pendiente"] = ["falta la fuente"]
    assert any("no puede estar aprobado" in e for e in validar_escenario(pendiente_aprobado))
    multi = copy.deepcopy(por_id["MULTI-01"])
    multi["categoria_esperada"] = "general"
    assert any("categorias_esperadas" in e for e in validar_escenario(multi))
    ocr = copy.deepcopy(por_id["OCR-01"])
    ocr["adjunto"]["calidad"] = "borrosa"
    assert validar_escenario(ocr)
    fuentes = copy.deepcopy(por_id["IPU-04"])
    fuentes["fuentes_esperadas"] = "Ley 44 de 1990"
    assert validar_escenario(fuentes)
    assert por_id["ROB-01"]["categoria_esperada"] is None  # falla del orquestador: sin clasificar
    alternativas = copy.deepcopy(por_id["GEN-01"])
    alternativas["categorias_aceptadas"] = ["general", "fuera_de_alcance"]
    alternativas["comportamientos_aceptados"] = ["responder", "informar_fuera_de_alcance"]
    assert not validar_escenario(alternativas)
    sin_principal = copy.deepcopy(alternativas)
    sin_principal["categorias_aceptadas"] = ["fuera_de_alcance"]
    assert any("categorias_aceptadas" in e for e in validar_escenario(sin_principal))
    desconocido = copy.deepcopy(alternativas)
    desconocido["comportamientos_aceptados"] = ["responder", "adivinar"]
    assert any("comportamientos_aceptados" in e for e in validar_escenario(desconocido))


@pytest.mark.unit
@pytest.mark.req("RNF-16 · Tasa de respuestas correctas")
def test_aprobar_borra_una_aprobacion_vieja_si_queda_pendiente_o_excluido(tmp_path) -> None:
    copia = tmp_path / "escenarios"
    copia.mkdir()
    for nombre in ("IPU-04.yaml", "IPU-05.yaml"):
        texto = (DIR_ESCENARIOS / nombre).read_text("utf-8")
        texto = re.sub(r"^aprobado_por:.*$", 'aprobado_por: "Alguien"', texto, flags=re.M)
        (copia / nombre).write_text(texto, encoding="utf-8")
    datos = yaml.safe_load((copia / "IPU-05.yaml").read_text("utf-8"))
    datos["respuesta_referencia"] = "PENDIENTE: falta la fuente"
    datos["pendiente"] = ["falta la fuente"]
    (copia / "IPU-05.yaml").write_text(yaml.safe_dump(datos, allow_unicode=True), "utf-8")
    aprobados, excluidos, pendientes = aprobar_referencias(
        "Rodolfo Angel Gilart Pulido", frozenset({"IPU-04"}), directorio=copia
    )
    assert (aprobados, excluidos, pendientes) == ([], ["IPU-04"], ["IPU-05"])
    for nombre in ("IPU-04.yaml", "IPU-05.yaml"):
        assert yaml.safe_load((copia / nombre).read_text("utf-8"))["aprobado_por"] == ""
