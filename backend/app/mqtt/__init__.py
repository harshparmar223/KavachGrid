"""
KAVACHGRID 3.0 — MQTT Integration Module
Phase 3: Complete Implementation
"""

from app.mqtt.client import (
    KavachMQTTClient,
    mqtt_client,
    start_mqtt_client,
    stop_mqtt_client,
)
from app.mqtt.handlers import (
    decode_payload,
    handle_alert_message,
    handle_consumer_telemetry,
    handle_feeder_telemetry,
    handle_localization_telemetry,
    normalize_telemetry_payload,
    route_and_process_message,
)
from app.mqtt.topics import (
    TYPE_ALERT,
    TYPE_COMMAND,
    TYPE_CONSUMER,
    TYPE_FEEDER,
    TYPE_LOCALIZATION,
    TopicMatchResult,
    get_alert_topic,
    get_command_topic,
    get_consumer_topic,
    get_feeder_topic,
    get_localization_topic,
    validate_payload_topic_match,
    validate_topic,
)

__all__ = [
    "KavachMQTTClient",
    "mqtt_client",
    "start_mqtt_client",
    "stop_mqtt_client",
    "route_and_process_message",
    "decode_payload",
    "normalize_telemetry_payload",
    "handle_feeder_telemetry",
    "handle_consumer_telemetry",
    "handle_localization_telemetry",
    "handle_alert_message",
    "validate_topic",
    "validate_payload_topic_match",
    "TopicMatchResult",
    "TYPE_FEEDER",
    "TYPE_CONSUMER",
    "TYPE_LOCALIZATION",
    "TYPE_ALERT",
    "TYPE_COMMAND",
    "get_feeder_topic",
    "get_consumer_topic",
    "get_localization_topic",
    "get_alert_topic",
    "get_command_topic",
]
