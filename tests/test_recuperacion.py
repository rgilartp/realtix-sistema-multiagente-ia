"""B8: segmentación, ingesta idempotente y recuperación híbrida (Chroma + BM25 + RRF).

Las unitarias usan embeddings falsos y deterministas y un Chroma en proceso; las de integración, el
Chroma de Compose. Las que usan los embeddings reales de OpenAI solo corren con
`REALTIX_PRUEBAS_REALES=1` y la base ya ingerida (`scripts/ingestar.py`).
"""

import os
import re
import shutil
import uuid
from pathlib import Path

import chromadb
import numpy as np
import pytest
from langchain_chroma import Chroma

from src.agents.agente import ConfigAgente, ejecutar_agente
from src.agents.dependencias import Dependencias
from src.agents.graph import configuracion_de_hilo
from src.agents.herramientas.ipu import HERRAMIENTAS_IPU
from src.agents.prompts import prompt_de_agente
from src.agents.state import entrada_de_turno
from src.integrations.ingesta import CLAVE_VERSION, ingestar
from src.integrations.recuperacion_hibrida import (
    K_CANAL,
    RecuperadorHibrido,
    filtro_de_vigencia,
    fusion_rrf,
)
from src.integrations.recuperador import RAIZ_BASE
from src.integrations.segmentacion import (
    MAX_TOKENS,
    SIN_FIN,
    SIN_INICIO,
    contar_tokens,
    partir,
    segmentar_base,
    version_del_corpus,
)
from tests.ayudas_chroma import cliente_chroma_compose
from tests.embeddings_falsos import EmbeddingsFalsos
from tests.modelo_falso import ModeloFalso, final

REALES = os.environ.get("REALTIX_PRUEBAS_REALES") == "1"
CON_NOTA_DE_VIGENCIA = (
    "normativa_ica/acuerdo_65_2002.md",
    "normativa_ica/acuerdo_98_2003.md",
    "normativa_ipu/acuerdo_105_2003.md",
    "normativa_ipu/acuerdo_648_2016.md",
    "normativa_ipu/acuerdo_780_2020.md",
    "normativa_ica/acuerdo_1019_2025_ica.md",
    "normativa_ica/acuerdo_1084_2026_ica.md",
)
METADATOS = {"norma", "articulo", "coleccion", "url", "vigencia_desde", "vigencia_hasta",
             "archivo", "parte", "texto_anterior", "hash"}  # fmt: skip
NORMA_NUEVA = """# Resolución de ejemplo 001 de 2026

Fuente: https://ejemplo.invalid/resolucion-001 (consultada en octubre de 2026)

## Artículo 1

Artículo 1. Calendario de pruebas. Los contribuyentes del predial de ejemplo pagan la cuota
única de ejemplo a más tardar el quinto día hábil de diciembre de 2026.
"""


@pytest.fixture(scope="module")
def fragmentos():
    return segmentar_base()


@pytest.fixture(scope="module")
def base_falsa():
    """Chroma en proceso con toda la base ingerida con embeddings falsos (un prefijo por módulo)."""
    cliente = chromadb.EphemeralClient()
    embeddings = EmbeddingsFalsos()
    prefijo = f"p{uuid.uuid4().hex[:8]}_"
    reportes = ingestar(cliente, embeddings, prefijo=prefijo)
    return cliente, embeddings, prefijo, reportes


def recuperador_de(base) -> RecuperadorHibrido:
    cliente, embeddings, prefijo, _ = base
    return RecuperadorHibrido(cliente, embeddings, prefijo=prefijo)


# -- Segmentación ---------------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.req("RF-IPU-05 · Citación de la norma")
def test_un_fragmento_por_articulo_con_los_metadatos_de_la_seccion_5_2(fragmentos) -> None:
    todos = [f for lista in fragmentos.values() for f in lista]
    assert set(fragmentos) == {"normativa_ipu", "normativa_ica", "normativa_datos",
                               "plataforma_general"}  # fmt: skip
    for f in todos:
        assert set(f.metadatos) == METADATOS, f.id
        assert f.metadatos["norma"], f.id
        if (
            f.metadatos["coleccion"] != "plataforma_general"
        ):  # el manual y el glosario son sintéticos
            assert f.metadatos["url"].startswith("http"), f.id
        assert contar_tokens(f.texto) <= MAX_TOKENS, f.id
    # La Ley 44 de 1990 tiene 30 artículos cortos: 30 fragmentos, uno por artículo.
    ley_44 = [
        f for f in fragmentos["normativa_ipu"] if f.metadatos["archivo"].endswith("ley_44_1990.md")
    ]
    assert len(ley_44) == 30 and {f.metadatos["parte"] for f in ley_44} == {1}
    assert len({f.id for f in todos}) == len(todos)


