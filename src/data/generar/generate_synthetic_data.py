"""Generador de la base sintética de RealSit v2 (sección 4.1 de la especificación técnica).

Produce exactamente 500 predios con 4 vigencias de IPU (2.000 obligaciones), las obligaciones de
ICA, los pagos y la tabla de tarifas del ICA. Todo sale de la semilla (`random.Random` y la
instancia de Faker), de `datos/` y de dos archivos de este paquete: `parametros_sinteticos.yaml` y
`usuarios_fijos.yaml`. Las tarifas del predial y del ICA se buscan siempre con
`buscar_tarifa_ipu` y `buscar_tarifa_ica` (año 2026, que es el único con datos); las vigencias de
2023 a 2025 quedan marcadas `origen_tarifa = 'sintetica'`.

Uso:
    uv run python -m src.data.generar.generate_synthetic_data [--semilla 42] [--predios 500]
        [--salida datos/realsit_sintetico.db] [--registrar-huella]
"""

import argparse
import random
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Any

import holidays
import yaml
from faker import Faker

from src.data.database import crear_base
from src.data.huella import RUTA_HUELLA, calcular_huella
from src.data.models import (
    Contribuyente,
    ObligacionTributaria,
    Pago,
    Predio,
)
from src.services.datos_anuales import calendario, umbral_ica_pesos
from src.services.ica import FilaTablaICA, PeriodoICA, actividades_de_la_tabla, buscar_tarifa_ica
from src.services.predial import buscar_tarifa_ipu, descuento_pronto_pago, valor_impuesto

AQUI = Path(__file__).resolve().parent
ANIO_DE_DATOS = 2026  # único año gravable con tarifas en datos/
CUOTAS_SPAC = 4


@dataclass
class DatosSinteticos:
    """Todo lo que se escribe en la base, antes de escribirlo."""

    fecha_referencia: date
    semilla: int
    contribuyentes: list[Contribuyente] = field(default_factory=list)
    predios: list[Predio] = field(default_factory=list)
    avaluos: list[tuple[str, int, int]] = field(default_factory=list)
    obligaciones: list[ObligacionTributaria] = field(default_factory=list)
    pagos: list[Pago] = field(default_factory=list)
    tarifas: list[FilaTablaICA] = field(default_factory=list)


def primer_dia_habil(anio: int, mes: int) -> date:
    """Primer día hábil del mes, con los festivos de Colombia."""
    festivos = holidays.CO(years=anio)
    dia = date(anio, mes, 1)
    while dia.weekday() >= 5 or dia in festivos:
        dia += timedelta(days=1)
    return dia


def _cargar(nombre: str) -> dict[str, Any]:
    return yaml.safe_load((AQUI / nombre).read_text(encoding="utf-8"))


def _pesos(valor: Decimal) -> int:
    return int(valor.quantize(Decimal(1), rounding=ROUND_HALF_UP))


