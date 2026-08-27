"""
KAVACHGRID 3.0 — Pydantic Schemas Package
Phase 2: Complete — All validation models

Re-exports all schemas for convenient importing:
    from app.schemas import DeviceCreate, DeviceResponse, TelemetryCreate, ...
"""

from app.schemas.user import (
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
)
from app.schemas.device import (
    DeviceCreate,
    DeviceResponse,
    DeviceStatus,
    DeviceUpdate,
)
from app.schemas.telemetry import (
    TelemetryBatch,
    TelemetryCreate,
    TelemetryResponse,
    TelemetryStats,
)
from app.schemas.alert import (
    AlertAcknowledge,
    AlertCreate,
    AlertResponse,
    AlertSummary,
)
from app.schemas.risk import (
    RiskRanking,
    RiskScoreCreate,
    RiskScoreResponse,
)
from app.schemas.localization import (
    LocalizationCreate,
    LocalizationResponse,
    LocalizationUpdate,
    SuspectDevice,
)

__all__ = [
    # Users
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserLogin",
    # Devices
    "DeviceCreate",
    "DeviceUpdate",
    "DeviceResponse",
    "DeviceStatus",
    # Telemetry
    "TelemetryCreate",
    "TelemetryResponse",
    "TelemetryBatch",
    "TelemetryStats",
    # Alerts
    "AlertCreate",
    "AlertAcknowledge",
    "AlertResponse",
    "AlertSummary",
    # Risk
    "RiskScoreCreate",
    "RiskScoreResponse",
    "RiskRanking",
    # Localization
    "LocalizationCreate",
    "LocalizationUpdate",
    "LocalizationResponse",
    "SuspectDevice",
]