@pytest.mark.unit
@pytest.mark.req("RF-IPU-04 · Plazos y descuentos", "RF-ICA-03 · Fechas de declaración")
def test_la_nota_de_vigencia_va_en_cada_fragmento_de_su_archivo(fragmentos) -> None:
    todos = [f for lista in fragmentos.values() for f in lista]
    for archivo in CON_NOTA_DE_VIGENCIA:
        del_archivo = [f for f in todos if f.metadatos["archivo"] == archivo]
        assert del_archivo, archivo
        assert all("**Vigencia por año gravable.**" in f.texto for f in del_archivo), archivo


@pytest.mark.unit
@pytest.mark.req(
    "RF-ICA-01 · Consultas conceptuales de ICA", "RF-IPU-01 · Consultas conceptuales de IPU"
)
def test_los_textos_anteriores_van_aparte_con_su_vigencia(fragmentos) -> None:
    def de(archivo: str, articulo: str) -> list:
        todos = [f for lista in fragmentos.values() for f in lista]
        m = [(f, f.metadatos) for f in todos]
        return [f for f, d in m if d["archivo"] == archivo and d["articulo"] == articulo]

    acuerdo_65 = de("normativa_ica/acuerdo_65_2002.md", "Artículo 3")
    vigente = [f for f in acuerdo_65 if not f.metadatos["texto_anterior"]]
    anterior = [f for f in acuerdo_65 if f.metadatos["texto_anterior"]]
    assert vigente and anterior
    assert {f.metadatos["vigencia_desde"] for f in vigente} == {20261101}
    assert {f.metadatos["vigencia_hasta"] for f in anterior} == {20261231}
    con_filas = [f for f in vigente if re.search(r"^\|.*\| \d+ \|", f.texto, re.MULTILINE)]
    assert len(con_filas) > 1  # la tabla de tarifas se partió y cada parte repite su encabezado
    encabezado = re.compile(r"^\| Actividad \| CIIU \|.*\|\n\|---", re.MULTILINE)
    assert all(encabezado.search(f.texto) for f in con_filas)
    # Texto nuevo del art. 2 del Acuerdo 105: desde 2027; su texto original de 2003 no rige.
    acuerdo_105 = de("normativa_ipu/acuerdo_105_2003.md", "Artículo 2")
    assert {
        f.metadatos["vigencia_desde"] for f in acuerdo_105 if not f.metadatos["texto_anterior"]
    } == {20270101}
    assert {
        f.metadatos["vigencia_hasta"] for f in acuerdo_105 if f.metadatos["texto_anterior"]
    } == {SIN_INICIO}
    # Secciones marcadas «Texto anterior, no vigente» (Ley 14, arts. 33 y 36).
    for articulo in ("Artículo 33", "Artículo 36"):
        (ley_14,) = de("normativa_ica/ley_14_1983.md", articulo)
        assert (
            ley_14.metadatos["texto_anterior"] and ley_14.metadatos["vigencia_hasta"] == SIN_INICIO
        )
        assert "(texto anterior, no vigente)" in ley_14.texto.splitlines()[0]
    # Decreto 807, art. 12: tras cada numeral reemplazado sigue el texto vigente (revisión de B8).
    art_12 = de("normativa_ipu/decreto_807_1993_ipu.md", "Artículo 12")
    vigente_12 = "\n".join(f.texto for f in art_12 if not f.metadatos["texto_anterior"])
    anterior_12 = "\n".join(f.texto for f in art_12 if f.metadatos["texto_anterior"])
    assert "3. Declaración mensual del impuesto al consumo sobre la producción" in vigente_12
    assert "Parágrafo 1º" in vigente_12 and "Adicionado por el art.2, Decreto 349" in vigente_12
    assert (
        "2. Declaración bimestral del impuesto de industria y comercio, avisos y tableros."
        in anterior_12
    )
    assert "Artículo 12. Declaraciones tributarias. A partir del 1° de enero de 1994" in anterior_12
    assert "<El nuevo texto es el siguiente>" not in anterior_12
    # Un artículo adicionado después del texto original del artículo es vigente (art. 11-1).
    art_11 = de("normativa_ipu/decreto_807_1993_ipu.md", "Artículo 11")
    assert "Artículo 11-1" in "\n".join(
        f.texto for f in art_11 if not f.metadatos["texto_anterior"]
    )
    # Un artículo sin regla rige siempre.
    (art_4,) = de("normativa_ipu/ley_44_1990.md", "Artículo 4")
    assert (art_4.metadatos["vigencia_desde"], art_4.metadatos["vigencia_hasta"]) == (
        SIN_INICIO,
        SIN_FIN,
    )


