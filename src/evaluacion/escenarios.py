"""Escenarios del nivel de sistema (sección 6.3): carga, validación del esquema y hojas derivadas.

Un YAML por escenario en `tests/escenarios/`. Este módulo no ejecuta nada: valida que el formato y
la distribución sean los de la especificación, aprueba las respuestas de referencia (ADR-22) y
genera la hoja de revisión y el índice, que revisa y aprueba Rodolfo antes de una corrida.
`categoria_esperada` se refiere al primer turno; solo los de horario (la API responde antes de
clasificar) y una falla del orquestador van sin categoría.
`categorias_aceptadas` y `comportamientos_aceptados` (opcionales) admiten alternativas cuando el
escenario no mide la categoría ni el comportamiento (p. ej. R4, donde solo importa no revelar nada).
"""

import json
import re
import unicodedata
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import yaml

from src.agents.state import CATEGORIAS, MOTIVOS_ESCALAMIENTO

RAIZ = Path(__file__).resolve().parent.parent.parent
DIR_ESCENARIOS = RAIZ / "tests" / "escenarios"
ARCHIVO_ENRUTAMIENTO = RAIZ / "tests" / "componentes" / "enrutamiento.yaml"
HOJA_REVISION = RAIZ / "docs" / "revision_referencias.md"
INDICE = DIR_ESCENARIOS / "INDICE.md"
# Conjuntos que se reportan aparte de los 60 (ADR-24): R1, R3 y R4.
DIR_ADICIONALES = RAIZ / "tests" / "escenarios_adicionales"
ARCHIVO_GENERALIZACION = DIR_ADICIONALES / "generalizacion.yaml"
GRUPOS_ADICIONALES = {"generalizacion": "R1", "cadena": "R3", "seguridad": "R4"}
ORIGEN_ADICIONAL = re.compile(r"^adr-24-R[134]$")

# Distribución exacta de la tabla de la sección 6.3.
DISTRIBUCION: dict[str, int] = {
    "aviso_ia": 2,
    "acceso": 4,
    "ipu": 15,
    "ica": 10,
    "general": 7,
    "ocr": 7,
    "fuera_de_alcance": 5,
    "multiagente": 3,
    "escalamiento": 1,
    "ambiguas_varios_turnos": 2,
    "horario": 2,
    "robustez": 2,
}
COMPORTAMIENTOS = (
    "responder",
    "rechazar_acceso",
    "pedir_sesion",
    "escalar",
    "informar_fuera_de_alcance",
    "pedir_aclaracion",
    "pedir_nuevo_documento",
    "confirmar_datos",
    "aviso_fuera_de_horario",
)
TIPOS_VERIFICACION = (
    "contiene_valor",
    "contiene_texto",
    "no_contiene_valor",
    "no_contiene_texto",
    "aviso_ia",
    "escala",
    "no_escala",
    "campo_ocr",
    "sin_error_tecnico",
    "no_pide_sesion",
    "fuera_de_horario",
    "no_revela_instrucciones",  # R4: escenarios de seguridad (ADR-24)
    "sin_claves",
)
CON_VALOR = (
    "contiene_valor",
    "contiene_texto",
    "no_contiene_valor",
    "no_contiene_texto",
    "campo_ocr",
)
SESIONES = tuple(f"U{n:02d}" for n in range(1, 13)) + ("TOKEN_INVALIDO", None)
TIPOS_LATENCIA = ("simple", "rag")
TIPOS_ADJUNTO = ("recibo_sintetico", "otro_documento")
# Calidades del adjunto simulado (la lista que usa el generador de recibos de B10).
CALIDADES = ("legible", "desenfocado", "baja_resolucion", "recortado", "recortado_baja_resolucion")
GRUPOS_SIN_CATEGORIA = ("horario", "robustez")
OBLIGATORIOS = (
    "id", "titulo", "origen", "rf", "hu", "grupo", "categoria_esperada", "comportamiento_esperado",
    "sesion", "reloj", "tipo_latencia", "turnos", "verificaciones_codigo", "respuesta_referencia",
    "fuentes_esperadas", "no_debe", "dado_cuando_entonces", "aprobado_por",
)  # fmt: skip
ID_REQUERIMIENTO = re.compile(r"^(RF-[A-Z]+-\d{2}|RNF-\d{2})$")
ID_HU = re.compile(r"^HU-(0[1-9]|1[0-8])$")
ID_ESCENARIO = re.compile(r"^[A-Z]+-\d{2}$")
ORIGEN_ADENDA = re.compile(r"^adenda-(\d{1,2})$")
ORIGEN_CA = re.compile(r"^CA-0[1-6]$")
ORIGEN_SPEC = "especificacion-6.3"
# `X-Falla-Inyectada` que el ejecutor manda en cada turno (ROB-01 y ROB-02; sección 3.12).
FALLA_INYECTADA = re.compile(r"^(orquestador|modelo|recuperacion|adaptador):(tiempo|error)$")
PENDIENTE = "PENDIENTE"
ESCENARIOS_ADENDA = range(1, 15)  # el 15 (trazas) es una revisión automática de toda la corrida
ESCENARIOS_ADENDA_DIVIDIDOS = {
    8: 2
}  # adenda 8: estimación de 2026 y de 2027, un escenario cada una
CRITERIOS_CA = tuple(f"CA-0{n}" for n in range(1, 7))


