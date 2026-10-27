"""Verificador de referencias (ADR-24, A7): corre antes de la corrida 1.

1. Cada fuente esperada que es una norma existe en `knowledge_base/` y cada ruta de `datos/` existe.
2. Cada cifra de la referencia y de las verificaciones con valor (pesos, porcentajes, por mil, UVT,
   SMMLV y fechas; no los números de norma, de artículo ni los años sueltos) coincide con alguna de:
   - `datos/` (tarifas, calendario, regímenes, UVT y SMMLV por año gravable);
   - los valores del usuario de la sesión: `usuarios_prueba.yaml` (escrito a mano y comprobado
     contra el adaptador) y el adaptador sintético (semilla 42);
   - el texto de las normas citadas en `knowledge_base/` (ajuste 3 de Rodolfo);
   - las cifras que da el propio contribuyente en sus mensajes;
   - una operación de dos cifras ya verificadas de la misma referencia o de esas fuentes (una
     diferencia, una suma, un porcentaje o base × tarifa / 1.000), que se informa como derivada;
   - en las fechas, el siguiente día hábil después del reloj del escenario (fines de semana y
     festivos de Colombia, del paquete `holidays`), que es lo que anuncia el aviso fuera de horario.
El «/ 1.000» de una operación por mil no es una cifra del escenario.

Limitación: se comprueba que la cifra exista en su fuente y con su tipo, no que sea la fila
correcta de una tabla (una tarifa de otro rango pasaría); ese error lo delata el valor en pesos
derivado, que sí debe cuadrar.
Lo que no coincide se lista; ninguna referencia aprobada se cambia sin que Rodolfo lo decida.
"""

import contextlib
import re
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from functools import cache
from typing import Any

import yaml

from src.evaluacion.escenarios import RAIZ
from src.evaluacion.recuperacion import NORMA, clave_de_norma, normas_de_la_base
from src.integrations.recuperador import RAIZ_BASE, normas_por_archivo

DIR_DATOS = RAIZ / "datos"
USUARIOS_PRUEBA = RAIZ / "tests" / "fixtures" / "usuarios_prueba.yaml"
MESES = (
    "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre",
    "octubre", "noviembre", "diciembre",
)  # fmt: skip
FECHA = re.compile(rf"\b(\d{{1,2}}) de ({'|'.join(MESES)}) de (\d{{4}})", re.IGNORECASE)
PESOS = re.compile(
    r"\$\s?(\d{1,3}(?:\.\d{3})+|\d+)(?!\.\d)|(?<![\w.,])(\d{1,3}(?:\.\d{3})+)(?![\w.,]?\d)"
)
PORCENTAJE = re.compile(r"(\d+(?:,\d+)?)\s?%")
POR_MIL = re.compile(r"(\d+(?:,\d+)?)\s?por mil")
UNIDADES = re.compile(
    r"(\d{1,3}(?:\.\d{3})*|\d+)(?:,\d+)?\s?(UVT|SMMLV|salarios m[ií]nimos)", re.IGNORECASE
)
DIVISOR_POR_MIL = re.compile(r"/\s?1\.000(?![\d.])")
NUMERO = re.compile(r"\d+(?:[.,]\d+)*")


@dataclass(frozen=True)
class Cifra:
    texto: str
    tipo: str  # pesos, porcentaje, por_mil, unidades o fecha
    valor: Decimal | date


@dataclass
class Resultado:
    escenario: str
    fuentes_faltantes: list[str] = field(default_factory=list)
    verificadas: list[tuple[str, str]] = field(default_factory=list)  # (cifra, dónde)
    sin_resolver: list[str] = field(default_factory=list)

    @property
    def pasa(self) -> bool:
        return not self.fuentes_faltantes and not self.sin_resolver


def _decimal(texto: str) -> Decimal:
    return Decimal(texto.replace(".", "").replace(",", "."))


