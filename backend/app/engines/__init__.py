"""
KAVACHGRID 3.0 — Analytics Engines Package
Phases 6-11: Core analytics engines

Engines:
- energy_balance.py   — Phase 6:  Unaccounted energy calculation ✅
- meter_health.py     — Phase 7:  Meter health scoring (0-100) ✅
- ai_anomaly.py       — Phase 8:  Autoencoder-based anomaly detection (0-1) ✅
- device_trust.py     — Phase 9:  Zero Trust device validation (0-100) ✅
- risk_engine.py      — Phase 10: Composite risk scoring (0-100) ✅
- localization.py     — Phase 11: Progressive localization ✅
"""

from app.engines.energy_balance import EnergyBalanceEngine, energy_balance_engine
from app.engines.meter_health import MeterHealthEngine, meter_health_engine
from app.engines.ai_anomaly import AIAnomalyEngine, ai_anomaly_engine
from app.engines.device_trust import DeviceTrustEngine, device_trust_engine
from app.engines.risk_engine import KavachRiskEngine, kavach_risk_engine
from app.engines.localization import LocalizationEngine, localization_engine

__all__ = [
    "EnergyBalanceEngine",
    "energy_balance_engine",
    "MeterHealthEngine",
    "meter_health_engine",
    "AIAnomalyEngine",
    "ai_anomaly_engine",
    "DeviceTrustEngine",
    "device_trust_engine",
    "KavachRiskEngine",
    "kavach_risk_engine",
    "LocalizationEngine",
    "localization_engine",
]
