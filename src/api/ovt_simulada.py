"""Sesión de la OVT simulada (ADR-07): solo con `OVT_SIMULADA_ACTIVA=true`.

Emite el token de uno de los usuarios de prueba fijos (sección 4.2) y lista esos usuarios para la
página de la OVT simulada (B11). Con la bandera apagada, los dos responden 404.
"""

from fastapi import APIRouter, HTTPException

from src.api.acceso import DURACION_TOKEN_S, emitir_token
from src.api.comun import Servicios
from src.api.esquemas import SesionSimulada, SolicitudSesionSimulada, UsuarioSimulado

router = APIRouter(prefix="/api/v1/ovt-simulada", tags=["OVT simulada"])


def _exigir_activa(servicios: Servicios) -> None:
    if not servicios.settings.ovt_simulada_activa:
        raise HTTPException(status_code=404, detail="No encontré lo que buscas.")


@router.post("/sesion", response_model=SesionSimulada)
def sesion(solicitud: SolicitudSesionSimulada, servicios: Servicios) -> SesionSimulada:
    _exigir_activa(servicios)
    usuario = next((u for u in servicios.usuarios if u["usuario"] == solicitud.usuario), None)
    if usuario is None:
        raise HTTPException(status_code=404, detail="Ese usuario de prueba no existe.")
    token = emitir_token(usuario["contribuyente_id"], servicios.settings.ovt_hmac_secret)
    return SesionSimulada(token=token, usuario=usuario["usuario"], expira_en_s=DURACION_TOKEN_S)


@router.get("/usuarios", response_model=list[UsuarioSimulado])
def usuarios(servicios: Servicios) -> list[UsuarioSimulado]:
    _exigir_activa(servicios)
    return [
        UsuarioSimulado(usuario=u["usuario"], nombre=u["nombre"], tipo_persona=u["tipo_persona"])
        for u in servicios.usuarios
    ]
