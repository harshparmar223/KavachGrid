"""
KAVACHGRID 3.0 — Telemetry API
Phase 5: Telemetry ingestion and retrieval

Endpoints:
    POST /telemetry                     — Ingest a telemetry reading (API key)
    GET  /telemetry/latest              — Latest readings for all devices
    GET  /telemetry/{device_id}         — Device telemetry history (paginated)
    GET  /telemetry/{device_id}/latest  — Latest reading for a single device
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db, verify_api_key_header
from app.db.models import Telemetry, User
from app.schemas.telemetry import (
    TelemetryBatch,
    TelemetryCreate,
    TelemetryResponse,
)
from app.services.device_service import device_service
from app.services.telemetry_service import telemetry_service

router = APIRouter(prefix="/telemetry", tags=["Telemetry"])


@router.post(
    "",
    response_model=TelemetryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest telemetry reading (API key required)",
)
async def ingest_telemetry(
    data: TelemetryCreate,
    db: Session = Depends(get_db),
    _api_key: str = Depends(verify_api_key_header),
):
    """
    Ingest a single telemetry reading from an ESP32 device or simulator.
    Requires X-API-Key header for authentication.
    """
    telemetry = telemetry_service.ingest_telemetry(db, data)
    return telemetry


@router.get(
    "/latest",
    response_model=List[TelemetryResponse],
    summary="Latest readings for all devices",
)
async def get_all_latest(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """Get the most recent telemetry reading for every registered device."""
    latest_map = telemetry_service.get_all_latest(db)
    return list(latest_map.values())


@router.get(
    "/{device_id}",
    response_model=TelemetryBatch,
    summary="Device telemetry history",
)
async def get_device_telemetry(
    device_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=1000, description="Records per page"),
    start_time: Optional[datetime] = Query(None, description="Filter from time"),
    end_time: Optional[datetime] = Query(None, description="Filter until time"),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """
    Get paginated telemetry history for a specific device.
    Optionally filter by time range.
    """
    device = device_service.get_by_device_id(db, device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device '{device_id}' not found",
        )

    # Count total records matching the query
    count_query = db.query(func.count(Telemetry.id)).filter(
        Telemetry.device_id == device_id
    )
    if start_time:
        count_query = count_query.filter(Telemetry.timestamp >= start_time)
    if end_time:
        count_query = count_query.filter(Telemetry.timestamp <= end_time)

    total = count_query.scalar() or 0

    offset = (page - 1) * page_size
    data_query = db.query(Telemetry).filter(Telemetry.device_id == device_id)
    if start_time:
        data_query = data_query.filter(Telemetry.timestamp >= start_time)
    if end_time:
        data_query = data_query.filter(Telemetry.timestamp <= end_time)

    records = (
        data_query.order_by(Telemetry.timestamp.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    return TelemetryBatch(
        total=total,
        page=page,
        page_size=page_size,
        data=records,
    )


@router.get(
    "/{device_id}/latest",
    response_model=TelemetryResponse,
    summary="Latest reading for a device",
)
async def get_device_latest(
    device_id: str,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """Get the most recent telemetry reading for a specific device."""
    telemetry = telemetry_service.get_latest_by_device(db, device_id)
    if not telemetry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No telemetry found for device '{device_id}'",
        )
    return telemetry
