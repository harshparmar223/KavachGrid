"""
KAVACHGRID 3.0 — Risk Service
Phase 5: Risk Score CRUD Operations

Handles:
    - Persisting risk scores from the Risk Engine (Phase 10)
    - Retrieving latest and historical risk scores per device
    - Building ranked risk listings for the dashboard
"""

from datetime import datetime, timezone
from typing import List, Optional
import uuid

from sqlalchemy.orm import Session

from app.db.models import RiskScore
from app.schemas.risk import RiskScoreCreate
from app.services.device_service import device_service


class RiskService:
    """Service layer for KAVACH Risk Score persistence and retrieval."""

    @staticmethod
    def create_risk_score(db: Session, data: RiskScoreCreate) -> RiskScore:
        """Persist a new risk score calculated by the Risk Engine."""
        # Ensure the device exists
        device_service.ensure_device_exists(db, data.device_id)

        now = datetime.now(timezone.utc)
        risk_score = RiskScore(
            id=uuid.uuid4(),
            device_id=data.device_id,
            overall_score=data.overall_score,
            energy_balance_score=data.energy_balance_score,
            ai_anomaly_score=data.ai_anomaly_score,
            meter_health_score=data.meter_health_score,
            device_trust_score=data.device_trust_score,
            comm_reliability_score=data.comm_reliability_score,
            risk_level=data.risk_level,
            details=data.details,
            calculated_at=now,
        )

        db.add(risk_score)
        db.commit()
        db.refresh(risk_score)
        return risk_score

    @staticmethod
    def get_latest_by_device(
        db: Session, device_id: str
    ) -> Optional[RiskScore]:
        """Fetch the most recent risk score for a specific device."""
        return (
            db.query(RiskScore)
            .filter(RiskScore.device_id == device_id)
            .order_by(RiskScore.calculated_at.desc())
            .first()
        )

    @staticmethod
    def get_risk_ranking(
        db: Session,
        limit: int = 50,
        risk_level: Optional[str] = None,
    ) -> List[RiskScore]:
        """
        Get ranked risk scores (highest risk first).

        Returns only the latest score per device, ordered by overall_score DESC.
        Uses a subquery to get the most recent calculated_at per device_id,
        then joins back to get the full records.
        """
        from sqlalchemy import func

        # Subquery: latest calculated_at per device
        latest_sub = (
            db.query(
                RiskScore.device_id,
                func.max(RiskScore.calculated_at).label("max_calc"),
            )
            .group_by(RiskScore.device_id)
            .subquery()
        )

        query = (
            db.query(RiskScore)
            .join(
                latest_sub,
                (RiskScore.device_id == latest_sub.c.device_id)
                & (RiskScore.calculated_at == latest_sub.c.max_calc),
            )
        )

        if risk_level:
            query = query.filter(RiskScore.risk_level == risk_level)

        return (
            query.order_by(RiskScore.overall_score.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_risk_history(
        db: Session,
        device_id: str,
        limit: int = 100,
    ) -> List[RiskScore]:
        """Fetch historical risk scores for a device, most recent first."""
        return (
            db.query(RiskScore)
            .filter(RiskScore.device_id == device_id)
            .order_by(RiskScore.calculated_at.desc())
            .limit(limit)
            .all()
        )


risk_service = RiskService()