class _Generador:
    def __init__(self, semilla: int, fecha_referencia: date) -> None:
        self.p = _cargar("parametros_sinteticos.yaml")
        self.rng = random.Random(semilla)
        self.fake = Faker("es_CO")
        self.fake.seed_instance(semilla)
        self.ref = fecha_referencia
        self.cal = calendario(ANIO_DE_DATOS)
        self.datos = DatosSinteticos(fecha_referencia, semilla)
        self._usados: dict[str, set[str]] = {
            k: set() for k in ("contribuyente", "matricula", "chip", "obligacion", "pago")
        }
        self.crecimiento = Decimal(self.p["crecimiento_anual_del_avaluo"])
        self.umbral_ica = umbral_ica_pesos(ANIO_DE_DATOS)

    # -- identificadores únicos, derivados de la semilla (H-03) --------------------------

    def _unico(self, clase: str, crear) -> str:
        for _ in range(10_000):
            valor = crear()
            if valor not in self._usados[clase]:
                self._usados[clase].add(valor)
                return valor
        raise RuntimeError(f"No se pudo generar un identificador único de {clase}.")

    def _id_obligacion(self) -> str:
        return self._unico("obligacion", lambda: f"OBL-{self.rng.getrandbits(40):010X}")

    def _id_pago(self) -> str:
        return self._unico("pago", lambda: f"PAG-{self.rng.getrandbits(40):010X}")

    def _reservar(self, clase: str, valor: str) -> str:
        if valor in self._usados[clase]:
            raise ValueError(f"Identificador repetido: {valor}")
        self._usados[clase].add(valor)
        return valor

    # -- fechas y avalúos ------------------------------------------------------------------

    def avaluo_de(self, avaluo_2026: int, vigencia: int) -> int:
        """Avalúo de la vigencia: el de 2026 deflactado con el crecimiento sintético."""
        valor = Decimal(avaluo_2026) / (1 + self.crecimiento) ** (ANIO_DE_DATOS - vigencia)
        return int((valor / 1000).quantize(Decimal(1), rounding=ROUND_HALF_UP)) * 1000

    def _fechas_ipu(self, vigencia: int) -> tuple[date, date]:
        if vigencia == ANIO_DE_DATOS:
            descuento = date.fromisoformat(self.cal["predial_pronto_pago_10"][0])
            limite = date.fromisoformat(self.cal["predial_sin_descuento"][0])
        else:
            f = self.p["fechas_sinteticas"]["ipu"][vigencia]
            descuento, limite = date.fromisoformat(f["descuento"]), date.fromisoformat(f["limite"])
        return descuento, limite

    def _pago(self, id_obligacion: str, fecha: date, valor: int) -> Pago:
        pago = Pago(
            id_pago=self._id_pago(),
            id_obligacion=id_obligacion,
            fecha_pago=fecha,
            valor_pagado=valor,
            medio_pago=self.rng.choice(self.p["medios_de_pago"]),
        )
        self.datos.pagos.append(pago)
        return pago

    # -- IPU -----------------------------------------------------------------------------------

    def _ipu(self, predio: Predio, vigencia: int, estado: str, opciones: dict[str, Any]) -> None:
        """Una obligación de IPU. `estado`: AL_DIA, VENCIDO o SPAC; NO_OBLIGADO sale de la regla."""
        avaluo = self.avaluo_de(predio.avaluo_catastral, vigencia)
        tarifa = buscar_tarifa_ipu(ANIO_DE_DATOS, predio.destino, predio.estrato, avaluo)
        descuento_limite, limite = self._fechas_ipu(vigencia)
        origen = "oficial" if vigencia == ANIO_DE_DATOS else "sintetica"
        obligado = tarifa.obligado
        valor = valor_impuesto(avaluo, tarifa.tarifa_por_mil) if obligado else 0
        descuento = descuento_pronto_pago(valor, ANIO_DE_DATOS)
        id_obl = self._id_obligacion()
        en_spac = False
        fecha_limite = limite
        if not obligado:
            estado_final = "NO_OBLIGADO"
        elif estado == "AL_DIA":
            estado_final = "AL_DIA"
            con_descuento = opciones.get("pagada_con_descuento", False)
            if con_descuento:
                fecha = descuento_limite - timedelta(days=self.rng.randint(1, 60))
                self._pago(id_obl, fecha, valor - descuento)
            else:
                fecha = limite - timedelta(
                    days=self.rng.randint(0, (limite - descuento_limite).days - 1)
                )
                self._pago(id_obl, fecha, valor)
        elif estado == "SPAC":
            estado_final, en_spac = "PENDIENTE", True
            cuotas = [date.fromisoformat(f) for f in self.cal["spac_cuotas"]]
            fecha_limite = next(c for c in cuotas if c >= self.ref)
            base, resto = divmod(valor, CUOTAS_SPAC)
            for i, fecha_cuota in enumerate(cuotas):
                if fecha_cuota < self.ref:
                    monto = base + (resto if i == CUOTAS_SPAC - 1 else 0)
                    self._pago(id_obl, fecha_cuota - timedelta(days=self.rng.randint(0, 5)), monto)
        else:
            estado_final = "VENCIDO"
        if estado_final == "VENCIDO" and limite >= self.ref:
            raise ValueError("Una obligación vencida debe tener su fecha límite antes del corte.")
        self.datos.obligaciones.append(
            ObligacionTributaria(
                id_obligacion=id_obl,
                matricula_catastral=predio.matricula_catastral,
                tipo_tributo="IPU",
                vigencia_fiscal=vigencia,
                base_gravable=avaluo,
                tarifa_por_mil=tarifa.tarifa_por_mil,
                valor_liquidado=valor,
                descuento_pronto_pago=descuento,
                fecha_limite_descuento=None if not obligado else descuento_limite,
                fecha_limite_pago=fecha_limite,
                estado_pago=estado_final,
                origen_tarifa=origen,
                en_spac=en_spac,
            )
        )

    def _ipu_del_predio(self, predio: Predio, opciones: dict[str, Any] | None = None) -> None:
        """Las 4 vigencias de IPU de un predio (2.000 en total con 500 predios)."""
        op = opciones or {}
        pr = self.p["proporciones"]
        for vigencia in self.p["vigencias_de_ipu"]:
            opv = dict(op)
            if vigencia == ANIO_DE_DATOS:
                estado = op.get("ipu_2026") or self._estado_ipu_2026(pr)
                if estado == "AL_DIA" and "pagada_con_descuento" not in op:
                    prob = pr["ipu_2026_pagada_con_descuento"]
                    opv["pagada_con_descuento"] = self.rng.random() < prob
            else:
                mora = op.get(f"mora_{vigencia}")
                if mora is None:
                    mora = self.rng.random() < pr["mora_en_vigencias_anteriores"]
                estado = "VENCIDO" if mora else "AL_DIA"
                opv["pagada_con_descuento"] = self.rng.random() < 0.4
            self._ipu(predio, vigencia, estado, opv)

    def _estado_ipu_2026(self, pr: dict[str, Any]) -> str:
        x = self.rng.random()
        if x < pr["ipu_2026"]["al_dia"]:
            return "AL_DIA"
        if x < pr["ipu_2026"]["al_dia"] + pr["ipu_2026"]["spac"]:
            return "SPAC"
        return "VENCIDO"

    # -- ICA ----------------------------------------------------------------------------------

    def _ica(self, contribuyente: Contribuyente, predio: Predio, ica: dict[str, Any]) -> None:
        """Una obligación de ICA por vigencia, en el predio donde se ejerce la actividad."""
        ciiu = contribuyente.codigo_ciiu or ""
        anual = buscar_tarifa_ica(ciiu, PeriodoICA(ANIO_DE_DATOS))
        ingresos: dict[int, int] = ica["ingresos"]
        regimen = contribuyente.regimen_ica
        for vigencia in (2023, 2024, 2025):
            base = ingresos[vigencia]
            valor = valor_impuesto(base, anual.tarifa_por_mil)
            limite = date.fromisoformat(str(self.p["fechas_sinteticas"]["ica_anual"][vigencia]))
            mora = ica.get("mora", {}).get(vigencia)
            if mora is None:
                mora = self.rng.random() < self.p["proporciones"]["mora_en_vigencias_anteriores"]
            id_obl = self._id_obligacion()
            if not mora:
                self._pago(id_obl, limite - timedelta(days=self.rng.randint(1, 15)), valor)
            self.datos.obligaciones.append(
                ObligacionTributaria(
                    id_obligacion=id_obl,
                    matricula_catastral=predio.matricula_catastral,
                    tipo_tributo="ICA",
                    vigencia_fiscal=vigencia,
                    base_gravable=base,
                    tarifa_por_mil=anual.tarifa_por_mil,
                    valor_liquidado=valor,
                    descuento_pronto_pago=0,
                    fecha_limite_descuento=None,
                    fecha_limite_pago=limite,
                    estado_pago="VENCIDO" if mora else "AL_DIA",
                    periodicidad="bimestral" if regimen == "comun_bimestral" else "anual",
                    origen_tarifa="sintetica",
                )
            )
        if regimen == "comun_bimestral":
            self._ica_2026_bimestral(
                predio, ciiu, int(ica["bimestre_2026"]), float(ica.get("prob_pago_bimestre", 1.0))
            )
        else:
            base = ingresos[ANIO_DE_DATOS]
            self.datos.obligaciones.append(
                ObligacionTributaria(
                    id_obligacion=self._id_obligacion(),
                    matricula_catastral=predio.matricula_catastral,
                    tipo_tributo="ICA",
                    vigencia_fiscal=ANIO_DE_DATOS,
                    base_gravable=base,
                    tarifa_por_mil=anual.tarifa_por_mil,
                    valor_liquidado=valor_impuesto(base, anual.tarifa_por_mil),
                    descuento_pronto_pago=0,
                    fecha_limite_descuento=None,
                    fecha_limite_pago=date.fromisoformat(
                        self.cal["ica_anual_comun_hasta_391_uvt_y_preferencial"][0]
                    ),
                    estado_pago="PENDIENTE",
                    periodicidad="anual",
                )
            )

    def _ica_2026_bimestral(
        self, predio: Predio, ciiu: str, base_bimestre: int, prob_pago: float
    ) -> None:
        """Bimestres ya causados al corte: su tarifa sale de ica_2026.yaml (art. 21 del Acuerdo
        1084: desde el bimestre 6 de 2026 rige ica_2027.yaml, que aún no se causa)."""
        plazos = [date.fromisoformat(f) for f in self.cal["ica_bimestral_comun_mayor_391_uvt"]]
        causados = [b for b in range(1, 7) if self._fin_bimestre(b) < self.ref]
        id_obl = self._id_obligacion()
        total_base = total_valor = 0
        sin_pagar: list[date] = []
        ultimo_plazo = plazos[causados[-1] - 1]
        tarifa = buscar_tarifa_ica(ciiu, PeriodoICA(ANIO_DE_DATOS, "bimestral", causados[-1]))
        for b in causados:
            tarifa_b = buscar_tarifa_ica(ciiu, PeriodoICA(ANIO_DE_DATOS, "bimestral", b))
            valor_b = valor_impuesto(base_bimestre, tarifa_b.tarifa_por_mil)
            total_base += base_bimestre
            total_valor += valor_b
            vencido = plazos[b - 1] < self.ref
            if vencido and self.rng.random() < prob_pago:
                self._pago(id_obl, plazos[b - 1] - timedelta(days=self.rng.randint(1, 10)), valor_b)
            else:
                sin_pagar.append(plazos[b - 1])
        vencidas = [f for f in sin_pagar if f < self.ref]
        estado = "VENCIDO" if vencidas else "PENDIENTE"
        self.datos.obligaciones.append(
            ObligacionTributaria(
                id_obligacion=id_obl,
                matricula_catastral=predio.matricula_catastral,
                tipo_tributo="ICA",
                vigencia_fiscal=ANIO_DE_DATOS,
                base_gravable=total_base,
                tarifa_por_mil=tarifa.tarifa_por_mil,
                valor_liquidado=total_valor,
                descuento_pronto_pago=0,
                fecha_limite_descuento=None,
                fecha_limite_pago=min(vencidas) if vencidas else ultimo_plazo,
                estado_pago=estado,
                periodicidad="bimestral",
            )
        )

    def _fin_bimestre(self, b: int) -> date:
        mes = 2 * b
        siguiente = date(ANIO_DE_DATOS + (mes == 12), mes % 12 + 1, 1)
        return siguiente - timedelta(days=1)

    # -- contribuyentes y predios --------------------------------------------------------------

    def _ica_aleatorio(self, ingresos_2025: int) -> dict[str, Any]:
        crec = Decimal(1) + self.crecimiento

        def ajustar(valor: Decimal) -> int:
            return int((valor / 1000).quantize(Decimal(1), rounding=ROUND_HALF_UP)) * 1000

        i25 = Decimal(ingresos_2025)
        return {
            "ingresos": {
                2023: ajustar(i25 / crec**2),
                2024: ajustar(i25 / crec),
                2025: ingresos_2025,
                2026: ajustar(i25 * crec),
            },
            "bimestre_2026": ajustar(i25 * crec / 6),
            "prob_pago_bimestre": self.p["proporciones"]["bimestre_pagado"],
        }

    def _regimen(self, ciiu: str, ingresos_2025: int) -> str:
        impuesto_2025 = valor_impuesto(
            ingresos_2025, buscar_tarifa_ica(ciiu, PeriodoICA(ANIO_DE_DATOS)).tarifa_por_mil
        )
        if impuesto_2025 > self.umbral_ica:
            return "comun_bimestral"
        if self.rng.random() < self.p["proporciones"]["preferencial_entre_los_de_hasta_391_uvt"]:
            return "preferencial"
        return "comun_anual"

    def _agregar_predio(self, predio: Predio, opciones: dict[str, Any] | None = None) -> None:
        self.datos.predios.append(predio)
        for vigencia in self.p["vigencias_de_ipu"]:
            self.datos.avaluos.append(
                (
                    predio.matricula_catastral,
                    vigencia,
                    self.avaluo_de(predio.avaluo_catastral, vigencia),
                )
            )
        self._ipu_del_predio(predio, opciones)

    def _predio_aleatorio(self, id_contribuyente: str, destino: str | None) -> Predio:
        pr = self.p["proporciones"]
        destino = (
            destino
            or self.rng.choices(list(pr["destino"]), weights=list(pr["destino"].values()))[0]
        )
        estrato = None
        if destino == "residencial":
            estrato = self.rng.choices(list(pr["estrato"]), weights=list(pr["estrato"].values()))[0]
            minimo, maximo = self.p["avaluo_millones"]["estrato"][estrato]
        else:
            minimo, maximo = self.p["avaluo_millones"][destino]
        avaluo = self.rng.randint(minimo, maximo) * 1_000_000 // 10 * 10
        localidad = self.rng.choice(self.p["localidades"])
        matricula = self._unico(
            "matricula", lambda: f"50C-{self.rng.randint(1_000_000, 8_999_999)}"
        )
        chip = self._unico("chip", lambda: f"AAA{self.rng.randint(1_000_000, 8_999_999)}")
        return Predio(
            matricula_catastral=matricula,
            chip=chip,
            id_contribuyente=id_contribuyente,
            direccion=f"{self.fake.street_address()}, {localidad}",
            localidad=localidad,
            estrato=estrato,
            destino=destino,
            avaluo_catastral=avaluo,
        )

    def _contribuyente_aleatorio(self) -> tuple[Contribuyente, dict[str, Any] | None]:
        pr = self.p["proporciones"]
        juridica = self.rng.random() < pr["persona_juridica"]
        if juridica:
            id_c = self._unico(
                "contribuyente", lambda: f"NIT-{self.rng.randint(10**9, 10**10 - 1)}"
            )
            nombre, tipo_doc, tipo = self.fake.company(), "NIT", "juridica"
        else:
            id_c = self._unico("contribuyente", lambda: f"CC-{self.rng.randint(10**8, 10**9 - 1)}")
            nombre, tipo_doc, tipo = self.fake.name(), "CC", "natural"
        con_actividad = juridica or self.rng.random() < pr["natural_con_actividad"]
        contribuyente = Contribuyente(id_c, tipo_doc, id_c.split("-")[1], nombre, tipo)
        if not con_actividad:
            return contribuyente, None
        ciiu = self.rng.choice(self.p["ciiu_de_muestra"])
        ica = self._ica_aleatorio(
            self.rng.randint(*self.p["ingresos_anuales_millones"]) * 1_000_000
        )
        contribuyente.codigo_ciiu = ciiu
        contribuyente.actividad_economica = buscar_tarifa_ica(
            ciiu, PeriodoICA(ANIO_DE_DATOS)
        ).actividad
        contribuyente.regimen_ica = self._regimen(ciiu, ica["ingresos"][2025])  # type: ignore[assignment]
        return contribuyente, ica

    def agregar_usuarios_fijos(self) -> None:
        """Los usuarios de prueba de la sección 4.2, con sus entradas de usuarios_fijos.yaml."""
        for u in _cargar("usuarios_fijos.yaml")["usuarios"]:
            c = u["contribuyente"]
            ica = u.get("ica")
            if ica:  # los usuarios fijos no tienen mora al azar en el ICA de 2023 a 2025
                ica = {"mora": dict.fromkeys((2023, 2024, 2025), False), **ica}
            id_c = self._reservar("contribuyente", c["id"])
            contribuyente = Contribuyente(
                id_c, id_c.split("-")[0], id_c.split("-")[1], c["nombre"], c["tipo_persona"]
            )
            predio_ica: Predio | None = None
            if ica:
                contribuyente.codigo_ciiu = ica["ciiu"]
                contribuyente.actividad_economica = buscar_tarifa_ica(
                    ica["ciiu"], PeriodoICA(ANIO_DE_DATOS)
                ).actividad
                contribuyente.regimen_ica = ica["regimen"]
                impuesto_2025 = valor_impuesto(
                    ica["ingresos"][2025],
                    buscar_tarifa_ica(ica["ciiu"], PeriodoICA(ANIO_DE_DATOS)).tarifa_por_mil,
                )
                if (ica["regimen"] == "comun_bimestral") != (impuesto_2025 > self.umbral_ica):
                    raise ValueError(f"{u['id']}: el régimen no corresponde al umbral de 391 UVT")
            self.datos.contribuyentes.append(contribuyente)
            for d in u["predios"]:
                predio = Predio(
                    matricula_catastral=self._reservar("matricula", d["matricula"]),
                    chip=self._reservar("chip", d["chip"]),
                    id_contribuyente=id_c,
                    direccion=f"Dirección sintética de {u['id']}, {d['localidad']}",
                    localidad=d["localidad"],
                    estrato=d["estrato"],
                    destino=d["destino"],
                    avaluo_catastral=d["avaluo_2026"],
                )
                sin_mora = {f"mora_{v}": False for v in (2023, 2024, 2025)}
                self._agregar_predio(predio, {**sin_mora, **d})
                if d.get("ejerce_actividad"):
                    predio_ica = predio
            if ica:
                self._ica(contribuyente, predio_ica or self.datos.predios[-1], ica)

    def agregar_poblacion(self, n_predios: int) -> None:
        """Contribuyentes aleatorios hasta completar exactamente `n_predios` predios."""
        pr = self.p["proporciones"]
        while len(self.datos.predios) < n_predios:
            contribuyente, ica = self._contribuyente_aleatorio()
            self.datos.contribuyentes.append(contribuyente)
            restantes = n_predios - len(self.datos.predios)
            cantidad = min(2 if self.rng.random() < pr["dos_predios"] else 1, restantes)
            predio_ica = None
            for i in range(cantidad):
                comercial = (
                    "comercial"
                    if ica
                    and i == 0
                    and self.rng.random() < pr["primer_predio_comercial_si_hay_actividad"]
                    else None
                )
                predio = self._predio_aleatorio(contribuyente.id_contribuyente, comercial)
                self._agregar_predio(predio)
                if predio_ica is None or (
                    predio.destino == "comercial" and predio_ica.destino != "comercial"
                ):
                    predio_ica = predio
            if ica and predio_ica:
                self._ica(contribuyente, predio_ica, ica)


