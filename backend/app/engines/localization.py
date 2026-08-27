"""
KAVACHGRID 3.0 — Progressive Localization Engine
Phase 11: Investigation Area Narrowing & Suspect Ranking

Purpose:
    Narrows suspicious areas by analyzing zone-level energy balances,
    ranking individual consumers by composite evidence, and assigning
    investigation priorities.

CRITICAL:
    This engine does NOT claim guaranteed identification of theft.
    It is an Investigation Support System that:
    - Ranks candidates by suspicion score
    - Calculates localization confidence
    - Suggests investigation priority
    - Provides human-readable reasoning for each suspect

Algorithm:
    1. Query all devices in a zone
    2. Calculate zone-level energy balance (feeder vs. sum of consumers)
    3. For each consumer:
       suspicion_score = risk_score × energy_deviation_factor
    4. Rank consumers by suspicion_score DESC
    5. confidence = f(imbalance_magnitude, score_spread, num_suspects)
    6. priority = f(confidence, estimated_loss_kwh)
"""

import logging
import math
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models import Device, LocalizationResult, RiskScore, Telemetry
from app.engines.energy_balance import energy_balance_engine
from app.schemas.localization import LocalizationCreate, SuspectDevice
from app.services.localization_service import localization_service

logger = logging.getLogger("kavachgrid.engines.localization")


# ============================================
# Configuration
# ============================================
# Minimum energy imbalance (W) to trigger localization
MIN_IMBALANCE_THRESHOLD: float = 100.0

# Minimum number of consumers needed for meaningful localization
MIN_CONSUMERS_FOR_LOCALIZATION: int = 2

# Confidence scaling factors
CONFIDENCE_IMBALANCE_WEIGHT: float = 0.40
CONFIDENCE_SCORE_SPREAD_WEIGHT: float = 0.35
CONFIDENCE_DATA_QUALITY_WEIGHT: float = 0.25

# Priority thresholds
PRIORITY_CRITICAL_CONFIDENCE: float = 0.80
PRIORITY_HIGH_CONFIDENCE: float = 0.60
PRIORITY_MEDIUM_CONFIDENCE: float = 0.40


class SuspectAnalysis:
    """Analysis result for a single suspect consumer."""

    def __init__(
        self,
        device_id: str,
        suspicion_score: float,
        risk_score: float,
        energy_deviation: float,
        reason: str,
        recommended_action: str,
    ):
        self.device_id = device_id
        self.suspicion_score = suspicion_score
        self.risk_score = risk_score
        self.energy_deviation = energy_deviation
        self.reason = reason
        self.recommended_action = recommended_action

    def to_suspect_device(self) -> SuspectDevice:
        """Convert to Pydantic SuspectDevice schema."""
        return SuspectDevice(
            device_id=self.device_id,
            suspicion_score=round(self.suspicion_score, 2),
            reason=self.reason,
            recommended_action=self.recommended_action,
        )


class LocalizationAnalysisResult:
    """Complete localization analysis for a zone."""

    def __init__(
        self,
        zone_id: str,
        confidence: float,
        priority: str,
        estimated_loss_kwh: Optional[float],
        suspects: List[SuspectAnalysis],
        zone_imbalance_w: float,
        total_consumers: int,
    ):
        self.zone_id = zone_id
        self.confidence = confidence
        self.priority = priority
        self.estimated_loss_kwh = estimated_loss_kwh
        self.suspects = suspects
        self.zone_imbalance_w = zone_imbalance_w
        self.total_consumers = total_consumers