def cifras_de(texto: str) -> list[Cifra]:
    """Cifras con tipo de un texto en español."""
    salida: list[Cifra] = []
    for m in FECHA.finditer(texto):
        dia, mes, anio = int(m.group(1)), MESES.index(m.group(2).lower()) + 1, int(m.group(3))
        salida.append(Cifra(m.group(0), "fecha", date(anio, mes, dia)))
    sin_fechas = DIVISOR_POR_MIL.sub(" ", FECHA.sub(" ", texto))
    for m in POR_MIL.finditer(sin_fechas):
        salida.append(Cifra(m.group(0), "por_mil", _decimal(m.group(1))))
    for m in PORCENTAJE.finditer(sin_fechas):
        salida.append(Cifra(m.group(0), "porcentaje", _decimal(m.group(1))))
    for m in UNIDADES.finditer(sin_fechas):
        salida.append(Cifra(m.group(0), "unidades", _decimal(m.group(1))))
    sin_otras = UNIDADES.sub(" ", POR_MIL.sub(" ", sin_fechas))
    for m in PESOS.finditer(sin_otras):
        crudo = m.group(1) or m.group(2)
        salida.append(Cifra(m.group(0).strip(), "pesos", _decimal(crudo)))
    return salida


TASAS_POR_CLAVE = {"porcentaje": "porcentaje", "tarifa": "por_mil", "por_mil": "por_mil"}


@dataclass
class _Acumulado:
    numeros: set[Decimal] = field(default_factory=set)
    tasas: dict[str, set[Decimal]] = field(
        default_factory=lambda: {"porcentaje": set(), "por_mil": set()}
    )
    fechas: set[date] = field(default_factory=set)

    def texto(self, valor: str) -> None:
        for c in cifras_de(valor):
            if c.tipo == "fecha":
                self.fechas.add(c.valor)  # type: ignore[arg-type]
            elif c.tipo in self.tasas:
                self.tasas[c.tipo].add(c.valor)  # type: ignore[arg-type]
            else:
                self.numeros.add(c.valor)  # type: ignore[arg-type]
        for n in NUMERO.findall(valor):
            with contextlib.suppress(InvalidOperation):
                self.numeros.add(Decimal(n) if "," not in n and n.count(".") <= 1 else _decimal(n))


def _numeros_de(valor: Any, destino: _Acumulado, tasa: str | None = None) -> None:
    """Números, tasas y fechas de una estructura de YAML; la clave dice si un número es una tasa
    («porcentaje…», «tarifa…», «…por_mil»)."""
    if isinstance(valor, dict):
        for clave, v in valor.items():
            tipo = next((t for k, t in TASAS_POR_CLAVE.items() if k in str(clave)), tasa)
            _numeros_de(v, destino, tipo)
    elif isinstance(valor, list | tuple):
        for v in valor:
            _numeros_de(v, destino, tasa)
    elif isinstance(valor, bool):
        return
    elif isinstance(valor, int | float | Decimal) or (
        tasa and isinstance(valor, str) and re.fullmatch(r"\d+(?:\.\d+)?", valor)
    ):
        numero = Decimal(str(valor))
        (destino.tasas[tasa] if tasa else destino.numeros).add(numero)
        destino.numeros.add(numero)
    elif isinstance(valor, date):
        destino.fechas.add(valor)
    elif isinstance(valor, str):
        try:
            destino.fechas.add(date.fromisoformat(valor))
        except ValueError:
            destino.texto(valor)


@dataclass(frozen=True)
class Fuente:
    nombre: str
    numeros: frozenset[Decimal]
    porcentajes: frozenset[Decimal]
    por_mil: frozenset[Decimal]
    fechas: frozenset[date]


def _fuente(nombre: str, *estructuras: Any) -> Fuente:
    a = _Acumulado()
    for e in estructuras:
        _numeros_de(e, a)
    return Fuente(
        nombre,
        frozenset(a.numeros),
        frozenset(a.tasas["porcentaje"]),
        frozenset(a.tasas["por_mil"]),
        frozenset(a.fechas),
    )


@cache
def fuente_datos() -> Fuente:
    archivos = sorted(DIR_DATOS.rglob("*.yaml"))
    return _fuente("datos/", *(yaml.safe_load(a.read_text(encoding="utf-8")) for a in archivos))


