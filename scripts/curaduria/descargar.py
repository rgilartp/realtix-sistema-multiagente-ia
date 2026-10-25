"""Descarga cada fuente del catálogo a `scripts/curaduria/descargas/` (carpeta ignorada por git).

Si un enlace falla o falta, lo anota en `descargas/estado.yaml` y sigue con las demás.
Uso: uv run python scripts/curaduria/descargar.py
"""

import httpx
import yaml
from comun import DESCARGAS, cargar_catalogo

_EXTENSION = {"html": "html", "pdf": "pdf", "pdf_escaneado": "pdf"}


def descargar() -> dict[str, dict]:
    catalogo = cargar_catalogo()
    DESCARGAS.mkdir(exist_ok=True)
    estado: dict[str, dict] = {}
    with httpx.Client(
        follow_redirects=True, timeout=60, headers={"User-Agent": "curaduria/1.0"}
    ) as cliente:
        for fuente in catalogo["fuentes"]:
            url = fuente["url"]
            if not url:
                estado[fuente["id"]] = {"estado": "sin_enlace"}
                continue
            destino = DESCARGAS / f"{fuente['id']}.{_EXTENSION[fuente['formato']]}"
            if destino.exists():
                estado[fuente["id"]] = {"estado": "ok", "bytes": destino.stat().st_size}
                continue
            try:
                respuesta = cliente.get(url)
                respuesta.raise_for_status()
                destino.write_bytes(respuesta.content)
                estado[fuente["id"]] = {"estado": "ok", "bytes": len(respuesta.content)}
            except httpx.HTTPError as error:
                estado[fuente["id"]] = {"estado": "falla", "motivo": type(error).__name__}
    (DESCARGAS / "estado.yaml").write_text(
        yaml.safe_dump(estado, allow_unicode=True), encoding="utf-8"
    )
    return estado


if __name__ == "__main__":
    for id_fuente, datos in descargar().items():
        print(f"{id_fuente}: {datos['estado']}")
