"""
KAVACHGRID 3.0 — Localization Service
Phase 5: Progressive Localization CRUD Operations

Handles:
    - Persisting localization results from the Localization Engine (Phase 11)
    - Retrieving and filtering investigation records
    - Updating investigation status (investigating, resolved, false_alarm)
"""

from datetime import datetime, timezone
from typing import List, Optional
import uuid

from sqlalchemy.orm import Session

from app.db.models import LocalizationResult
from app.schemas.localization import LocalizationCreate, LocalizationUpdate


class LocalizationService:
    """Service layer for progressive localization result management."""

    @staticmethod
    def create_result(
        db: Session, data: LocalizationCreate
    ) -> LocalizationResult:
        """Persist a new localization result from the Localization Engine."""
        now = datetime.now(timezone.utc)

        # Convert SuspectDevice models to dicts for JSONB storage
        suspect_devices_json = [
            sd.model_dump() for sd in data.suspect_devices
        ]

        result = LocalizationResult(
            id=uuid.uuid4(),
            zone_id=data.zone_id,
            confidence=data.confidence,
            priority=data.priority,
            estimated_loss_kwh=data.estimated_loss_kwh,
            suspect_devices=suspect_devices_json,
            status="pending",
            created_at=now,
            updated_at=now,
        )

        db.add(result)
        db.commit()
        db.refresh(result)
        return result

    @staticmethod
    def get_by_id(
        db: Session, result_id: uuid.UUID
    ) -> Optional[LocalizationResult]:
        """Fetch a single localization result by primary key UUID."""
        return (
            db.query(LocalizationResult)
            .filter(LocalizationResult.id == result_id)
            .first()
        )

    @staticmethod
    def list_results(
        db: Session,
        zone_id: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        limit: int = 50,
    ) -> List[LocalizationResult]:
        """List localization results with optional filters."""
        query = db.query(LocalizationResult)

        if zone_id:
            query = query.filter(LocalizationResult.zone_id == zone_id)
        if status:
            query = query.filter(LocalizationResult.status == status)
        if priority:
            query = query.filter(LocalizationResult.priority == priority)

        return (
            query.order_by(LocalizationResult.created_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def update_status(
        db: Session,
        result_id: uuid.UUID,
        data: LocalizationUpdate,
    ) -> Optional[LocalizationResult]:
        """Update an investigation's status and notes."""
        result = LocalizationService.get_by_id(db, result_id)
        if not result:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(result, field, value)

        result.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(result)
        return result


localization_service = LocalizationService()
