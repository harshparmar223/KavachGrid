"""
KAVACHGRID 3.0 — Energy Balance Engine
Phase 6: Unaccounted Energy Detection

Purpose:
    Detects unexplained energy losses by comparing total energy entering
    a distribution segment (feeder) against the sum of all consumers.

    This is the PRIMARY theft-indicator signal in KAVACHGRID.

Formula:
    Unaccounted Energy = Feeder Energy − Σ(Consumer Energy) − Expected Technical Loss
    Expected Technical Loss = Feeder Energy × TECHNICAL_LOSS_PERCENT

    Energy Imbalance Score (0-100):
        0   = Perfect balance (no unexplained loss)
        100 = Severe imbalance (major unexplained loss)

Important:
    This engine does NOT prove theft. It flags statistical anomalies
    that warrant investigation. Unaccounted energy can also be caused
    by meter inaccuracies, uncalibrated sensors, or legitimate losses.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models import Alert, Device, Telemetry
from app.schemas.alert import AlertCreate

logger = logging.getLogger("kavachgrid.engines.energy_balance")


# ============================================
# Configuration Constants
# ============================================
# Expected technical loss as a fraction of feeder energy (5-8% is typical)
TECHNICAL_LOSS_PERCENT: float = 0.05

# Alert thresholds (as a fraction of feeder power)
ALERT_THRESHOLD_LOW: float = 0.10       # 10% unexplained → low alert
ALERT_THRESHOLD_MEDIUM: float = 0.15    # 15% unexplained → medium alert
ALERT_THRESHOLD_HIGH: float = 0.25      # 25% unexplained → high alert
ALERT_THRESHOLD_CRITICAL: float = 0.40  # 40% unexplained → critical alert

# Minimum feeder power (W) to run calculation — avoid division by zero
MIN_FEEDER_POWER: float = 50.0

# Time window for real-time calculation (seconds)
REALTIME_WINDOW_SECONDS: int = 60


class EnergyBalanceResult:
    """Holds the output of a single energy balance calculation."""

    def __init__(
        self,
        feeder_power: float,
        total_consumer_power: float,
        expected_loss: float,
        unaccounted_power: float,
        imbalance_percent: float,
        imbalance_score: float,
        severity: Optional[str],
        consumer_breakdown: Dict[str, float],
        zone_id: Optional[str],
        timestamp: datetime,
    ):
        self.feeder_power = feeder_power
        self.total_consumer_power = total_consumer_power
        self.expected_loss = expected_loss
        self.unaccounted_power = unaccounted_power
        self.imbalance_percent = imbalance_percent
        self.imbalance_score = imbalance_score
        self.severity = severity
        self.consumer_breakdown = consumer_breakdown
        self.zone_id = zone_id
        self.timestamp = timestamp

    def to_dict(self) -> Dict:
        """Serialize for storage in alert/risk_score details JSONB."""
        return {
            "feeder_power_w": round(self.feeder_power, 2),
            "total_consumer_power_w": round(self.total_consumer_power, 2),
            "expected_loss_w": round(self.expected_loss, 2),
            "unaccounted_power_w": round(self.unaccounted_power, 2),
            "imbalance_percent": round(self.imbalance_percent, 2),
            "imbalance_score": round(self.imbalance_score, 2),
            "technical_loss_percent": TECHNICAL_LOSS_PERCENT * 100,
            "consumer_breakdown": {
                k: round(v, 2) for k, v in self.consumer_breakdown.items()
            },
            "zone_id": self.zone_id,
            "timestamp": self.timestamp.isoformat(),
        }


class EnergyBalanceEngine:
    """
    Energy Balance Engine — Phase 6

    Calculates the difference between energy input (feeder) and
    energy output (sum of consumers + expected technical losses)
    to detect unexplained energy losses that may indicate theft.

    Usage:
        engine = EnergyBalanceEngine()
        result = engine.calculate_realtime(db, zone_id="ZONE-A")
        if result and result.severity:
            # Alert generated automatically
            pass
    """

    # --------------------------------------------------
    # Public API
    # --------------------------------------------------

    def calculate_realtime(
        self,
        db: Session,
        zone_id: Optional[str] = None,
    ) -> Optional[EnergyBalanceResult]:
        """
        Calculate real-time energy balance using the latest readings
        from feeder and consumer devices within the specified zone.

        Args:
            db: Database session
            zone_id: Optional zone filter. If None, uses all devices.

        Returns:
            EnergyBalanceResult or None if insufficient data.
        """
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(seconds=REALTIME_WINDOW_SECONDS)

        # 1. Get latest feeder reading
        feeder_power = self._get_latest_feeder_power(db, zone_id, window_start)
        if feeder_power is None or feeder_power < MIN_FEEDER_POWER:
            logger.debug(
                "Skipping energy balance: feeder power %.2f W below minimum %.2f W",
                feeder_power or 0,
                MIN_FEEDER_POWER,
            )
            return None

        # 2. Get latest consumer readings
        consumer_breakdown = self._get_latest_consumer_powers(
            db, zone_id, window_start
        )
        if not consumer_breakdown:
            logger.debug("Skipping energy balance: no consumer readings available")
            return None

        total_consumer_power = sum(consumer_breakdown.values())

        # 3. Calculate energy balance
        result = self._compute_balance(
            feeder_power=feeder_power,
            total_consumer_power=total_consumer_power,
            consumer_breakdown=consumer_breakdown,
            zone_id=zone_id,
            timestamp=now,
        )

        # 4. Generate alert if threshold exceeded
        if result.severity:
            self._generate_alert(db, result)

        logger.info(
            "Energy balance [%s]: feeder=%.1fW, consumers=%.1fW, "
            "unaccounted=%.1fW (%.1f%%), score=%.1f",
            zone_id or "ALL",
            result.feeder_power,
            result.total_consumer_power,
            result.unaccounted_power,
            result.imbalance_percent,
            result.imbalance_score,
        )

        return result

    def calculate_historical(
        self,
        db: Session,
        zone_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Optional[EnergyBalanceResult]:
        """
        Calculate historical energy balance using cumulative energy (Wh)
        readings over a time period.

        Args:
            db: Database session
            zone_id: Optional zone filter
            start_time: Period start (defaults to 1 hour ago)
            end_time: Period end (defaults to now)

        Returns:
            EnergyBalanceResult or None if insufficient data.
        """
        now = datetime.now(timezone.utc)
        if end_time is None:
            end_time = now
        if start_time is None:
            start_time = end_time - timedelta(hours=1)

        # Get feeder energy delta over the period
        feeder_energy = self._get_energy_delta(
            db, device_type="feeder", zone_id=zone_id,
            start_time=start_time, end_time=end_time,
        )
        if feeder_energy is None or feeder_energy <= 0:
            return None

        # Get consumer energy deltas
        consumer_deltas = self._get_consumer_energy_deltas(
            db, zone_id=zone_id, start_time=start_time, end_time=end_time,
        )
        if not consumer_deltas:
            return None

        total_consumer_energy = sum(consumer_deltas.values())

        # Convert Wh to average W over the period for consistent scoring
        period_hours = (end_time - start_time).total_seconds() / 3600
        if period_hours <= 0:
            return None

        feeder_avg_power = feeder_energy / period_hours
        consumer_avg_power = total_consumer_energy / period_hours
        consumer_power_breakdown = {
            k: v / period_hours for k, v in consumer_deltas.items()
        }

        result = self._compute_balance(
            feeder_power=feeder_avg_power,
            total_consumer_power=consumer_avg_power,
            consumer_breakdown=consumer_power_breakdown,
            zone_id=zone_id,
            timestamp=end_time,
        )

        if result.severity:
            self._generate_alert(db, result)

        return result

    def get_per_consumer_deviation(
        self,
        db: Session,
        zone_id: Optional[str] = None,
    ) -> Dict[str, float]:
        """
        Calculate each consumer's share of the unaccounted energy.

        Returns a dict of {device_id: deviation_score} where higher
        scores mean the consumer accounts for a larger portion of the loss.

        Used by the Localization Engine (Phase 11) to rank suspects.
        """
        result = self.calculate_realtime(db, zone_id)
        if not result or result.unaccounted_power <= 0:
            return {}

        # Each consumer's deviation = their power as a fraction of total
        # Consumers reporting LESS than expected get higher deviation scores
        deviation_scores: Dict[str, float] = {}
        num_consumers = len(result.consumer_breakdown)
        if num_consumers == 0:
            return {}

        # Expected equal share (simplified — in production use sanctioned load)
        expected_per_consumer = (
            (result.feeder_power - result.expected_loss) / num_consumers
        )

        for device_id, power in result.consumer_breakdown.items():
            if expected_per_consumer > 0:
                # How much less than expected this consumer is reporting
                deficit = max(0, expected_per_consumer - power)
                deviation = (deficit / expected_per_consumer) * 100
                deviation_scores[device_id] = min(deviation, 100.0)
            else:
                deviation_scores[device_id] = 0.0

        return deviation_scores

    # --------------------------------------------------
    # Private Helpers
    # --------------------------------------------------

    def _compute_balance(
        self,
        feeder_power: float,
        total_consumer_power: float,
        consumer_breakdown: Dict[str, float],
        zone_id: Optional[str],
        timestamp: datetime,
    ) -> EnergyBalanceResult:
        """Core balance computation — shared by realtime and historical."""

        expected_loss = feeder_power * TECHNICAL_LOSS_PERCENT
        unaccounted = feeder_power - total_consumer_power - expected_loss

        # Clamp to zero — negative unaccounted means consumers report MORE
        # than feeder (possible meter over-reading, not a theft indicator)
        unaccounted = max(0.0, unaccounted)

        # Imbalance as a percentage of feeder power
        imbalance_percent = (
            (unaccounted / feeder_power) * 100 if feeder_power > 0 else 0.0
        )

        # Normalize to 0-100 score
        # 0% imbalance → score 0, ≥50% imbalance → score 100
        imbalance_score = min((imbalance_percent / 50.0) * 100, 100.0)

        # Determine severity
        severity = self._classify_severity(imbalance_percent / 100.0)

        return EnergyBalanceResult(
            feeder_power=feeder_power,
            total_consumer_power=total_consumer_power,
            expected_loss=expected_loss,
            unaccounted_power=unaccounted,
            imbalance_percent=imbalance_percent,
            imbalance_score=imbalance_score,
            severity=severity,
            consumer_breakdown=consumer_breakdown,
            zone_id=zone_id,
            timestamp=timestamp,
        )

    @staticmethod
    def _classify_severity(imbalance_fraction: float) -> Optional[str]:
        """Classify the imbalance fraction into an alert severity."""
        if imbalance_fraction >= ALERT_THRESHOLD_CRITICAL:
            return "critical"
        elif imbalance_fraction >= ALERT_THRESHOLD_HIGH:
            return "high"
        elif imbalance_fraction >= ALERT_THRESHOLD_MEDIUM:
            return "medium"
        elif imbalance_fraction >= ALERT_THRESHOLD_LOW:
            return "low"
        return None  # Below all thresholds — no alert

    def _get_latest_feeder_power(
        self,
        db: Session,
        zone_id: Optional[str],
        window_start: datetime,
    ) -> Optional[float]:
        """Get the latest power reading from a feeder device."""
        query = (
            db.query(Telemetry.power)
            .join(Device, Device.device_id == Telemetry.device_id)
            .filter(
                Device.device_type == "feeder",
                Telemetry.timestamp >= window_start,
            )
        )
        if zone_id:
            query = query.filter(Device.zone_id == zone_id)

        row = query.order_by(Telemetry.timestamp.desc()).first()
        return float(row[0]) if row else None

    def _get_latest_consumer_powers(
        self,
        db: Session,
        zone_id: Optional[str],
        window_start: datetime,
    ) -> Dict[str, float]:
        """Get the latest power reading for each consumer device."""
        # Get all consumer device_ids in this zone
        device_query = db.query(Device.device_id).filter(
            Device.device_type == "consumer"
        )
        if zone_id:
            device_query = device_query.filter(Device.zone_id == zone_id)

        consumer_ids = [row[0] for row in device_query.all()]

        breakdown: Dict[str, float] = {}
        for cid in consumer_ids:
            row = (
                db.query(Telemetry.power)
                .filter(
                    Telemetry.device_id == cid,
                    Telemetry.timestamp >= window_start,
                )
                .order_by(Telemetry.timestamp.desc())
                .first()
            )
            if row:
                breakdown[cid] = float(row[0])

        return breakdown

    def _get_energy_delta(
        self,
        db: Session,
        device_type: str,
        zone_id: Optional[str],
        start_time: datetime,
        end_time: datetime,
    ) -> Optional[float]:
        """
        Calculate cumulative energy delta for a device type over a period.
        Uses max(energy) - min(energy) since energy is a cumulative counter.
        """
        query = (
            db.query(
                func.max(Telemetry.energy) - func.min(Telemetry.energy),
            )
            .join(Device, Device.device_id == Telemetry.device_id)
            .filter(
                Device.device_type == device_type,
                Telemetry.timestamp >= start_time,
                Telemetry.timestamp <= end_time,
            )
        )
        if zone_id:
            query = query.filter(Device.zone_id == zone_id)

        row = query.first()
        return float(row[0]) if row and row[0] is not None else None

    def _get_consumer_energy_deltas(
        self,
        db: Session,
        zone_id: Optional[str],
        start_time: datetime,
        end_time: datetime,
    ) -> Dict[str, float]:
        """Get energy delta per consumer device over a period."""
        query = (
            db.query(
                Telemetry.device_id,
                func.max(Telemetry.energy) - func.min(Telemetry.energy),
            )
            .join(Device, Device.device_id == Telemetry.device_id)
            .filter(
                Device.device_type == "consumer",
                Telemetry.timestamp >= start_time,
                Telemetry.timestamp <= end_time,
            )
            .group_by(Telemetry.device_id)
        )
        if zone_id:
            query = query.filter(Device.zone_id == zone_id)

        results = query.all()
        return {
            row[0]: float(row[1])
            for row in results
            if row[1] is not None and row[1] > 0
        }

    @staticmethod
    def _generate_alert(db: Session, result: EnergyBalanceResult) -> None:
        """Create an energy_imbalance alert from the balance result."""
        alert = Alert(
            device_id=None,  # System-level alert (not device-specific)
            alert_type="energy_imbalance",
            severity=result.severity,
            title=f"Energy Imbalance Detected — {result.imbalance_percent:.1f}% Unaccounted",
            message=(
                f"Unaccounted energy of {result.unaccounted_power:.1f}W detected"
                f"{f' in {result.zone_id}' if result.zone_id else ''}. "
                f"Feeder: {result.feeder_power:.1f}W, "
                f"Consumers: {result.total_consumer_power:.1f}W, "
                f"Expected loss: {result.expected_loss:.1f}W. "
                f"This warrants investigation — it does NOT confirm theft."
            ),
            details=result.to_dict(),
            acknowledged=False,
        )
        db.add(alert)
        db.commit()
        logger.warning(
            "🚨 Energy imbalance alert [%s]: %.1f%% unaccounted (%.1fW)",
            result.severity,
            result.imbalance_percent,
            result.unaccounted_power,
        )


# Module-level singleton
energy_balance_engine = EnergyBalanceEngine()
