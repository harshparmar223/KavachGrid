"""
KAVACHGRID 3.0 — Telemetry Service
Phase 3 & Phase 5: Time-Series Sensor Ingestion & Retrieval

Handles:
    - Ingesting incoming telemetry readings from MQTT/API
    - Updating device connection status and last_seen timestamp
    - High-performance time-series queries
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional
import uuid

from sqlalchemy.orm import Session

from app.db.models import Device, Telemetry
from app.schemas.telemetry import TelemetryCreate
from app.services.device_service import device_service
from app.engines.ai_anomaly import ai_anomaly_engine


class TelemetryService:
    """Service layer handling telemetry ingestion and time-series queries."""

    @staticmethod
    def ingest_telemetry(
        db: Session,
        data: TelemetryCreate,
        raw_payload: Optional[Dict] = None,
        trust_score: Optional[float] = None,
        anomaly_score: Optional[float] = None,
    ) -> Telemetry:
        """
        Ingest a single sensor reading into the database.
        Automatically updates device last_seen_at timestamp and online status.
        """
        device = device_service.ensure_device_exists(db, data.device_id)

        if anomaly_score is None:
            anomaly_score = ai_anomaly_engine.compute_anomaly_score(data)

        reading_time = data.timestamp or datetime.now(timezone.utc)
        if reading_time.tzinfo is None:
            reading_time = reading_time.replace(tzinfo=timezone.utc)

        received_time = datetime.now(timezone.utc)

        telemetry = Telemetry(
            id=uuid.uuid4(),
            device_id=data.device_id,
            voltage=float(data.voltage),
            current=float(data.current),
            power=float(data.power),
            energy=float(data.energy),
            power_factor=data.power_factor,
            frequency=data.frequency,
            trust_score=trust_score,
            anomaly_score=anomaly_score,
            raw_payload=raw_payload,
            timestamp=reading_time,
            received_at=received_time,
        )

        db.add(telemetry)

        # Update device last_seen_at and status
        device.last_seen_at = reading_time
        device.status = "online"
        device.updated_at = received_time

        db.commit()
        db.refresh(telemetry)
        return telemetry

    @staticmethod
    def get_latest_by_device(db: Session, device_id: str) -> Optional[Telemetry]:
        """Fetch the most recent telemetry reading for a device."""
        return (
            db.query(Telemetry)
            .filter(Telemetry.device_id == device_id)
            .order_by(Telemetry.timestamp.desc())
            .first()
        )

    @staticmethod
    def get_device_history(
        db: Session,
        device_id: str,
        limit: int = 100,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[Telemetry]:
        """Fetch historical readings for a device within an optional time range."""
        query = db.query(Telemetry).filter(Telemetry.device_id == device_id)

        if start_time:
            query = query.filter(Telemetry.timestamp >= start_time)
        if end_time:
            query = query.filter(Telemetry.timestamp <= end_time)

        return query.order_by(Telemetry.timestamp.desc()).limit(limit).all()

    @staticmethod
    def get_all_latest(db: Session) -> Dict[str, Telemetry]:
        """
        Get the latest telemetry reading for every distinct registered device.
        """
        devices = db.query(Device.device_id).all()
        latest_readings = {}

        for (dev_id,) in devices:
            latest = TelemetryService.get_latest_by_device(db, dev_id)
            if latest:
                latest_readings[dev_id] = latest

        return latest_readings


telemetry_service = TelemetryService()
