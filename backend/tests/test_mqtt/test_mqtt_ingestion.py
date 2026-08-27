"""
KAVACHGRID 3.0 — MQTT Ingestion Pipeline Tests
Phase 3 / Phase 14: Verifying end-to-end message ingestion into database and device status updates.
"""

from datetime import datetime, timezone
import json
from unittest.mock import MagicMock, patch
import uuid

import pytest

from app.db.models import Device, Telemetry
from app.mqtt.handlers import route_and_process_message
from app.schemas.telemetry import TelemetryCreate
from app.services.device_service import DeviceService
from app.services.telemetry_service import TelemetryService


class TestMQTTIngestionPipeline:
    """Test full telemetry and alert ingestion pipeline with database service interactions."""

    def test_telemetry_service_ingest_logic(self):
        """Test TelemetryService.ingest_telemetry creates record and updates device status."""
        mock_db = MagicMock()
        mock_device = Device(
            id=uuid.uuid4(),
            device_id="CONSUMER-H1",
            device_type="consumer",
            name="Consumer Node",
            api_key="test_key",
            status="offline",
        )

        with patch.object(DeviceService, "ensure_device_exists", return_value=mock_device):
            data = TelemetryCreate(
                device_id="CONSUMER-H1",
                voltage=230.4,
                current=2.15,
                power=495.36,
                energy=1024.5,
                power_factor=0.98,
                frequency=50.01,
            )

            res = TelemetryService.ingest_telemetry(mock_db, data, raw_payload={"raw": 1})

            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once()

            assert mock_device.status == "online"
            assert mock_device.last_seen_at is not None

    def test_full_pipeline_via_route_and_process(self):
        """Verify routing a consumer MQTT message leads to successful database ingestion."""
        mock_db = MagicMock()
        mock_device = Device(
            id=uuid.uuid4(),
            device_id="CONSUMER-H2",
            device_type="consumer",
            name="Consumer Node H2",
            api_key="test_key",
            status="offline",
        )

        with patch.object(DeviceService, "get_by_device_id", return_value=mock_device):
            topic = "kavachgrid/meter/h2"
            payload_bytes = json.dumps({
                "voltage": 231.2,
                "current": 3.4,
                "power": 786.08,
                "energy": 2500.0,
                "power_factor": 0.99,
                "frequency": 49.98,
            }).encode("utf-8")

            result = route_and_process_message(topic, payload_bytes, db=mock_db)

            assert result["status"] == "success"
            assert result["type"] == "consumer_telemetry"
            assert result["device_id"] == "CONSUMER-H2"
            assert mock_db.commit.called