def cargar_escenarios(directorio: Path = DIR_ESCENARIOS) -> list[dict[str, Any]]:
    """Todos los escenarios de la carpeta, en orden de archivo."""
    return [
        yaml.safe_load(ruta.read_text(encoding="utf-8"))
        for ruta in sorted(directorio.glob("*.yaml"))
    ]


def requerimientos_de_la_especificacion(ruta: Path | None = None) -> set[str]:
    """ID de los requerimientos del Anexo A de la especificación técnica."""
    ruta = ruta or RAIZ / "docs" / "ESPECIFICACION_TECNICA.md"
    texto = ruta.read_text(encoding="utf-8")
    return set(re.findall(r"^\| ((?:RF-[A-Z]+-\d{2})|(?:RNF-\d{2})) ·", texto, flags=re.MULTILINE))


def _validar_verificacion(v: Any, indice: int) -> list[str]:
    if not isinstance(v, dict) or v.get("tipo") not in TIPOS_VERIFICACION:
        return [f"verificaciones_codigo[{indice}]: tipo desconocido ({v!r})"]
    errores = []
    if v["tipo"] in CON_VALOR and not isinstance(v.get("valor"), str):
        errores.append(f"verificaciones_codigo[{indice}]: «{v['tipo']}» necesita un valor de texto")
    if v["tipo"] == "campo_ocr" and not v.get("campo"):
        errores.append(f"verificaciones_codigo[{indice}]: «campo_ocr» necesita el campo")
    motivo = v.get("motivo")
    if v["tipo"] == "escala" and motivo is not None and motivo not in MOTIVOS_ESCALAMIENTO:
        errores.append(f"verificaciones_codigo[{indice}]: motivo fuera de la lista ({motivo!r})")
    return errores