MARCA_DE_TEXTO_ANTERIOR = re.compile(r"\bera(?:n)? el siguiente\b", re.IGNORECASE)


@pytest.mark.unit
@pytest.mark.req("RF-IPU-05 · Citación de la norma", "RF-GEN-03 · Respuesta sustentada en fuentes")
def test_ningun_fragmento_vigente_trae_un_texto_anterior_o_derogado(fragmentos) -> None:
    """Revisión externa: toda «… era el siguiente» de la base (párrafo suelto o marca `<…>`
    dentro de un párrafo) abre un texto anterior; si falta una variante, esta prueba falla."""
    sin_reconocer = [
        f.id
        for lista in fragmentos.values()
        for f in lista
        if not f.metadatos["texto_anterior"] and MARCA_DE_TEXTO_ANTERIOR.search(f.texto)
    ]
    assert sin_reconocer == []


@pytest.mark.unit
@pytest.mark.req("RF-IPU-04 · Plazos y descuentos", "RF-IPU-05 · Citación de la norma")
def test_los_textos_derogados_no_rigen(fragmentos) -> None:
    todos = [f for lista in fragmentos.values() for f in lista]

    def de(archivo: str, articulo: str, anterior: bool) -> str:
        return "\n".join(
            f.texto
            for f in todos
            if f.metadatos["archivo"] == archivo
            and f.metadatos["articulo"] == articulo
            and f.metadatos["texto_anterior"] is anterior
        )

    # Acuerdo 648, art. 1: los topes de aumento, derogados por el Acuerdo 927 de 2024.
    acuerdo_648 = [
        f
        for f in todos
        if f.metadatos["archivo"] == "normativa_ipu/acuerdo_648_2016.md"
        and f.metadatos["articulo"] == "Artículo 1"
    ]
    vigente = de("normativa_ipu/acuerdo_648_2016.md", "Artículo 1", anterior=False)
    anterior = de("normativa_ipu/acuerdo_648_2016.md", "Artículo 1", anterior=True)
    for tope in ("20%", "15%", "10%", "18%", "Índice de Precios al Consumidor"):
        assert tope in anterior and tope not in vigente
    assert "| 1 y 2 | 16 smlmv | 107 smlmv | 1 por mil |" in vigente  # las tarifas siguen
    assert "IPVN" in vigente
    assert {
        (f.metadatos["vigencia_desde"], f.metadatos["vigencia_hasta"])
        for f in acuerdo_648
        if f.metadatos["texto_anterior"]
    } == {(SIN_INICIO, SIN_INICIO)}
    # Ley 14, art. 4: la marca va dentro del párrafo; el artículo entero es anterior.
    assert "Derogado por el art. 336, Ley 1955 de 2019." in de(
        "normativa_ica/ley_14_1983.md", "Artículo 4", anterior=False
    )
    ley_14 = de("normativa_ica/ley_14_1983.md", "Artículo 4", anterior=True)
    assert "A partir del 1 de enero de 1984" in ley_14
    assert "Los terrenos y las edificaciones" in ley_14
    # Decreto 807, art. 24: «El texto derogado era el siguiente» y el artículo entero.
    assert "Artículo 24. Firmeza de la Declaración Privada" in de(
        "normativa_ipu/decreto_807_1993_ipu.md", "Artículo 24", anterior=True
    )
    assert "Firmeza de la Declaración Privada" not in de(
        "normativa_ipu/decreto_807_1993_ipu.md", "Artículo 24", anterior=False
    )