@cache
def _usuarios() -> dict[str, dict[str, Any]]:
    datos = yaml.safe_load(USUARIOS_PRUEBA.read_text(encoding="utf-8"))
    return {u["id"]: u for u in datos["usuarios"]}


@cache
def _adaptador() -> Any:
    from src.data.generar.generate_synthetic_data import generar_datos
    from src.data.memoria import RealSitEnMemoria

    return RealSitEnMemoria(generar_datos(42))


@cache
def fuente_usuario(sesion: str) -> Fuente:
    """Valores del usuario de prueba y de sus predios en el adaptador."""
    usuario = _usuarios()[sesion]
    adaptador = _adaptador()
    contribuyente = usuario["contribuyente_id"]
    del_adaptador: list[Any] = []
    for predio in adaptador.get_predios_contribuyente(contribuyente):
        estado = adaptador.get_estado_cuenta(predio.matricula_catastral, contribuyente)
        pagos = adaptador.get_historial_pagos(predio.matricula_catastral, contribuyente)
        del_adaptador.append(vars(predio))
        del_adaptador.append({"saldo": estado.saldo_total_pendiente})
        del_adaptador += [vars(o) for o in estado.obligaciones]
        del_adaptador += [vars(p) for p in pagos]
    return _fuente(f"usuario {sesion} y adaptador", usuario, del_adaptador)


@cache
def _textos_de_normas() -> dict[str, str]:
    """Clave de norma -> texto de sus archivos en la base."""
    textos: dict[str, list[str]] = {}
    for archivo, (norma, _) in normas_por_archivo().items():
        if clave := clave_de_norma(norma):
            textos.setdefault(clave, []).append((RAIZ_BASE / archivo).read_text(encoding="utf-8"))
    return {k: "\n".join(v) for k, v in textos.items()}


def normas_citadas(esc: dict[str, Any]) -> set[str]:
    """Claves de las normas de las fuentes esperadas y de las que cita la referencia."""
    textos = [*(esc.get("fuentes_esperadas") or []), str(esc["respuesta_referencia"])]
    claves = {clave_de_norma(t) for t in esc.get("fuentes_esperadas") or []}
    for m in NORMA.finditer(" ".join(textos)):
        claves.add(clave_de_norma(m.group(0)))
    return {c for c in claves if c}


def fuente_normas(claves: frozenset[str]) -> Fuente:
    textos = _textos_de_normas()
    return _fuente("normas citadas", *(textos[c] for c in sorted(claves) if c in textos))


def _coincide(c: Cifra, fuente: Fuente) -> bool:
    """Una cifra coincide con otra de su mismo tipo (un porcentaje, con un porcentaje)."""
    if c.tipo == "fecha":
        return c.valor in fuente.fechas
    if c.tipo == "porcentaje":
        return c.valor in fuente.porcentajes or c.valor / 100 in fuente.porcentajes  # type: ignore[operator]
    if c.tipo == "por_mil":
        return c.valor in fuente.por_mil
    return c.valor in fuente.numeros


@dataclass
class _Conocidas:
    pesos: set[Decimal] = field(default_factory=set)
    porcentajes: set[Decimal] = field(default_factory=set)
    por_mil: set[Decimal] = field(default_factory=set)

    def agregar(self, c: Cifra) -> None:
        destino = {"porcentaje": self.porcentajes, "por_mil": self.por_mil}.get(c.tipo, self.pesos)
        if isinstance(c.valor, Decimal):
            destino.add(c.valor)


def _derivada(c: Cifra, k: _Conocidas) -> str | None:
    """Una suma o diferencia de dos cifras en pesos verificadas, o una cifra verificada por una tasa
    verificada de la misma referencia (base × tarifa / 1.000 o base × porcentaje / 100)."""
    if c.tipo != "pesos":
        return None
    objetivo = c.valor
    for a in k.pesos:
        if any(a + b == objetivo or a - b == objetivo for b in k.pesos):
            return "suma o diferencia de dos cifras verificadas"
        if any((a * t / 1000).quantize(Decimal(1)) == objetivo for t in k.por_mil):
            return "base × tarifa por mil verificadas"
        if any((a * p / 100).quantize(Decimal(1)) == objetivo for p in k.porcentajes):
            return "base × porcentaje verificados"
    return None


