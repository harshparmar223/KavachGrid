"""
KAVACHGRID 3.0 — Device Pydantic Schemas
Phase 2: Request/Response validation models for Devices

Schemas:
    - DeviceCreate: Registration input
    - DeviceUpdate: Partial update input
    - DeviceResponse: API response output
    - DeviceStatus: Status-only response
"""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class DeviceBase(BaseModel):
    """Shared device fields."""

    device_id: str = Field(
        ...,
        min_length=1,
        max_length=50,
        examples=["CONSUMER-H1"],
        description="Unique human-readable device identifier",
    )
    device_type: str = Field(
        ...,
        pattern="^(feeder|consumer|localization)$",
        examples=["consumer"],
    )
    name: str = Field(..., min_length=1, max_length=100, examples=["House 1 — Sharma Residence"])
    location: Optional[str] = Field(None, max_length=255, examples=["Plot 101, Sector 5"])
    latitude: Optional[float] = Field(None, ge=-90, le=90, examples=[28.6145])
    longitude: Optional[float] = Field(None, ge=-180, le=180, examples=[77.2095])
    zone_id: Optional[str] = Field(None, max_length=50, examples=["ZONE-A"])


class DeviceCreate(DeviceBase):
    """Schema for registering a new device."""

    metadata: Optional[Dict[str, Any]] = Field(
        None,
        examples=[{"hardware": "ESP32 + INA219", "max_current": 15.0}],
    )


class DeviceUpdate(BaseModel):
    """Schema for partially updating a device."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    location: Optional[str] = Field(None, max_length=255)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    zone_id: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = Field(None, pattern="^(online|offline|warning)$")
    metadata: Optional[Dict[str, Any]] = None


class DeviceResponse(DeviceBase):
    """Schema for device API responses."""

    id: UUID
    api_key: str = Field(..., description="Device authentication key (visible only to admin)")
    status: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    last_seen_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class DeviceStatus(BaseModel):
    """Lightweight status-only response for device listings."""

    device_id: str
    name: str
    device_type: str
    status: str
    last_seen_at: Optional[datetime] = None
    zone_id: Optional[str] = None

    model_config = {"from_attributes": True}
