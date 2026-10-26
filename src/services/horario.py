"""Horario de atención con festivos de Colombia y reloj inyectable (RNF-06 y RNF-07).

El reloj se inyecta para que el modo de evaluación (ADR-16) y las pruebas fijen la fecha. Los
festivos salen de `holidays` (incluye los trasladados por la Ley Emiliani).
"""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Any, Protocol
from zoneinfo import ZoneInfo

import holidays

DIAS = ("lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo")
MESES = (
    "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre",
    "octubre", "noviembre", "diciembre",
)  # fmt: skip


class Reloj(Protocol):
    def ahora(self) -> datetime: ...


@dataclass(frozen=True)
class RelojSistema:
    zona: str = "America/Bogota"

    def ahora(self) -> datetime:
        return datetime.now(ZoneInfo(self.zona))


@dataclass
class RelojFijo:
    """Reloj simulado: devuelve siempre el momento dado (o el que se le asigne)."""

    momento: datetime

    def ahora(self) -> datetime:
        return self.momento


def _hora(valor: time) -> str:
    sufijo = "a. m." if valor.hour < 12 else "p. m."
    hora = valor.hour % 12 or 12
    return f"{hora}:{valor.minute:02d} {sufijo}"


class Horario:
    """Lunes a viernes no festivos, de `inicio` (incluida) a `fin` (excluida), hora de Bogotá."""

    def __init__(
        self,
        inicio: time = time(8, 0),
        fin: time = time(17, 0),
        zona: str = "America/Bogota",
        reloj: Reloj | None = None,
    ) -> None:
        if inicio >= fin:
            raise ValueError("El inicio del horario debe ser anterior al fin.")
        self.inicio, self.fin = inicio, fin
        self.zona = ZoneInfo(zona)
        self.reloj = reloj or RelojSistema(zona)
        self._festivos: dict[int, Any] = {}

    @classmethod
    def desde_settings(cls, settings: Any, reloj: Reloj | None = None) -> "Horario":
        return cls(settings.horario_inicio, settings.horario_fin, settings.zona_horaria, reloj)

    def _local(self, momento: datetime | None) -> datetime:
        momento = momento or self.reloj.ahora()
        if momento.tzinfo is None:
            return momento.replace(tzinfo=self.zona)
        return momento.astimezone(self.zona)

    def _festivo(self, dia: date) -> bool:
        if dia.year not in self._festivos:
            self._festivos[dia.year] = holidays.Colombia(years=dia.year)
        return dia in self._festivos[dia.year]

    def _habil(self, dia: date) -> bool:
        return dia.weekday() < 5 and not self._festivo(dia)

    def en_horario(self, momento: datetime | None = None) -> bool:
        local = self._local(momento)
        return self._habil(local.date()) and self.inicio <= local.time() < self.fin

    def proxima_apertura(self, momento: datetime | None = None) -> datetime:
        """Primer momento de atención desde `momento`, saltando fines de semana y festivos."""
        local = self._local(momento)
        dia = local.date()
        if not (self._habil(dia) and local.time() < self.inicio):
            dia += timedelta(days=1)
            while not self._habil(dia):
                dia += timedelta(days=1)
        return datetime.combine(dia, self.inicio, tzinfo=self.zona)

    def aviso_fuera_de_horario(self, momento: datetime | None = None) -> str:
        """Aviso informativo con el horario y cuándo se vuelve a atender (RNF-07)."""
        apertura = self.proxima_apertura(momento)
        cuando = (
            f"{DIAS[apertura.weekday()]} {apertura.day} de {MESES[apertura.month - 1]} "
            f"de {apertura.year} a las {_hora(apertura.time())}."
        )
        return (
            "En este momento estoy fuera del horario de atención. Atiendo de lunes a viernes, de "
            f"{_hora(self.inicio)} a {_hora(self.fin)} (hora de Colombia), sin contar festivos. "
            f"Vuelvo a atender el {cuando} Fuera de ese horario no puedo responder consultas ni "
            "transferirlas a un funcionario: escríbeme de nuevo entonces."
        )