def siguiente_dia_habil(desde: date) -> date:
    import holidays

    festivos = holidays.country_holidays("CO", years=range(desde.year, desde.year + 2))
    dia = desde + timedelta(days=1)
    while dia.weekday() >= 5 or dia in festivos:
        dia += timedelta(days=1)
    return dia


def verificar_escenario(esc: dict[str, Any], normas: set[str] | None = None) -> Resultado:
    normas = normas if normas is not None else normas_de_la_base()
    resultado = Resultado(esc["id"])
    for f in esc.get("fuentes_esperadas") or []:
        clave = clave_de_norma(f)
        ruta = re.search(r"datos/[\w./-]+\.yaml", f)
        if ruta and not (RAIZ / ruta.group(0)).exists() or clave and clave not in normas:
            resultado.fuentes_faltantes.append(f)
    if str(esc["respuesta_referencia"]).strip().startswith("PENDIENTE"):
        return resultado
    textos = [str(esc["respuesta_referencia"])]
    textos += [
        str(v["valor"])
        for v in esc["verificaciones_codigo"]
        if v["tipo"] in ("contiene_valor", "campo_ocr") and v.get("valor")
    ]
    cifras = list(dict.fromkeys(c for t in textos for c in cifras_de(t)))
    preguntas = _fuente("mensajes del contribuyente", [t["usuario"] for t in esc["turnos"]])
    fuentes = [fuente_datos(), fuente_normas(frozenset(normas_citadas(esc))), preguntas]
    if esc.get("sesion") in _usuarios():
        fuentes.insert(0, fuente_usuario(esc["sesion"]))
    pendientes = []
    conocidas = _Conocidas()
    for c in cifras:
        donde = next((f.nombre for f in fuentes if _coincide(c, f)), None)
        if donde:
            resultado.verificadas.append((c.texto, donde))
            conocidas.agregar(c)
        else:
            pendientes.append(c)
    habil = siguiente_dia_habil(datetime.fromisoformat(str(esc["reloj"])).date())
    avanzo = True
    while avanzo:  # una cifra derivada sirve para derivar la siguiente
        avanzo = False
        for c in list(pendientes):
            motivo = "siguiente día hábil después del reloj" if c.valor == habil else None
            motivo = motivo or _derivada(c, conocidas)
            if motivo:
                resultado.verificadas.append((c.texto, f"derivada: {motivo}"))
                conocidas.agregar(c)
                pendientes.remove(c)
                avanzo = True
    resultado.sin_resolver = [c.texto for c in pendientes]
    return resultado


def reporte(resultados: list[Resultado]) -> str:
    sin_resolver = [r for r in resultados if not r.pasa]
    lineas = [
        "# Verificación de las referencias (A7)",
        "",
        "Generado por `scripts/verificar_referencias.py`; no se edita a mano. Cada fuente esperada "
        "existe en la base y cada cifra coincide con `datos/`, con el usuario de prueba y el "
        "adaptador, con el texto de la norma citada o con una operación de cifras verificadas.",
        "",
        f"Escenarios revisados: {len(resultados)}. Cifras verificadas: "
        f"{sum(len(r.verificadas) for r in resultados)}. Escenarios con algo sin resolver: "
        f"{len(sin_resolver)}.",
        "",
    ]
    if sin_resolver:
        lineas += [
            "## Sin resolver (las decide Rodolfo)",
            "",
            "| Escenario | Fuente faltante | Cifra sin resolver |",
            "|---|---|---|",
        ]
        for r in sin_resolver:
            lineas.append(
                f"| {r.escenario} | {'; '.join(r.fuentes_faltantes) or '—'} | "
                f"{'; '.join(r.sin_resolver) or '—'} |"
            )
        lineas.append("")
    lineas += ["## Detalle", "", "| Escenario | Cifra | Dónde coincide |", "|---|---|---|"]
    for r in resultados:
        for cifra, donde in r.verificadas:
            lineas.append(f"| {r.escenario} | {cifra} | {donde} |")
    return "\n".join(lineas) + "\n"
