"""
KAVACHGRID 3.0 — Localization Pydantic Schemas
Phase 2: Request/Response validation models for Progressive Localization

Important: This is an Investigation Support System.
It does NOT claim guaranteed identification of theft.
It ranks candidates and calculates investigation confidence.

Schemas:
    - LocalizationCreate: New localization result
    - LocalizationUpdate: Investigation status update
    - LocalizationResponse: API response output
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SuspectDevice(BaseModel):
    """A single suspected device within a localization result."""

    device_id: str = Field(..., examples=["CONSUMER-H1"])
    suspicion_score: float = Field(
        ..., ge=0, le=100, examples=[78.5],
        description="Individual suspicion score (0-100)",
    )
    reason: str = Field(
        ...,
        examples=["High energy imbalance + AI anomaly flagged"],
        description="Human-readable explanation for suspicion",
    )
    recommended_action: str = Field(
        default="field_inspection",
        examples=["field_inspection"],
        description="Suggested investigation action",
    )


class LocalizationCreate(BaseModel):
    """Schema for creating a new localization result."""

    zone_id: str = Field(..., max_length=50, examples=["ZONE-A"])
    confidence: float = Field(
        ..., ge=0, le=1, examples=[0.82],
        description="Localization confidence (0-1). Higher = more confident in narrowing.",
    )
    priority: str = Field(
        ...,
        pattern="^(low|medium|high|critical)$",
        examples=["high"],
    )
    estimated_loss_kwh: Optional[float] = Field(
        None, ge=0, examples=[12.5],
        description="Estimated energy loss in this zone (kWh)",
    )
    suspect_devices: List[SuspectDevice] = Field(
        ...,
        min_length=1,
        description="Ranked list of suspect devices in this zone",
    )


class LocalizationUpdate(BaseModel):
    """Schema for updating an investigation status."""

    status: Optional[str] = Field(
        None,
        pattern="^(pending|investigating|resolved|false_alarm)$",
        examples=["investigating"],
    )
    investigation_notes: Optional[str] = Field(
        None,
        examples=["Field team dispatched. Meter inspection scheduled for 2024-01-15."],
    )
    resolved_by: Optional[UUID] = None


class LocalizationResponse(BaseModel):
    """Schema for localization API responses."""

    id: UUID
    zone_id: str
    confidence: float
    priority: str
    estimated_loss_kwh: Optional[float] = None
    suspect_devices: List[Dict[str, Any]]
    investigation_notes: Optional[str] = None
    status: str
    resolved_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
