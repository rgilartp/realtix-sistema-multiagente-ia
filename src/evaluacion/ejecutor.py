"""Ejecutor de escenarios por la API (sección 8.12; RF-OBS-05 · Ejecución repetible de pruebas).

Corre cada escenario como una conversación completa contra la API, local (`TestClient`) o
desplegada (`httpx`), en el modo de evaluación (ADR-16): cada turno lleva `X-Escenario-Id`, el
reloj del escenario en `X-Reloj-Simulado` y, en ROB-01 y ROB-02, `X-Falla-Inyectada`. La sesión de
cada usuario sale de la OVT simulada; los turnos con adjunto suben el recibo sintético de B10 por
`/api/v1/chat/documento`. Cada ensayo se agrega a `resultados.jsonl` apenas termina, para no perder
lo ya pagado si la corrida se interrumpe; `ya_corridos` permite reanudarla.
"""

import json
import time
import uuid
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any, Protocol

from src.data.generar.recibos import DESTINO as DIR_RECIBOS

TOKEN_INVALIDO = "token-invalido-de-prueba"
TIPO_ADJUNTO = "image/png"


class Respuesta(Protocol):
    status_code: int

    def json(self) -> Any: ...


class ClienteAPI(Protocol):
    """Lo que el ejecutor usa de `TestClient` o de `httpx.Client`."""

    def post(self, url: str, **kwargs: Any) -> Respuesta: ...


def ruta_del_recibo(nombre: str, directorio: Path = DIR_RECIBOS) -> Path:
    """PNG del recibo sintético de B10; si no están generados, los genera (semilla 42)."""
    ruta = directorio / f"{nombre}.png"
    if not ruta.exists():
        from src.data.generar.recibos import generar_recibos

        generar_recibos(directorio)
    if not ruta.exists():
        raise FileNotFoundError(f"No existe el recibo sintético «{nombre}».")
    return ruta


