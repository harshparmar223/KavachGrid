"""
KAVACHGRID 3.0 — Unit Tests for Async MQTT Client
Phase 3 / Phase 14: Testing client lifecycle, publish/subscribe worker management, and health metrics.
"""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.mqtt.client import (
    KavachMQTTClient,
    start_mqtt_client,
    stop_mqtt_client,
)


class TestKavachMQTTClient:
    """Test suite for KavachMQTTClient connection, worker lifecycle, and status reporting."""

    def test_client_init_defaults(self):
        client = KavachMQTTClient(
            host="localhost",
            port=1883,
            username="test_user",
            password="test_password",
        )
        assert client.host == "localhost"
        assert client.port == 1883
        assert client.username == "test_user"
        assert client.password == "test_password"
        assert client.is_connected is False
        assert client.subscribe_topic == "kavachgrid/#"
        assert client.messages_received == 0

    def test_client_status_summary(self):
        client = KavachMQTTClient(host="127.0.0.1", port=1883)
        summary = client.status_summary
        assert summary["connected"] is False
        assert summary["status"] == "stopped"
        assert summary["broker"] == "127.0.0.1:1883"
        assert summary["subscription"] == "kavachgrid/#"
        assert summary["messages_received"] == 0

    @pytest.mark.asyncio
    async def test_client_start_and_stop(self):
        client = KavachMQTTClient()
        with patch.object(client, "_subscriber_loop", new_callable=AsyncMock) as mock_loop:
            mock_loop.side_effect = asyncio.CancelledError

            await client.start()
            assert client._running is True
            assert client._task is not None

            await client.stop()
            assert client._running is False
            assert client.is_connected is False

    @pytest.mark.asyncio
    async def test_publish_dict_payload(self):
        client = KavachMQTTClient()
        mock_aiomqtt_instance = AsyncMock()

        with patch("aiomqtt.Client") as mock_client_cls:
            mock_client_cls.return_value.__aenter__.return_value = mock_aiomqtt_instance

            payload = {"device_id": "FEEDER-01", "voltage": 230.0}
            success = await client.publish("kavachgrid/feeder", payload)

            assert success is True
            assert client.messages_published == 1
            mock_aiomqtt_instance.publish.assert_called_once()
            call_args = mock_aiomqtt_instance.publish.call_args
            assert call_args[0][0] == "kavachgrid/feeder"
            assert "230.0" in call_args[1]["payload"]

    @pytest.mark.asyncio
    async def test_start_stop_global_hooks(self):
        with patch("app.mqtt.client.mqtt_client.start", new_callable=AsyncMock) as mock_start:
            with patch("app.mqtt.client.mqtt_client.stop", new_callable=AsyncMock) as mock_stop:
                await start_mqtt_client()
                mock_start.assert_called_once()

                await stop_mqtt_client()
                mock_stop.assert_called_once()