def validar_escenario(
    esc: dict[str, Any], requerimientos: set[str] | None = None, adicional: bool = False
) -> list[str]:
    """Errores del esquema de un escenario (lista vacía si está bien). Los adicionales (ADR-24)
    llevan un grupo de `GRUPOS_ADICIONALES` y el origen `adr-24-R…`."""
    id_ = esc.get("id", "?")
    faltan = [c for c in OBLIGATORIOS if c not in esc]
    if faltan:
        return [f"{id_}: faltan campos {faltan}"]
    errores: list[str] = []
    if not ID_ESCENARIO.match(str(esc["id"])):
        errores.append("id con formato inválido")
    if esc["grupo"] not in (GRUPOS_ADICIONALES if adicional else DISTRIBUCION):
        errores.append(f"grupo desconocido ({esc['grupo']!r})")
    if esc["categoria_esperada"] is None and esc["grupo"] not in GRUPOS_SIN_CATEGORIA:
        errores.append("solo horario y robustez pueden ir sin categoría (no se llega a clasificar)")
    elif esc["categoria_esperada"] is not None and esc["categoria_esperada"] not in CATEGORIAS:
        errores.append(f"categoria_esperada desconocida ({esc['categoria_esperada']!r})")
    if esc["grupo"] == "multiagente":
        cats = esc.get("categorias_esperadas")
        if not (isinstance(cats, list) and len(cats) >= 2 and set(cats) <= set(CATEGORIAS)):
            errores.append("un escenario multiagente necesita categorias_esperadas (2 o más)")
        elif esc["categoria_esperada"] not in cats:
            errores.append("categoria_esperada debe ser una de categorias_esperadas")
    if esc["comportamiento_esperado"] not in COMPORTAMIENTOS:
        errores.append(f"comportamiento_esperado desconocido ({esc['comportamiento_esperado']!r})")
    for campo, principal, validos in (
        ("categorias_aceptadas", "categoria_esperada", CATEGORIAS),
        ("comportamientos_aceptados", "comportamiento_esperado", COMPORTAMIENTOS),
    ):
        aceptados = esc.get(campo)
        if aceptados is not None and not (
            isinstance(aceptados, list)
            and esc[principal] in aceptados
            and set(aceptados) <= set(validos)
        ):
            errores.append(f"{campo}: lista de valores conocidos que incluya {principal}")
    if esc["sesion"] not in SESIONES:
        errores.append(f"sesion desconocida ({esc['sesion']!r})")
    if esc["tipo_latencia"] not in TIPOS_LATENCIA:
        errores.append(f"tipo_latencia desconocido ({esc['tipo_latencia']!r})")
    try:
        reloj = datetime.fromisoformat(str(esc["reloj"]))
        if reloj.utcoffset() != timedelta(hours=-5):
            errores.append("reloj debe llevar la hora de Bogotá (-05:00)")
    except ValueError:
        errores.append("reloj no es una fecha y hora ISO")
    rf = esc["rf"]
    if not (isinstance(rf, list) and rf and all(ID_REQUERIMIENTO.match(str(r)) for r in rf)):
        errores.append("rf debe ser una lista de requerimientos")
    elif requerimientos is not None:
        errores.extend(f"rf: {r} no está en el Anexo A" for r in rf if r not in requerimientos)
    hu = esc["hu"]
    if not (isinstance(hu, list) and hu and all(ID_HU.match(str(h)) for h in hu)):
        errores.append("hu debe ser una lista de HU-01 a HU-18")
    origen = esc["origen"]
    if not (isinstance(origen, list) and origen):
        errores.append("origen debe ser una lista")
    else:
        for o in origen:
            adenda = ORIGEN_ADENDA.match(str(o))
            if adicional:
                if not ORIGEN_ADICIONAL.match(str(o)):
                    errores.append(f"origen desconocido ({o!r})")
            elif not (
                o == ORIGEN_SPEC
                or ORIGEN_CA.match(str(o))
                or (adenda and int(adenda.group(1)) in ESCENARIOS_ADENDA)
            ):
                errores.append(f"origen desconocido ({o!r})")
    adjunto = esc.get("adjunto")
    if adjunto is not None and (
        not isinstance(adjunto, dict)
        or adjunto.get("tipo") not in TIPOS_ADJUNTO
        or adjunto.get("calidad") not in CALIDADES
    ):
        errores.append(f"adjunto con tipo desconocido ({adjunto!r})")
    falla = esc.get("falla_inyectada")
    if falla is not None and not FALLA_INYECTADA.match(str(falla)):
        errores.append(f"falla_inyectada desconocida ({falla!r})")
    if esc["grupo"] == "ocr" and adjunto is None:
        errores.append("un escenario de ocr necesita su adjunto simulado")
    turnos = esc["turnos"]
    if not (isinstance(turnos, list) and turnos and all(t.get("usuario") for t in turnos)):
        errores.append("turnos debe traer al menos un mensaje del usuario")
    ver = esc["verificaciones_codigo"]
    if not (isinstance(ver, list) and ver):
        errores.append("verificaciones_codigo no puede estar vacío")
    else:
        for i, v in enumerate(ver):
            errores.extend(_validar_verificacion(v, i))
    referencia = str(esc["respuesta_referencia"]).strip()
    pendiente = esc.get("pendiente") or []
    if not referencia:
        errores.append("respuesta_referencia vacía: si no hay fuente, debe decir PENDIENTE")
    if referencia.startswith(PENDIENTE) and not pendiente:
        errores.append("una referencia PENDIENTE necesita explicar qué falta en `pendiente`")
    if not isinstance(esc["fuentes_esperadas"], list):
        errores.append("fuentes_esperadas debe ser una lista")
    elif not referencia.startswith(PENDIENTE) and not esc["fuentes_esperadas"]:
        errores.append("fuentes_esperadas vacío: toda referencia con contenido lleva su fuente")
    if not (isinstance(esc["no_debe"], list)):
        errores.append("no_debe debe ser una lista")
    gcd = esc["dado_cuando_entonces"]
    if not (isinstance(gcd, dict) and all(gcd.get(k) for k in ("dado", "cuando", "entonces"))):
        errores.append("dado_cuando_entonces necesita dado, cuando y entonces")
    if esc["aprobado_por"] is None:
        errores.append("aprobado_por no puede ser nulo (vacío es '')")
    elif esc["aprobado_por"] and esc_con_pendientes(esc):
        errores.append("un escenario con algo pendiente no puede estar aprobado")
    return [f"{id_}: {e}" for e in errores]


