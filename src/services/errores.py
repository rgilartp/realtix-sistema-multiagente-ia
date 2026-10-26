"""Errores del dominio: los servicios fallan de forma explícita y nunca estiman un dato faltante."""


class AnioSinDatosError(LookupError):
    """No hay archivo de `datos/` para el año gravable pedido."""

    def __init__(self, anio: int, que: str) -> None:
        super().__init__(f"No hay datos de {que} para el año gravable {anio}.")
        self.anio = anio


class DatoNoPublicadoError(LookupError):
    """El dato existe en `datos/`, pero su valor aún no se publica (p. ej. el SMMLV de 2027)."""

    def __init__(self, dato: str, anio: int) -> None:
        super().__init__(f"El {dato} de {anio} aún no se publica; no se estima.")
        self.dato = dato
        self.anio = anio


class ActividadNoReconocidaError(LookupError):
    """La actividad económica (CIIU) no está en la tabla de tarifas del ICA."""

    def __init__(self, actividad: str) -> None:
        super().__init__(f"Actividad económica no reconocida: {actividad}")
        self.actividad = actividad
