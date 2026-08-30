"""
KAVACHGRID 3.0 — Virtual Feeder Node
Phase 15: Software-based feeder simulation

Generates realistic feeder telemetry and publishes via MQTT.
The feeder sums all consumer loads, adds technical losses and any
active theft tapping, and produces the total substation reading.

Usage:
    feeder = VirtualFeeder(mqtt_client)
    feeder.update_consumer_loads({"CONSUMER-H1": 450.0, ...})
    await feeder.publish_reading()
"""

import asyncio
import json
import logging
import math
import random
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger("kavachgrid.simulator.feeder")


class VirtualFeeder:
    """
    Simulates a 100 kVA Distribution Transformer (DT) feeder node.

    The feeder's reported power = sum of all consumer loads
                                + technical losses (configurable %)
                                + any active theft tapping (invisible to consumer meters)

    This mirrors exactly how a real DT feeder would see the aggregated
    street-level load, creating the Energy Balance deficit that our
    backend engines detect.
    """

    # ── Physical constants ──────────────────────────────────────
    RATED_CAPACITY_KVA = 100.0          # 100 kVA transformer
    NOMINAL_VOLTAGE = 230.0             # Indian standard 230V
    NOMINAL_FREQUENCY = 50.0            # 50 Hz
    BASE_POWER_FACTOR = 0.95            # Residential PF

    # ── Simulation defaults ─────────────────────────────────────
    TECHNICAL_LOSS_PCT = 0.05           # 5% line losses (I²R)
    VOLTAGE_JITTER = 2.0               # ±2V random fluctuation
    FREQUENCY_JITTER = 0.05            # ±0.05 Hz jitter
    PF_JITTER = 0.02                   # ±0.02 power factor jitter

    def __init__(
        self,
        mqtt_client=None,
        device_id: str = "FEEDER-01",
        mqtt_topic: str = "kavachgrid/feeder",
        technical_loss_pct: float = 0.05,
    ):
        self.mqtt_client = mqtt_client
        self.device_id = device_id
        self.mqtt_topic = mqtt_topic
        self.technical_loss_pct = technical_loss_pct

        # ── Internal state ──────────────────────────────────────
        self._consumer_loads: Dict[str, float] = {}     # device_id → actual watts
        self._theft_tapping_w: float = 0.0               # extra load from illegal tap
        self._cumulative_energy_wh: float = 0.0
        self._last_publish_time: Optional[float] = None
        self._reading_count: int = 0

        # ── Base load (transformer idle + street lighting) ──────
        self._base_load_w: float = random.uniform(80.0, 150.0)

        logger.info(
            f"🏭 VirtualFeeder '{device_id}' initialized | "
            f"Capacity={self.RATED_CAPACITY_KVA}kVA | "
            f"TechnicalLoss={technical_loss_pct*100:.1f}%"
        )

    # ── Consumer load management ────────────────────────────────

    def update_consumer_loads(self, loads: Dict[str, float]) -> None:
        """Update the current actual power draw from each consumer meter."""
        self._consumer_loads = loads.copy()

    def set_theft_tapping(self, watts: float) -> None:
        """
        Set additional load representing illegal tapping (bypasses meters).

        This power appears on the feeder but NOT on any consumer meter,
        creating the energy deficit that our Energy Balance Engine detects.
        """
        self._theft_tapping_w = max(0.0, watts)
        if watts > 0:
            logger.warning(f"⚡ Theft tapping set to {watts:.1f}W on {self.device_id}")

    # ── Telemetry generation ────────────────────────────────────

    def _compute_total_load(self) -> float:
        """
        Feeder Power = Σ(consumer loads) + theft tapping + base load

        Technical loss is applied ON TOP of this (the feeder meter sees
        all of this plus the I²R losses in the cables).
        """
        consumer_total = sum(self._consumer_loads.values())
        raw_load = consumer_total + self._theft_tapping_w + self._base_load_w
        total_with_losses = raw_load * (1.0 + self.technical_loss_pct)
        return total_with_losses

    def generate_reading(self) -> Dict[str, Any]:
        """
        Generate a single feeder telemetry reading with realistic noise.

        Returns a JSON-compatible dictionary matching the TelemetryCreate schema.
        """
        now = time.time()
        total_power = self._compute_total_load()

        # Apply realistic noise to simulate sensor measurement jitter
        voltage = self.NOMINAL_VOLTAGE + random.uniform(
            -self.VOLTAGE_JITTER, self.VOLTAGE_JITTER
        )
        frequency = self.NOMINAL_FREQUENCY + random.uniform(
            -self.FREQUENCY_JITTER, self.FREQUENCY_JITTER
        )
        power_factor = min(1.0, max(0.80, self.BASE_POWER_FACTOR + random.uniform(
            -self.PF_JITTER, self.PF_JITTER
        )))

        # Derive current from power: P = V × I × PF
        current = total_power / (voltage * power_factor) if voltage > 0 else 0.0

        # Add small measurement noise to power (±0.5%)
        power_noise = total_power * random.uniform(-0.005, 0.005)
        reported_power = max(0.0, total_power + power_noise)

        # Update cumulative energy (Wh)
        if self._last_publish_time is not None:
            dt_hours = (now - self._last_publish_time) / 3600.0
            self._cumulative_energy_wh += reported_power * dt_hours
        self._last_publish_time = now
        self._reading_count += 1

        reading = {
            "device_id": self.device_id,
            "voltage": round(voltage, 2),
            "current": round(current, 3),
            "power": round(reported_power, 2),
            "energy": round(self._cumulative_energy_wh, 2),
            "power_factor": round(power_factor, 3),
            "frequency": round(frequency, 2),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        return reading

    async def publish_reading(self) -> Dict[str, Any]:
        """Generate and publish a feeder reading to MQTT."""
        reading = self.generate_reading()

        if self.mqtt_client:
            try:
                await self.mqtt_client.publish(
                    self.mqtt_topic,
                    json.dumps(reading),
                    qos=0,
                )
                logger.info(
                    f"📤 Feeder published: V={reading['voltage']}V | "
                    f"I={reading['current']}A | P={reading['power']}W | "
                    f"E={reading['energy']}Wh"
                )
            except Exception as e:
                logger.error(f"❌ Feeder publish failed: {e}")
        else:
            logger.debug(f"📋 Feeder reading (no MQTT): {json.dumps(reading)}")

        return reading

    # ── Diagnostics ─────────────────────────────────────────────

    @property
    def status(self) -> Dict[str, Any]:
        """Return current feeder simulation state."""
        return {
            "device_id": self.device_id,
            "total_load_w": round(self._compute_total_load(), 2),
            "consumer_loads": {k: round(v, 2) for k, v in self._consumer_loads.items()},
            "theft_tapping_w": round(self._theft_tapping_w, 2),
            "base_load_w": round(self._base_load_w, 2),
            "technical_loss_pct": self.technical_loss_pct,
            "cumulative_energy_wh": round(self._cumulative_energy_wh, 2),
            "reading_count": self._reading_count,
        }
