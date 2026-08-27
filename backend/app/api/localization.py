"""
KAVACHGRID 3.0 — Localization API
Phase 5: Progressive localization endpoints

Endpoints:
    GET  /localization                — List localization results (filterable)
    POST /localization                — Create result (API key — engine use)
    GET  /localization/{result_id}    — Get single result
    PUT  /localization/{result_id}    — Update investigation status
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db, require_role, verify_api_key_header
from app.db.models import User
from app.schemas.localization import (
    LocalizationCreate,
    LocalizationResponse,
    LocalizationUpdate,
)
from app.services.localization_service import localization_service

router = APIRouter(prefix="/localization", tags=["Localization"])


@router.get(
    "",
    response_model=List[LocalizationResponse],
    summary="List localization results",
)
async def list_results(
    zone_id: Optional[str] = Query(None, description="Filter by zone"),
    status_filter: Optional[str] = Query(
        None, alias="status",
        pattern="^(pending|investigating|resolved|false_alarm)$",
        description="Filter by investigation status",
    ),
    priority: Optional[str] = Query(
        None, pattern="^(low|medium|high|critical)$",
        description="Filter by priority",
    ),
    limit: int = Query(50, ge=1, le=500, description="Max records"),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """List localization investigation results with optional filters."""
    results = localization_service.list_results(
        db,
        zone_id=zone_id,
        status=status_filter,
        priority=priority,
        limit=limit,
    )
    return results


@router.post(
    "",
    response_model=LocalizationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create localization result (engine use — API key)",
)
async def create_result(
    data: LocalizationCreate,
    db: Session = Depends(get_db),
    _api_key: str = Depends(verify_api_key_header),
):
    """
    Create a new localization result from the Localization Engine.
    Requires X-API-Key header.
    """
    result = localization_service.create_result(db, data)
    return result


@router.get(
    "/{result_id}",
    response_model=LocalizationResponse,
    summary="Get localization result",
)
async def get_result(
    result_id: UUID,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """Get full details of a specific localization investigation."""
    result = localization_service.get_by_id(db, result_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Localization result not found",
        )
    return result


@router.put(
    "/{result_id}",
    response_model=LocalizationResponse,
    summary="Update investigation status",
    dependencies=[Depends(require_role("admin", "investigator"))],
)
async def update_result(
    result_id: UUID,
    data: LocalizationUpdate,
    db: Session = Depends(get_db),
):
    """
    Update an investigation's status and notes.
    Only admins and investigators can modify investigation records.
    """
    result = localization_service.update_status(db, result_id, data)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Localization result not found",
        )
    return result
