"""
KAVACHGRID 3.0 — Alerts API
Phase 5: Alert management endpoints

Endpoints:
    GET  /alerts                         — List alerts (filterable)
    POST /alerts                         — Create alert (API key — engine use)
    GET  /alerts/summary                 — Dashboard summary counts
    GET  /alerts/{alert_id}              — Get single alert
    PUT  /alerts/{alert_id}/acknowledge  — Acknowledge an alert
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db, require_role, verify_api_key_header
from app.db.models import User
from app.schemas.alert import (
    AlertCreate,
    AlertResponse,
    AlertSummary,
)
from app.services.alert_service import alert_service

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get(
    "",
    response_model=List[AlertResponse],
    summary="List alerts",
)
async def list_alerts(
    limit: int = Query(50, ge=1, le=500, description="Max records"),
    unacknowledged_only: bool = Query(False, description="Only unacknowledged"),
    severity: Optional[str] = Query(
        None, pattern="^(low|medium|high|critical)$",
        description="Filter by severity",
    ),
    alert_type: Optional[str] = Query(
        None,
        description="Filter by alert type",
    ),
    device_id: Optional[str] = Query(None, description="Filter by device"),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """List alerts with optional filters for severity, type, device, and acknowledgement status."""
    alerts = alert_service.get_active_alerts(
        db,
        limit=limit,
        unacknowledged_only=unacknowledged_only,
        severity=severity,
        alert_type=alert_type,
        device_id=device_id,
    )
    return alerts


@router.post(
    "",
    response_model=AlertResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create alert (engine use — API key)",
)
async def create_alert(
    data: AlertCreate,
    db: Session = Depends(get_db),
    _api_key: str = Depends(verify_api_key_header),
):
    """
    Create a new alert. Used internally by analytics engines.
    Requires X-API-Key header.
    """
    alert = alert_service.create_alert(db, data)
    return alert


@router.get(
    "/summary",
    response_model=AlertSummary,
    summary="Dashboard alert summary",
)
async def get_alert_summary(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """Get aggregated alert counts by severity and type for the dashboard."""
    return alert_service.get_alert_summary(db)


@router.get(
    "/{alert_id}",
    response_model=AlertResponse,
    summary="Get single alert",
)
async def get_alert(
    alert_id: UUID,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """Get full details of a specific alert."""
    alert = alert_service.get_alert_by_id(db, alert_id)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found",
        )
    return alert


@router.put(
    "/{alert_id}/acknowledge",
    response_model=AlertResponse,
    summary="Acknowledge an alert",
    dependencies=[Depends(require_role("admin", "operator"))],
)
async def acknowledge_alert(
    alert_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Mark an alert as acknowledged by the current operator/admin.
    """
    alert = alert_service.acknowledge_alert(db, alert_id, user_id=current_user.id)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found",
        )
    return alert