class LocalizationEngine:
    """
    Progressive Localization Engine — Phase 11

    Analyzes zones to narrow investigation areas and rank suspects.
    Works in tandem with the Energy Balance Engine (Phase 6) and
    Risk Engine (Phase 10).

    Usage:
        engine = LocalizationEngine()
        result = engine.analyze_zone(db, "ZONE-A")
        if result:
            print(f"Zone {result.zone_id}: {result.priority} priority")
            for s in result.suspects:
                print(f"  {s.device_id}: {s.suspicion_score}")
    """

    # --------------------------------------------------
    # Public API
    # --------------------------------------------------

    def analyze_zone(
        self,
        db: Session,
        zone_id: str,
    ) -> Optional[LocalizationAnalysisResult]:
        """
        Run full localization analysis for a single zone.

        Steps:
        1. Get zone energy balance
        2. Get per-consumer risk scores
        3. Get per-consumer energy deviations
        4. Compute suspicion scores (risk × deviation)
        5. Calculate confidence
        6. Assign priority
        7. Persist results

        Returns:
            LocalizationAnalysisResult or None if insufficient data.
        """
        # 1. Get zone energy balance
        balance = energy_balance_engine.calculate_realtime(db, zone_id=zone_id)
        if not balance:
            logger.debug("Localization skipped for %s: no energy balance data", zone_id)
            return None

        if balance.unaccounted_power < MIN_IMBALANCE_THRESHOLD:
            logger.debug(
                "Localization skipped for %s: imbalance %.1fW below threshold %.1fW",
                zone_id, balance.unaccounted_power, MIN_IMBALANCE_THRESHOLD,
            )
            return None

        # 2. Get all consumer devices in this zone
        consumers = (
            db.query(Device)
            .filter(
                Device.device_type == "consumer",
                Device.zone_id == zone_id,
            )
            .all()
        )

        if len(consumers) < MIN_CONSUMERS_FOR_LOCALIZATION:
            logger.debug(
                "Localization skipped for %s: only %d consumers (need %d)",
                zone_id, len(consumers), MIN_CONSUMERS_FOR_LOCALIZATION,
            )
            return None

        # 3. Get per-consumer energy deviations
        energy_deviations = energy_balance_engine.get_per_consumer_deviation(
            db, zone_id=zone_id
        )

        # 4. Get per-consumer risk scores
        risk_scores = self._get_latest_risk_scores(db, consumers)

        # 5. Compute suspicion scores
        suspects = self._compute_suspicion_scores(
            consumers, risk_scores, energy_deviations, balance
        )

        if not suspects:
            return None

        # 6. Calculate confidence
        confidence = self._calculate_confidence(
            balance, suspects, consumers
        )

        # 7. Estimate loss in kWh (assuming imbalance is sustained for 1 hour)
        estimated_loss_kwh = round(balance.unaccounted_power / 1000.0, 3)

        # 8. Assign priority
        priority = self._assign_priority(confidence, estimated_loss_kwh)

        # Build result
        result = LocalizationAnalysisResult(
            zone_id=zone_id,
            confidence=round(confidence, 4),
            priority=priority,
            estimated_loss_kwh=estimated_loss_kwh,
            suspects=suspects,
            zone_imbalance_w=balance.unaccounted_power,
            total_consumers=len(consumers),
        )

        # 9. Persist to database
        self._persist_localization(db, result)

        logger.info(
            "📍 Localization [%s]: confidence=%.2f, priority=%s, "
            "suspects=%d/%d, imbalance=%.1fW, est_loss=%.3f kWh",
            zone_id, confidence, priority,
            len(suspects), len(consumers),
            balance.unaccounted_power, estimated_loss_kwh,
        )

        return result

    def analyze_all_zones(
        self,
        db: Session,
    ) -> List[LocalizationAnalysisResult]:
        """
        Run localization analysis for ALL zones with consumer devices.

        Returns:
            List of LocalizationAnalysisResult, sorted by priority.
        """
        # Get all distinct zone_ids
        zone_rows = (
            db.query(Device.zone_id)
            .filter(
                Device.device_type == "consumer",
                Device.zone_id.isnot(None),
            )
            .distinct()
            .all()
        )

        results: List[LocalizationAnalysisResult] = []
        for (zone_id,) in zone_rows:
            try:
                result = self.analyze_zone(db, zone_id)
                if result:
                    results.append(result)
            except Exception as e:
                logger.error("Localization failed for zone %s: %s", zone_id, e)

        # Sort by priority (critical first)
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        results.sort(key=lambda r: priority_order.get(r.priority, 4))

        return results

    # --------------------------------------------------
    # Suspicion Score Computation
    # --------------------------------------------------

    def _compute_suspicion_scores(
        self,
        consumers: List[Device],
        risk_scores: Dict[str, float],
        energy_deviations: Dict[str, float],
        balance,
    ) -> List[SuspectAnalysis]:
        """
        Compute suspicion score for each consumer.

        Formula:
            suspicion = (risk_score × 0.6) + (energy_deviation × 0.4)

        Both components are 0-100, so suspicion is also 0-100.
        """
        suspects: List[SuspectAnalysis] = []

        for device in consumers:
            did = device.device_id
            risk = risk_scores.get(did, 0.0)
            deviation = energy_deviations.get(did, 0.0)

            # Weighted combination
            suspicion = (risk * 0.6) + (deviation * 0.4)
            suspicion = min(100.0, max(0.0, suspicion))

            # Generate reason based on dominant factor
            reason = self._generate_suspect_reason(did, risk, deviation, suspicion)

            # Recommend action based on suspicion level
            action = self._recommend_action(suspicion)

            suspects.append(SuspectAnalysis(
                device_id=did,
                suspicion_score=suspicion,
                risk_score=risk,
                energy_deviation=deviation,
                reason=reason,
                recommended_action=action,
            ))

        # Sort by suspicion score DESC
        suspects.sort(key=lambda s: s.suspicion_score, reverse=True)

        return suspects

    def _get_latest_risk_scores(
        self,
        db: Session,
        consumers: List[Device],
    ) -> Dict[str, float]:
        """Get the latest risk score for each consumer."""
        scores: Dict[str, float] = {}

        for device in consumers:
            latest = (
                db.query(RiskScore)
                .filter(RiskScore.device_id == device.device_id)
                .order_by(RiskScore.calculated_at.desc())
                .first()
            )
            if latest:
                scores[device.device_id] = latest.overall_score
            else:
                scores[device.device_id] = 0.0

        return scores

    # --------------------------------------------------
    # Confidence Calculation
    # --------------------------------------------------

    def _calculate_confidence(
        self,
        balance,
        suspects: List[SuspectAnalysis],
        consumers: List[Device],
    ) -> float:
        """
        Calculate localization confidence (0-1).

        Higher confidence when:
        1. Energy imbalance is large and clear
        2. Suspicion scores are spread (one device clearly stands out)
        3. We have good data quality (enough readings)

        Lower confidence when:
        - Imbalance is small (could be noise)
        - All consumers have similar scores (can't distinguish)
        - Missing data for some consumers
        """
        # Component 1: Imbalance magnitude (0-1)
        # 500W+ imbalance → high confidence on this factor
        imbalance_confidence = min(balance.unaccounted_power / 500.0, 1.0)

        # Component 2: Score spread (0-1)
        # High when one suspect clearly stands out
        if len(suspects) >= 2:
            scores = [s.suspicion_score for s in suspects]
            max_score = max(scores)
            second_max = sorted(scores, reverse=True)[1]
            spread = (max_score - second_max) / 100.0 if max_score > 0 else 0.0
            score_spread_confidence = min(spread * 2.0, 1.0)  # Amplify
        else:
            score_spread_confidence = 0.3  # Low confidence with only 1 suspect

        # Component 3: Data quality (0-1)
        # Based on how many consumers we have data for
        consumers_with_data = sum(1 for s in suspects if s.risk_score > 0)
        data_quality = consumers_with_data / len(consumers) if consumers else 0.0

        # Weighted combination
        confidence = (
            imbalance_confidence * CONFIDENCE_IMBALANCE_WEIGHT
            + score_spread_confidence * CONFIDENCE_SCORE_SPREAD_WEIGHT
            + data_quality * CONFIDENCE_DATA_QUALITY_WEIGHT
        )

        return min(1.0, max(0.0, confidence))

    # --------------------------------------------------
    # Priority Assignment
    # --------------------------------------------------

    @staticmethod
    def _assign_priority(confidence: float, estimated_loss_kwh: float) -> str:
        """
        Assign investigation priority based on confidence and loss magnitude.

        High loss with high confidence → critical
        High confidence alone → high
        Moderate confidence → medium
        Low confidence → low
        """
        # Boost priority for large losses
        loss_factor = min(estimated_loss_kwh / 5.0, 1.0)  # 5+ kWh = max factor
        effective_confidence = confidence * 0.7 + loss_factor * 0.3

        if effective_confidence >= PRIORITY_CRITICAL_CONFIDENCE:
            return "critical"
        elif effective_confidence >= PRIORITY_HIGH_CONFIDENCE:
            return "high"
        elif effective_confidence >= PRIORITY_MEDIUM_CONFIDENCE:
            return "medium"
        return "low"

    # --------------------------------------------------
    # Reason & Action Generation
    # --------------------------------------------------

    @staticmethod
    def _generate_suspect_reason(
        device_id: str,
        risk_score: float,
        energy_deviation: float,
        suspicion: float,
    ) -> str:
        """Generate human-readable reason for suspicion."""
        factors = []

        if risk_score >= 70:
            factors.append(f"high composite risk score ({risk_score:.0f}/100)")
        elif risk_score >= 40:
            factors.append(f"elevated risk score ({risk_score:.0f}/100)")

        if energy_deviation >= 50:
            factors.append(f"significant energy reporting deficit ({energy_deviation:.0f}%)")
        elif energy_deviation >= 20:
            factors.append(f"moderate energy reporting gap ({energy_deviation:.0f}%)")

        if not factors:
            return f"Low suspicion — within normal parameters (score: {suspicion:.1f}/100)"

        return f"Flagged due to: {'; '.join(factors)}"

    @staticmethod
    def _recommend_action(suspicion_score: float) -> str:
        """Suggest investigation action based on suspicion level."""
        if suspicion_score >= 75:
            return "immediate_field_inspection"
        elif suspicion_score >= 50:
            return "field_inspection"
        elif suspicion_score >= 30:
            return "enhanced_monitoring"
        return "routine_monitoring"

    # --------------------------------------------------
    # Persistence
    # --------------------------------------------------

    def _persist_localization(
        self, db: Session, result: LocalizationAnalysisResult
    ) -> None:
        """Save localization result to the database."""
        try:
            suspect_devices = [
                s.to_suspect_device() for s in result.suspects
            ]

            loc_data = LocalizationCreate(
                zone_id=result.zone_id,
                confidence=result.confidence,
                priority=result.priority,
                estimated_loss_kwh=result.estimated_loss_kwh,
                suspect_devices=suspect_devices,
            )

            localization_service.create_result(db, loc_data)

        except Exception as e:
            logger.error(
                "Failed to persist localization for zone %s: %s",
                result.zone_id, e,
            )


# Module-level singleton
localization_engine = LocalizationEngine()
