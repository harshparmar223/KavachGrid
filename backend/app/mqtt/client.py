"""
KAVACHGRID 3.0 — Async MQTT Client & Background Subscriber
Phase 3: Complete Implementation

Provides:
    - Asynchronous MQTT subscription using aiomqtt
    - Background worker loop attached to FastAPI lifecycle
    - Non-blocking startup with auto-reconnection & exponential backoff
    - Async publish capability for backend alerts/commands
    - Live client health & telemetry ingestion metrics
"""

import asyncio
from datetime import datetime, timezone
import json
import logging
from typing import Any, Dict, Optional, Union

import aiomqtt
from fastapi import FastAPI

from app.config import settings
from app.mqtt.handlers import route_and_process_message

logger = logging.getLogger("kavachgrid.mqtt.client")


class KavachMQTTClient:
    """
    Manages the asynchronous MQTT connection, subscription worker,
    and publishing interface for KAVACHGRID backend.
    """

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        keepalive: Optional[int] = None,
        subscribe_topic: str = "kavachgrid/#",
    ):
        self.host = host or settings.MQTT_BROKER_HOST
        self.port = port or settings.MQTT_BROKER_PORT
        self.username = username or settings.MQTT_USERNAME
        self.password = password or settings.MQTT_PASSWORD
        self.keepalive = keepalive or settings.MQTT_KEEPALIVE
        self.subscribe_topic = subscribe_topic

        self._running = False
        self._connected = False
        self._task: Optional[asyncio.Task] = None
        self._client: Optional[aiomqtt.Client] = None

        # Metrics
        self.messages_received: int = 0
        self.messages_processed_ok: int = 0
        self.messages_failed: int = 0
        self.messages_published: int = 0
        self.last_connected_at: Optional[datetime] = None
        self.last_message_at: Optional[datetime] = None
        self.last_error: Optional[str] = None

    @property
    def is_connected(self) -> bool:
        """Return current broker connection status."""
        return self._connected

    @property
    def status_summary(self) -> Dict[str, Any]:
        """Return dictionary representation of MQTT client status."""
        return {
            "status": "connected" if self._connected else ("starting" if self._running else "stopped"),
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

    async def start(self) -> None:
        """Start the background subscriber worker."""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._subscriber_loop(), name="kavachgrid-mqtt-worker")
        logger.info(f"📡 MQTT client worker initiated for {self.host}:{self.port}")

    async def stop(self) -> None:
        """Gracefully stop subscriber worker and disconnect."""
        logger.info("🛑 Stopping MQTT client worker...")
        self._running = False
        self._connected = False

        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await asyncio.wait_for(self._task, timeout=3.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass
            self._task = None

        logger.info("✅ MQTT client worker stopped.")

    async def publish(
        self,
        topic: str,
        payload: Union[str, bytes, Dict[str, Any]],
        qos: int = 0,
        retain: bool = False,
    ) -> bool:
        """
        Publish a message to an MQTT topic.
        """
        if isinstance(payload, dict):
            payload_str = json.dumps(payload)
        elif isinstance(payload, bytes):
            payload_str = payload.decode("utf-8")
        else:
            payload_str = str(payload)

        try:
            client_kwargs = {
                "hostname": self.host,
                "port": self.port,
                "timeout": 5.0,
            }
            if self.username and self.password:
                client_kwargs["username"] = self.username
                client_kwargs["password"] = self.password

            async with aiomqtt.Client(**client_kwargs) as client:
                await client.publish(topic, payload=payload_str, qos=qos, retain=retain)
                self.messages_published += 1
                logger.info(f"📤 Published to '{topic}': {payload_str[:80]}...")
                return True
        except Exception as e:
            self.last_error = f"Publish error: {e}"
            logger.error(f"❌ Failed to publish to '{topic}': {e}")
            return False

    async def _subscriber_loop(self) -> None:
        """
        Continuous subscription loop with exponential backoff on connection errors.
        """
        backoff = 1.0
        max_backoff = 30.0

        while self._running:
            try:
                client_kwargs = {
                    "hostname": self.host,
                    "port": self.port,
                    "keepalive": self.keepalive,
                    "identifier": f"kavach-backend-{id(self)}",
                    "timeout": 10.0,
                }
                if self.username and self.password:
                    client_kwargs["username"] = self.username
                    client_kwargs["password"] = self.password

                logger.info(f"🔄 Connecting to MQTT Broker at {self.host}:{self.port}...")
                async with aiomqtt.Client(**client_kwargs) as client:
                    self._client = client
                    self._connected = True
                    self.last_connected_at = datetime.now(timezone.utc)
                    self.last_error = None
                    backoff = 1.0
                    logger.info(f"✅ Connected to MQTT Broker. Subscribing to '{self.subscribe_topic}'...")

                    await client.subscribe(self.subscribe_topic)
                    logger.info(f"🎯 Subscribed to '{self.subscribe_topic}' successfully.")

                    async for message in client.messages:
                        if not self._running:
                            break

                        self.messages_received += 1
                        self.last_message_at = datetime.now(timezone.utc)
                        topic_str = str(message.topic)
                        payload_raw = message.payload

                        try:
                            result = route_and_process_message(topic_str, payload_raw)
                            if result.get("status") in ("success", "unhandled"):
                                self.messages_processed_ok += 1
                            else:
                                self.messages_failed += 1
                        except Exception as proc_err:
                            self.messages_failed += 1
                            logger.error(f"Error dispatching MQTT message: {proc_err}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                self._connected = False
                self.last_error = str(e)
                logger.warning(
                    f"⚠️ MQTT Broker unreachable ({e}). Retrying in {backoff:.1f}s..."
                )
                try:
                    await asyncio.sleep(backoff)
                except asyncio.CancelledError:
                    break
                backoff = min(backoff * 1.5, max_backoff)
            finally:
                self._connected = False
                self._client = None


mqtt_client = KavachMQTTClient()


async def start_mqtt_client(app: Optional[FastAPI] = None) -> KavachMQTTClient:
    """Start the global MQTT client subscriber."""
    await mqtt_client.start()
    return mqtt_client


async def stop_mqtt_client(app: Optional[FastAPI] = None) -> None:
    """Stop the global MQTT client subscriber."""
    await mqtt_client.stop()
