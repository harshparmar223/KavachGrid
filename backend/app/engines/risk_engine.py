"""
KAVACHGRID 3.0 — KAVACH Risk Engine
Phase 10: Composite Risk Scoring

The CORE INTELLIGENCE of KAVACHGRID. Combines 5 engine outputs
into a single composite risk score (0-100) per consumer device.

Formula:
    overall = (energy_balance    × 0.30)
            + (ai_anomaly × 100  × 0.25)    # Normalize 0-1 → 0-100
            + ((100 - meter_health)  × 0.20) # Invert: low health = high risk
            + ((100 - device_trust)  × 0.15) # Invert: low trust = high risk
            + ((100 - comm_reliability) × 0.10)

Risk Levels:
    0-25   → low
    25-50  → medium
    50-75  → high
    75-100 → critical

Important:
    This engine is an Investigation Support System.
    It does NOT automatically prove theft.
    It prioritizes inspections using multiple evidence signals.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.db.models import Device, RiskScore, Telemetry
from app.engines.energy_balance import energy_balance_engine
from app.engines.meter_health import meter_health_engine
from app.engines.ai_anomaly import ai_anomaly_engine
from app.engines.device_trust import device_trust_engine
from app.schemas.risk import RiskScoreCreate
from app.services.risk_service import risk_service

logger = logging.getLogger("kavachgrid.engines.risk")


# ============================================
# Risk Level Thresholds
# ============================================
RISK_THRESHOLD_LOW = 25.0
RISK_THRESHOLD_MEDIUM = 50.0
RISK_THRESHOLD_HIGH = 75.0


class RiskScoreResult:
    """Holds the output of a single risk score computation."""

    def __init__(
        self,
        device_id: str,
        overall_score: float,
        energy_balance_score: float,
        ai_anomaly_score: float,
        meter_health_score: float,
        device_trust_score: float,
        comm_reliability_score: float,
        risk_level: str,
        explanation: str,
        details: Dict,
    ):
        self.device_id = device_id
        self.overall_score = overall_score
        self.energy_balance_score = energy_balance_score
        self.ai_anomaly_score = ai_anomaly_score
        self.meter_health_score = meter_health_score
        self.device_trust_score = device_trust_score
        self.comm_reliability_score = comm_reliability_score
        self.risk_level = risk_level
        self.explanation = explanation
        self.details = details


class KavachRiskEngine:
    """
    KAVACH Risk Engine — Phase 10

    Combines all 5 analytics engine outputs into a single composite
    risk score per consumer device. Runs periodically (every 30 seconds)
    and stores results in the risk_scores table.

    Usage:
        engine = KavachRiskEngine()
        results = engine.calculate_all_risks(db)
        # or for a single device:
        result = engine.calculate_risk(db, "CONSUMER-H1")
    """

    def __init__(self):
        # Weights from config (default: 0.30, 0.25, 0.20, 0.15, 0.10)
        self.w_energy = settings.ENERGY_BALANCE_WEIGHT
        self.w_ai = settings.AI_ANOMALY_WEIGHT
        self.w_health = settings.METER_HEALTH_WEIGHT
        self.w_trust = settings.DEVICE_TRUST_WEIGHT
        self.w_comm = settings.COMM_RELIABILITY_WEIGHT

    # --------------------------------------------------
    # Public API
    # --------------------------------------------------

    def calculate_risk(
        self,
        db: Session,
        device_id: str,
        zone_id: Optional[str] = None,
    ) -> Optional[RiskScoreResult]:
        """
        Calculate the composite risk score for a single consumer device.

        Collects the latest output from each of the 5 engines and
        combines them using the weighted formula.

        Args:
            db: Database session
            device_id: Consumer device ID
            zone_id: Zone for energy balance context

        Returns:
            RiskScoreResult or None if device not found.
        """
        device = (
            db.query(Device)
            .filter(Device.device_id == device_id)
            .first()
        )
        if not device:
            logger.warning("Risk calculation skipped: device '%s' not found", device_id)
            return None

        # ---- Collect Component Scores ----

        # 1. Energy Balance Score (0-100, higher = more imbalance = higher risk)
        energy_score = self._get_energy_balance_score(db, device, zone_id)

        # 2. AI Anomaly Score (0-1, normalized to 0-100 for weighting)
        ai_score_raw = self._get_ai_anomaly_score(db, device)

        # 3. Meter Health Score (0-100, higher = healthier)
        health_score = self._get_meter_health_score(db, device_id)

        # 4. Device Trust Score (0-100, higher = more trusted)
        trust_score = self._get_device_trust_score(db, device_id)

        # 5. Communication Reliability Score (0-100, higher = more reliable)
        comm_score = self._get_comm_reliability_score(db, device)

        # ---- Weighted Composite ----
        # Risk increases when:
        #   - energy_balance is HIGH (more imbalance)
        #   - ai_anomaly is HIGH (more anomalous)
        #   - health is LOW (unhealthy meter → invert)
        #   - trust is LOW (untrusted device → invert)
        #   - comm is LOW (unreliable comms → invert)

        overall = (
            energy_score * self.w_energy
            + (ai_score_raw * 100) * self.w_ai  # Normalize 0-1 → 0-100
            + (100.0 - health_score) * self.w_health  # Invert
            + (100.0 - trust_score) * self.w_trust  # Invert
            + (100.0 - comm_score) * self.w_comm  # Invert
        )

        # Clamp to 0-100
        overall = max(0.0, min(100.0, round(overall, 2)))

        # Classify risk level
        risk_level = self._classify_risk_level(overall)

        # Generate human-readable explanation
        explanation = self._generate_explanation(
            device_id, overall, risk_level,
            energy_score, ai_score_raw, health_score, trust_score, comm_score,
        )

        # Build details dict for JSONB storage
        details = {
            "weights": {
                "energy_balance": self.w_energy,
                "ai_anomaly": self.w_ai,
                "meter_health": self.w_health,
                "device_trust": self.w_trust,
                "comm_reliability": self.w_comm,
            },
            "raw_scores": {
                "energy_balance": round(energy_score, 2),
                "ai_anomaly_raw": round(ai_score_raw, 4),
                "ai_anomaly_normalized": round(ai_score_raw * 100, 2),
                "meter_health": round(health_score, 2),
                "device_trust": round(trust_score, 2),
                "comm_reliability": round(comm_score, 2),
            },
            "weighted_contributions": {
                "energy_balance": round(energy_score * self.w_energy, 2),
                "ai_anomaly": round((ai_score_raw * 100) * self.w_ai, 2),
                "meter_health": round((100 - health_score) * self.w_health, 2),
                "device_trust": round((100 - trust_score) * self.w_trust, 2),
                "comm_reliability": round((100 - comm_score) * self.w_comm, 2),
            },
            "explanation": explanation,
        }

        result = RiskScoreResult(
            device_id=device_id,
            overall_score=overall,
            energy_balance_score=energy_score,
            ai_anomaly_score=ai_score_raw,
            meter_health_score=health_score,
            device_trust_score=trust_score,
            comm_reliability_score=comm_score,
            risk_level=risk_level,
            explanation=explanation,
            details=details,
        )

        # Persist to database
        self._persist_risk_score(db, result)

        logger.info(
            "⚡ Risk score [%s]: %.1f (%s) — E:%.0f AI:%.2f H:%.0f T:%.0f C:%.0f",
            device_id, overall, risk_level,
            energy_score, ai_score_raw, health_score, trust_score, comm_score,
        )

        return result

    def calculate_all_risks(
        self,
        db: Session,
        zone_id: Optional[str] = None,
    ) -> List[RiskScoreResult]:
        """
        Calculate risk scores for ALL consumer devices.
        This is the method called by the periodic scoring task.

        Args:
            db: Database session
            zone_id: Optional zone filter (None = all zones)

        Returns:
            List of RiskScoreResult for each consumer device.
        """
        query = db.query(Device).filter(Device.device_type == "consumer")
        if zone_id:
            query = query.filter(Device.zone_id == zone_id)

        consumers = query.all()
        results: List[RiskScoreResult] = []

        for device in consumers:
            try:
                result = self.calculate_risk(
                    db, device.device_id, zone_id=device.zone_id
                )
                if result:
                    results.append(result)
            except Exception as e:
                logger.error(
                    "Failed to calculate risk for %s: %s",
                    device.device_id, str(e),
                )

        # Sort by overall score descending (highest risk first)
        results.sort(key=lambda r: r.overall_score, reverse=True)

        logger.info(
            "🔄 Risk scoring cycle complete: %d consumers scored",
            len(results),
        )

        return results

    def get_risk_ranking(
        self,
        db: Session,
        zone_id: Optional[str] = None,
    ) -> List[Dict]:
        """
        Get the current risk ranking from stored scores.
        Returns a list of dicts sorted by overall_score DESC.
        """
        rankings = risk_service.get_risk_ranking(db, limit=100)
        return [
            {
                "device_id": r.device_id,
                "overall_score": r.overall_score,
                "risk_level": r.risk_level,
                "energy_balance_score": r.energy_balance_score,
                "ai_anomaly_score": r.ai_anomaly_score,
                "meter_health_score": r.meter_health_score,
                "device_trust_score": r.device_trust_score,
                "comm_reliability_score": r.comm_reliability_score,
                "calculated_at": r.calculated_at.isoformat() if r.calculated_at else None,
            }
            for r in rankings
        ]

    # --------------------------------------------------
    # Component Score Collection
    # --------------------------------------------------

    def _get_energy_balance_score(
        self, db: Session, device: Device, zone_id: Optional[str]
    ) -> float:
        """
        Get energy balance imbalance score (0-100).
        Uses the per-consumer deviation from the Energy Balance Engine.
        """
        try:
            deviations = energy_balance_engine.get_per_consumer_deviation(
                db, zone_id=zone_id or device.zone_id
            )
            return deviations.get(device.device_id, 0.0)
        except Exception as e:
            logger.debug("Energy balance score unavailable for %s: %s", device.device_id, e)
            return 0.0

    def _get_ai_anomaly_score(self, db: Session, device: Device) -> float:
        """
        Get AI anomaly score (0-1).
        Uses the latest telemetry reading and runs it through the autoencoder.
        """
        try:
            latest = (
                db.query(Telemetry)
                .filter(Telemetry.device_id == device.device_id)
                .order_by(Telemetry.timestamp.desc())
                .first()
            )
            if not latest:
                return 0.0

            # If anomaly_score was already computed during ingestion, use it
            if latest.anomaly_score is not None:
                return float(latest.anomaly_score)

            # Otherwise compute it now
            from app.schemas.telemetry import TelemetryCreate
            telemetry_data = TelemetryCreate(
                device_id=device.device_id,
                voltage=latest.voltage,
                current=latest.current,
                power=latest.power,
                energy=latest.energy,
                power_factor=latest.power_factor,
                frequency=latest.frequency,
                timestamp=latest.timestamp,
            )
            return ai_anomaly_engine.compute_anomaly_score(telemetry_data)
        except Exception as e:
            logger.debug("AI anomaly score unavailable for %s: %s", device.device_id, e)
            return 0.0

    def _get_meter_health_score(self, db: Session, device_id: str) -> float:
        """
        Get meter health score (0-100, higher = healthier).
        Uses the Meter Health Engine.
        """
        try:
            health_result = meter_health_engine.evaluate_health(db, device_id)
            return float(health_result.get("score", 100.0))
        except Exception as e:
            logger.debug("Meter health score unavailable for %s: %s", device_id, e)
            return 100.0  # Assume healthy if unavailable

    def _get_device_trust_score(self, db: Session, device_id: str) -> float:
        """
        Get device trust score (0-100, higher = more trusted).
        Uses the latest trust evaluation from Device Trust Engine.
        """
        try:
            latest = (
                db.query(Telemetry)
                .filter(Telemetry.device_id == device_id)
                .order_by(Telemetry.timestamp.desc())
                .first()
            )
            if latest and latest.trust_score is not None:
                return float(latest.trust_score)

            # Fall back to evaluating trust now
            trust_result = device_trust_engine.evaluate_trust(
                db, device_id=device_id, auto_alert=False
            )
            return float(trust_result.get("trust_score", 100.0))
        except Exception as e:
            logger.debug("Device trust score unavailable for %s: %s", device_id, e)
            return 100.0  # Assume trusted if unavailable

    def _get_comm_reliability_score(self, db: Session, device: Device) -> float:
        """
        Calculate communication reliability score (0-100).

        Based on:
        - How recently we received data (freshness)
        - Ratio of received vs expected readings in the last hour

        100 = perfect communication, 0 = no communication
        """
        now = datetime.now(timezone.utc)

        # Freshness component (0-50 points)
        freshness_score = 50.0
        if device.last_seen_at:
            last_seen = device.last_seen_at
            if last_seen.tzinfo is None:
                last_seen = last_seen.replace(tzinfo=timezone.utc)
            age_seconds = (now - last_seen).total_seconds()

            if age_seconds <= 10:
                freshness_score = 50.0  # Very fresh
            elif age_seconds <= 30:
                freshness_score = 45.0
            elif age_seconds <= 60:
                freshness_score = 35.0
            elif age_seconds <= 300:
                freshness_score = 20.0
            elif age_seconds <= 900:
                freshness_score = 10.0
            else:
                freshness_score = 0.0  # No data for 15+ minutes
        else:
            freshness_score = 0.0  # Never seen

        # Delivery ratio component (0-50 points)
        # Expected: 1 reading every 5 seconds = 720 readings/hour
        # Check last hour
        one_hour_ago = now - timedelta(hours=1)
        actual_count = (
            db.query(Telemetry)
            .filter(
                Telemetry.device_id == device.device_id,
                Telemetry.timestamp >= one_hour_ago,
            )
            .count()
        )

        expected_count = 720  # 1 reading per 5 seconds
        delivery_ratio = min(actual_count / expected_count, 1.0) if expected_count > 0 else 0.0
        delivery_score = delivery_ratio * 50.0

        return round(freshness_score + delivery_score, 2)

    # --------------------------------------------------
    # Helpers
    # --------------------------------------------------

    @staticmethod
    def _classify_risk_level(score: float) -> str:
        """Classify overall score into risk level."""
        if score >= RISK_THRESHOLD_HIGH:
            return "critical"
        elif score >= RISK_THRESHOLD_MEDIUM:
            return "high"
        elif score >= RISK_THRESHOLD_LOW:
            return "medium"
        return "low"

    @staticmethod
    def _generate_explanation(
        device_id: str,
        overall: float,
        risk_level: str,
        energy: float,
        ai: float,
        health: float,
        trust: float,
        comm: float,
    ) -> str:
        """Generate a human-readable explanation of the risk score."""
        factors = []

        if energy > 50:
            factors.append(f"significant energy imbalance ({energy:.0f}/100)")
        elif energy > 20:
            factors.append(f"moderate energy imbalance ({energy:.0f}/100)")

        if ai > 0.5:
            factors.append(f"AI anomaly detected (score {ai:.2f})")
        elif ai > 0.3:
            factors.append(f"mild AI anomaly (score {ai:.2f})")

        if health < 50:
            factors.append(f"poor meter health ({health:.0f}/100)")
        elif health < 70:
            factors.append(f"degraded meter health ({health:.0f}/100)")

        if trust < 60:
            factors.append(f"low device trust ({trust:.0f}/100)")
        elif trust < 80:
            factors.append(f"reduced device trust ({trust:.0f}/100)")

        if comm < 50:
            factors.append(f"poor communication reliability ({comm:.0f}/100)")

        if not factors:
            return (
                f"Device {device_id} has a {risk_level} risk score of {overall:.1f}/100. "
                f"All indicators are within normal range."
            )

        factor_text = "; ".join(factors)
        return (
            f"Device {device_id} has a {risk_level} risk score of {overall:.1f}/100 "
            f"due to: {factor_text}. "
            f"This warrants investigation — it does NOT confirm theft."
        )

    @staticmethod
    def _persist_risk_score(db: Session, result: RiskScoreResult) -> None:
        """Save the risk score to the database via the risk service."""
        try:
            risk_data = RiskScoreCreate(
                device_id=result.device_id,
                overall_score=result.overall_score,
                energy_balance_score=result.energy_balance_score,
                ai_anomaly_score=result.ai_anomaly_score,
                meter_health_score=result.meter_health_score,
                device_trust_score=result.device_trust_score,
                comm_reliability_score=result.comm_reliability_score,
                risk_level=result.risk_level,
                details=result.details,
            )
            risk_service.create_risk_score(db, risk_data)
        except Exception as e:
            logger.error("Failed to persist risk score for %s: %s", result.device_id, e)


# Module-level singleton
kavach_risk_engine = KavachRiskEngine()
