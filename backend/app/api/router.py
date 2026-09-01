"""
KAVACHGRID 3.0 — Central API Router
Phase 5: Aggregates all sub-routers under /api/v1/ prefix

Route map:
    /api/v1/auth          → Authentication (login, register, profile)
    /api/v1/devices       → Device CRUD
    /api/v1/telemetry     → Telemetry ingestion & retrieval
    /api/v1/alerts        → Alert management
    /api/v1/risk          → Risk scores
    /api/v1/localization  → Progressive localization
    /ws/dashboard         → WebSocket (no version prefix)
"""

from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.devices import router as devices_router
from app.api.telemetry import router as telemetry_router
from app.api.alerts import router as alerts_router
from app.api.risk import router as risk_router
from app.api.localization import router as localization_router
from app.api.gis import router as gis_router
from app.api.websocket import router as websocket_router

# ============================================
# Versioned API Router — /api/v1/
# ============================================
api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(devices_router)
api_router.include_router(telemetry_router)
api_router.include_router(alerts_router)
api_router.include_router(risk_router)
api_router.include_router(localization_router)
api_router.include_router(gis_router)

# ============================================
# WebSocket Router (no version prefix)
# ============================================
# The websocket_router is mounted directly on the app (not under /api/v1/)
# since WebSocket endpoints don't follow REST versioning conventions.