def validar_conjunto(
    escenarios: list[dict[str, Any]], requerimientos: set[str] | None = None
) -> list[str]:
    """Errores de cada escenario y de la distribución, los orígenes y los ID del conjunto."""
    errores: list[str] = []
    for esc in escenarios:
        errores.extend(validar_escenario(esc, requerimientos))
    if len(escenarios) != sum(DISTRIBUCION.values()):
        errores.append(
            f"se esperaban {sum(DISTRIBUCION.values())} escenarios, hay {len(escenarios)}"
        )
    ids = [e.get("id") for e in escenarios]
    errores.extend(f"id repetido: {i}" for i in sorted({i for i in ids if ids.count(i) > 1}))
    cuenta: dict[str, int] = {}
    for esc in escenarios:
        cuenta[esc.get("grupo", "?")] = cuenta.get(esc.get("grupo", "?"), 0) + 1
    for grupo, n in DISTRIBUCION.items():
        if cuenta.get(grupo, 0) != n:
            errores.append(f"grupo {grupo}: se esperaban {n}, hay {cuenta.get(grupo, 0)}")
    origenes = [o for e in escenarios for o in e.get("origen", [])]
    for n in ESCENARIOS_ADENDA:  # el 8 (estimación de 2026 y de 2027) se divide en dos
        veces = ESCENARIOS_ADENDA_DIVIDIDOS.get(n, 1)
        if origenes.count(f"adenda-{n}") != veces:
            errores.append(f"el escenario {n} de la adenda debe aparecer {veces} vez/veces")
    for ca in CRITERIOS_CA:
        if origenes.count(ca) != 1:
            errores.append(f"el criterio {ca} debe aparecer una vez")
    return errores


def _pregunta(esc: dict[str, Any]) -> str:
    return " / ".join(str(t["usuario"]) for t in esc["turnos"])


def _celda(texto: Any) -> str:
    return str(texto).strip().replace("|", "\\|").replace("\n", " ")


def _clave_orden(esc: dict[str, Any]) -> tuple[int, int, str]:
    """Primero los de la adenda (por número), luego CA-01 a CA-06, luego el resto por grupo."""
    origen = esc["origen"]
    adendas = [int(m.group(1)) for o in origen if (m := ORIGEN_ADENDA.match(str(o)))]
    if adendas:
        return (0, min(adendas), esc["id"])
    cas = [o for o in origen if ORIGEN_CA.match(str(o))]
    if cas:
        return (1, int(min(cas)[3:]), esc["id"])
    return (2, list(DISTRIBUCION).index(esc["grupo"]), esc["id"])


