"""Segunda implementación del contrato `RealSitAdapter`: los mismos datos, en memoria.

Sirve a las pruebas de contrato (RF-SYS-05) y a los nodos simulados de B4, que no necesitan
SQLite. Aplica exactamente las reglas de `AdaptadorBase`; solo aporta el almacenamiento.
"""

from collections import defaultdict

from src.data.adapter import VIGENCIA_ACTUAL, AdaptadorBase, RegistroDeCasos
from src.data.generar.generate_synthetic_data import DatosSinteticos
from src.data.models import ObligacionTributaria, Pago, Predio, Tarifa


class RealSitEnMemoria(AdaptadorBase):
    def __init__(
        self,
        datos: DatosSinteticos,
        registro_casos: RegistroDeCasos | None = None,
        vigencia: int = VIGENCIA_ACTUAL,
    ) -> None:
        super().__init__(registro_casos, vigencia)
        self._predios = {p.matricula_catastral: p for p in datos.predios}
        self._por_contribuyente: dict[str, list[Predio]] = defaultdict(list)
        for p in sorted(datos.predios, key=lambda x: x.matricula_catastral):
            self._por_contribuyente[p.id_contribuyente].append(p)
        self._obligaciones_por_predio: dict[str, list[ObligacionTributaria]] = defaultdict(list)
        por_id: dict[str, ObligacionTributaria] = {}
        for o in datos.obligaciones:
            self._obligaciones_por_predio[o.matricula_catastral].append(o)
            por_id[o.id_obligacion] = o
        self._pagos_por_predio: dict[str, list[Pago]] = defaultdict(list)
        for pago in datos.pagos:
            self._pagos_por_predio[por_id[pago.id_obligacion].matricula_catastral].append(pago)
        self._avaluos = {(m, v): a for m, v, a in datos.avaluos}
        self._tarifas = {
            t.ciiu: Tarifa(t.ciiu, t.tarifa_por_mil, t.actividad, t.vigencia, t.fuente, t.grupo)
            for t in datos.tarifas
        }

    def _predio(self, matricula: str) -> Predio | None:
        return self._predios.get(matricula)

    def _predios_de(self, contribuyente_id: str) -> list[Predio]:
        return list(self._por_contribuyente.get(contribuyente_id, []))

    def _obligaciones(self, matricula: str) -> list[ObligacionTributaria]:
        return list(self._obligaciones_por_predio.get(matricula, []))

    def _pagos(self, matricula: str) -> list[Pago]:
        return list(self._pagos_por_predio.get(matricula, []))

    def _avaluo(self, matricula: str, vigencia: int) -> int | None:
        return self._avaluos.get((matricula, vigencia))

    def _tarifa_ica(self, codigo: str) -> Tarifa | None:
        return self._tarifas.get(codigo)
