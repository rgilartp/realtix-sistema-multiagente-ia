"""Configuración del sistema multiagente de IA, leída de variables de entorno (RNF-14).

Los secretos y lo propio de cada máquina van en `.env` (ver `.env.example`). Los parámetros
(umbral, pesos, horario y tiempos) tienen aquí su valor por defecto y, en el servidor, en
`deploy/servidor.env`.
"""

from datetime import time
from pathlib import Path
from typing import Annotated

from pydantic import Field, SecretStr, ValidationError, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class ConfiguracionIncompletaError(RuntimeError):
    """Falta una variable obligatoria o alguna tiene un valor inválido."""


class Settings(BaseSettings):
    """Variables de entorno de la sección 3.10 de la especificación técnica."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        # Un valor vacío (como los de .env.example) cuenta como variable faltante.
        env_ignore_empty=True,
    )

    # Modelos (ADR-02). La clave nunca se llama ANTHROPIC_API_KEY: se pasa explícita al cliente.
    realtix_anthropic_api_key: SecretStr
    openai_api_key: SecretStr
    modelo_orquestador: str = "claude-sonnet-5-5"
    modelo_ipu: str = "claude-haiku-5-5"
    modelo_ica: str = "claude-haiku-5-5"
    modelo_general: str = "claude-haiku-5-5"
    modelo_ocr: str = "claude-haiku-5-5"
    modelo_juez: str = "claude-opus-5-5"
    modelo_embeddings: str = "text-embedding-3-large"

    # Observabilidad (ADR-11)
    langsmith_api_key: SecretStr | None = None
    langsmith_project: str = "realtix-sistema-multiagente-ia"
    langsmith_tracing: bool = False

    # Datos (ADR-05)
    realsit_db_path: Path = Path("datos/realsit_sintetico.db")
    database_url: SecretStr
    chroma_host: str = "localhost"
    chroma_port: int = 8000

    # Confianza y enrutamiento (ADR-17)
    umbral_confianza: float = Field(default=0.7, ge=0, le=1)
    peso_similitud: float = Field(default=0.4, ge=0, le=1)
    peso_suficiencia: float = Field(default=0.4, ge=0, le=1)
    peso_cobertura: float = Field(default=0.2, ge=0, le=1)
    max_reclasificaciones: int = Field(default=2, ge=0)

    # Tiempos máximos, en segundos (RNF-08)
    timeout_modelo_s: float = Field(default=20.0, gt=0)
    timeout_chroma_s: float = Field(default=5.0, gt=0)
    timeout_adaptador_s: float = Field(default=5.0, gt=0)

    # Seguridad
    ovt_hmac_secret: SecretStr
    token_funcionario: SecretStr
    token_admin: SecretStr
    cors_origenes: Annotated[list[str], NoDecode] = ["http://localhost:5173"]
    ovt_simulada_activa: bool = False

    # Horario y evaluación (RNF-06 y ADR-16)
    horario_inicio: time = time(8, 0)
    horario_fin: time = time(17, 0)
    zona_horaria: str = "America/Bogota"
    modo_evaluacion: bool = False
    fallas_inyectables: bool = False

    # Archivos (RF-OCR-01)
    tamano_maximo_archivo_mb: int = Field(default=5, gt=0)

    @field_validator("cors_origenes", mode="before")
    @classmethod
    def _separar_origenes(cls, valor: object) -> object:
        """Acepta los orígenes como texto separado por comas."""
        if isinstance(valor, str):
            return [origen.strip() for origen in valor.split(",") if origen.strip()]
        return valor

    @model_validator(mode="after")
    def _validar_coherencia(self) -> "Settings":
        """Los pesos de la confianza suman 1 y el horario empieza antes de terminar."""
        suma = self.peso_similitud + self.peso_suficiencia + self.peso_cobertura
        if abs(suma - 1) > 1e-9:
            raise ValueError(f"PESO_SIMILITUD + PESO_SUFICIENCIA + PESO_COBERTURA = {suma}, no 1")
        if self.horario_inicio >= self.horario_fin:
            raise ValueError("HORARIO_INICIO debe ser anterior a HORARIO_FIN")
        return self


def cargar_configuracion(env_file: str | Path | None = ".env") -> Settings:
    """Lee la configuración y, si algo falla, explica en español qué variable revisar."""
    try:
        return Settings(_env_file=env_file)
    except ValidationError as error:
        faltantes = sorted(
            str(e["loc"][0]).upper() for e in error.errors() if e["type"] == "missing" and e["loc"]
        )
        invalidas = [
            f"{str(e['loc'][0]).upper() if e['loc'] else 'configuración'}: {e['msg']}"
            for e in error.errors()
            if e["type"] != "missing"
        ]
        partes = []
        if faltantes:
            partes.append("Faltan variables de entorno obligatorias: " + ", ".join(faltantes) + ".")
        if invalidas:
            partes.append("Hay valores inválidos: " + "; ".join(invalidas) + ".")
        partes.append("Revise el archivo .env; .env.example explica cada variable.")
        raise ConfiguracionIncompletaError(" ".join(partes)) from None
