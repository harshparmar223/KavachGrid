"""
KAVACHGRID 3.0 — Robust MQTT Client for Windows & Linux
Uses standard paho-mqtt with background loop thread and asyncio WebSocket bridge.
"""

import asyncio
from datetime import datetime, timezone
import json
import logging
import threading
from typing import Any, Dict, Optional, Union

import paho.mqtt.client as paho_mqtt
from fastapi import FastAPI

from app.config import settings
from app.mqtt.handlers import route_and_process_message

logger = logging.getLogger("kavachgrid.mqtt.client")


class KavachMQTTClient:
    """
    Manages MQTT connection and dispatches messages to database and WebSocket clients.
    Thread-safe and cross-platform compatible.
    """

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        subscribe_topic: str = "kavachgrid/#",
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        self.host = host or settings.MQTT_BROKER_HOST
        self.port = port or settings.MQTT_BROKER_PORT
        self.subscribe_topic = subscribe_topic
        self.username = username or settings.MQTT_USERNAME
        self.password = password or settings.MQTT_PASSWORD

        self._client: Optional[paho_mqtt.Client] = None
        self._connected = False
        self._loop: Optional[asyncio.AbstractEventLoop] = None

        self.messages_received = 0
        self.messages_processed_ok = 0
        self.messages_failed = 0
        self.messages_published = 0
        self.last_connected_at: Optional[datetime] = None
        self.last_message_at: Optional[datetime] = None
        self.last_error: Optional[str] = None

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def status_summary(self) -> Dict[str, Any]:
        return {
            "status": "running" if self._connected else "stopped",
            "connected": self._connected,
            "broker": f"{self.host}:{self.port}",
            "subscription": self.subscribe_topic,
            "messages_received": self.messages_received,
            "messages_processed_ok": self.messages_processed_ok,
            "messages_failed": self.messages_failed,
            "messages_published": self.messages_published,
            "last_connected_at": self.last_connected_at.isoformat() if self.last_connected_at else None,
            "last_message_at": self.last_message_at.isoformat() if self.last_message_at else None,
            "last_error": self.last_error,
        }

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            self._connected = True
            self.last_connected_at = datetime.now(timezone.utc)
            self.last_error = None
            logger.info(f"✅ Connected to MQTT Broker at {self.host}:{self.port}")
            client.subscribe(self.subscribe_topic)
            logger.info(f"🎯 Subscribed to '{self.subscribe_topic}'")
        else:
            self._connected = False
            self.last_error = f"Connection failed with code {rc}"
            logger.error(f"❌ MQTT Connection failed with code {rc}")

    def _on_disconnect(self, client, userdata, rc, properties=None):
        self._connected = False
        if rc != 0:
            logger.warning(f"⚠️ Unexpected MQTT disconnect (rc={rc}). Auto-reconnecting...")

    def _on_message(self, client, userdata, msg):
        self.messages_received += 1
        self.last_message_at = datetime.now(timezone.utc)
        topic_str = str(msg.topic)
        payload_raw = msg.payload

        logger.info(f"📥 MQTT Packet on {topic_str}: {payload_raw[:80]}")

        # 1. Process with business logic / DB
        try:
            result = route_and_process_message(topic_str, payload_raw)
            if result.get("status") in ("success", "unhandled"):
                self.messages_processed_ok += 1
            else:
                self.messages_failed += 1
        except Exception as e:
            self.messages_failed += 1
            logger.error(f"Error processing MQTT message: {e}")

        # 2. Push to WebSocket clients on FastAPI event loop
        if self._loop and self._loop.is_running():
            try:
                if isinstance(payload_raw, bytes):
                    p_data = json.loads(payload_raw.decode("utf-8"))
                elif isinstance(payload_raw, str):
                    p_data = json.loads(payload_raw)
                else:
                    p_data = payload_raw

                if isinstance(p_data, dict):
                    dev_id = str(p_data.get("device_id") or p_data.get("node_id") or ("FEEDER-01" if "feeder" in topic_str else "CONSUMER-H1")).strip().upper()
                    if dev_id in ("CONSUMER-01", "CONSUMER_01", "METER-01", "METER_101", "HOUSE1", "H1", "HOUSE-1"):
                        dev_id = "CONSUMER-H1"
                    elif dev_id in ("CONSUMER-02", "CONSUMER_02", "METER-02", "METER_102", "HOUSE2", "H2", "HOUSE-2"):
                        dev_id = "CONSUMER-H2"
                    elif dev_id in ("FEEDER-1", "FEEDER_01", "FEEDER"):
                        dev_id = "FEEDER-01"
                    
                    if "feeder" in topic_str or "meter" in topic_str or "consumer" in topic_str or "localization" in topic_str:
                        v = float(p_data.get("voltage") or p_data.get("v") or 230.0)
                        c = float(p_data.get("current") or p_data.get("i") or 0.0)
                        p = p_data.get("power") or p_data.get("p") or p_data.get("w")
                        if p is None:
                            p = v * c
                        else:
                            p = float(p)

                        telemetry_ws = {
                            "id": f"{dev_id}-{p_data.get('seq', datetime.now().timestamp())}",
                            "device_id": dev_id,
                            "voltage": v,
                            "current": c,
                            "power": p,
                            "frequency": float(p_data.get("frequency") or p_data.get("freq") or 50.0),
                            "power_factor": float(p_data.get("power_factor") or p_data.get("pf") or 0.98),
                            "trust_score": float(p_data.get("trust_score", 99.0)),
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                        from app.api.websocket import broadcast_update
                        asyncio.run_coroutine_threadsafe(
                            broadcast_update("telemetry_update", telemetry_ws),
                            self._loop
                        )
                    elif "alert" in topic_str:
                        from app.api.websocket import broadcast_update
                        asyncio.run_coroutine_threadsafe(
                            broadcast_update("alert_created", p_data),
                            self._loop
                        )
            except Exception as ws_err:
                logger.debug(f"WS push error: {ws_err}")

    async def start(self) -> None:
        """Start the background MQTT client loop."""
        try:
            self._loop = asyncio.get_running_loop()
        except RuntimeError:
            self._loop = None

        try:
            self._client = paho_mqtt.Client(paho_mqtt.CallbackAPIVersion.VERSION2, f"kavach-backend-{id(self)}")
        except (AttributeError, TypeError):
            self._client = paho_mqtt.Client(f"kavach-backend-{id(self)}")

        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message

        try:
            self._client.connect(self.host, self.port, 60)
            self._client.loop_start()
            logger.info(f"📡 MQTT client loop started for {self.host}:{self.port}")
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"❌ Failed to connect to MQTT Broker: {e}")

    async def stop(self) -> None:
        """Gracefully stop MQTT client."""
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()
            self._client = None
            self._connected = False
            logger.info("🛑 MQTT client stopped.")

    async def publish(
        self,
        topic: str,
        payload: Union[str, bytes, Dict[str, Any]],
        qos: int = 0,
        retain: bool = False,
    ) -> bool:
        if isinstance(payload, dict):
            payload_str = json.dumps(payload)
        elif isinstance(payload, bytes):
            payload_str = payload.decode("utf-8")
        else:
            payload_str = str(payload)

        if not self._client:
            return False

        try:
            self._client.publish(topic, payload_str, qos=qos, retain=retain)
            self.messages_published += 1
            return True
        except Exception as e:
            self.last_error = str(e)
            return False


mqtt_client = KavachMQTTClient()


async def start_mqtt_client(app: Optional[FastAPI] = None) -> KavachMQTTClient:
    await mqtt_client.start()
    return mqtt_client


async def stop_mqtt_client(app: Optional[FastAPI] = None) -> None:
    await mqtt_client.stop()
