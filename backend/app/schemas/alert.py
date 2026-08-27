"""
KAVACHGRID 3.0 — Alert Pydantic Schemas
Phase 2: Request/Response validation models for Alerts

Schemas:
    - AlertCreate: Engine-generated alert input
    - AlertAcknowledge: Operator acknowledgement
    - AlertResponse: API response output
    - AlertSummary: Dashboard summary counts
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class AlertCreate(BaseModel):
    """Schema for creating an alert (from analytics engines)."""

    device_id: Optional[str] = Field(None, examples=["CONSUMER-H1"])
    alert_type: str = Field(
        ...,
        pattern="^(energy_imbalance|anomaly|meter_health|device_trust|communication|localization)$",
        examples=["energy_imbalance"],
    )
    severity: str = Field(
        ...,
        pattern="^(low|medium|high|critical)$",
        examples=["high"],
    )
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        examples=["High Energy Imbalance Detected"],
    )
    message: str = Field(
        ...,
        min_length=1,
        examples=["Unaccounted energy of 450W detected in Zone A. Feeder: 2100W, Consumers: 1500W, Expected loss: 150W."],
    )
    details: Optional[Dict[str, Any]] = Field(
        None,
        examples=[{
            "feeder_power": 2100.0,
            "consumer_power": 1500.0,
            "expected_loss": 150.0,
            "unaccounted": 450.0,
            "threshold": 200.0,
        }],
    )


class AlertAcknowledge(BaseModel):
    """Schema for acknowledging an alert."""

    acknowledged_by: UUID = Field(..., description="User ID of the acknowledging operator")


class AlertResponse(BaseModel):
    """Schema for alert API responses."""

    id: UUID
    device_id: Optional[str] = None
    alert_type: str
    severity: str
    title: str
    message: str
    details: Optional[Dict[str, Any]] = None
    acknowledged: bool
    acknowledged_by: Optional[UUID] = None
    acknowledged_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AlertSummary(BaseModel):
    """Dashboard alert summary."""

    total: int
    unacknowledged: int
    by_severity: Dict[str, int] = Field(
        ...,
        examples=[{"critical": 2, "high": 5, "medium": 10, "low": 3}],
    )
    by_type: Dict[str, int] = Field(
        ...,
        examples=[{"energy_imbalance": 3, "anomaly": 7, "meter_health": 5}],
    )
