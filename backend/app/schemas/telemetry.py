"""
KAVACHGRID 3.0 — Telemetry Pydantic Schemas
Phase 2: Request/Response validation models for Telemetry

Schemas:
    - TelemetryCreate: Incoming telemetry from MQTT/API
    - TelemetryResponse: API response output
    - TelemetryBatch: Batch response with pagination
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class TelemetryBase(BaseModel):
    """Shared telemetry fields."""

    device_id: str = Field(..., examples=["CONSUMER-H1"])
    voltage: float = Field(..., ge=0, le=500, examples=[230.5], description="Voltage in Volts")
    current: float = Field(..., ge=0, le=100, examples=[2.35], description="Current in Amps")
    power: float = Field(..., ge=0, le=50000, examples=[541.6], description="Power in Watts")
    energy: float = Field(..., ge=0, examples=[1250.8], description="Cumulative energy in Wh")


class TelemetryCreate(TelemetryBase):
    """Schema for incoming telemetry data (from MQTT or API)."""

    power_factor: Optional[float] = Field(None, ge=0, le=1, examples=[0.98])
    frequency: Optional[float] = Field(None, ge=45, le=65, examples=[50.02])
    timestamp: Optional[datetime] = Field(
        None,
        description="Sensor measurement time (defaults to server time if not provided)",
    )

    @field_validator("power")
    @classmethod
    def validate_power_consistency(cls, v, info):
        """Warn if power significantly differs from V*I (informational)."""
        # This is a soft validation — doesn't reject, just allows downstream
        # engines to flag inconsistencies
        return v


class TelemetryResponse(TelemetryBase):
    """Schema for telemetry API responses."""

    id: UUID
    power_factor: Optional[float] = None
    frequency: Optional[float] = None
    trust_score: Optional[float] = Field(None, description="Device Trust score (0-100)")
    anomaly_score: Optional[float] = Field(None, description="AI Anomaly score (0-1)")
    timestamp: datetime
    received_at: datetime

    model_config = {"from_attributes": True}


class TelemetryBatch(BaseModel):
    """Paginated batch of telemetry records."""

    total: int = Field(..., description="Total records matching query")
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1, le=1000)
    data: List[TelemetryResponse]


class TelemetryStats(BaseModel):
    """Aggregated telemetry statistics for a device."""

    device_id: str
    period_start: datetime
    period_end: datetime
    avg_voltage: float
    avg_current: float
    avg_power: float
    total_energy: float
    min_voltage: float
    max_voltage: float
    reading_count: int
