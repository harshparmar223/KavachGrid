"""
KAVACHGRID 3.0 — Unit Tests for MQTT Message Handlers & Normalization
Phase 3 / Phase 14: Testing payload decoding, telemetry normalization, and handler routing.
"""

from datetime import datetime, timezone
import json
from unittest.mock import MagicMock, patch

import pytest

from app.mqtt.handlers import (
    decode_payload,
    handle_alert_message,
    handle_consumer_telemetry,
    handle_feeder_telemetry,
    handle_localization_telemetry,
    normalize_telemetry_payload,
    route_and_process_message,
)
from app.mqtt.topics import validate_topic


class TestMQTTHandlers:
    """Test payload decoding, normalization, and handler functions."""

    def test_decode_payload_valid_json_str(self):
        payload_str = '{"device_id": "CONSUMER-H1", "voltage": 230.5, "current": 2.1}'
        is_valid, data, err = decode_payload(payload_str)
        assert is_valid is True
        assert data["device_id"] == "CONSUMER-H1"
        assert data["voltage"] == 230.5
        assert err is None

    def test_decode_payload_valid_bytes(self):
        payload_bytes = b'{"voltage": 229.0, "current": 3.0, "power": 687.0}'
        is_valid, data, err = decode_payload(payload_bytes)
        assert is_valid is True
        assert data["power"] == 687.0

    def test_decode_payload_dict_direct(self):
        raw = {"test": 123}
        is_valid, data, err = decode_payload(raw)
        assert is_valid is True
        assert data["test"] == 123

    def test_decode_payload_malformed_json(self):
        is_valid, data, err = decode_payload('{"voltage": 230.0, current:')
        assert is_valid is False
        assert data is None
        assert "Invalid JSON" in err

    def test_decode_payload_empty(self):
        is_valid, data, err = decode_payload("")
        assert is_valid is False
        assert "empty" in err

    def test_normalize_telemetry_payload_aliases(self):
        raw = {
            "v": 232.0,
            "i": 1.5,
            "e": 500.0,
            "pf": 0.95,
            "hz": 49.9,
            "node_id": "h2",
        }
        norm = normalize_telemetry_payload(raw)
        assert norm["device_id"] == "CONSUMER-H2"
        assert norm["voltage"] == 232.0
        assert norm["current"] == 1.5
        assert norm["power"] == 232.0 * 1.5
        assert norm["energy"] == 500.0
        assert norm["power_factor"] == 0.95
        assert norm["frequency"] == 49.9
        assert isinstance(norm["timestamp"], datetime)

    def test_normalize_telemetry_timestamp_unix(self):
        raw = {"v": 230.0, "i": 1.0, "p": 230.0, "e": 10.0, "ts": 1700000000}
        norm = normalize_telemetry_payload(raw, default_device_id="FEEDER-01")
        assert norm["device_id"] == "FEEDER-01"
        assert norm["timestamp"] == datetime.fromtimestamp(1700000000, tz=timezone.utc)

    def test_route_and_process_invalid_topic(self):
        res = route_and_process_message("invalid/topic/path", b'{"voltage": 230}')
        assert res["status"] == "rejected"
        assert res["reason"] == "invalid_topic"

    def test_route_and_process_malformed_json(self):
        res = route_and_process_message("kavachgrid/feeder", b'NOT_JSON')
        assert res["status"] == "rejected"
        assert res["reason"] == "malformed_payload"

    @patch("app.mqtt.handlers.telemetry_service.ingest_telemetry")
    @patch("app.mqtt.handlers.device_service.ensure_device_exists")
    def test_handle_feeder_telemetry(self, mock_ensure_dev, mock_ingest):
        mock_telemetry = MagicMock()
        mock_telemetry.id = "mock-uuid"
        mock_telemetry.device_id = "FEEDER-01"
        mock_telemetry.voltage = 230.0
        mock_telemetry.current = 10.5
        mock_telemetry.power = 2415.0
        mock_telemetry.timestamp = datetime.now(timezone.utc)
        mock_ingest.return_value = mock_telemetry

        topic_info = validate_topic("kavachgrid/feeder")
        payload = {"voltage": 230.0, "current": 10.5, "power": 2415.0, "energy": 5000.0}
        mock_db = MagicMock()

        res = handle_feeder_telemetry(topic_info, payload, mock_db)
        assert res["status"] == "success"
        assert res["type"] == "feeder_telemetry"
        assert res["device_id"] == "FEEDER-01"
        mock_ensure_dev.assert_called_once()
        mock_ingest.assert_called_once()

    @patch("app.mqtt.handlers.telemetry_service.ingest_telemetry")
    @patch("app.mqtt.handlers.device_service.ensure_device_exists")
    def test_handle_consumer_telemetry(self, mock_ensure_dev, mock_ingest):
        mock_telemetry = MagicMock()
        mock_telemetry.id = "mock-uuid-c1"
        mock_telemetry.device_id = "CONSUMER-H1"
        mock_telemetry.voltage = 228.0
        mock_telemetry.current = 2.0
        mock_telemetry.power = 456.0
        mock_telemetry.timestamp = datetime.now(timezone.utc)
        mock_ingest.return_value = mock_telemetry

        topic_info = validate_topic("kavachgrid/meter/h1")
        payload = {"voltage": 228.0, "current": 2.0, "energy": 1200.0}
        mock_db = MagicMock()

        res = handle_consumer_telemetry(topic_info, payload, mock_db)
        assert res["status"] == "success"
        assert res["type"] == "consumer_telemetry"
        assert res["device_id"] == "CONSUMER-H1"

    @patch("app.mqtt.handlers.alert_service.create_alert")
    def test_handle_alert_message(self, mock_create_alert):
        mock_alert = MagicMock()
        mock_alert.id = "mock-alert-uuid"
        mock_alert.severity = "critical"
        mock_alert.title = "High Current Spike Detected"
        mock_alert.device_id = "CONSUMER-H1"
        mock_create_alert.return_value = mock_alert

        topic_info = validate_topic("kavachgrid/alerts")
        payload = {
            "device_id": "CONSUMER-H1",
            "alert_type": "meter_health",
            "severity": "critical",
            "title": "High Current Spike Detected",
            "message": "Current exceeded 15A threshold on consumer meter H1.",
        }
        mock_db = MagicMock()

        res = handle_alert_message(topic_info, payload, mock_db)
        assert res["status"] == "success"
        assert res["type"] == "alert"
        assert res["severity"] == "critical"
        mock_create_alert.assert_called_once()
