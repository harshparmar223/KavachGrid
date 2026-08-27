"""
KAVACHGRID 3.0 — MQTT Message Handlers & Routing Dispatcher
Phase 3: Complete Implementation

Routes incoming MQTT messages to the appropriate service based on topic pattern matching:
    - Feeder Telemetry       -> TelemetryService (device_type='feeder')
    - Consumer Telemetry     -> TelemetryService (device_type='consumer')
    - Localization Telemetry -> TelemetryService (device_type='localization')
    - Alert Messages         -> AlertService
    - Commands               -> Command Dispatcher

Includes payload sanitization, Pydantic validation, schema normalization, and DB session lifecycle.
"""

from datetime import datetime, timezone
import json
import logging
from typing import Any, Dict, Optional, Tuple, Union

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.mqtt.topics import (
    TYPE_ALERT,
    TYPE_COMMAND,
    TYPE_CONSUMER,
    TYPE_FEEDER,
    TYPE_LOCALIZATION,
    TYPE_UNKNOWN,
    TopicMatchResult,
    validate_payload_topic_match,
    validate_topic,
)
from app.schemas.alert import AlertCreate
from app.schemas.telemetry import TelemetryCreate
from app.services.alert_service import alert_service
from app.services.device_service import device_service
from app.services.telemetry_service import telemetry_service
from app.engines.device_trust import device_trust_engine

logger = logging.getLogger("kavachgrid.mqtt.handlers")


def decode_payload(payload_raw: Union[bytes, str, dict]) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """
    Safely decode raw MQTT payload bytes/string into a Python dictionary.

    Returns:
        (is_valid, parsed_dict, error_message)
    """
    if isinstance(payload_raw, dict):
        return True, payload_raw, None

    if isinstance(payload_raw, bytes):
        try:
            payload_str = payload_raw.decode("utf-8")
        except UnicodeDecodeError as e:
            return False, None, f"UTF-8 decoding failed: {e}"
    elif isinstance(payload_raw, str):
        payload_str = payload_raw
    else:
        return False, None, f"Unsupported payload type: {type(payload_raw)}"

    if not payload_str or not payload_str.strip():
        return False, None, "Payload is empty."

    try:
        parsed = json.loads(payload_str)
        if not isinstance(parsed, dict):
            return False, None, f"Expected JSON object, got {type(parsed).__name__}"
        return True, parsed, None
    except json.JSONDecodeError as e:
        return False, None, f"Invalid JSON syntax: {e}"


