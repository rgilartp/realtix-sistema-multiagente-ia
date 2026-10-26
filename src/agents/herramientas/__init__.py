"""Herramientas de los agentes sobre el adaptador y los servicios (sin lógica tributaria).

Cada herramienta llama al adaptador (con tiempo máximo y un reintento, RNF-08), al servicio que
calcula y entrega al modelo un diccionario con solo matrícula, vigencias, valores y estados
(`minimizar`, RNF-03), con las cifras ya formateadas para que el modelo las copie. Las notas y las
fuentes viajan aparte: el agente las agrega tal cual al final de la respuesta.

Los errores del dominio no son fallas: un dato no publicado, un año sin datos o una actividad no
reconocida vuelven al modelo como resultado, para que lo diga o pida el dato. El rechazo por
acceso (`PredioInaccesibleError`) y la falla del adaptador sí se propagan: los maneja el agente.
"""

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any, Literal, TypeVar

from src.data.adapter import RealSitAdapter
from src.integrations.robustez import con_tiempo_y_reintento
from src.services import obligaciones
from src.services.errores import ActividadNoReconocidaError, AnioSinDatosError, DatoNoPublicadoError
from src.services.horario import MESES
from src.services.obligaciones import CuentaTributo

T = TypeVar("T")
MATRICULA = re.compile(r"^50C-\d{7}$", re.IGNORECASE)
FUENTE_REALSIT = "Datos de tu cuenta en RealSit (base sintética de pruebas)"
TipoResultado = Literal[
    "ok", "no_publicado", "actividad_no_reconocida", "sin_sesion", "falta_dato", "argumentos"
]


@dataclass
class Contexto:
    """Lo que ve una herramienta: el adaptador, la sesión y la fecha de hoy (del reloj)."""

    adaptador: RealSitAdapter
    contribuyente_id: str | None
    predios_autorizados: list[str]
    hoy: date
    timeout_adaptador_s: float = 5.0
    matriculas_usadas: list[str] = field(default_factory=list)

    def llamar(self, funcion: Callable[[], T]) -> T:
        """Llamada al adaptador con tiempo máximo y un reintento."""
        return con_tiempo_y_reintento(funcion, self.timeout_adaptador_s, servicio="adaptador")


@dataclass(frozen=True)
class Resultado:
    datos: dict[str, Any]
    fuentes: tuple[str, ...] = ()
    notas: tuple[str, ...] = ()
    tipo: TipoResultado = "ok"


class FaltaDatoError(ValueError):
    """Falta un dato que debe dar el contribuyente (la matrícula, la sesión…)."""

    def __init__(self, mensaje: str, tipo: TipoResultado = "falta_dato") -> None:
        super().__init__(mensaje)
        self.tipo = tipo


@dataclass(frozen=True)
class Herramienta:
    nombre: str
    descripcion: str
    propiedades: dict[str, Any]
    requeridas: tuple[str, ...]
    funcion: Callable[[Contexto, dict[str, Any]], Resultado]

    def especificacion(self) -> dict[str, Any]:
        """Definición de la herramienta en el formato de la API de Anthropic."""
        return {
            "name": self.nombre,
            "description": self.descripcion,
            "input_schema": {
                "type": "object",
                "properties": self.propiedades,
                "required": list(self.requeridas),
                "additionalProperties": False,
            },
        }

    def ejecutar(self, contexto: Contexto, argumentos: dict[str, Any]) -> Resultado:
        """Ejecuta la herramienta; los errores del dominio vuelven como resultado."""
        try:
            return self.funcion(contexto, argumentos)
        except (DatoNoPublicadoError, AnioSinDatosError) as error:
            return Resultado({"no_publicado": str(error)}, tipo="no_publicado")
        except ActividadNoReconocidaError as error:
            return Resultado(
                {"actividad_no_reconocida": f"{error} Pide confirmar el código CIIU."},
                tipo="actividad_no_reconocida",
            )
        except FaltaDatoError as error:
            return Resultado({"falta_dato": str(error)}, tipo=error.tipo)
        except (ValueError, KeyError, TypeError) as error:
            return Resultado({"argumentos_invalidos": str(error)}, tipo="argumentos")


# -- Formato (presentación, no cálculo) ---------------------------------------------------------


def pesos(valor: int | None) -> str | None:
    return None if valor is None else "$" + f"{valor:,}".replace(",", ".")


def por_mil(valor: Decimal | None) -> str | None:
    if valor is None:
        return None
    texto = format(valor.normalize(), "f").replace(".", ",")
    return f"{texto} por mil"


def fecha(valor: date | str | None) -> str | None:
    if valor is None:
        return None
    if isinstance(valor, str):
        valor = date.fromisoformat(valor)
    return f"{valor.day} de {MESES[valor.month - 1]} de {valor.year}"


def entero(argumentos: dict[str, Any], nombre: str) -> int | None:
    valor = argumentos.get(nombre)
    return None if valor in (None, "") else int(valor)


# -- Sesión y predio ----------------------------------------------------------------------------


def exigir_sesion(contexto: Contexto) -> str:
    if not contexto.contribuyente_id:
        raise FaltaDatoError(
            "Para consultar datos de la cuenta hay que iniciar sesión en la OVT simulada.",
            tipo="sin_sesion",
        )
    return contexto.contribuyente_id


def resolver_matricula(contexto: Contexto, argumentos: dict[str, Any]) -> str:
    """La matrícula pedida o, si la sesión tiene un solo predio, ese; si no, falta el dato."""
    exigir_sesion(contexto)
    matricula = str(argumentos.get("matricula") or "").strip().upper()
    if not matricula:
        if len(contexto.predios_autorizados) == 1:
            matricula = contexto.predios_autorizados[0]
        else:
            propios = ", ".join(contexto.predios_autorizados) or "ninguno"
            raise FaltaDatoError(f"Falta saber de cuál predio. Predios de la sesión: {propios}.")
    if not MATRICULA.match(matricula):
        raise FaltaDatoError(f"«{matricula}» no es una matrícula catastral válida (50C-0000000).")
    contexto.matriculas_usadas.append(matricula)
    return matricula


def cuenta_tributo(contexto: Contexto, matricula: str, tributo: str) -> CuentaTributo:
    """Obligaciones y pagos de un solo tributo del predio (el adaptador verifica que sea propio)."""
    cid = exigir_sesion(contexto)
    estado = contexto.llamar(lambda: contexto.adaptador.get_estado_cuenta(matricula, cid))
    pagos = contexto.llamar(lambda: contexto.adaptador.get_historial_pagos(matricula, cid))
    return obligaciones.de_tributo(estado, pagos, tributo, contexto.hoy)


MATRICULA_OPCIONAL = {
    "matricula": {
        "type": "string",
        "description": "Matrícula catastral (50C-0000000); si se omite y la sesión tiene un solo "
        "predio, se usa ese.",
    }
}
ANIO = {"anio": {"type": "integer", "description": "Año gravable."}}
