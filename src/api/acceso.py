"""Capa de acceso (RF-AUT-01 a RF-AUT-04, ADR-07): token de la OVT simulada y tokens de rol.

El token es `base64url(carga).base64url(HMAC-SHA256(carga))`; la carga lleva el contribuyente
(`sub`), la emisión (`iat`) y el vencimiento (`exp`, 2 horas), en segundos. Un token inválido,
alterado o vencido equivale a no tener sesión (sección 3.11). El vencimiento se mide con el reloj
real, también en el modo de evaluación (el reloj simulado solo cambia el horario y «hoy»).
"""

import base64
import hashlib
import hmac
import json
import logging
import time
from dataclasses import dataclass, field

from fastapi import HTTPException
from pydantic import SecretStr

from src.data.adapter import RealSitAdapter
from src.integrations.robustez import con_tiempo_y_reintento

registro = logging.getLogger(__name__)

DURACION_TOKEN_S = 2 * 60 * 60


@dataclass(frozen=True)
class Sesion:
    """Lo que la capa de acceso le pasa al turno: el contribuyente, sus predios y su nombre (solo
    para el anonimizador; nunca va al estado del grafo ni a las trazas)."""

    contribuyente_id: str
    predios: list[str] = field(default_factory=list)
    nombres: tuple[str, ...] = ()


def _b64(datos: bytes) -> str:
    return base64.urlsafe_b64encode(datos).rstrip(b"=").decode("ascii")


def _de_b64(texto: str) -> bytes:
    return base64.urlsafe_b64decode(texto + "=" * (-len(texto) % 4))


def _firma(carga: str, secreto: SecretStr) -> str:
    clave = secreto.get_secret_value().encode("utf-8")
    return _b64(hmac.new(clave, carga.encode("ascii"), hashlib.sha256).digest())


def emitir_token(
    contribuyente_id: str,
    secreto: SecretStr,
    ahora: float | None = None,
    duracion_s: int = DURACION_TOKEN_S,
) -> str:
    """Token firmado de la OVT simulada."""
    emision = int(time.time() if ahora is None else ahora)
    datos = {"sub": contribuyente_id, "iat": emision, "exp": emision + duracion_s}
    carga = _b64(json.dumps(datos, separators=(",", ":")).encode("utf-8"))
    return f"{carga}.{_firma(carga, secreto)}"


def validar_token(token: str, secreto: SecretStr, ahora: float | None = None) -> str | None:
    """El contribuyente del token o `None` si no es válido (firma, forma o vencimiento)."""
    try:
        carga, firma = token.split(".")
        if not hmac.compare_digest(firma, _firma(carga, secreto)):
            return None
        datos = json.loads(_de_b64(carga))
        momento = time.time() if ahora is None else ahora
        if not isinstance(datos.get("sub"), str) or not (datos["iat"] <= momento < datos["exp"]):
            return None
        return datos["sub"]
    except (ValueError, KeyError, TypeError):
        return None


def token_de_cabecera(autorizacion: str | None) -> str | None:
    """`Authorization: Bearer <token>` -> el token."""
    if not autorizacion:
        return None
    tipo, _, token = autorizacion.partition(" ")
    if tipo.lower() != "bearer":
        return None
    return token.strip() or None


def resolver_sesion(
    autorizacion: str | None,
    secreto: SecretStr,
    adaptador: RealSitAdapter,
    nombre_de: dict[str, str],
    timeout_adaptador_s: float,
) -> Sesion | None:
    """Sesión del contribuyente con sus predios autorizados (sección 3.3, paso 1); sin token
    válido, `None` (solo consultas generales, RF-AUT-03)."""
    token = token_de_cabecera(autorizacion)
    contribuyente = validar_token(token, secreto) if token else None
    if contribuyente is None:
        return None
    predios = con_tiempo_y_reintento(
        lambda: adaptador.get_predios_contribuyente(contribuyente),
        timeout_adaptador_s,
        servicio="adaptador",
    )
    nombre = nombre_de.get(contribuyente)
    return Sesion(
        contribuyente, [p.matricula_catastral for p in predios], (nombre,) if nombre else ()
    )


def exigir_rol(autorizacion: str | None, esperado: SecretStr) -> None:
    """Token de funcionario o de administrador; si no coincide, 401 sin más detalle."""
    token = token_de_cabecera(autorizacion)
    if token is None or not hmac.compare_digest(
        token.encode("utf-8"), esperado.get_secret_value().encode("utf-8")
    ):
        raise HTTPException(status_code=401, detail="Necesitas un token válido para esta consulta.")
