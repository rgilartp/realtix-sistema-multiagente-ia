"""Muestra de calibración del juez y su kappa (sección 6.4 y ADR-24: R2, A5 y A6).

- La muestra son 30 respuestas de la corrida 2, estratificadas por el veredicto del juez: la mitad
  aprobadas (correcta o parcial, sin alucinación) y la mitad no. Si un estrato tiene menos de 15, se
  toma completo y se completa con el otro. Ni el CSV ni la clave muestran el veredicto del juez: el
  kappa lo lee después de `juez.jsonl`.
- Cada evaluador califica por separado (veredicto de 3 niveles y si hubo alucinación); luego
  acuerdan el consenso. El kappa se calcula entre el juez y el consenso (binario y ponderado lineal
  de 3 niveles) y entre los dos evaluadores antes del consenso, con intervalos por bootstrap.
- Al exportar se guarda la huella del juez: desde la corrida 2 el juez queda congelado (A5).
"""

import csv
import html
import json
import random
from pathlib import Path
from typing import Any

from src.evaluacion.ejecutor import leer_resultados
from src.evaluacion.juez import CasoJuez, anonimizador_de_prueba, caso_del_ensayo
from src.evaluacion.metricas_eval import SEMILLA, VEREDICTOS, kappa_con_intervalo

TAMANO = 30
COLUMNAS_EVALUADORES = (
    "rodolfo_veredicto", "rodolfo_alucinacion",
    "dayanna_veredicto", "dayanna_alucinacion",
    "consenso_veredicto", "consenso_alucinacion",
)  # fmt: skip
SI = ("si", "sí", "s", "true", "1")
EVALUADORES = {"rodolfo": "Rodolfo Angel Gilart Pulido", "dayanna": "Dayanna Liceth Varón Puerto"}


def aprobada(veredicto: str, alucinacion: bool) -> bool:
    return veredicto in ("correcta", "parcialmente correcta") and not alucinacion


def elegir(calificados: list[dict[str, Any]], tamano: int = TAMANO, semilla: int = SEMILLA):
    """Muestra estratificada por el veredicto del juez (de los 60 escenarios, con juez)."""
    candidatos = [c for c in calificados if c["conjunto"] == "principal" and c["juez"]]
    si = [c for c in candidatos if aprobada(c["juez"]["veredicto"], c["juez"]["alucinacion"])]
    no = [c for c in candidatos if c not in si]
    azar = random.Random(semilla)
    mitad = tamano // 2
    n_no = min(len(no), tamano - min(len(si), mitad))
    n_si = min(len(si), tamano - n_no)
    muestra = azar.sample(si, n_si) + azar.sample(no, n_no)
    azar.shuffle(muestra)  # el orden no delata el estrato
    return muestra


