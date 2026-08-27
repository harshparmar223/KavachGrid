"""
KAVACHGRID 3.0 — Meter Health Engine
Phase 7: Meter Health Scoring

Detects:
- Missing data gaps
- Communication failures
- Sensor drift
- Stuck readings
- Impossible values

Output: Health Score (0-100)
"""
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.db.models import Device, Telemetry
from app.services.alert_service import alert_service
from app.schemas.alert import AlertCreate
from app.services.device_service import device_service
from app.services.telemetry_service import telemetry_service

class MeterHealthEngine:
    # Point deductions for issues
    PENALTY_MISSING_DATA = 20
    PENALTY_COMM_FAILURE = 30
    PENALTY_STUCK_READING = 20
    PENALTY_SENSOR_DRIFT = 15
    PENALTY_IMPOSSIBLE_VALUE = 50

    def evaluate_health(self, db: Session, device_id: str) -> Dict[str, any]:
        score = 100
        alerts_generated = []

        # 1. Fetch required data
        device = device_service.get_device_by_id(db, device_id)
        if not device:
            return {"score": 0, "status": "DEVICE_NOT_FOUND"}

        # Fetch history for the last 1 hour for stuck/drift detection
        now = datetime.now(timezone.utc)
        one_hour_ago = now - timedelta(hours=1)
        history = telemetry_service.get_device_history(db, device_id, limit=60, start_time=one_hour_ago)
        
        latest_telemetry = history[0] if history else None

        # 2. Apply detection algorithms
        
        # Communication failures
        if self._detect_communication_failures(device, now):
            score -= self.PENALTY_COMM_FAILURE
            alert_service.create_alert(db, AlertCreate(
                device_id=device_id,
                alert_type="COMM_FAILURE",
                severity="HIGH",
                title="Device Communication Failure",
                message=f"Device {device_id} is offline or hasn't reported recently."
            ))
            alerts_generated.append("COMM_FAILURE")

        # Missing data gaps
        if latest_telemetry and self._detect_missing_data(latest_telemetry, now):
            score -= self.PENALTY_MISSING_DATA
            alert_service.create_alert(db, AlertCreate(
                device_id=device_id,
                alert_type="MISSING_DATA",
                severity="MEDIUM",
                title="Missing Data Gaps",
                message=f"Device {device_id} data gap detected. Latest telemetry is too old."
            ))
            alerts_generated.append("MISSING_DATA")

        # Impossible values
        if latest_telemetry and self._detect_impossible_values(latest_telemetry):
            score -= self.PENALTY_IMPOSSIBLE_VALUE
            alert_service.create_alert(db, AlertCreate(
                device_id=device_id,
                alert_type="IMPOSSIBLE_VALUE",
                severity="CRITICAL",
                title="Impossible Sensor Values",
                message=f"Device {device_id} reported physically impossible readings."
            ))
            alerts_generated.append("IMPOSSIBLE_VALUE")

        # Stuck readings
        if len(history) > 10 and self._detect_stuck_readings(history):
            score -= self.PENALTY_STUCK_READING
            alert_service.create_alert(db, AlertCreate(
                device_id=device_id,
                alert_type="STUCK_READING",
                severity="MEDIUM",
                title="Stuck Sensor Readings",
                message=f"Device {device_id} readings have not changed over the recent window."
            ))
            alerts_generated.append("STUCK_READING")

        # Sensor drift
        if len(history) > 20 and self._detect_sensor_drift(history):
            score -= self.PENALTY_SENSOR_DRIFT
            alert_service.create_alert(db, AlertCreate(
                device_id=device_id,
                alert_type="SENSOR_DRIFT",
                severity="LOW",
                title="Sensor Drift Detected",
                message=f"Device {device_id} is exhibiting possible sensor drift."
            ))
            alerts_generated.append("SENSOR_DRIFT")

        score = max(0, score)
        return {
            "score": score,
            "alerts": alerts_generated,
            "device_id": device_id,
            "timestamp": now.isoformat()
        }

    def _detect_missing_data(self, latest_telemetry: Telemetry, now: datetime) -> bool:
        """Return True if the gap between now and the last reading is > 10 mins (excluding complete comm failure)."""
        # Let's say missing data gap is > 5 mins
        if not latest_telemetry.timestamp:
            return True
        tz = latest_telemetry.timestamp.tzinfo or timezone.utc
        diff = now - latest_telemetry.timestamp.replace(tzinfo=tz)
        return diff > timedelta(minutes=5)

    def _detect_communication_failures(self, device: Device, now: datetime) -> bool:
        """Return True if device status is offline or not seen for > 15 mins."""
        if device.status == "offline":
            return True
        if device.last_seen_at:
            tz = device.last_seen_at.tzinfo or timezone.utc
            diff = now - device.last_seen_at.replace(tzinfo=tz)
            if diff > timedelta(minutes=15):
                return True
        return False

    def _detect_stuck_readings(self, history: List[Telemetry]) -> bool:
        """Return True if voltage or current remains exactly the same for 10+ consecutive readings."""
        # History is ordered by desc, so history[0] is latest.
        # Check first 10 items
        if len(history) < 10:
            return False
            
        recent = history[:10]
        first_voltage = recent[0].voltage
        first_current = recent[0].current
        
        voltage_stuck = all(r.voltage == first_voltage for r in recent)
        current_stuck = all(r.current == first_current for r in recent)
        
        return voltage_stuck or current_stuck

    def _detect_sensor_drift(self, history: List[Telemetry]) -> bool:
        """Simple check: if voltage monotonically increases or decreases over 20 readings but changes very little."""
        if len(history) < 20:
            return False
            
        recent = history[:20]
        voltages = [r.voltage for r in recent]
        # Re-order to chronological
        voltages.reverse()
        
        # Check if strictly increasing or decreasing
        increasing = all(voltages[i] < voltages[i+1] for i in range(len(voltages)-1))
        decreasing = all(voltages[i] > voltages[i+1] for i in range(len(voltages)-1))
        
        return increasing or decreasing

    def _detect_impossible_values(self, telemetry: Telemetry) -> bool:
        """Return True if voltage < 0, current < 0, PF not between 0 and 1, etc."""
        if telemetry.voltage is not None and telemetry.voltage < 0:
            return True
        if telemetry.current is not None and telemetry.current < 0:
            return True
        if telemetry.power_factor is not None and (telemetry.power_factor < 0 or telemetry.power_factor > 1):
            return True
        if telemetry.frequency is not None and (telemetry.frequency < 40 or telemetry.frequency > 70):
            return True
        return False

meter_health_engine = MeterHealthEngine()
