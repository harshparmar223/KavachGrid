"""
KAVACHGRID 3.0 — Device Trust Engine
Phase 9: Lightweight Zero Trust Device Validation & Scoring

Pillars of Zero Trust Evaluation (0–100 score):
1. Identity Verification (0–25 pts): Valid ID format, DB registration, device_type consistency, status check.
2. Authentication & Key Integrity (0–25 pts): API key match (device or system key), credential validity.
3. Topic & Scope Authorization (0–25 pts): Topic hierarchy matching, device-topic isolation, spoofing detection.
4. Payload Validity & Physical Plausibility (0–25 pts): Range checks (V, I, P, PF, Hz), power consistency (P ≈ V*I*PF), timestamp freshness.

Outputs:
- Trust Score (0–100)
- Trust Level: "TRUSTED" (90-100), "ADEQUATE" (70-89), "SUSPICIOUS" (50-69), "UNTRUSTED" (<50)
- Automatic Alert generation for low-trust readings (<60)
"""

from datetime import datetime, timezone, timedelta
import logging
import math
import re
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.config import settings
from app.db.models import Device
from app.schemas.alert import AlertCreate
from app.services.alert_service import alert_service
from app.services.device_service import device_service

logger = logging.getLogger("kavachgrid.engines.device_trust")

# Regex for standard device ID validation
DEVICE_ID_REGEX = re.compile(r"^[A-Za-z0-9_-]{3,50}$")


