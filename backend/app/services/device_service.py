"""
KAVACHGRID 3.0 — Device Service
Phase 3 & Phase 5: Device Registry & Status Management

Provides database operations for registered IoT nodes:
    - Lookup by device ID
    - Device auto-registration / existence guarantee
    - Online/Offline status and last_seen updates
    - Device queries by type and zone
    - Full CRUD operations for API routes (Phase 5)
"""

from datetime import datetime, timezone
import secrets
from typing import List, Optional
import uuid

from sqlalchemy.orm import Session

from app.db.models import Device
from app.schemas.device import DeviceCreate, DeviceUpdate


class DeviceService:
    """Service layer handling device persistence and status management."""

    @staticmethod
    def get_by_device_id(db: Session, device_id: str) -> Optional[Device]:
        """Fetch a single device by its human-readable device_id."""
        return db.query(Device).filter(Device.device_id == device_id).first()

    @staticmethod
    def get_by_id(db: Session, id_val: uuid.UUID) -> Optional[Device]:
        """Fetch a single device by primary key UUID."""
        return db.query(Device).filter(Device.id == id_val).first()

    @staticmethod
    def ensure_device_exists(
        db: Session,
        device_id: str,
        device_type: str = "consumer",
        name: Optional[str] = None,
        zone_id: Optional[str] = None,
    ) -> Device:
        """
        Find an existing device or auto-register a new device with sensible defaults.
        Ensures foreign key constraints are satisfied during MQTT telemetry ingestion.
        """
        device = DeviceService.get_by_device_id(db, device_id)
        if device:
            return device

        clean_id = device_id.upper()
        if not name:
            if "FEEDER" in clean_id:
                name = f"Grid Feeder ({device_id})"
                device_type = "feeder"
            elif "LOC" in clean_id:
                name = f"Localization Sensor ({device_id})"
                device_type = "localization"
            else:
                name = f"Consumer Meter ({device_id})"
                device_type = "consumer"

        if not zone_id and "-" in device_id:
            zone_id = "ZONE-A"

        now = datetime.now(timezone.utc)
        device = Device(
            device_id=device_id,
            device_type=device_type,
            name=name,
            location="Smart Grid Sector",
            api_key=secrets.token_urlsafe(24),
            status="online",
            zone_id=zone_id,
            created_at=now,
            updated_at=now,
            last_seen_at=now,
        )
        db.add(device)
        db.commit()
        db.refresh(device)
        return device

    @staticmethod
    def update_last_seen(
        db: Session,
        device_id: str,
        status: str = "online",
        seen_at: Optional[datetime] = None,
    ) -> Optional[Device]:
        """Update last_seen_at and status when new telemetry arrives."""
        device = DeviceService.get_by_device_id(db, device_id)
        if not device:
            return None

        if seen_at is None:
            seen_at = datetime.now(timezone.utc)

        device.last_seen_at = seen_at
        device.status = status
        device.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(device)
        return device

    @staticmethod
    def list_devices(
        db: Session,
        device_type: Optional[str] = None,
        zone_id: Optional[str] = None,
    ) -> List[Device]:
        """List all devices with optional filters."""
        query = db.query(Device)
        if device_type:
            query = query.filter(Device.device_type == device_type)
        if zone_id:
            query = query.filter(Device.zone_id == zone_id)
        return query.order_by(Device.device_id.asc()).all()

    # ============================================
    # Phase 5: Full CRUD for API routes
    # ============================================

    @staticmethod
    def create_device(db: Session, data: DeviceCreate) -> Device:
        """
        Explicitly register a new device via the API.
        Auto-generates a secure API key for the device.
        """
        now = datetime.now(timezone.utc)
        device = Device(
            device_id=data.device_id,
            device_type=data.device_type,
            name=data.name,
            location=data.location,
            latitude=data.latitude,
            longitude=data.longitude,
            api_key=secrets.token_urlsafe(32),
            status="offline",
            zone_id=data.zone_id,
            device_metadata=data.metadata,
            created_at=now,
            updated_at=now,
        )
        db.add(device)
        db.commit()
        db.refresh(device)
        return device

    @staticmethod
    def update_device(
        db: Session, device_id: str, data: DeviceUpdate
    ) -> Optional[Device]:
        """Partially update a device's mutable fields."""
        device = DeviceService.get_by_device_id(db, device_id)
        if not device:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "metadata":
                setattr(device, "device_metadata", value)
            else:
                setattr(device, field, value)

        device.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(device)
        return device

    @staticmethod
    def delete_device(db: Session, device_id: str) -> bool:
        """
        Hard-delete a device and cascade to telemetry/risk_scores.
        Returns True if deleted, False if not found.
        """
        device = DeviceService.get_by_device_id(db, device_id)
        if not device:
            return False

        db.delete(device)
        db.commit()
        return True


device_service = DeviceService()