def exportar(
    muestra: list[dict[str, Any]],
    ensayos: dict[str, dict[str, Any]],
    escenarios: dict[str, dict[str, Any]],
    destino: Path,
    huella_juez: str,
) -> Path:
    """`muestra.csv` (sin el veredicto del juez), `clave.json` y `huella_juez.txt`."""
    destino.mkdir(parents=True, exist_ok=True)
    anonimizar = anonimizador_de_prueba()
    ruta = destino / "muestra.csv"
    clave = {}
    with ruta.open("w", newline="", encoding="utf-8") as archivo:
        escritor = csv.writer(archivo)
        escritor.writerow(
            ["muestra", "pregunta", "respuesta", "referencia", "fuentes", *COLUMNAS_EVALUADORES]
        )
        for i, c in enumerate(muestra, 1):
            ensayo = ensayos[c["id_conversacion"]]
            esc = escenarios[c["escenario"]]
            pregunta = " / ".join(t["usuario"] for t in ensayo["turnos"])
            respuesta = "\n---\n".join(t.get("respuesta") or "" for t in ensayo["turnos"])
            escritor.writerow(
                [
                    f"M{i:02d}",
                    anonimizar(pregunta),
                    anonimizar(respuesta),
                    anonimizar(str(esc["respuesta_referencia"]).strip()),
                    "; ".join(esc.get("fuentes_esperadas") or []),
                    *[""] * len(COLUMNAS_EVALUADORES),
                ]
            )
            clave[f"M{i:02d}"] = {
                "escenario": c["escenario"],
                "ensayo": c["ensayo"],
                "id_conversacion": c["id_conversacion"],
            }
    aprobadas_juez = sum(
        aprobada(c["juez"]["veredicto"], c["juez"]["alucinacion"]) for c in muestra if c.get("juez")
    )
    clave["_reparto"] = {  # el reparto de la estratificación (R2), sin decir cuáles
        "aprobadas_por_el_juez": aprobadas_juez,
        "no_aprobadas_por_el_juez": len(muestra) - aprobadas_juez,
    }
    (destino / "clave.json").write_text(
        json.dumps(clave, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (destino / "huella_juez.txt").write_text(huella_juez + "\n", encoding="utf-8")
    return ruta


def huella_guardada(destino: Path) -> str | None:
    ruta = destino / "huella_juez.txt"
    return ruta.read_text(encoding="utf-8").strip() if ruta.exists() else None


def _veredicto(texto: str) -> str:
    v = " ".join(texto.strip().lower().split())
    if v in ("parcial", "parcialmente"):
        v = "parcialmente correcta"
    if v not in VEREDICTOS:
        raise ValueError(f"Veredicto desconocido en la muestra: «{texto}»")
    return v


def calcular_kappa(destino: Path, archivo_juez: Path) -> dict[str, Any]:
    """Kappa del juez frente al consenso y entre los evaluadores, con la muestra ya calificada."""
    clave = json.loads((destino / "clave.json").read_text(encoding="utf-8"))
    juez = {j["id_conversacion"]: j["veredicto"] for j in leer_resultados(archivo_juez)}
    with (destino / "muestra.csv").open(encoding="utf-8") as archivo:
        filas = list(csv.DictReader(archivo))
    pendientes = [
        f["muestra"] for f in filas if not all(f[c].strip() for c in COLUMNAS_EVALUADORES)
    ]
    if pendientes:
        raise ValueError(f"Faltan calificaciones en: {', '.join(pendientes)}")

    def de(persona: str, f: dict[str, str]) -> tuple[str, bool]:
        return _veredicto(f[f"{persona}_veredicto"]), f[
            f"{persona}_alucinacion"
        ].strip().lower() in SI

    calif = {p: [de(p, f) for f in filas] for p in ("rodolfo", "dayanna", "consenso")}
    del_juez = [juez[clave[f["muestra"]]["id_conversacion"]] for f in filas]
    calif["juez"] = [(j["veredicto"], j["alucinacion"]) for j in del_juez]

    def comparar(a: str, b: str) -> dict[str, Any]:
        binario_a = [aprobada(*x) for x in calif[a]]
        binario_b = [aprobada(*x) for x in calif[b]]
        return {
            "binario": kappa_con_intervalo(binario_a, binario_b),
            "ponderado_3_niveles": kappa_con_intervalo(
                [v for v, _ in calif[a]], [v for v, _ in calif[b]], VEREDICTOS
            ),
        }

    return {
        "muestra": len(filas),
        "juez_frente_al_consenso": comparar("juez", "consenso"),
        "entre_evaluadores": comparar("rodolfo", "dayanna"),
        "aprobadas_por_el_juez": sum(aprobada(*x) for x in calif["juez"]),
    }


# -- Material para calificar sin el repositorio (B15): HTML de lectura y hoja por evaluador --

RUBRICA_PARA_PERSONAS = """
<h2>Cómo calificar</h2> <p>Cada respuesta numerada (M01 a M30) es una conversación real del
sistema multiagente de IA con un contribuyente de prueba sintético. Califícala comparándola con la
<strong>respuesta de referencia</strong>, que redactaron los autores a partir de las normas, y con
las <strong>fuentes que tuvo el sistema</strong>: los fragmentos de normas, los datos de las
herramientas, las notas del sistema, los datos leídos del recibo y el aviso de IA. Son las mismas
fuentes que recibe el juez automático. Califica por tu lado, sin hablar con el otro evaluador
hasta terminar y sin ayuda de ninguna IA. El orden es aleatorio y no dice nada de cómo se calificó
cada respuesta.</p> <ol> <li><strong>Fidelidad.</strong> Cada afirmación (cifra, fecha,
porcentaje, norma, artículo, requisito o procedimiento) debe salir de la referencia, de alguna de
las fuentes del sistema o de los datos del propio contribuyente que aparecen en la conversación.
Lo que no sale de ninguna, o las contradice (por ejemplo, una cifra distinta de la que dio la
herramienta), es una <em>alucinación</em>, aunque parezca de sentido común.</li>
<li><strong>Citas.</strong> Si cita una norma, la norma debe sustentar lo que le atribuye.</li>
<li><strong>Cobertura.</strong> Atiende todo lo que se preguntó y lo esencial de la
referencia.</li> <li><strong>Fuentes primarias.</strong> Prefiere la norma o los datos del
contribuyente a las generalidades.</li> <li><strong>Mesura.</strong> No agrega pasos, datos ni
consejos que nadie pidió.</li> </ol> <h2>Veredictos</h2> <ul> <li><strong>correcta:</strong>
coincide en lo esencial con la referencia, sin errores ni alucinaciones; puede usar otras palabras
u otro orden.</li> <li><strong>parcialmente correcta:</strong> lo esencial es correcto, pero omite
un elemento secundario de la referencia o es imprecisa en un detalle que no cambia la
conclusión.</li> <li><strong>incorrecta:</strong> contradice la referencia, da una cifra, fecha o
conclusión equivocada, omite lo esencial, hace algo de la lista «la respuesta no debe» o tiene una
alucinación que podría llevar al contribuyente a actuar mal.</li> </ul> <p>Una respuesta con una
alucinación nunca es «correcta». En la hoja de calificaciones, elige en las listas el
<strong>veredicto</strong> y si hubo <strong>alucinación</strong> (sí o no), y si quieres deja un
comentario breve.</p>
"""


def _lista(titulo: str, valores: list[str]) -> str:
    if not valores:
        return ""
    items = "".join(f"<li><pre>{html.escape(v)}</pre></li>" for v in valores)
    return f"<h4>{html.escape(titulo)}</h4><ul>{items}</ul>"


def _bloque(codigo: str, caso: CasoJuez) -> str:
    turnos = "".join(
        f"<p class=c><strong>Contribuyente ({i}):</strong> {html.escape(t['contribuyente'])}</p>"
        f"<pre class=a>{html.escape(t['asistente'])}</pre>"
        for i, t in enumerate(caso.conversacion, 1)
    )
    fuentes = "".join(
        (
            _lista("Aviso de IA que vio el contribuyente", caso.avisos),
            _lista("Fuentes que citó el sistema", caso.fuentes_citadas),
            _lista("Fragmentos de normas que recuperó el sistema", caso.contextos),
            _lista("Datos que entregaron las herramientas del sistema", caso.datos_herramientas),
            _lista("Notas que agregó el sistema", caso.notas_sistema),
            _lista("Datos que el sistema leyó del recibo", caso.datos_recibo),
        )
    )
    referencia = (
        f"<h4>Respuesta de referencia</h4><pre>{html.escape(caso.referencia)}</pre>"
        + _lista("Fuentes de la referencia", caso.fuentes_referencia)
        + _lista("La respuesta no debe", caso.no_debe)
    )
    return (
        f"<section id={codigo}><h3>{codigo}</h3><h4>Conversación</h4>{turnos}{referencia}"
        f"<details><summary>Fuentes que tuvo el sistema</summary>{fuentes or '<p>Ninguna.</p>'}"
        "</details></section>"
    )


def _html(nombre: str, bloques: list[str]) -> str:
    estilo = (
        "body{font-family:system-ui,sans-serif;max-width:60rem;margin:auto;padding:1rem;"
        "line-height:1.45;color:#1d1d1f;background:#fff}pre{white-space:pre-wrap;"
        "font-family:inherit;background:#f4f4f6;padding:.5rem;border-radius:4px}"
        "pre.a{background:#eef4ff}section{border-top:2px solid #888;margin-top:2rem}"
        "details{margin:.5rem 0}summary{cursor:pointer;font-weight:600}"
    )
    indice = " · ".join(f"<a href=#M{i:02d}>M{i:02d}</a>" for i in range(1, len(bloques) + 1))
    return (
        "<!doctype html><html lang=es><head><meta charset=utf-8>"
        "<meta name=viewport content='width=device-width,initial-scale=1'>"
        f"<title>Calibración del juez · {html.escape(nombre)}</title><style>{estilo}</style>"
        f"</head><body><h1>Calibración del juez · {html.escape(nombre)}</h1>"
        f"{RUBRICA_PARA_PERSONAS}<p>{indice}</p>{''.join(bloques)}</body></html>"
    )


def _hoja(ruta: Path, codigos: list[str], titulo: str) -> None:
    from openpyxl import Workbook
    from openpyxl.worksheet.datavalidation import DataValidation

    libro = Workbook()
    hoja = libro.active
    hoja.title = "Calificaciones"
    hoja.append(["muestra", "veredicto", "alucinacion", "comentario"])
    for codigo in codigos:
        hoja.append([codigo, None, None, None])
    ultima = len(codigos) + 1
    veredictos = DataValidation(
        type="list", formula1='"' + ",".join(VEREDICTOS) + '"', allow_blank=False
    )
    alucinacion = DataValidation(type="list", formula1='"sí,no"', allow_blank=False)
    for validacion, columna in ((veredictos, "B"), (alucinacion, "C")):
        validacion.error = "Elige un valor de la lista."
        hoja.add_data_validation(validacion)
        validacion.add(f"{columna}2:{columna}{ultima}")
    for columna, ancho in (("A", 10), ("B", 24), ("C", 14), ("D", 60)):
        hoja.column_dimensions[columna].width = ancho
    instrucciones = libro.create_sheet("Instrucciones")
    for linea in (
        titulo,
        "Lee cada respuesta en el HTML de lectura y elige aquí, en las listas, el veredicto y si "
        "hubo alucinación. El comentario es opcional.",
        "Califica por tu lado, sin hablar con el otro evaluador hasta terminar y sin ayuda de "
        "ninguna IA. No cambies la columna «muestra».",
    ):
        instrucciones.append([linea])
    libro.save(ruta)


def exportar_para_evaluadores(
    muestra: list[dict[str, Any]],
    ensayos: dict[str, dict[str, Any]],
    escenarios: dict[str, dict[str, Any]],
    destino: Path,
) -> list[Path]:
    """Por evaluador, un HTML de lectura que se abre sin el repositorio (cada respuesta con la
    conversación, la referencia y las mismas fuentes que ve el juez v3, anonimizadas) y una hoja
    .xlsx con listas desplegables; más la hoja del consenso. Sin el veredicto del juez, en el orden
    de `muestra.csv` (aleatorio)."""
    codigos = [f"M{i:02d}" for i in range(1, len(muestra) + 1)]
    bloques = [
        _bloque(
            codigo,
            caso_del_ensayo(
                escenarios[c["escenario"]], ensayos[c["id_conversacion"]]
            ).anonimizado(),
        )
        for codigo, c in zip(codigos, muestra, strict=True)
    ]
    rutas = []
    for clave, nombre in EVALUADORES.items():
        carpeta = destino / clave
        carpeta.mkdir(parents=True, exist_ok=True)
        lectura = carpeta / f"calibracion_{clave}.html"
        lectura.write_text(_html(nombre, bloques), encoding="utf-8")
        hoja = carpeta / f"calificaciones_{clave}.xlsx"
        _hoja(hoja, codigos, f"Calificaciones de {nombre}")
        rutas += [lectura, hoja]
    consenso = destino / "consenso"
    consenso.mkdir(parents=True, exist_ok=True)
    hoja = consenso / "calificaciones_consenso.xlsx"
    _hoja(hoja, codigos, "Consenso de los dos evaluadores, después de calificar por separado")
    return [*rutas, hoja]


def importar_calificaciones(destino: Path) -> int:
    """Pasa las hojas de los evaluadores y del consenso a `muestra.csv`; devuelve cuántas filas
    quedaron completas. Un veredicto fuera de la lista detiene la importación."""
    from openpyxl import load_workbook

    hojas = {clave: destino / clave / f"calificaciones_{clave}.xlsx" for clave in EVALUADORES}
    hojas["consenso"] = destino / "consenso" / "calificaciones_consenso.xlsx"
    calificaciones: dict[str, dict[str, tuple[str, str]]] = {}
    for persona, ruta in hojas.items():
        filas = load_workbook(ruta, read_only=True)["Calificaciones"].iter_rows(values_only=True)
        next(filas)
        calificaciones[persona] = {
            str(m): (
                _veredicto(str(v)) if v else "",
                ("sí" if str(a).lower() in SI else "no") if a else "",
            )
            for m, v, a, *_ in filas
            if m
        }
    ruta_csv = destino / "muestra.csv"
    with ruta_csv.open(encoding="utf-8") as archivo:
        lector = csv.DictReader(archivo)
        columnas = list(lector.fieldnames or [])
        filas_csv = list(lector)
    for fila in filas_csv:
        for persona, de_la_persona in calificaciones.items():
            veredicto, alucinacion = de_la_persona.get(fila["muestra"], ("", ""))
            fila[f"{persona}_veredicto"], fila[f"{persona}_alucinacion"] = veredicto, alucinacion
    with ruta_csv.open("w", newline="", encoding="utf-8") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=columnas)
        escritor.writeheader()
        escritor.writerows(filas_csv)
    return sum(all(f[c] for c in COLUMNAS_EVALUADORES) for f in filas_csv)
