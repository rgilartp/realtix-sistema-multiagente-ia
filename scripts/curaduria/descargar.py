"""Descarga cada fuente del catálogo a `scripts/curaduria/descargas/` (carpeta ignorada por git).

Si un enlace falla o falta, lo anota en `descargas/estado.yaml` y sigue con las demás.
Uso: uv run python scripts/curaduria/descargar.py
"""

import httpx
import yaml
from comun import DESCARGAS, cargar_catalogo

_NAVEGADOR = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36"
_EXTENSION = {"html": "html", "pdf": "pdf", "pdf_escaneado": "pdf"}


def descargar() -> dict[str, dict]:
    catalogo = cargar_catalogo()
    DESCARGAS.mkdir(exist_ok=True)
    estado: dict[str, dict] = {}
    with httpx.Client(
        follow_redirects=True, timeout=60, headers={"User-Agent": _NAVEGADOR}
    ) as cliente:
        for fuente in catalogo["fuentes"] + catalogo.get("verificacion", []):
            urls = fuente["url"] if isinstance(fuente["url"], list) else [fuente["url"]]
            if not urls[0]:
                estado[fuente["id"]] = {"estado": "sin_enlace"}
                continue
            if fuente.get("archivo"):  # comparte el archivo de otra entrada
                estado[fuente["id"]] = {"estado": "ok", "archivo": fuente["archivo"]}
                continue
            tamano, falla = 0, None
            for n, url in enumerate(urls):
                sufijo = "" if n == 0 else f"__{n + 1}"
                destino = DESCARGAS / f"{fuente['id']}{sufijo}.{_EXTENSION[fuente['formato']]}"
                if not destino.exists():
                    try:
                        respuesta = cliente.get(url)
                        respuesta.raise_for_status()
                        destino.write_bytes(respuesta.content)
                    except httpx.HTTPError as error:
                        falla = type(error).__name__
                        break
                tamano += destino.stat().st_size
            estado[fuente["id"]] = (
                {"estado": "falla", "motivo": falla} if falla else {"estado": "ok", "bytes": tamano}
            )
    (DESCARGAS / "estado.yaml").write_text(
        yaml.safe_dump(estado, allow_unicode=True), encoding="utf-8"
    )
    return estado


if __name__ == "__main__":
    for id_fuente, datos in descargar().items():
        print(f"{id_fuente}: {datos['estado']}")