@pytest.mark.unit
@pytest.mark.req("RF-IPU-05 · Citación de la norma")
def test_un_texto_largo_se_parte_con_solape_y_uno_corto_queda_entero() -> None:
    corto = "Artículo corto."
    assert partir(corto) == [corto]
    largo = "\n\n".join(f"Párrafo {i}: " + "palabra " * 120 for i in range(12))
    trozos = partir(largo)
    assert len(trozos) > 1 and all(contar_tokens(t) <= MAX_TOKENS for t in trozos)
    for anterior, siguiente in zip(trozos, trozos[1:], strict=False):
        primero = siguiente.split("\n\n")[0]  # el solape: el final del trozo anterior
        assert anterior.endswith(primero.removeprefix("[…] ")) or primero in anterior
        assert 50 <= contar_tokens(primero.removeprefix("[…] ")) <= 100


# -- Fusión, coseno y canales -------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.req("RF-IPU-01 · Consultas conceptuales de IPU")
def test_fusion_rrf_con_k_60() -> None:
    fusion = fusion_rrf([["a", "b"], ["b", "c"]])
    assert [id_ for id_, _ in fusion] == ["b", "a", "c"]
    assert fusion[0][1] == pytest.approx(1 / 62 + 1 / 61)
    assert fusion[1][1] == pytest.approx(1 / 61)


@pytest.mark.unit
@pytest.mark.req("RF-IPU-05 · Citación de la norma")
@pytest.mark.parametrize(
    ("consulta", "archivo"),
    [("Ley 44 de 1990", "ley_44_1990.md"), ("artículo 354", "ley_1819_2016.md")],
)
def test_los_identificadores_literales_llegan_primero_por_bm25(
    base_falsa, consulta, archivo
) -> None:
    recuperador = recuperador_de(base_falsa)
    bm25 = recuperador._canal_bm25("normativa_ipu", consulta, 2026)
    assert archivo in bm25[0] and len(bm25) <= K_CANAL
    fusion = recuperador.recuperar(consulta, coleccion="normativa_ipu", anio=2026)
    assert any(f.fuente.endswith(archivo) for f in fusion)


class EmbeddingsSinNormalizar(EmbeddingsFalsos):
    """Como los falsos, pero con una norma distinta por texto: así 1 - d²/2 no da el coseno."""

    def _vector(self, texto: str) -> list[float]:
        return [x * (1 + len(texto) % 7) for x in super()._vector(texto)]


@pytest.mark.unit
@pytest.mark.req("RF-ESC-01 · Cálculo del nivel de confianza")
def test_el_coseno_coincide_con_numpy_tambien_para_lo_que_solo_trae_bm25() -> None:
    cliente, embeddings = chromadb.EphemeralClient(), EmbeddingsSinNormalizar()
    prefijo = f"c{uuid.uuid4().hex[:8]}_"
    ingestar(cliente, embeddings, prefijo=prefijo)
    recuperador = RecuperadorHibrido(cliente, embeddings, prefijo=prefijo)
    consulta = "artículo 354"
    vector = recuperador._canal_vectorial("normativa_ipu", embeddings.embed_query(consulta), 2026)
    fragmentos = recuperador.recuperar(consulta, coleccion="normativa_ipu", anio=2026)
    solo_bm25 = [f for f in fragmentos if f.id not in vector]
    assert any(f.fuente.endswith("ley_1819_2016.md") for f in solo_bm25)  # llegó solo por BM25
    q = np.array(embeddings.embed_query(consulta))
    for f in fragmentos:
        d = np.array(embeddings.embed_documents([f.texto])[0])
        assert f.similitud == pytest.approx(float(q @ d / (np.linalg.norm(q) * np.linalg.norm(d))))
        assert f.similitud != pytest.approx(1 - float(np.sum((q - d) ** 2)) / 2)


