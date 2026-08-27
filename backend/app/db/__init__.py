"""
KAVACHGRID 3.0 — Database Package
Phase 2: Complete

Exports:
    - Base: SQLAlchemy declarative base
    - engine: SQLAlchemy engine
    - SessionLocal: Session factory
    - get_db: FastAPI dependency for DB sessions
    - init_db: Create all tables
    - All ORM models
"""

from app.db.database import Base, SessionLocal, engine, get_db, init_db
from app.db.models import (
    Alert,
    AuditLog,
    Device,
    LocalizationResult,
    RiskScore,
    Telemetry,
    User,
)

__all__ = [
    "Base",
    "engine",
    "SessionLocal",
    "get_db",
    "init_db",
    "User",
    "Device",
    "Telemetry",
    "Alert",
    "RiskScore",
    "LocalizationResult",
    "AuditLog",
]
