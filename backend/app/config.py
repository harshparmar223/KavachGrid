"""
KAVACHGRID 3.0 — Application Configuration

Centralized settings management using pydantic-settings.
All settings are loaded from environment variables or .env file.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ---------- PostgreSQL ----------
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "kavachgrid"
    POSTGRES_USER: str = "kavach_admin"
    POSTGRES_PASSWORD: str = "change_me_in_production"

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # ---------- FastAPI ----------
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    SECRET_KEY: str = "generate-a-secure-random-key-here"
    API_KEY: str = "kavach-device-api-key-change-me"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # ---------- MQTT ----------
    MQTT_BROKER_HOST: str = "localhost"
    MQTT_BROKER_PORT: int = 1883
    MQTT_BROKER_TLS_PORT: int = 8883
    MQTT_USERNAME: str = "kavachgrid"
    MQTT_PASSWORD: str = "change_me_in_production"
    MQTT_KEEPALIVE: int = 60

    # ---------- AI Engine ----------
    AI_MODEL_PATH: str = "ai/models/autoencoder_v1.h5"
    ANOMALY_THRESHOLD: float = 0.5

    # ---------- Risk Engine Weights ----------
    ENERGY_BALANCE_WEIGHT: float = 0.30
    AI_ANOMALY_WEIGHT: float = 0.25
    METER_HEALTH_WEIGHT: float = 0.20
    DEVICE_TRUST_WEIGHT: float = 0.15
    COMM_RELIABILITY_WEIGHT: float = 0.10


settings = Settings()