@pytest.mark.unit
@pytest.mark.req("RF-IPU-04 · Plazos y descuentos", "RF-ICA-03 · Fechas de declaración")
def test_el_filtro_por_vigencia_de_2026_y_2027(base_falsa) -> None:
    cliente, embeddings, prefijo, _ = base_falsa

    def ids(coleccion: str, anio: int) -> set[str]:
        tienda = Chroma(collection_name=f"{prefijo}{coleccion}", embedding_function=embeddings,
                        client=cliente)  # fmt: skip
        return set(tienda.get(where=filtro_de_vigencia(anio))["ids"])

    for anio in (2026, 2027):
        for coleccion in ("normativa_ipu", "normativa_ica"):
            anteriores = {i for i in ids(coleccion, anio) if "#anterior-" in i}
            permitidos = (
                {"acuerdo_65_2002.md", "acuerdo_1019_2025_ica.md"} if anio == 2026 else set()
            )
            assert {re.sub(r"#.*", "", i).split("/")[1] for i in anteriores} <= permitidos
    nuevo_105 = "normativa_ipu/acuerdo_105_2003.md#Artículo 2#vigente-1"
    assert nuevo_105 not in ids("normativa_ipu", 2026) and nuevo_105 in ids("normativa_ipu", 2027)
    ica_nuevo = "normativa_ica/acuerdo_65_2002.md#Artículo 3#vigente-1"
    assert ica_nuevo in ids("normativa_ica", 2026)  # bimestre 6 de 2026
    # Derogados por el Acuerdo 1084 que rigen solo en 2026, y tarifas de 2002 que no rigen.
    acuerdo_98 = "normativa_ica/acuerdo_98_2003.md#Artículo 1#vigente-1"
    assert acuerdo_98 in ids("normativa_ica", 2026) and acuerdo_98 not in ids("normativa_ica", 2027)
    tarifas_2002 = "normativa_ica/decreto_352_2002_cap2.md#Artículo 53#vigente-1"
    assert all(tarifas_2002 not in ids("normativa_ica", a) for a in (2026, 2027))
    # Sin año tampoco salen los textos que no rigen.
    sin_anio = ids("normativa_ipu", None)
    assert not [i for i in sin_anio if "decreto_807_1993_ipu.md#Artículo 12#anterior" in i]


# -- Ingesta ------------------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.req("RF-OBS-04 · Actualización de la base vectorial")
def test_la_reingesta_sin_cambios_no_calcula_embeddings(base_falsa) -> None:
    cliente, embeddings, prefijo, primera = base_falsa
    assert sum(r.embebidos for r in primera) == sum(r.fragmentos for r in primera) > 1000
    antes = embeddings.textos_embebidos
    segunda = ingestar(cliente, embeddings, prefijo=prefijo)
    assert embeddings.textos_embebidos == antes
    assert all(r.embebidos == 0 and r.borrados == 0 and r.costo_usd == 0 for r in segunda)
    coleccion = cliente.get_collection(f"{prefijo}normativa_ipu")
    assert coleccion.metadata[CLAVE_VERSION] == version_del_corpus()


@pytest.mark.unit
@pytest.mark.req("RF-OBS-04 · Actualización de la base vectorial")
def test_cambiar_una_vigencia_actualiza_ese_articulo_sin_volver_a_embeber(tmp_path) -> None:
    raiz = tmp_path / "knowledge_base"
    shutil.copytree(RAIZ_BASE, raiz)
    cliente, embeddings = chromadb.EphemeralClient(), EmbeddingsFalsos()
    prefijo = f"v{uuid.uuid4().hex[:8]}_"
    ingestar(cliente, embeddings, raiz, prefijo=prefijo)
    vigencias = raiz / "vigencias.yaml"
    texto = vigencias.read_text("utf-8").replace(
        "articulo: Artículo 20\n    vigente: {desde: 2027-01-01}",
        "articulo: Artículo 20\n    vigente: {desde: 2027-02-01}",
    )
    vigencias.write_text(texto, "utf-8")
    antes = embeddings.textos_embebidos
    reportes = ingestar(cliente, embeddings, raiz, prefijo=prefijo)
    ipu = next(r for r in reportes if r.coleccion == "normativa_ipu")
    clave = "normativa_ipu/acuerdo_1084_2026.md#Artículo 20#"
    del_art_20 = [f for f in segmentar_base(raiz)["normativa_ipu"] if f.id.startswith(clave)]
    # El texto no cambió: se actualizan los metadatos y se reutiliza el embedding, sin costo.
    assert ipu.reutilizados == len(del_art_20) > 0 and ipu.embebidos == 0
    assert sum(r.reutilizados for r in reportes) == ipu.reutilizados
    assert embeddings.textos_embebidos == antes
    tienda = Chroma(collection_name=f"{prefijo}normativa_ipu", embedding_function=embeddings,
                    client=cliente)  # fmt: skip
    metadatos = tienda.get(ids=[del_art_20[0].id])["metadatas"][0]
    assert metadatos["vigencia_desde"] == 20270201