def generar_datos(
    semilla: int = 42, n_predios: int = 500, fecha_referencia: date | None = None
) -> DatosSinteticos:
    """Datos sintéticos de RealSit v2. La fecha de referencia es un parámetro fijo del conjunto:
    por defecto, el primer día hábil de octubre de 2026."""
    ref = fecha_referencia or primer_dia_habil(2026, 10)
    g = _Generador(semilla, ref)
    g.agregar_usuarios_fijos()
    g.agregar_poblacion(n_predios)
    g.datos.tarifas = actividades_de_la_tabla(ANIO_DE_DATOS)
    return g.datos


def poblar_base(db_path: str | Path, datos: DatosSinteticos) -> str:
    """Escribe los datos en SQLite (único camino de escritura) y devuelve la huella SHA-256."""
    with crear_base(db_path) as c:
        c.executemany(
            "INSERT INTO contribuyente VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    x.id_contribuyente,
                    x.tipo_documento,
                    x.numero_documento,
                    x.nombre,
                    x.tipo_persona,
                    x.codigo_ciiu,
                    x.actividad_economica,
                    x.regimen_ica,
                )
                for x in datos.contribuyentes
            ],
        )
        c.executemany(
            "INSERT INTO predio VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    x.matricula_catastral,
                    x.chip,
                    x.id_contribuyente,
                    x.direccion,
                    x.localidad,
                    x.estrato,
                    x.destino,
                    x.avaluo_catastral,
                    x.municipio,
                )
                for x in datos.predios
            ],
        )
        c.executemany("INSERT INTO avaluo_vigencia VALUES (?, ?, ?)", datos.avaluos)
        c.executemany(
            "INSERT INTO obligacion_tributaria VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    o.id_obligacion,
                    o.matricula_catastral,
                    o.tipo_tributo,
                    o.vigencia_fiscal,
                    o.periodicidad,
                    o.base_gravable,
                    format(o.tarifa_por_mil, "f"),
                    o.valor_liquidado,
                    o.descuento_pronto_pago,
                    o.fecha_limite_descuento.isoformat() if o.fecha_limite_descuento else None,
                    o.fecha_limite_pago.isoformat(),
                    o.estado_pago,
                    o.origen_tarifa,
                    int(o.en_spac),
                )
                for o in datos.obligaciones
            ],
        )
        c.executemany(
            "INSERT INTO pago VALUES (?, ?, ?, ?, ?)",
            [
                (p.id_pago, p.id_obligacion, p.fecha_pago.isoformat(), p.valor_pagado, p.medio_pago)
                for p in datos.pagos
            ],
        )
        c.executemany(
            "INSERT INTO tarifa_ica VALUES (?, ?, ?, ?, ?, ?)",
            [
                (t.ciiu, t.actividad, t.grupo, format(t.tarifa_por_mil, "f"), t.vigencia, t.fuente)
                for t in datos.tarifas
            ],
        )
    return calcular_huella(db_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera la base sintética de RealSit v2.")
    parser.add_argument("--semilla", type=int, default=42)
    parser.add_argument("--predios", type=int, default=500)
    parser.add_argument("--salida", default="datos/realsit_sintetico.db")
    parser.add_argument("--registrar-huella", action="store_true")
    args = parser.parse_args()
    datos = generar_datos(args.semilla, args.predios)
    huella = poblar_base(args.salida, datos)
    print(f"Contribuyentes: {len(datos.contribuyentes)}")
    print(f"Predios: {len(datos.predios)}")
    print(f"Obligaciones: {len(datos.obligaciones)}")
    print(f"Pagos: {len(datos.pagos)}")
    print(f"Fecha de referencia: {datos.fecha_referencia.isoformat()}")
    print(f"Huella SHA-256: {huella}")
    if args.registrar_huella:
        RUTA_HUELLA.write_text(huella + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