class DeviceTrustEngine:
    """
    Zero Trust-inspired validation engine for KAVACHGRID 3.0 nodes.
    Computes a composite trust score (0-100) across 4 foundational pillars.
    """

    TRUST_THRESHOLD_ALERT = 60.0
    TRUST_LEVEL_TRUSTED = "TRUSTED"
    TRUST_LEVEL_ADEQUATE = "ADEQUATE"
    TRUST_LEVEL_SUSPICIOUS = "SUSPICIOUS"
    TRUST_LEVEL_UNTRUSTED = "UNTRUSTED"

    def __init__(self):
        pass

    # =========================================================================
    # Pillar 1: Device Identity & Registry Verification (Max 25 pts)
    # =========================================================================
    def _verify_identity(
        self,
        db: Session,
        device_id: str,
        raw_payload: Dict[str, Any],
        reasons: List[str],
    ) -> float:
        score = 25.0

        # Check format
        if not device_id or not DEVICE_ID_REGEX.match(str(device_id)):
            score -= 15.0
            reasons.append(f"Invalid device ID format: '{device_id}'")
            return max(0.0, score)

        # Check registration in DB
        device = device_service.get_by_device_id(db, device_id)
        if not device:
            # Unregistered / newly seen node
            score -= 5.0
            reasons.append(f"Device '{device_id}' is not pre-registered in registry")
        else:
            # Check device status
            if device.status == "warning":
                score -= 6.0
                reasons.append(f"Device '{device_id}' currently has status 'warning'")

            # Check type consistency if payload provides a type hint
            payload_type = raw_payload.get("device_type") or raw_payload.get("type")
            if payload_type:
                payload_type_clean = str(payload_type).strip().lower()
                if payload_type_clean != device.device_type.lower():
                    score -= 8.0
                    reasons.append(
                        f"Device type mismatch: registered as '{device.device_type}', payload claimed '{payload_type_clean}'"
                    )

        return max(0.0, score)

    # =========================================================================
    # Pillar 2: Authentication & API Key Integrity (Max 25 pts)
    # =========================================================================
    def _verify_authentication(
        self,
        db: Session,
        device_id: str,
        raw_payload: Dict[str, Any],
        api_key: Optional[str],
        reasons: List[str],
    ) -> float:
        device = device_service.get_by_device_id(db, device_id)
        provided_key = (
            api_key
            or raw_payload.get("api_key")
            or raw_payload.get("key")
            or raw_payload.get("token")
        )

        if provided_key:
            # Explicit key provided — verify strictly
            if device and device.api_key and provided_key == device.api_key:
                return 25.0
            if settings.API_KEY and provided_key == settings.API_KEY:
                return 25.0
            # Key was supplied but is invalid!
            reasons.append("Provided API key does not match device or system key")
            return 0.0

        # No explicit API key in payload/args (standard for basic MQTT payloads)
        if device:
            # Device exists in database
            return 20.0

        # Unregistered node with no credentials
        reasons.append("No API key provided for unverified device")
        return 12.0

    # =========================================================================
    # Pillar 3: Topic & Namespace Authorization (Max 25 pts)
    # =========================================================================
    def _verify_topic_authorization(
        self,
        device_id: str,
        topic: Optional[str],
        reasons: List[str],
    ) -> float:
        if not topic:
            # Ingestion via direct API call without MQTT topic
            return 25.0

        from app.mqtt.topics import (
            TYPE_CONSUMER,
            TYPE_FEEDER,
            TYPE_LOCALIZATION,
            TopicMatchResult,
            validate_payload_topic_match,
            validate_topic,
        )

        score = 25.0
        topic_match: TopicMatchResult = validate_topic(topic)

        if not topic_match.is_valid:
            reasons.append(f"Invalid MQTT topic: {topic_match.error_message or topic}")
            return 0.0

        # Check payload/device match with topic (Anti-spoofing check)
        is_topic_match = validate_payload_topic_match(topic, device_id)
        if not is_topic_match:
            score -= 20.0
            reasons.append(
                f"Topic authorization violation: device '{device_id}' published to mismatched topic '{topic}'"
            )
            return max(0.0, score)

        # Role consistency checks
        clean_dev = device_id.upper()
        if "FEEDER" in clean_dev and topic_match.topic_type != TYPE_FEEDER:
            score -= 10.0
            reasons.append(f"Feeder device '{device_id}' published to non-feeder topic '{topic}'")
        elif ("CONSUMER" in clean_dev or "METER" in clean_dev) and topic_match.topic_type != TYPE_CONSUMER:
            score -= 10.0
            reasons.append(f"Consumer device '{device_id}' published to non-consumer topic '{topic}'")
        elif "LOC" in clean_dev and topic_match.topic_type != TYPE_LOCALIZATION:
            score -= 10.0
            reasons.append(f"Localization device '{device_id}' published to non-localization topic '{topic}'")

        return max(0.0, score)

    # =========================================================================
    # Pillar 4: Payload Validity & Physical Plausibility (Max 25 pts)
    # =========================================================================
    def _verify_payload_validity(
        self,
        raw_payload: Dict[str, Any],
        reasons: List[str],
    ) -> float:
        score = 25.0

        # 1. Voltage validation
        v_raw = raw_payload.get("voltage") or raw_payload.get("v")
        if v_raw is not None:
            try:
                v = float(v_raw)
                if v < 0 or v > 500:
                    score -= 8.0
                    reasons.append(f"Voltage out of physical range: {v}V")
                elif v < 160 or v > 280:
                    score -= 3.0
                    reasons.append(f"Voltage abnormal for grid standard: {v}V")
            except (ValueError, TypeError):
                score -= 6.0
                reasons.append(f"Invalid voltage format: {v_raw}")
        else:
            score -= 4.0
            reasons.append("Missing voltage in telemetry payload")

        # 2. Current validation
        i_raw = raw_payload.get("current") or raw_payload.get("current_a") or raw_payload.get("i")
        if i_raw is not None:
            try:
                i = float(i_raw)
                if i < 0:
                    score -= 8.0
                    reasons.append(f"Negative current reading: {i}A")
                elif i > 120:
                    score -= 4.0
                    reasons.append(f"Extreme overcurrent reading: {i}A")
            except (ValueError, TypeError):
                score -= 6.0
                reasons.append(f"Invalid current format: {i_raw}")
        else:
            score -= 4.0
            reasons.append("Missing current in telemetry payload")

        # 3. Power validation & Physical Consistency (P ≈ V * I * PF)
        p_raw = raw_payload.get("power") or raw_payload.get("power_w") or raw_payload.get("p") or raw_payload.get("w")
        if p_raw is not None:
            try:
                p = float(p_raw)
                if p < 0:
                    score -= 8.0
                    reasons.append(f"Negative power reading: {p}W")

                # Cross-check V * I vs Power if both V and I exist
                if v_raw is not None and i_raw is not None:
                    try:
                        v = float(v_raw)
                        i = float(i_raw)
                        pf_raw = raw_payload.get("power_factor") or raw_payload.get("pf") or 0.98
                        pf = max(0.1, min(1.0, float(pf_raw)))
                        expected_power = v * i * pf

                        # Check tolerance: allow ±35% + 15W margin
                        diff = abs(p - expected_power)
                        allowed_tolerance = 0.35 * expected_power + 15.0
                        if diff > allowed_tolerance and (v > 10 and i > 0.05):
                            score -= 5.0
                            reasons.append(
                                f"Power inconsistency: reported {p:.1f}W vs expected {expected_power:.1f}W (V*I*PF)"
                            )
                    except Exception:
                        pass
            except (ValueError, TypeError):
                score -= 5.0
                reasons.append(f"Invalid power format: {p_raw}")

        # 4. Frequency validation
        f_raw = raw_payload.get("frequency") or raw_payload.get("freq") or raw_payload.get("hz")
        if f_raw is not None:
            try:
                freq = float(f_raw)
                if freq < 45.0 or freq > 65.0:
                    score -= 3.0
                    reasons.append(f"Grid frequency out of bounds: {freq}Hz")
            except (ValueError, TypeError):
                score -= 2.0

        # 5. Timestamp freshness validation
        ts_raw = raw_payload.get("timestamp") or raw_payload.get("ts")
        if ts_raw:
            now = datetime.now(timezone.utc)
            ts = None
            if isinstance(ts_raw, (int, float)):
                if ts_raw > 1e11:
                    ts = datetime.fromtimestamp(ts_raw / 1000.0, tz=timezone.utc)
                else:
                    ts = datetime.fromtimestamp(ts_raw, tz=timezone.utc)
            elif isinstance(ts_raw, str):
                try:
                    ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
                except ValueError:
                    pass

            if ts:
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                
                # Check future timestamp (> 5 mins)
                if ts > now + timedelta(minutes=5):
                    score -= 6.0
                    reasons.append(f"Future timestamp detected: {ts.isoformat()}")
                # Check stale data (> 48 hours in past)
                elif ts < now - timedelta(hours=48):
                    score -= 4.0
                    reasons.append(f"Stale historical timestamp detected: {ts.isoformat()}")

        return max(0.0, score)

    # =========================================================================
    # Master Evaluation Method
    # =========================================================================
    def evaluate_trust(
        self,
        db: Session,
        device_id: str,
        topic: Optional[str] = None,
        raw_payload: Optional[Dict[str, Any]] = None,
        api_key: Optional[str] = None,
        auto_alert: bool = True,
    ) -> Dict[str, Any]:
        """
        Evaluate full Zero Trust score (0-100) and component breakdown.

        Args:
            db: Database session
            device_id: Human-readable device ID
            topic: MQTT topic where payload was published (if applicable)
            raw_payload: Raw or parsed telemetry dictionary
            api_key: Optional API key passed in request header/auth
            auto_alert: Whether to generate an alert if trust score is below threshold

        Returns:
            Dict containing composite trust_score, component scores, status, and explanations.
        """
        payload = raw_payload or {}
        reasons: List[str] = []

        # 1. Evaluate 4 Pillars
        identity_score = self._verify_identity(db, device_id, payload, reasons)
        auth_score = self._verify_authentication(db, device_id, payload, api_key, reasons)
        topic_score = self._verify_topic_authorization(device_id, topic, reasons)
        payload_score = self._verify_payload_validity(payload, reasons)

        # 2. Composite Score (Sum of 4 components, each 0-25 => Total 0-100)
        total_score = round(identity_score + auth_score + topic_score + payload_score, 1)

        # Zero Trust Integrity Guard: If multiple severe physical impossibilities exist (e.g. negative V/I/P),
        # cap total score so corrupted or spoofed sensors cannot pass as ADEQUATE/TRUSTED
        severe_violations = sum(
            1 for r in reasons if "out of physical range" in r or "Negative" in r or "frequency out of bounds" in r
        )
        if severe_violations >= 2:
            total_score = min(total_score, 55.0)

        total_score = max(0.0, min(100.0, total_score))

        # 3. Categorize Status
        if total_score >= 90.0:
            status = self.TRUST_LEVEL_TRUSTED
        elif total_score >= 70.0:
            status = self.TRUST_LEVEL_ADEQUATE
        elif total_score >= 50.0:
            status = self.TRUST_LEVEL_SUSPICIOUS
        else:
            status = self.TRUST_LEVEL_UNTRUSTED

        is_trusted = total_score >= 70.0

        # 4. Trigger alert if trust score is below threshold (< 60)
        if auto_alert and total_score < self.TRUST_THRESHOLD_ALERT:
            severity = "critical" if total_score < 40.0 else "high"
            reason_summary = "; ".join(reasons) if reasons else "Multiple trust criteria failed."
            try:
                alert_service.create_alert(
                    db,
                    AlertCreate(
                        device_id=device_id,
                        alert_type="device_trust",
                        severity=severity,
                        title=f"Low Device Trust Score: {device_id} ({total_score}/100)",
                        message=(
                            f"Device trust evaluation failed Zero Trust validation with score {total_score}/100 "
                            f"[{status}]. Reasons: {reason_summary}"
                        ),
                        details={
                            "trust_score": total_score,
                            "status": status,
                            "identity_score": identity_score,
                            "auth_score": auth_score,
                            "topic_score": topic_score,
                            "payload_score": payload_score,
                            "reasons": reasons,
                            "topic": topic,
                        },
                    ),
                )
                logger.warning(
                    f"🛡️ Low trust alert triggered for {device_id}: score={total_score} [{status}]"
                )
            except Exception as e:
                logger.error(f"Failed to generate device_trust alert for {device_id}: {e}")

        return {
            "device_id": device_id,
            "trust_score": total_score,
            "is_trusted": is_trusted,
            "status": status,
            "identity_score": identity_score,
            "auth_score": auth_score,
            "topic_score": topic_score,
            "payload_score": payload_score,
            "reasons": reasons,
            "details": {
                "identity_score": identity_score,
                "auth_score": auth_score,
                "topic_score": topic_score,
                "payload_score": payload_score,
                "topic": topic,
            },
        }

    def calculate_trust_score(
        self,
        db: Session,
        device_id: str,
        topic: Optional[str] = None,
        raw_payload: Optional[Dict[str, Any]] = None,
        api_key: Optional[str] = None,
        auto_alert: bool = True,
    ) -> float:
        """Convenience method returning float trust score (0.0 to 100.0)."""
        result = self.evaluate_trust(
            db,
            device_id=device_id,
            topic=topic,
            raw_payload=raw_payload,
            api_key=api_key,
            auto_alert=auto_alert,
        )
        return result["trust_score"]


device_trust_engine = DeviceTrustEngine()