def _base_con_norma_nueva(tmp_path: Path) -> Path:
    raiz = tmp_path / "knowledge_base"
    shutil.copytree(RAIZ_BASE, raiz)
    (raiz / "normativa_ipu" / "resolucion_ejemplo_001_2026.md").write_text(NORMA_NUEVA, "utf-8")
    return raiz


@pytest.mark.unit
@pytest.mark.req("RF-OBS-04 · Actualización de la base vectorial")
def test_un_documento_nuevo_se_ingiere_sin_cambiar_el_codigo_y_bm25_se_reconstruye(
    tmp_path,
) -> None:
    cliente, embeddings = chromadb.EphemeralClient(), EmbeddingsFalsos()
    prefijo = f"n{uuid.uuid4().hex[:8]}_"
    ingestar(cliente, embeddings, prefijo=prefijo)
    recuperador = RecuperadorHibrido(cliente, embeddings, prefijo=prefijo, ttl_version_s=0)
    consulta = "cuota única de ejemplo quinto día hábil de diciembre"
    antes = recuperador.recuperar(consulta, coleccion="normativa_ipu", anio=2026)
    assert not any("resolucion_ejemplo" in f.fuente for f in antes)
    construcciones = recuperador.reconstrucciones
    reportes = ingestar(cliente, embeddings, _base_con_norma_nueva(tmp_path), prefijo=prefijo)
    ipu = next(r for r in reportes if r.coleccion == "normativa_ipu")
    assert ipu.embebidos == 1 and sum(r.embebidos for r in reportes) == 1
    despues = recuperador.recuperar(consulta, coleccion="normativa_ipu", anio=2026)
    assert "resolucion_ejemplo_001_2026.md" in despues[0].fuente
    assert recuperador.reconstrucciones > construcciones  # la versión cambió: BM25 nuevo
    # Quitar el documento lo borra de Chroma.
    reportes = ingestar(cliente, embeddings, prefijo=prefijo)
    assert next(r for r in reportes if r.coleccion == "normativa_ipu").borrados == 1


# -- El agente con la recuperación híbrida ------------------------------------------------------


@pytest.mark.unit
@pytest.mark.req(
    "RF-IPU-01 · Consultas conceptuales de IPU", "RF-OBS-05 · Ejecución repetible de pruebas"
)
def test_en_modo_de_evaluacion_la_parte_guarda_contextos_y_version(
    base_falsa, datos_sinteticos
) -> None:
    from langchain_core.messages import AIMessage

    from src.data.memoria import RealSitEnMemoria

    modelo = ModeloFalso(
        [AIMessage(content="El predial…"), final("El predial…", fragmentos_citados=[1])]
    )
    deps = Dependencias(RealSitEnMemoria(datos_sinteticos), modelos=lambda _: modelo,
                        recuperador=recuperador_de(base_falsa), modo_evaluacion=True)  # fmt: skip
    estado = entrada_de_turno("¿Qué es el impuesto predial unificado?", "eval")
    estado["parte_actual"] = {"categoria": "ipu", "texto": "¿Qué es el impuesto predial unificado?"}
    agente = ConfigAgente("ipu", prompt_de_agente("ipu"), ("normativa_ipu",), HERRAMIENTAS_IPU)
    respuesta, _ = ejecutar_agente(agente, deps, estado, configuracion_de_hilo("eval"))
    assert len(respuesta["contextos"]) == 5
    assert respuesta["version_corpus"] == version_del_corpus()
    assert respuesta["similitud"] == pytest.approx(
        recuperador_de(base_falsa)
        .recuperar("¿Qué es el impuesto predial unificado?", coleccion="normativa_ipu", anio=2026)[
            0
        ]
        .similitud
    )


@pytest.mark.unit
@pytest.mark.req("RNF-08 · Tiempos de espera y degradación")
def test_si_chroma_no_responde_el_agente_reporta_fallo_de_servicio(datos_sinteticos) -> None:
    from src.data.memoria import RealSitEnMemoria

    class Caido:
        def recuperar(self, *_, **__):
            raise ConnectionError("Chroma no responde")

    deps = Dependencias(RealSitEnMemoria(datos_sinteticos), modelos=lambda _: ModeloFalso(),
                        recuperador=Caido())  # fmt: skip
    estado = entrada_de_turno("¿Qué es el predial?", "caido")
    agente = ConfigAgente("ipu", prompt_de_agente("ipu"), ("normativa_ipu",), HERRAMIENTAS_IPU)
    respuesta, _ = ejecutar_agente(agente, deps, estado, configuracion_de_hilo("caido"))
    assert respuesta["fallo_servicio"]