def normalize_telemetry_payload(raw_dict: Dict[str, Any], default_device_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Normalize telemetry fields accommodating aliases (e.g. v/voltage, i/current, w/power).
    """
    device_id = raw_dict.get("device_id") or raw_dict.get("node_id") or raw_dict.get("id") or default_device_id

    # If it's a meter shorthand like 'h1', format to 'CONSUMER-H1'
    if device_id and device_id.lower().startswith("h") and len(device_id) <= 4:
        device_id = f"CONSUMER-{device_id.upper()}"
    elif device_id:
        device_id = str(device_id).strip()

    voltage = raw_dict.get("voltage") or raw_dict.get("v") or 230.0
    current = raw_dict.get("current") or raw_dict.get("current_a") or raw_dict.get("i") or raw_dict.get("a") or 0.0
    power = raw_dict.get("power") or raw_dict.get("power_w") or raw_dict.get("p") or raw_dict.get("w")
    if power is None:
        power = float(voltage) * float(current)

    energy = raw_dict.get("energy") or raw_dict.get("energy_wh") or raw_dict.get("e") or raw_dict.get("wh") or 0.0
    power_factor = raw_dict.get("power_factor") or raw_dict.get("pf") or 0.98
    frequency = raw_dict.get("frequency") or raw_dict.get("freq") or raw_dict.get("hz") or 50.0

    raw_ts = raw_dict.get("timestamp") or raw_dict.get("ts")
    ts = None
    if raw_ts:
        if isinstance(raw_ts, (int, float)):
            if raw_ts > 1e11:  # ms
                ts = datetime.fromtimestamp(raw_ts / 1000.0, tz=timezone.utc)
            else:
                ts = datetime.fromtimestamp(raw_ts, tz=timezone.utc)
        elif isinstance(raw_ts, str):
            try:
                ts = datetime.fromisoformat(raw_ts.replace("Z", "+00:00"))
            except ValueError:
                ts = datetime.now(timezone.utc)
    else:
        ts = datetime.now(timezone.utc)

    return {
        "device_id": device_id,
        "voltage": float(voltage),
        "current": float(current),
        "power": float(power),
        "energy": float(energy),
        "power_factor": float(power_factor) if power_factor is not None else None,
        "frequency": float(frequency) if frequency is not None else None,
        "timestamp": ts,
    }


def handle_feeder_telemetry(
    topic_info: TopicMatchResult,
    raw_payload: Dict[str, Any],
    db: Session,
) -> Dict[str, Any]:
    """Process incoming feeder node telemetry."""
    default_dev_id = topic_info.device_id or "FEEDER-01"
    normalized = normalize_telemetry_payload(raw_payload, default_device_id=default_dev_id)

    # Ensure device is marked as feeder
    device_service.ensure_device_exists(
        db,
        device_id=normalized["device_id"],
        device_type="feeder",
        name=f"Main Feeder ({normalized['device_id']})",
        zone_id="ZONE-ALL",
    )

    schema = TelemetryCreate(**normalized)
    trust_score = device_trust_engine.calculate_trust_score(
        db,
        device_id=normalized["device_id"],
        topic=topic_info.topic,
        raw_payload=raw_payload,
    )
    telemetry = telemetry_service.ingest_telemetry(
        db, schema, raw_payload=raw_payload, trust_score=trust_score
    )

    logger.info(
        f"⚡ Feeder telemetry ingested: {telemetry.device_id} | "
        f"V={telemetry.voltage:.1f}V | I={telemetry.current:.2f}A | P={telemetry.power:.1f}W | Trust={telemetry.trust_score}"
    )
    return {
        "status": "success",
        "type": "feeder_telemetry",
        "device_id": telemetry.device_id,
        "id": str(telemetry.id),
        "trust_score": telemetry.trust_score,
        "timestamp": telemetry.timestamp.isoformat(),
    }


def handle_consumer_telemetry(
    topic_info: TopicMatchResult,
    raw_payload: Dict[str, Any],
    db: Session,
) -> Dict[str, Any]:
    """Process incoming consumer smart meter telemetry."""
    default_dev_id = topic_info.device_id or "CONSUMER-H1"
    normalized = normalize_telemetry_payload(raw_payload, default_device_id=default_dev_id)

    # Ensure consumer device exists
    device_service.ensure_device_exists(
        db,
        device_id=normalized["device_id"],
        device_type="consumer",
        name=f"Consumer Node ({normalized['device_id']})",
    )

    schema = TelemetryCreate(**normalized)
    trust_score = device_trust_engine.calculate_trust_score(
        db,
        device_id=normalized["device_id"],
        topic=topic_info.topic,
        raw_payload=raw_payload,
    )
    telemetry = telemetry_service.ingest_telemetry(
        db, schema, raw_payload=raw_payload, trust_score=trust_score
    )

    logger.info(
        f"🏠 Consumer telemetry ingested: {telemetry.device_id} | "
        f"V={telemetry.voltage:.1f}V | I={telemetry.current:.2f}A | P={telemetry.power:.1f}W | Trust={telemetry.trust_score}"
    )
    return {
        "status": "success",
        "type": "consumer_telemetry",
        "device_id": telemetry.device_id,
        "id": str(telemetry.id),
        "trust_score": telemetry.trust_score,
        "timestamp": telemetry.timestamp.isoformat(),
    }


def handle_localization_telemetry(
    topic_info: TopicMatchResult,
    raw_payload: Dict[str, Any],
    db: Session,
) -> Dict[str, Any]:
    """Process telemetry from localization / branch CT clamp sensors."""
    zone_id = topic_info.zone_id or "ZONE-A"
    default_dev_id = topic_info.device_id or f"LOC-{zone_id.upper()}"
    normalized = normalize_telemetry_payload(raw_payload, default_device_id=default_dev_id)

    device_service.ensure_device_exists(
        db,
        device_id=normalized["device_id"],
        device_type="localization",
        name=f"Localization Node ({zone_id.upper()})",
        zone_id=zone_id.upper(),
    )

    schema = TelemetryCreate(**normalized)
    trust_score = device_trust_engine.calculate_trust_score(
        db,
        device_id=normalized["device_id"],
        topic=topic_info.topic,
        raw_payload=raw_payload,
    )
    telemetry = telemetry_service.ingest_telemetry(
        db, schema, raw_payload=raw_payload, trust_score=trust_score
    )

    logger.info(
        f"📍 Localization telemetry ingested: {telemetry.device_id} (Zone {zone_id}) | "
        f"I={telemetry.current:.2f}A | P={telemetry.power:.1f}W | Trust={telemetry.trust_score}"
    )
    return {
        "status": "success",
        "type": "localization_telemetry",
        "device_id": telemetry.device_id,
        "zone_id": zone_id,
        "trust_score": telemetry.trust_score,
        "id": str(telemetry.id),
    }


def handle_alert_message(
    topic_info: TopicMatchResult,
    raw_payload: Dict[str, Any],
    db: Session,
) -> Dict[str, Any]:
    """Process alerts published over MQTT (e.g. from edge nodes)."""
    device_id = raw_payload.get("device_id") or topic_info.device_id
    alert_type = raw_payload.get("alert_type") or raw_payload.get("type") or "meter_health"
    severity = raw_payload.get("severity") or "high"
    title = raw_payload.get("title") or f"Edge Alert from {device_id or 'System'}"
    message = raw_payload.get("message") or raw_payload.get("description") or "Edge threshold exceeded."
    details = raw_payload.get("details") or {k: v for k, v in raw_payload.items() if k not in ["device_id", "alert_type", "severity", "title", "message"]}

    schema = AlertCreate(
        device_id=device_id,
        alert_type=alert_type,
        severity=severity,
        title=title,
        message=message,
        details=details,
    )
    alert = alert_service.create_alert(db, schema)
    logger.warning(
        f"🚨 Alert received & stored: [{alert.severity.upper()}] {alert.title} (Device: {alert.device_id})"
    )
    return {
        "status": "success",
        "type": "alert",
        "alert_id": str(alert.id),
        "severity": alert.severity,
    }


def handle_command_message(
    topic_info: TopicMatchResult,
    raw_payload: Dict[str, Any],
    db: Session,
) -> Dict[str, Any]:
    """Process command acknowledgements or instructions from nodes."""
    device_id = topic_info.device_id or raw_payload.get("device_id")
    logger.info(f"⚙️ Command message received for {device_id}: {raw_payload}")
    return {
        "status": "success",
        "type": "command_ack",
        "device_id": device_id,
    }


def route_and_process_message(
    topic: str,
    payload_raw: Union[bytes, str, Dict[str, Any]],
    db: Optional[Session] = None,
) -> Dict[str, Any]:
    """
    Main MQTT message entry point.
    1. Validates topic
    2. Decodes JSON payload
    3. Manages DB session if not injected
    4. Dispatches to matching handler
    """
    topic_info = validate_topic(topic)
    if not topic_info.is_valid:
        logger.warning(f"❌ Rejected invalid topic '{topic}': {topic_info.error_message}")
        return {
            "status": "rejected",
            "reason": "invalid_topic",
            "topic": topic,
            "error": topic_info.error_message,
        }

    is_valid_json, raw_dict, decode_err = decode_payload(payload_raw)
    if not is_valid_json or raw_dict is None:
        logger.error(f"❌ Rejected malformed payload on topic '{topic}': {decode_err}")
        return {
            "status": "rejected",
            "reason": "malformed_payload",
            "topic": topic,
            "error": decode_err,
        }

    payload_dev = raw_dict.get("device_id") or raw_dict.get("node_id")
    if payload_dev and not validate_payload_topic_match(topic, str(payload_dev)):
        logger.warning(f"⚠️ Topic '{topic}' does not match payload device_id '{payload_dev}'")

    own_session = False
    if db is None:
        db = SessionLocal()
        own_session = True

    try:
        if topic_info.topic_type == TYPE_FEEDER:
            return handle_feeder_telemetry(topic_info, raw_dict, db)
        elif topic_info.topic_type == TYPE_CONSUMER:
            return handle_consumer_telemetry(topic_info, raw_dict, db)
        elif topic_info.topic_type == TYPE_LOCALIZATION:
            return handle_localization_telemetry(topic_info, raw_dict, db)
        elif topic_info.topic_type == TYPE_ALERT:
            return handle_alert_message(topic_info, raw_dict, db)
        elif topic_info.topic_type == TYPE_COMMAND:
            return handle_command_message(topic_info, raw_dict, db)
        else:
            return {
                "status": "unhandled",
                "topic_type": topic_info.topic_type,
                "topic": topic,
            }
    except ValidationError as ve:
        logger.error(f"❌ Schema validation failed on topic '{topic}': {ve}")
        return {
            "status": "rejected",
            "reason": "validation_error",
            "topic": topic,
            "error": str(ve),
        }
    except Exception as e:
        logger.exception(f"🔥 Error processing MQTT message on topic '{topic}': {e}")
        if own_session:
            db.rollback()
        return {
            "status": "error",
            "topic": topic,
            "error": str(e),
        }
    finally:
        if own_session:
            db.close()