class Ejecutor:
    """Corre escenarios por la API; una instancia por corrida."""

    def __init__(
        self,
        cliente: ClienteAPI,
        corrida: str,
        dir_recibos: Path = DIR_RECIBOS,
        reloj: Callable[[], float] = time.perf_counter,
    ) -> None:
        self.cliente = cliente
        self.corrida = corrida
        self.dir_recibos = dir_recibos
        self._reloj = reloj
        self._tokens: dict[str, str] = {}

    def autorizacion(self, sesion: str | None) -> dict[str, str]:
        """Cabecera de la sesión: token de la OVT simulada, uno inválido o ninguno."""
        if sesion is None:
            return {}
        if sesion == "TOKEN_INVALIDO":
            return {"Authorization": f"Bearer {TOKEN_INVALIDO}"}
        if sesion not in self._tokens:
            r = self.cliente.post("/api/v1/ovt-simulada/sesion", json={"usuario": sesion})
            if r.status_code != 200:
                raise RuntimeError(
                    f"La OVT simulada no dio sesión a {sesion} (HTTP {r.status_code}); "
                    "¿OVT_SIMULADA_ACTIVA está encendida?"
                )
            self._tokens[sesion] = r.json()["token"]
        return {"Authorization": f"Bearer {self._tokens[sesion]}"}

    def cabeceras(self, esc: dict[str, Any]) -> dict[str, str]:
        cabeceras = {"X-Escenario-Id": str(esc["id"]), "X-Reloj-Simulado": str(esc["reloj"])}
        if esc.get("falla_inyectada"):
            cabeceras["X-Falla-Inyectada"] = str(esc["falla_inyectada"])
        return cabeceras | self.autorizacion(esc.get("sesion"))

    def _turno(self, turno: dict[str, Any], id_conversacion: str, cabeceras: dict[str, str]):
        if turno.get("adjunto"):
            ruta = ruta_del_recibo(str(turno["adjunto"]), self.dir_recibos)
            return self.cliente.post(
                "/api/v1/chat/documento",
                headers=cabeceras,
                data={"id_conversacion": id_conversacion, "mensaje": str(turno["usuario"])},
                files={"archivo": (ruta.name, ruta.read_bytes(), TIPO_ADJUNTO)},
            )
        return self.cliente.post(
            "/api/v1/chat/mensaje",
            headers=cabeceras,
            json={"id_conversacion": id_conversacion, "mensaje": str(turno["usuario"])},
        )

    def correr_ensayo(self, esc: dict[str, Any], ensayo: int = 1) -> dict[str, Any]:
        """Conversación completa del escenario; nunca lanza: un error queda en el ensayo."""
        id_conversacion = f"{self.corrida}-{esc['id']}-{ensayo}-{uuid.uuid4().hex[:8]}"[:64]
        resultado: dict[str, Any] = {
            "corrida": self.corrida,
            "escenario": esc["id"],
            "ensayo": ensayo,
            "id_conversacion": id_conversacion,
            "tipo_latencia": esc.get("tipo_latencia"),
            "turnos": [],
            "error": None,
        }
        try:
            cabeceras = self.cabeceras(esc)
            for turno in esc["turnos"]:
                inicio = self._reloj()
                r = self._turno(turno, id_conversacion, cabeceras)
                cliente_ms = round((self._reloj() - inicio) * 1000, 1)
                datos = r.json() if r.status_code < 500 else {}
                meta = datos.get("meta") or {}
                resultado["turnos"].append(
                    {
                        "usuario": str(turno["usuario"]),
                        "adjunto": turno.get("adjunto"),
                        "codigo_http": r.status_code,
                        "respuesta": datos.get("respuesta", ""),
                        "aviso_ia": datos.get("aviso_ia"),
                        "interlocutor": datos.get("interlocutor"),
                        "estado": datos.get("estado"),
                        "meta": meta,
                        "latencia_cliente_ms": cliente_ms,
                        "latencia_servidor_ms": (meta.get("tiempos_ms") or {}).get("total"),
                    }
                )
        except Exception as error:  # la corrida sigue con el siguiente escenario
            resultado["error"] = f"{type(error).__name__}: {error}"
        return resultado

    def correr(
        self,
        escenarios: Iterable[dict[str, Any]],
        k: int,
        salida: Path,
        al_avanzar: Callable[[dict[str, Any]], None] | None = None,
    ) -> list[dict[str, Any]]:
        """k ensayos de cada escenario, agregados a `salida` (JSONL); salta los ya corridos."""
        salida.parent.mkdir(parents=True, exist_ok=True)
        hechos = ya_corridos(salida)
        nuevos = []
        for esc in escenarios:
            for ensayo in range(1, k + 1):
                if (esc["id"], ensayo) in hechos:
                    continue
                resultado = self.correr_ensayo(esc, ensayo)
                with salida.open("a", encoding="utf-8") as archivo:
                    archivo.write(json.dumps(resultado, ensure_ascii=False) + "\n")
                nuevos.append(resultado)
                if al_avanzar:
                    al_avanzar(resultado)
        return nuevos


def leer_resultados(ruta: Path) -> list[dict[str, Any]]:
    if not ruta.exists():
        return []
    return [json.loads(linea) for linea in ruta.read_text(encoding="utf-8").splitlines() if linea]


def ya_corridos(ruta: Path) -> set[tuple[str, int]]:
    """Ensayos sin error ya guardados; los que fallaron por la red se vuelven a correr."""
    return {(r["escenario"], r["ensayo"]) for r in leer_resultados(ruta) if not r.get("error")}


def tokens_por_modelo(ensayo: dict[str, Any]) -> dict[str, dict[str, int]]:
    """Suma de los tokens por modelo de los turnos (la API los da en el modo de evaluación)."""
    total: dict[str, dict[str, int]] = {}
    for turno in ensayo.get("turnos", []):
        for modelo, t in ((turno.get("meta") or {}).get("tokens_por_modelo") or {}).items():
            acumulado = total.setdefault(modelo, {"entrada": 0, "salida": 0})
            acumulado["entrada"] += int(t.get("entrada", 0))
            acumulado["salida"] += int(t.get("salida", 0))
    return total
