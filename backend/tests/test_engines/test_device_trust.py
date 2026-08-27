"""
KAVACHGRID 3.0 — Unit Tests for Device Trust Engine (Phase 9)
Tests Zero Trust validation across all 4 pillars:
1. Identity Verification
2. Authentication & Key Integrity
3. Topic & Scope Authorization
4. Payload Validity & Physical Plausibility
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from app.db.models import Device
from app.engines.device_trust import DeviceTrustEngine, device_trust_engine


class TestDeviceTrustEngine:
    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def sample_device(self):
        device = Device(
            device_id="CONSUMER-H1",
            device_type="consumer",
            name="House 1 Meter",
            api_key="secret-key-123",
            status="online",
        )
        return device

    def test_valid_telemetry_high_trust(self, mock_db, sample_device):
        with patch("app.services.device_service.device_service.get_by_device_id", return_value=sample_device):
            payload = {
                "voltage": 230.0,
                "current": 2.5,
                "power": 560.0,
                "energy": 1200.0,
                "power_factor": 0.98,
                "frequency": 50.0,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            result = device_trust_engine.evaluate_trust(
                db=mock_db,
                device_id="CONSUMER-H1",
                topic="kavachgrid/meter/h1",
                raw_payload=payload,
                auto_alert=False,
            )
            assert result["trust_score"] >= 85.0
            assert result["is_trusted"] is True
            assert result["status"] in ["TRUSTED", "ADEQUATE"]
            assert result["identity_score"] == 25.0
            assert result["topic_score"] == 25.0

    def test_topic_spoofing_violation(self, mock_db, sample_device):
        with patch("app.services.device_service.device_service.get_by_device_id", return_value=sample_device):
            payload = {
                "voltage": 230.0,
                "current": 2.0,
                "power": 460.0,
            }
            # Consumer H1 publishing to Feeder topic or Meter H2 topic
            result = device_trust_engine.evaluate_trust(
                db=mock_db,
                device_id="CONSUMER-H1",
                topic="kavachgrid/meter/h2",
                raw_payload=payload,
                auto_alert=False,
            )
            # Topic score should be severely docked
            assert result["topic_score"] <= 5.0
            assert any("Topic authorization violation" in r for r in result["reasons"])

    def test_invalid_api_key(self, mock_db, sample_device):
        with patch("app.services.device_service.device_service.get_by_device_id", return_value=sample_device):
            payload = {
                "voltage": 230.0,
                "current": 2.0,
                "power": 460.0,
                "api_key": "wrong-key",
            }
            result = device_trust_engine.evaluate_trust(
                db=mock_db,
                device_id="CONSUMER-H1",
                topic="kavachgrid/meter/h1",
                raw_payload=payload,
                auto_alert=False,
            )
            assert result["auth_score"] == 0.0
            assert any("Provided API key does not match" in r for r in result["reasons"])

    def test_valid_api_key(self, mock_db, sample_device):
        with patch("app.services.device_service.device_service.get_by_device_id", return_value=sample_device):
            payload = {
                "voltage": 230.0,
                "current": 2.0,
                "power": 460.0,
                "api_key": "secret-key-123",
            }
            result = device_trust_engine.evaluate_trust(
                db=mock_db,
                device_id="CONSUMER-H1",
                topic="kavachgrid/meter/h1",
                raw_payload=payload,
                auto_alert=False,
            )
            assert result["auth_score"] == 25.0

    def test_physical_plausibility_impossible_values(self, mock_db, sample_device):
        with patch("app.services.device_service.device_service.get_by_device_id", return_value=sample_device):
            payload = {
                "voltage": -50.0,  # Negative voltage
                "current": -10.0,  # Negative current
                "power": -500.0,   # Negative power
                "frequency": 95.0, # Impossible frequency
            }
            result = device_trust_engine.evaluate_trust(
                db=mock_db,
                device_id="CONSUMER-H1",
                topic="kavachgrid/meter/h1",
                raw_payload=payload,
                auto_alert=False,
            )
            assert result["payload_score"] <= 5.0
            assert result["trust_score"] < 60.0
            assert result["status"] in ["SUSPICIOUS", "UNTRUSTED"]

    def test_power_inconsistency_tampering_check(self, mock_db, sample_device):
        with patch("app.services.device_service.device_service.get_by_device_id", return_value=sample_device):
            # 230V * 10A = 2300W, but reported power is 100W (blatant bypass/tampering)
            payload = {
                "voltage": 230.0,
                "current": 10.0,
                "power": 100.0,
                "power_factor": 1.0,
            }
            result = device_trust_engine.evaluate_trust(
                db=mock_db,
                device_id="CONSUMER-H1",
                topic="kavachgrid/meter/h1",
                raw_payload=payload,
                auto_alert=False,
            )
            assert any("Power inconsistency" in r for r in result["reasons"])

    def test_future_timestamp_penalty(self, mock_db, sample_device):
        with patch("app.services.device_service.device_service.get_by_device_id", return_value=sample_device):
            future_ts = datetime.now(timezone.utc) + timedelta(hours=2)
            payload = {
                "voltage": 230.0,
                "current": 2.0,
                "power": 460.0,
                "timestamp": future_ts.isoformat(),
            }
            result = device_trust_engine.evaluate_trust(
                db=mock_db,
                device_id="CONSUMER-H1",
                topic="kavachgrid/meter/h1",
                raw_payload=payload,
                auto_alert=False,
            )
            assert any("Future timestamp detected" in r for r in result["reasons"])

    def test_alert_generation_on_low_trust(self, mock_db, sample_device):
        with patch("app.services.device_service.device_service.get_by_device_id", return_value=sample_device), \
             patch("app.services.alert_service.alert_service.create_alert") as mock_alert:
            payload = {
                "voltage": -230.0,
                "current": -5.0,
                "power": -1000.0,
                "api_key": "bad-key",
            }
            result = device_trust_engine.evaluate_trust(
                db=mock_db,
                device_id="CONSUMER-H1",
                topic="kavachgrid/meter/h2",  # Cross-topic mismatch
                raw_payload=payload,
                auto_alert=True,
            )
            assert result["trust_score"] < 40.0
            assert result["status"] == "UNTRUSTED"
            assert mock_alert.called
            call_args = mock_alert.call_args[0][1]
            assert call_args.alert_type == "device_trust"
            assert call_args.severity == "critical"
