"""Regla contra el sobreajuste (ADR-24, A8) y conjuntos adicionales (R1, R3 y R4).

Ningún texto, pregunta ni cifra de los escenarios puede estar en los prompts ni en el código del
sistema multiagente de IA: una corrección debe ser general. Se revisan:
- las preguntas de los turnos (de 5 palabras o más: «Te envío mi recibo» es el mensaje por defecto
  de la API), en todo `src/` salvo el arnés de evaluación y el generador de datos sintéticos (que es
  de donde salen los valores de los usuarios de prueba);
- las secuencias de 8 palabras de las respuestas de referencia, en los prompts versionados;
- las cifras en pesos de $10.000 o más de las verificaciones y de las referencias, en los prompts y
  en `src/agents/` (las menores, como el «/ 1.000» del por mil, no son propias de un escenario).
"""

import re
from pathlib import Path

import pytest

from src.evaluacion.escenarios import (
    ARCHIVO_GENERALIZACION,
    RAIZ,
    cargar_adicionales,
    cargar_conjunto,
    cargar_escenarios,
    normalizar_texto,
    requerimientos_de_la_especificacion,
    validar_escenario,
    validar_generalizacion,
)

OBS05 = "RF-OBS-05 · Ejecución repetible de pruebas"
SRC = RAIZ / "src"
EXCLUIDOS = (SRC / "evaluacion", SRC / "data" / "generar")
PROMPTS = SRC / "agents" / "prompts"
PESOS = re.compile(r"\d{1,3}(?:\.\d{3})+")
PALABRAS = 8
MINIMO_DE_PALABRAS = 5
CIFRA_MINIMA = 10_000


def _texto(rutas: list[Path]) -> str:
    return normalizar_texto("\n".join(r.read_text(encoding="utf-8") for r in rutas))


def _codigo() -> str:
    rutas = [
        r
        for r in SRC.rglob("*")
        if r.suffix in (".py", ".md", ".yaml") and not any(e in r.parents for e in EXCLUIDOS)
    ]
    return _texto(rutas)


def _todos() -> list[dict]:
    return cargar_conjunto(["principal", "R1", "R3", "R4"])


@pytest.mark.unit
@pytest.mark.req(OBS05, "RNF-16 · Tasa de respuestas correctas")
def test_ninguna_pregunta_de_un_escenario_esta_en_el_codigo() -> None:
    codigo = _codigo()
    encontradas = {
        e["id"]
        for e in _todos()
        for t in e["turnos"]
        if len(normalizar_texto(t["usuario"]).split()) >= MINIMO_DE_PALABRAS
        and normalizar_texto(t["usuario"]) in codigo
    }
    assert not encontradas, f"Preguntas de escenarios en el código: {sorted(encontradas)}"


@pytest.mark.unit
@pytest.mark.req(OBS05, "RNF-16 · Tasa de respuestas correctas")
def test_ninguna_referencia_esta_en_los_prompts() -> None:
    palabras_prompts = _texto(sorted(PROMPTS.glob("*.md"))).split()
    secuencias = {
        " ".join(palabras_prompts[i : i + PALABRAS])
        for i in range(len(palabras_prompts) - PALABRAS + 1)
    }
    copiadas = set()
    for e in _todos():
        ref = normalizar_texto(str(e["respuesta_referencia"])).split()
        if any(
            " ".join(ref[i : i + PALABRAS]) in secuencias for i in range(len(ref) - PALABRAS + 1)
        ):
            copiadas.add(e["id"])
    assert not copiadas, f"Referencias copiadas en los prompts: {sorted(copiadas)}"


@pytest.mark.unit
@pytest.mark.req(OBS05, "RNF-16 · Tasa de respuestas correctas")
def test_ninguna_cifra_de_un_escenario_esta_en_los_agentes() -> None:
    agentes = _texto([r for r in (SRC / "agents").rglob("*") if r.suffix in (".py", ".md")])
    cifras = set()
    for e in _todos():
        valores = [str(v.get("valor", "")) for v in e["verificaciones_codigo"]]
        cifras |= set(PESOS.findall(" ".join(valores) + " " + str(e["respuesta_referencia"])))
    cifras = {c for c in cifras if int(c.replace(".", "")) >= CIFRA_MINIMA}
    presentes = sorted(
        c for c in cifras if re.search(rf"(?<![\d.]){re.escape(c)}(?![\d.])", agentes)
    )
    assert not presentes, f"Cifras de escenarios en los agentes: {presentes}"


@pytest.mark.unit
@pytest.mark.req(OBS05)
def test_los_conjuntos_adicionales_cumplen_el_esquema() -> None:
    requerimientos = requerimientos_de_la_especificacion()
    adicionales = cargar_adicionales()
    errores = [x for e in adicionales for x in validar_escenario(e, requerimientos, adicional=True)]
    assert not errores
    assert sorted(e["id"] for e in adicionales) == [
        "CAD-01",
        "CAD-02",
        "CAD-03",
        "SEG-01",
        "SEG-02",
    ]
    assert validar_generalizacion(cargar_escenarios()) == []
    assert ARCHIVO_GENERALIZACION.exists()


@pytest.mark.unit
@pytest.mark.req(OBS05)
def test_los_encadenados_conservan_turnos_y_verificaciones_aprobados() -> None:
    principales = {e["id"]: e for e in cargar_escenarios()}
    for cadena in (e for e in cargar_adicionales() if e["grupo"] == "cadena"):
        origenes = [principales[i] for i in cadena["encadena"]]
        assert cadena["turnos"] == [t for o in origenes for t in o["turnos"]]
        for o in origenes:
            assert all(v in cadena["verificaciones_codigo"] for v in o["verificaciones_codigo"])
            assert str(o["respuesta_referencia"]).strip() in cadena["respuesta_referencia"]
            assert o["reloj"] == cadena["reloj"] and o["sesion"] in (cadena["sesion"], None)


@pytest.mark.unit
@pytest.mark.req(OBS05)
def test_las_variantes_vacias_no_se_corren_y_las_llenas_heredan_su_origen(tmp_path: Path) -> None:
    from src.evaluacion.escenarios import variantes_de_generalizacion

    principales = cargar_escenarios()
    assert variantes_de_generalizacion(principales) == []  # Dayanna aún no las escribe
    ruta = tmp_path / "generalizacion.yaml"
    ruta.write_text(
        'variantes:\n  - {id: VAR-01, id_origen: IPU-08, variante: "¿Hasta qué día hay plazo '
        'para el predial este año?"}\n  - {id: VAR-02, id_origen: IPU-07, variante: ""}\n',
        encoding="utf-8",
    )
    [variante] = variantes_de_generalizacion(principales, ruta)
    origen = next(e for e in principales if e["id"] == "IPU-08")
    assert variante["grupo"] == "generalizacion" and variante["id_origen"] == "IPU-08"
    assert variante["respuesta_referencia"] == origen["respuesta_referencia"]
    assert variante["verificaciones_codigo"] == origen["verificaciones_codigo"]
    assert variante["turnos"] != origen["turnos"]