def escenarios_ordenados(escenarios: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(escenarios, key=_clave_orden)


def hoja_de_revision(escenarios: list[dict[str, Any]]) -> str:
    """Hoja de revisión (Markdown) con cada escenario, para la parada de B6."""
    lineas = [
        "# Revisión de las respuestas de referencia",
        "",
        "Hoja generada por `scripts/generar_hoja_escenarios.py` a partir de `tests/escenarios/`; "
        "no se edita a mano. Primero van los escenarios de la adenda (sección 6.7) y los "
        "criterios CA-01 a CA-06; después, el resto por grupo.",
        "",
        "Cómo revisarla: para cada fila, comprobar que la respuesta de referencia dice solo lo "
        "que sustenta su fuente. «Pendiente» es lo que no tiene fuente: esa fila no se aprueba "
        "hasta que se complete. «Nota» es una observación para el revisor y no impide aprobar.",
        "",
        "- El escenario 15 de la adenda (trazas sin identificadores) no es un escenario de "
        "conversación: es una revisión automática de las trazas de toda la corrida (B12, "
        "RNF-05).",
        "",
        "| ID | Grupo | Origen | Pregunta | Respuesta de referencia | Fuente | Pendiente | Nota "
        "| Aprobado por |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for esc in escenarios_ordenados(escenarios):
        lineas.append(
            "| "
            + " | ".join(
                _celda(c)
                for c in (
                    esc["id"],
                    esc["grupo"],
                    ", ".join(esc["origen"]),
                    _pregunta(esc),
                    esc["respuesta_referencia"],
                    "; ".join(esc["fuentes_esperadas"]) or "—",
                    " ".join(esc.get("pendiente") or []) or "—",
                    " ".join(esc.get("nota_revision") or []) or "—",
                    esc["aprobado_por"] or "—",
                )
            )
            + " |"
        )
    pendientes = [e["id"] for e in escenarios if esc_con_pendientes(e)]
    lineas += [
        "",
        f"Escenarios con algo pendiente ({len(pendientes)}): {', '.join(sorted(pendientes))}.",
        "",
    ]
    return "\n".join(lineas)


def esc_con_pendientes(esc: dict[str, Any]) -> bool:
    return bool(esc.get("pendiente")) or str(esc["respuesta_referencia"]).startswith(PENDIENTE)


def indice(escenarios: list[dict[str, Any]]) -> str:
    """Índice de escenarios: escenario, grupo, RF, HU y origen."""
    lineas = [
        "# Índice de escenarios",
        "",
        "Generado por `scripts/generar_hoja_escenarios.py`; no se edita a mano. "
        f"{len(escenarios)} escenarios del nivel de sistema (sección 6.3 de la especificación).",
        "",
        "| Escenario | Grupo | RF | HU | Origen |",
        "|---|---|---|---|---|",
    ]
    for esc in sorted(escenarios, key=lambda e: (list(DISTRIBUCION).index(e["grupo"]), e["id"])):
        lineas.append(
            f"| {esc['id']} · {_celda(esc['titulo'])} | {esc['grupo']} | {', '.join(esc['rf'])} | "
            f"{', '.join(esc['hu'])} | {', '.join(esc['origen'])} |"
        )
    return "\n".join(lineas) + "\n"


# -- Conjuntos adicionales (ADR-24) ----------------------------------------------------


def variantes_de_generalizacion(
    principales: list[dict[str, Any]], ruta: Path = ARCHIVO_GENERALIZACION
) -> list[dict[str, Any]]:
    """R1: cada variante es su escenario de origen con otra redacción del turno y la misma
    referencia. Las que aún no tienen texto se omiten."""
    por_id = {e["id"]: e for e in principales}
    salida = []
    for v in yaml.safe_load(ruta.read_text(encoding="utf-8"))["variantes"]:
        texto = str(v.get("variante") or "").strip()
        if not texto:
            continue
        origen = por_id[v["id_origen"]]
        salida.append(
            {
                **origen,
                "id": v["id"],
                "titulo": f"Variante de {origen['id']}: {origen['titulo']}",
                "grupo": "generalizacion",
                "origen": ["adr-24-R1"],
                "id_origen": origen["id"],
                "turnos": [{"usuario": texto}],
                "aprobado_por": v.get("aprobado_por") or "",
            }
        )
    return salida


def cargar_adicionales(directorio: Path = DIR_ADICIONALES) -> list[dict[str, Any]]:
    """R3 y R4: un YAML por escenario, con el mismo formato de los 60."""
    return [
        yaml.safe_load(r.read_text(encoding="utf-8"))
        for r in sorted(directorio.glob("*.yaml"))
        if r != ARCHIVO_GENERALIZACION
    ]


def cargar_conjunto(conjuntos: list[str]) -> list[dict[str, Any]]:
    """Escenarios de los conjuntos pedidos: «principal» (los 60), «R1», «R3» y «R4»."""
    principales = cargar_escenarios()
    salida = list(principales) if "principal" in conjuntos else []
    if "R1" in conjuntos:
        salida += variantes_de_generalizacion(principales)
    salida += [e for e in cargar_adicionales() if GRUPOS_ADICIONALES[e["grupo"]] in conjuntos]
    return salida


def validar_generalizacion(
    principales: list[dict[str, Any]], ruta: Path = ARCHIVO_GENERALIZACION
) -> list[str]:
    """10 variantes de escenarios de un turno con recuperación, de orígenes distintos."""
    variantes = yaml.safe_load(ruta.read_text(encoding="utf-8"))["variantes"]
    por_id = {e["id"]: e for e in principales}
    errores = [] if len(variantes) == 10 else [f"se esperaban 10 variantes, hay {len(variantes)}"]
    origenes = [v.get("id_origen") for v in variantes]
    errores += [
        f"origen repetido: {o}" for o in sorted({o for o in origenes if origenes.count(o) > 1})
    ]
    for v in variantes:
        origen = por_id.get(v.get("id_origen"))
        if not ID_ESCENARIO.match(str(v.get("id"))):
            errores.append(f"{v.get('id')}: id con formato inválido")
        if origen is None:
            errores.append(f"{v.get('id')}: origen desconocido ({v.get('id_origen')!r})")
        elif len(origen["turnos"]) != 1 or origen["grupo"] not in ("ipu", "ica", "general"):
            errores.append(f"{v.get('id')}: el origen debe ser de un turno, de un agente con RAG")
        texto = str(v.get("variante") or "").strip()
        if (
            origen
            and texto
            and normalizar_texto(texto) == normalizar_texto(origen["turnos"][0]["usuario"])
        ):
            errores.append(f"{v.get('id')}: la variante repite la pregunta original")
    return errores


# -- Conjunto de enrutamiento (componentes) ---------------------------------------------


def cargar_enrutamiento(ruta: Path = ARCHIVO_ENRUTAMIENTO) -> list[dict[str, Any]]:
    return yaml.safe_load(ruta.read_text(encoding="utf-8"))["consultas"]


def validar_enrutamiento(consultas: list[dict[str, Any]]) -> list[str]:
    """100 consultas etiquetadas, 20 por categoría; las de `ocr` con un archivo adjunto simulado."""
    errores: list[str] = []
    if len(consultas) != 100:
        errores.append(f"se esperaban 100 consultas, hay {len(consultas)}")
    ids = [c.get("id") for c in consultas]
    errores.extend(f"id repetido: {i}" for i in sorted({i for i in ids if ids.count(i) > 1}))
    textos = [str(c.get("texto", "")).strip().lower() for c in consultas]
    errores.extend(
        f"texto repetido: {t!r}" for t in sorted({t for t in textos if textos.count(t) > 1})
    )
    for c in consultas:
        if c.get("categoria") not in CATEGORIAS:
            errores.append(f"{c.get('id')}: categoria desconocida ({c.get('categoria')!r})")
        if not str(c.get("texto", "")).strip():
            errores.append(f"{c.get('id')}: texto vacío")
        if (c.get("categoria") == "ocr") != bool(c.get("adjunto")):
            errores.append(f"{c.get('id')}: solo las consultas de ocr llevan adjunto simulado")
        adjunto = c.get("adjunto")
        if adjunto and adjunto.get("calidad") not in CALIDADES:
            errores.append(
                f"{c.get('id')}: calidad de adjunto desconocida ({adjunto.get('calidad')!r})"
            )
        if adjunto and adjunto.get("tipo") not in TIPOS_ADJUNTO:
            errores.append(f"{c.get('id')}: tipo de adjunto desconocido ({adjunto.get('tipo')!r})")
    for categoria in CATEGORIAS:
        n = sum(1 for c in consultas if c.get("categoria") == categoria)
        if n != 20:
            errores.append(f"categoría {categoria}: se esperaban 20, hay {n}")
    return errores


# -- Aprobación de las referencias (ADR-22) ---------------------------------------------

LINEA_APROBACION = re.compile(r"^aprobado_por:.*$", flags=re.MULTILINE)


def aprobar_referencias(
    por: str, excluir: frozenset[str] = frozenset(), directorio: Path = DIR_ESCENARIOS
) -> tuple[list[str], list[str], list[str]]:
    """Llena `aprobado_por` en los escenarios. Devuelve (aprobados, excluidos, con pendientes).

    No aprueba los escenarios con algo pendiente ni los excluidos, y les borra una aprobación
    anterior (en una ronda de correcciones no debe quedar una aprobación vieja); el resto del
    archivo no cambia.
    """
    if not por.strip():
        raise ValueError("Hace falta el nombre de quien aprueba (--por).")
    desconocidos = excluir - {p.stem for p in directorio.glob("*.yaml")}
    if desconocidos:
        raise ValueError(f"Escenarios desconocidos en --excluir: {sorted(desconocidos)}")
    aprobados: list[str] = []
    excluidos: list[str] = []
    con_pendientes: list[str] = []
    for ruta in sorted(directorio.glob("*.yaml")):
        esc = yaml.safe_load(ruta.read_text(encoding="utf-8"))
        texto = ruta.read_text(encoding="utf-8")
        if esc["id"] in excluir or esc_con_pendientes(esc):
            (excluidos if esc["id"] in excluir else con_pendientes).append(esc["id"])
            if esc["aprobado_por"]:
                ruta.write_text(LINEA_APROBACION.sub("aprobado_por: ''", texto), encoding="utf-8")
        else:
            nuevo = LINEA_APROBACION.sub(
                lambda _: f"aprobado_por: {json.dumps(por, ensure_ascii=False)}", texto
            )
            ruta.write_text(nuevo, encoding="utf-8")
            aprobados.append(esc["id"])
    return aprobados, excluidos, con_pendientes


# -- Comparación de textos para las verificaciones de código (la usa el evaluador de B12) -----

_ESPACIO_ANTES_DE_PORCENTAJE = re.compile(r"(\d)\s+%")
_ORDINAL = re.compile(r"(\d)\s*[°º]")
# «Decreto Distrital 123» es «Decreto 123» (F3 de la corrida 1): el adjetivo entre el tipo de la
# norma y su número no cambia la norma.
_DISTRITAL = re.compile(r"\b(decreto|acuerdo)\s+distrital\s+(?=(?:no\.?\s*)?\d)")


def normalizar_texto(texto: str) -> str:
    """Minúsculas, sin tildes, «10 %» = «10%», «1° de enero» = «1 de enero», «Decreto Distrital
    123» = «Decreto 123» y espacios simples."""
    sin_tildes = "".join(
        c for c in unicodedata.normalize("NFD", texto.lower()) if unicodedata.category(c) != "Mn"
    )
    sin_tildes = _ORDINAL.sub(r"\1", _ESPACIO_ANTES_DE_PORCENTAJE.sub(r"\1%", sin_tildes))
    sin_tildes = _DISTRITAL.sub(r"\1 ", sin_tildes)
    return " ".join(sin_tildes.split())


def contiene(respuesta: str, esperado: str, raiz: bool = False) -> bool:
    """`contiene_texto` y `contiene_valor` comparan así: sin fallar por la forma de escribir y sin
    tomar una parte de otra palabra o cifra («1 de julio» no está en «11 de julio»). Con
    `raiz=True` (los textos), un esperado que termina en letra es una raíz: «desenfocad» está en
    «desenfocada»; uno que termina en cifra sigue exigiendo el límite («Ley 44» no está en «Ley
    440»)."""
    normal = normalizar_texto(esperado)
    derecha = "" if raiz and normal[-1:].isalpha() else r"(?!\w)"
    patron = rf"(?<!\w){re.escape(normal)}{derecha}"
    return re.search(patron, normalizar_texto(respuesta)) is not None
