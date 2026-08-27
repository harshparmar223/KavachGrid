"""
KAVACHGRID 3.0 — SQLAlchemy ORM Models
Phase 2: Complete Database Models

Tables:
    1. User          — Dashboard users (operators, investigators, admins)
    2. Device        — Registered IoT nodes (feeder, consumer, localization)
    3. Telemetry     — Time-series sensor readings (high-volume)
    4. Alert         — Generated alerts from analytics engines
    5. RiskScore     — Composite risk score snapshots
    6. LocalizationResult — Progressive localization investigation records
    7. AuditLog      — Immutable system audit trail

Relationships:
    - Device  1:N  Telemetry
    - Device  1:N  Alert
    - Device  1:N  RiskScore
    - User    1:N  Alert (acknowledged_by)
    - User    1:N  LocalizationResult (resolved_by)
    - User    1:N  AuditLog (user_id)
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.database import Base


# ============================================
# 1. User — Dashboard Users
# ============================================
class User(Base):
    """Dashboard users: admins, operators, investigators, viewers."""

    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
    )
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(String(20), nullable=False, default="viewer")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    acknowledged_alerts = relationship(
        "Alert", back_populates="acknowledger", foreign_keys="Alert.acknowledged_by"
    )
    resolved_localizations = relationship(
        "LocalizationResult",
        back_populates="resolver",
        foreign_keys="LocalizationResult.resolved_by",
    )
    audit_logs = relationship("AuditLog", back_populates="user")

    __table_args__ = (
        CheckConstraint(
            "role IN ('admin', 'operator', 'investigator', 'viewer')",
            name="ck_users_role",
        ),
    )

    def __repr__(self):
        return f"<User(username='{self.username}', role='{self.role}')>"


# ============================================
# 2. Device — Registered IoT Nodes
# ============================================
class Device(Base):
    """Registered ESP32 nodes: feeders, consumers, localization nodes."""

    __tablename__ = "devices"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
    )
    device_id = Column(String(50), unique=True, nullable=False, index=True)
    device_type = Column(String(20), nullable=False)
    name = Column(String(100), nullable=False)
    location = Column(String(255), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    api_key = Column(String(255), nullable=False)
    status = Column(String(20), nullable=False, default="offline")
    zone_id = Column(String(50), nullable=True, index=True)
    metadata = Column(JSONB, nullable=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
    last_seen_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    telemetry_records = relationship(
        "Telemetry", back_populates="device", cascade="all, delete-orphan"
    )
    alerts = relationship("Alert", back_populates="device")
    risk_scores = relationship(
        "RiskScore", back_populates="device", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "device_type IN ('feeder', 'consumer', 'localization')",
            name="ck_devices_type",
        ),
        CheckConstraint(
            "status IN ('online', 'offline', 'warning')",
            name="ck_devices_status",
        ),
    )

    def __repr__(self):
        return f"<Device(device_id='{self.device_id}', type='{self.device_type}', status='{self.status}')>"


# ============================================
# 3. Telemetry — Sensor Readings (High-Volume)
# ============================================
class Telemetry(Base):
    """Time-series sensor readings from ESP32 nodes."""

    __tablename__ = "telemetry"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
    )
    device_id = Column(
        String(50),
        ForeignKey("devices.device_id", ondelete="CASCADE"),
        nullable=False,
    )
    voltage = Column(Float, nullable=False)
    current = Column(Float, nullable=False)
    power = Column(Float, nullable=False)
    energy = Column(Float, nullable=False)
    power_factor = Column(Float, nullable=True)
    frequency = Column(Float, nullable=True)
    trust_score = Column(Float, nullable=True)
    anomaly_score = Column(Float, nullable=True)
    raw_payload = Column(JSONB, nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    received_at = Column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )

    # Relationships
    device = relationship("Device", back_populates="telemetry_records")

    __table_args__ = (
        Index("idx_telemetry_device_time", "device_id", timestamp.desc()),
        Index("idx_telemetry_timestamp", timestamp.desc()),
    )

    def __repr__(self):
        return (
            f"<Telemetry(device='{self.device_id}', "
            f"V={self.voltage}, A={self.current}, W={self.power})>"
        )


# ============================================
# 4. Alert — System Alerts
# ============================================
class Alert(Base):
    """Alerts generated by the 6 analytics engines."""

    __tablename__ = "alerts"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
    )
    device_id = Column(
        String(50),
        ForeignKey("devices.device_id", ondelete="SET NULL"),
        nullable=True,
    )
    alert_type = Column(String(30), nullable=False)
    severity = Column(String(10), nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    details = Column(JSONB, nullable=True)
    acknowledged = Column(Boolean, nullable=False, default=False)
    acknowledged_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )

    # Relationships
    device = relationship("Device", back_populates="alerts")
    acknowledger = relationship(
        "User",
        back_populates="acknowledged_alerts",
        foreign_keys=[acknowledged_by],
    )

    __table_args__ = (
        CheckConstraint(
            "alert_type IN ('energy_imbalance', 'anomaly', 'meter_health', "
            "'device_trust', 'communication', 'localization')",
            name="ck_alerts_type",
        ),
        CheckConstraint(
            "severity IN ('low', 'medium', 'high', 'critical')",
            name="ck_alerts_severity",
        ),
        Index("idx_alerts_device", "device_id", created_at.desc()),
        Index("idx_alerts_unacked", "acknowledged", "severity"),
    )

    def __repr__(self):
        return (
            f"<Alert(type='{self.alert_type}', severity='{self.severity}', "
            f"device='{self.device_id}')>"
        )


# ============================================
# 5. RiskScore — Composite Risk Scores
# ============================================
class RiskScore(Base):
    """KAVACH Risk Engine output — composite risk score per device."""

    __tablename__ = "risk_scores"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
    )
    device_id = Column(
        String(50),
        ForeignKey("devices.device_id", ondelete="CASCADE"),
        nullable=False,
    )
    overall_score = Column(Float, nullable=False)
    energy_balance_score = Column(Float, nullable=False)
    ai_anomaly_score = Column(Float, nullable=False)
    meter_health_score = Column(Float, nullable=False)
    device_trust_score = Column(Float, nullable=False)
    comm_reliability_score = Column(Float, nullable=False)
    risk_level = Column(String(10), nullable=False)
    details = Column(JSONB, nullable=True)
    calculated_at = Column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )

    # Relationships
    device = relationship("Device", back_populates="risk_scores")

    __table_args__ = (
        CheckConstraint(
            "risk_level IN ('low', 'medium', 'high', 'critical')",
            name="ck_risk_level",
        ),
        Index("idx_risk_device_time", "device_id", calculated_at.desc()),
        Index("idx_risk_level", "risk_level", overall_score.desc()),
    )

    def __repr__(self):
        return (
            f"<RiskScore(device='{self.device_id}', "
            f"score={self.overall_score}, level='{self.risk_level}')>"
        )


# ============================================
# 6. LocalizationResult — Progressive Localization
# ============================================
class LocalizationResult(Base):
    """Progressive localization investigation records."""

    __tablename__ = "localization_results"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
    )
    zone_id = Column(String(50), nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    priority = Column(String(10), nullable=False)
    estimated_loss_kwh = Column(Float, nullable=True)
    suspect_devices = Column(JSONB, nullable=False, default=[])
    investigation_notes = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="pending")
    resolved_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at = Column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # Relationships
    resolver = relationship(
        "User",
        back_populates="resolved_localizations",
        foreign_keys=[resolved_by],
    )

    __table_args__ = (
        CheckConstraint(
            "priority IN ('low', 'medium', 'high', 'critical')",
            name="ck_localization_priority",
        ),
        CheckConstraint(
            "status IN ('pending', 'investigating', 'resolved', 'false_alarm')",
            name="ck_localization_status",
        ),
    )

    def __repr__(self):
        return (
            f"<LocalizationResult(zone='{self.zone_id}', "
            f"confidence={self.confidence}, status='{self.status}')>"
        )


# ============================================
# 7. AuditLog — System Audit Trail
# ============================================
class AuditLog(Base):
    """Immutable audit trail of all significant system actions."""

    __tablename__ = "audit_logs"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    action = Column(String(50), nullable=False)
    resource_type = Column(String(30), nullable=False)
    resource_id = Column(String(50), nullable=True)
    details = Column(JSONB, nullable=True)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )

    # Relationships
    user = relationship("User", back_populates="audit_logs")

    __table_args__ = (
        Index("idx_audit_user", "user_id", created_at.desc()),
        Index("idx_audit_resource", "resource_type", "resource_id"),
    )

    def __repr__(self):
        return (
            f"<AuditLog(action='{self.action}', "
            f"resource='{self.resource_type}/{self.resource_id}')>"
        )
