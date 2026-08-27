"""
KAVACHGRID 3.0 — MQTT Topic Definitions & Validation Logic
Phase 3: Complete Implementation

Defines the canonical MQTT topic hierarchy for KAVACHGRID 3.0:
    - Feeder Telemetry:        kavachgrid/feeder OR kavachgrid/feeder/{device_id}
    - Consumer Telemetry:      kavachgrid/meter/{meter_id} OR kavachgrid/consumer/{device_id}
    - Localization Telemetry:  kavachgrid/localization/{zone_id}
    - Alerts (System & Edge):  kavachgrid/alerts OR kavachgrid/alerts/{device_id}
    - Commands:                kavachgrid/commands/{device_id}

Provides topic parsing, validation, and payload matching rules.
"""

from dataclasses import dataclass
import re
from typing import Optional, Tuple


# Base topic namespace
TOPIC_ROOT = "kavachgrid"

# Topic Types
TYPE_FEEDER = "feeder"
TYPE_CONSUMER = "consumer"
TYPE_LOCALIZATION = "localization"
TYPE_ALERT = "alert"
TYPE_COMMAND = "command"
TYPE_UNKNOWN = "unknown"

# Regex patterns for strict topic validation
PATTERN_FEEDER = re.compile(r"^kavachgrid/feeder(?:/([a-zA-Z0-9_-]+))?$")
PATTERN_CONSUMER = re.compile(r"^kavachgrid/(?:meter|consumer)/([a-zA-Z0-9_-]+)$")
PATTERN_LOCALIZATION = re.compile(r"^kavachgrid/localization/([a-zA-Z0-9_-]+)$")
PATTERN_ALERTS = re.compile(r"^kavachgrid/alerts(?:/([a-zA-Z0-9_-]+))?$")
PATTERN_COMMANDS = re.compile(r"^kavachgrid/commands/([a-zA-Z0-9_-]+)$")


@dataclass
class TopicMatchResult:
    """Detailed result of topic validation and parsing."""

    is_valid: bool
    topic: str
    topic_type: str
    device_id: Optional[str] = None
    zone_id: Optional[str] = None
    error_message: Optional[str] = None


def validate_topic(topic: str) -> TopicMatchResult:
    """
    Validate and parse an MQTT topic string against the KAVACHGRID topic hierarchy.

    Args:
        topic: The MQTT topic string to validate.

    Returns:
        TopicMatchResult containing validity flag, extracted node type, and identifiers.
    """
    if not topic or not isinstance(topic, str):
        return TopicMatchResult(
            is_valid=False,
            topic=str(topic),
            topic_type=TYPE_UNKNOWN,
            error_message="Topic must be a non-empty string.",
        )

    topic = topic.strip()

    # Reject MQTT wildcard characters in publishing/routing validation
    if "+" in topic or "#" in topic:
        return TopicMatchResult(
            is_valid=False,
            topic=topic,
            topic_type=TYPE_UNKNOWN,
            error_message="Published topic cannot contain wildcard characters (+ or #).",
        )

    # Check root namespace
    if not topic.startswith(f"{TOPIC_ROOT}/") and topic != TOPIC_ROOT:
        return TopicMatchResult(
            is_valid=False,
            topic=topic,
            topic_type=TYPE_UNKNOWN,
            error_message=f"Topic must belong to the '{TOPIC_ROOT}' namespace.",
        )

    # 1. Feeder pattern
    match_feeder = PATTERN_FEEDER.match(topic)
    if match_feeder:
        dev_id = match_feeder.group(1) or "FEEDER-01"
        return TopicMatchResult(
            is_valid=True,
            topic=topic,
            topic_type=TYPE_FEEDER,
            device_id=dev_id,
        )

    # 2. Consumer / Meter pattern
    match_consumer = PATTERN_CONSUMER.match(topic)
    if match_consumer:
        meter_id = match_consumer.group(1)
        return TopicMatchResult(
            is_valid=True,
            topic=topic,
            topic_type=TYPE_CONSUMER,
            device_id=meter_id,
        )

    # 3. Localization pattern
    match_loc = PATTERN_LOCALIZATION.match(topic)
    if match_loc:
        zone = match_loc.group(1)
        return TopicMatchResult(
            is_valid=True,
            topic=topic,
            topic_type=TYPE_LOCALIZATION,
            zone_id=zone,
            device_id=f"LOC-{zone.upper()}",
        )

    # 4. Alerts pattern
    match_alerts = PATTERN_ALERTS.match(topic)
    if match_alerts:
        dev_id = match_alerts.group(1)
        return TopicMatchResult(
            is_valid=True,
            topic=topic,
            topic_type=TYPE_ALERT,
            device_id=dev_id,
        )

    # 5. Commands pattern
    match_cmd = PATTERN_COMMANDS.match(topic)
    if match_cmd:
        dev_id = match_cmd.group(1)
        return TopicMatchResult(
            is_valid=True,
            topic=topic,
            topic_type=TYPE_COMMAND,
            device_id=dev_id,
        )

    # Unrecognized topic structure
    return TopicMatchResult(
        is_valid=False,
        topic=topic,
        topic_type=TYPE_UNKNOWN,
        error_message=f"Topic '{topic}' does not match any recognized KAVACHGRID schema.",
    )


def validate_payload_topic_match(topic: str, payload_device_id: Optional[str]) -> bool:
    """
    Check if the device_id in the JSON payload matches or is compatible with the topic.
    """
    match_res = validate_topic(topic)
    if not match_res.is_valid:
        return False

    if not payload_device_id:
        return True

    payload_clean = str(payload_device_id).strip().upper()

    if match_res.topic_type == TYPE_FEEDER:
        if match_res.device_id:
            return match_res.device_id.upper() in payload_clean or payload_clean.startswith("FEEDER")
        return payload_clean.startswith("FEEDER")

    if match_res.topic_type == TYPE_CONSUMER:
        topic_dev = (match_res.device_id or "").upper()
        return (
            topic_dev == payload_clean
            or topic_dev in payload_clean
            or f"CONSUMER-{topic_dev}" == payload_clean
            or payload_clean.endswith(topic_dev)
        )

    if match_res.topic_type == TYPE_LOCALIZATION:
        zone = (match_res.zone_id or "").upper()
        return zone in payload_clean or payload_clean.startswith("LOC")

    return True


# Helper Topic Formatters
def get_feeder_topic(device_id: Optional[str] = None) -> str:
    """Return canonical topic for feeder node."""
    if device_id and device_id != "FEEDER-01":
        return f"{TOPIC_ROOT}/feeder/{device_id.lower()}"
    return f"{TOPIC_ROOT}/feeder"


def get_consumer_topic(meter_id: str) -> str:
    """Return canonical topic for consumer meter node."""
    clean_id = meter_id.lower().replace("consumer-", "")
    return f"{TOPIC_ROOT}/meter/{clean_id}"


def get_localization_topic(zone_id: str) -> str:
    """Return canonical topic for localization node."""
    clean_zone = zone_id.lower().replace("zone-", "zone").replace("loc-", "")
    return f"{TOPIC_ROOT}/localization/{clean_zone}"


def get_alert_topic(device_id: Optional[str] = None) -> str:
    """Return canonical topic for alerts."""
    if device_id:
        return f"{TOPIC_ROOT}/alerts/{device_id.lower()}"
    return f"{TOPIC_ROOT}/alerts"


def get_command_topic(device_id: str) -> str:
    """Return canonical topic for device commands."""
    return f"{TOPIC_ROOT}/commands/{device_id.lower()}"
