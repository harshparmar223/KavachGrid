"""
KAVACHGRID 3.0 — Devices API
Phase 5: Full CRUD for device management

Endpoints:
    GET    /devices                 — List all devices (filterable)
    POST   /devices                 — Register a new device (admin)
    GET    /devices/{device_id}     — Get single device
    PUT    /devices/{device_id}     — Update device (admin)
    DELETE /devices/{device_id}     — Delete device (admin)
    GET    /devices/{device_id}/status — Lightweight status check
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db, require_role
from app.db.models import User
from app.schemas.device import (
    DeviceCreate,
    DeviceResponse,
    DeviceStatus,
    DeviceUpdate,
)
from app.services.device_service import device_service

router = APIRouter(prefix="/devices", tags=["Devices"])


@router.get(
    "",
    response_model=List[DeviceResponse],
    summary="List all devices",
)
async def list_devices(
    device_type: Optional[str] = Query(
        None, pattern="^(feeder|consumer|localization)$",
        description="Filter by device type",
    ),
    zone_id: Optional[str] = Query(None, description="Filter by zone ID"),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """List all registered devices with optional type and zone filters."""
    devices = device_service.list_devices(db, device_type=device_type, zone_id=zone_id)
    return devices


@router.post(
    "",
    response_model=DeviceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new device (admin)",
    dependencies=[Depends(require_role("admin"))],
)
async def create_device(
    data: DeviceCreate,
    db: Session = Depends(get_db),
):
    """Register a new IoT device. Auto-generates a secure API key."""
    # Check for duplicate device_id
    existing = device_service.get_by_device_id(db, data.device_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Device '{data.device_id}' already registered",
        )

    device = device_service.create_device(db, data)
    return device


@router.get(
    "/{device_id}",
    response_model=DeviceResponse,
    summary="Get device details",
)
async def get_device(
    device_id: str,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """Get full details of a specific device by its device_id."""
    device = device_service.get_by_device_id(db, device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device '{device_id}' not found",
        )
    return device


@router.put(
    "/{device_id}",
    response_model=DeviceResponse,
    summary="Update device (admin)",
    dependencies=[Depends(require_role("admin"))],
)
async def update_device(
    device_id: str,
    data: DeviceUpdate,
    db: Session = Depends(get_db),
):
    """Partially update a device's configuration."""
    device = device_service.update_device(db, device_id, data)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device '{device_id}' not found",
        )
    return device


@router.delete(
    "/{device_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete device (admin)",
    dependencies=[Depends(require_role("admin"))],
)
async def delete_device(
    device_id: str,
    db: Session = Depends(get_db),
):
    """Delete a device and all associated telemetry/risk data."""
    deleted = device_service.delete_device(db, device_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device '{device_id}' not found",
        )
    return None


@router.get(
    "/{device_id}/status",
    response_model=DeviceStatus,
    summary="Get device status",
)
async def get_device_status(
    device_id: str,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """Get a lightweight status-only view of a device."""
    device = device_service.get_by_device_id(db, device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device '{device_id}' not found",
        )
    return device
