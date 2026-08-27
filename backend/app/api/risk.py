"""
KAVACHGRID 3.0 — Risk API
Phase 5: Risk score endpoints

Endpoints:
    GET  /risk/ranking              — Ranked risk scores for all devices
    POST /risk                      — Store a new risk score (API key — engine use)
    GET  /risk/{device_id}          — Latest risk score for a device
    GET  /risk/{device_id}/history  — Risk score history for a device
"""

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db, verify_api_key_header
from app.db.models import User
from app.schemas.risk import (
    RiskRanking,
    RiskScoreCreate,
    RiskScoreResponse,
)
from app.services.risk_service import risk_service

router = APIRouter(prefix="/risk", tags=["Risk Scores"])


@router.get(
    "/ranking",
    response_model=RiskRanking,
    summary="Risk ranking of all devices",
)
async def get_risk_ranking(
    limit: int = Query(50, ge=1, le=500, description="Max devices"),
    risk_level: Optional[str] = Query(
        None, pattern="^(low|medium|high|critical)$",
        description="Filter by risk level",
    ),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """
    Get all devices ranked by risk score (highest first).
    Returns only the latest score per device.
    """
    rankings = risk_service.get_risk_ranking(db, limit=limit, risk_level=risk_level)

    high_risk_count = sum(1 for r in rankings if r.risk_level == "high")
    critical_count = sum(1 for r in rankings if r.risk_level == "critical")

    last_calculated = (
        rankings[0].calculated_at if rankings
        else datetime.now(timezone.utc)
    )

    return RiskRanking(
        rankings=rankings,
        total_consumers=len(rankings),
        high_risk_count=high_risk_count,
        critical_count=critical_count,
        last_calculated=last_calculated,
    )


@router.post(
    "",
    response_model=RiskScoreResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Store risk score (engine use — API key)",
)
async def create_risk_score(
    data: RiskScoreCreate,
    db: Session = Depends(get_db),
    _api_key: str = Depends(verify_api_key_header),
):
    """
    Store a new risk score from the KAVACH Risk Engine.
    Requires X-API-Key header.
    """
    risk_score = risk_service.create_risk_score(db, data)
    return risk_score


@router.get(
    "/{device_id}",
    response_model=RiskScoreResponse,
    summary="Latest risk score for a device",
)
async def get_device_risk(
    device_id: str,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """Get the most recent risk score for a specific device."""
    risk_score = risk_service.get_latest_by_device(db, device_id)
    if not risk_score:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No risk score found for device '{device_id}'",
        )
    return risk_score


@router.get(
    "/{device_id}/history",
    response_model=List[RiskScoreResponse],
    summary="Risk score history for a device",
)
async def get_device_risk_history(
    device_id: str,
    limit: int = Query(100, ge=1, le=1000, description="Max records"),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """Get historical risk scores for a device, most recent first."""
    history = risk_service.get_risk_history(db, device_id, limit=limit)
    if not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No risk scores found for device '{device_id}'",
        )
    return history