# -- Integración con el Chroma de Compose -------------------------------------------------------


@pytest.mark.integration
@pytest.mark.req("RF-OBS-04 · Actualización de la base vectorial")
def test_ingesta_y_recuperacion_con_el_chroma_de_compose(tmp_path) -> None:
    cliente = cliente_chroma_compose()
    raiz = tmp_path / "kb"
    for coleccion in ("normativa_ipu", "normativa_ica", "normativa_datos", "plataforma_general"):
        (raiz / coleccion).mkdir(parents=True)
    shutil.copy(RAIZ_BASE / "normativa_ipu" / "ley_44_1990.md", raiz / "normativa_ipu")
    shutil.copy(RAIZ_BASE / "normativa_ipu" / "fuentes.yaml", raiz / "normativa_ipu")
    (raiz / "normativa_ipu" / "resolucion_ejemplo_001_2026.md").write_text(NORMA_NUEVA, "utf-8")
    embeddings = EmbeddingsFalsos()
    prefijo = f"ci{uuid.uuid4().hex[:8]}_"
    try:
        primera = ingestar(cliente, embeddings, raiz, prefijo=prefijo)
        assert next(r for r in primera if r.coleccion == "normativa_ipu").embebidos == 31
        segunda = ingestar(cliente, embeddings, raiz, prefijo=prefijo)
        assert sum(r.embebidos for r in segunda) == 0
        recuperador = RecuperadorHibrido(cliente, embeddings, prefijo=prefijo)
        fragmentos = recuperador.recuperar("Ley 44 de 1990", coleccion="normativa_ipu", anio=2026)
        assert fragmentos and all(f.fuente.endswith("ley_44_1990.md") for f in fragmentos)
        assert recuperador.version_corpus == version_del_corpus(raiz)
    finally:
        for coleccion in cliente.list_collections():
            nombre = getattr(coleccion, "name", coleccion)
            if str(nombre).startswith(prefijo):
                cliente.delete_collection(str(nombre))


# -- Con los embeddings reales (la base ya ingerida en el Chroma local) --------------------------


@pytest.mark.integration
@pytest.mark.skipif(not REALES, reason="Usa embeddings reales: REALTIX_PRUEBAS_REALES=1")
@pytest.mark.req(
    "RF-IPU-01 · Consultas conceptuales de IPU",
    "RF-ICA-01 · Consultas conceptuales de ICA",
    "RF-GEN-01 · Consultas transversales",
)
@pytest.mark.parametrize(
    ("consulta", "coleccion", "esperada"),
    [
        ("¿Hasta cuándo se puede pagar el predial con descuento?", "normativa_ipu",
         "Resolución SDH-000195 de 2025"),
        pytest.param(
            "¿Cuánto puede subir el predial de un año a otro?", "normativa_ipu", "Ley 1995 de 2019",
            marks=pytest.mark.xfail(
                reason="Hallazgo de B8: con las palabras del contribuyente, el art. 2 de la Ley "
                "1995 no entra en los 5; por eso el agente recupera con la búsqueda del "
                "orquestador (caso siguiente; docs/resumenes/fix-recuperacion.md)",
                strict=True,
            ),
        ),
        # La búsqueda que escribe el orquestador en los términos de la norma (revisión externa).
        ("límite al aumento anual del impuesto predial", "normativa_ipu",
         "Ley 1995 de 2019, art. 2"),
        ("¿Quién paga el impuesto de industria y comercio?", "normativa_ica", "Ley 14 de 1983"),
        ("¿Cómo pago por cuotas el predial?", "plataforma_general", "SPAC"),
        ("¿Qué puedo pedir sobre mis datos personales?", "normativa_datos", "Ley 1581 de 2012"),
    ],
)  # fmt: skip
def test_consultas_semanticas_con_los_embeddings_reales(consulta, coleccion, esperada) -> None:
    from src.container import Contenedor

    fragmentos = Contenedor().recuperador.recuperar(consulta, coleccion=coleccion, anio=2026)
    assert any(esperada in f"{f.cita} {f.texto[:300]}" for f in fragmentos), [
        f.cita for f in fragmentos
    ]
