"""
KAVACHGRID 3.0 — Virtual Consumer Node
Phase 15: Software-based consumer smart meter simulation

Generates realistic consumer telemetry with configurable behavioral modes:
    - normal:       Accurate power reporting with daily load profile
    - theft_bypass: Under-reports consumption by 40-70% (meter bypass)
    - stuck_sensor: Repeats identical frozen readings (sensor failure)
    - offline:      Stops transmitting entirely (communication drop)
    - power_spike:  Reports 2-3× sanctioned load (overload scenario)

Usage:
    consumer = VirtualConsumer("CONSUMER-H1", mqtt_client=client)
    consumer.set_mode("theft_bypass", bypass_pct=0.55)
    await consumer.publish_reading()
"""

import asyncio
import json
import logging
import math
import random
import time
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("kavachgrid.simulator.consumer")


class ConsumerMode(str, Enum):
    """Behavioral modes for consumer simulation."""
    NORMAL = "normal"
    THEFT_BYPASS = "theft_bypass"
    STUCK_SENSOR = "stuck_sensor"
    OFFLINE = "offline"
    POWER_SPIKE = "power_spike"


# ── Realistic Indian household load profiles ────────────────────
# Each tuple: (appliance_name, wattage, duty_cycle_pct)
# duty_cycle represents what fraction of the interval the appliance is ON

HOUSEHOLD_PROFILES: Dict[str, List[Tuple[str, float, float]]] = {
    "CONSUMER-H1": [
        ("LED Lights", 40.0, 0.8),
        ("Ceiling Fan x2", 140.0, 0.9),
        ("Refrigerator", 150.0, 0.35),
        ("TV 32-inch", 60.0, 0.5),
        ("Phone Charger x2", 20.0, 0.3),
        ("Water Pump", 750.0, 0.05),
    ],
    "CONSUMER-H2": [
        ("LED Lights", 60.0, 0.85),
        ("Ceiling Fan x3", 210.0, 0.85),
        ("Refrigerator", 180.0, 0.40),
        ("TV 43-inch", 80.0, 0.45),
        ("Washing Machine", 500.0, 0.08),
        ("Microwave", 1000.0, 0.03),
        ("AC 1.5 Ton", 1500.0, 0.30),
    ],
    "CONSUMER-H3": [
        ("LED Lights", 30.0, 0.7),
        ("Ceiling Fan x1", 70.0, 0.9),
        ("Refrigerator", 120.0, 0.30),
        ("TV 24-inch", 40.0, 0.6),
        ("Iron", 1000.0, 0.04),
    ],
    "CONSUMER-H4": [
        ("LED Lights", 50.0, 0.75),
        ("Ceiling Fan x2", 140.0, 0.85),
        ("Refrigerator", 160.0, 0.35),
        ("TV 32-inch", 55.0, 0.55),
        ("Laptop", 65.0, 0.4),
        ("AC 1 Ton", 1200.0, 0.25),
    ],
}

# Fallback profile for any unknown device
DEFAULT_PROFILE: List[Tuple[str, float, float]] = [
    ("LED Lights", 40.0, 0.7),
    ("Ceiling Fan", 70.0, 0.8),
    ("Refrigerator", 150.0, 0.35),
    ("TV", 60.0, 0.5),
]


class VirtualConsumer:
    """
    Simulates a household smart meter with realistic load patterns.

    Each consumer has a fixed appliance profile that generates a base load.
    The mode determines how that load is reported (or not reported) to the
    backend, enabling simulation of theft, failure, and overload scenarios.
    """

    NOMINAL_VOLTAGE = 230.0
    VOLTAGE_JITTER = 3.0        # ±3V
    FREQUENCY_JITTER = 0.08     # ±0.08 Hz
    PF_RANGE = (0.85, 0.98)

    def __init__(
        self,
        device_id: str = "CONSUMER-H1",
        mqtt_client=None,
        mqtt_topic: Optional[str] = None,
        zone_id: str = "ZONE-A",
    ):
        self.device_id = device_id
        self.mqtt_client = mqtt_client
        self.mqtt_topic = mqtt_topic or f"kavachgrid/meter/{device_id.lower().replace('consumer-', '')}"
        self.zone_id = zone_id

        # ── Load profile ────────────────────────────────────────
        self._appliances = HOUSEHOLD_PROFILES.get(device_id, DEFAULT_PROFILE)

        # ── Behavioral mode ─────────────────────────────────────
        self._mode: ConsumerMode = ConsumerMode.NORMAL
        self._bypass_pct: float = 0.55      # % of power hidden during theft
        self._spike_multiplier: float = 2.5  # multiplier for power spike mode

        # ── Internal state ──────────────────────────────────────
        self._cumulative_energy_wh: float = random.uniform(500.0, 5000.0)
        self._last_publish_time: Optional[float] = None
        self._stuck_reading: Optional[Dict[str, Any]] = None
        self._reading_count: int = 0
        self._actual_power_w: float = 0.0   # TRUE power (what feeder sees)

        logger.info(
            f"🏠 VirtualConsumer '{device_id}' initialized | "
            f"Zone={zone_id} | Appliances={len(self._appliances)} | "
            f"Topic={self.mqtt_topic}"
        )

    # ── Mode management ─────────────────────────────────────────

    def set_mode(
        self,
        mode: str,
        bypass_pct: float = 0.55,
        spike_multiplier: float = 2.5,
    ) -> None:
        """
        Set the consumer's behavioral mode.

        Args:
            mode: One of 'normal', 'theft_bypass', 'stuck_sensor', 'offline', 'power_spike'
            bypass_pct: Fraction of power hidden during theft (0.0–1.0)
            spike_multiplier: Power multiplier during spike scenario
        """
        self._mode = ConsumerMode(mode)
        self._bypass_pct = max(0.0, min(1.0, bypass_pct))
        self._spike_multiplier = max(1.0, spike_multiplier)

        # Reset stuck reading cache when changing modes
        if self._mode != ConsumerMode.STUCK_SENSOR:
            self._stuck_reading = None

        logger.info(
            f"🔧 {self.device_id} mode → {self._mode.value} | "
            f"bypass={self._bypass_pct:.0%} | spike_mult={self._spike_multiplier}x"
        )

    @property
    def mode(self) -> str:
        return self._mode.value

    @property
    def actual_power(self) -> float:
        """Return the TRUE power draw (what the feeder physically sees)."""
        return self._actual_power_w

    # ── Load computation ────────────────────────────────────────

    def _compute_actual_load(self) -> float:
        """
        Calculate the true instantaneous load from the appliance profile.

        Each appliance contributes: wattage × duty_cycle × random_factor
        This represents a realistic household at any given moment.
        """
        total = 0.0
        for name, wattage, duty in self._appliances:
            # Probabilistically determine if appliance is ON right now
            if random.random() < duty:
                # Apply ±10% measurement noise
                noise = random.uniform(0.90, 1.10)
                total += wattage * noise
        return max(0.0, total)

    def _apply_mode_to_reading(
        self, actual_power: float, voltage: float, pf: float
    ) -> Optional[Dict[str, Any]]:
        """
        Apply the current behavioral mode to transform actual power
        into what the meter REPORTS (which may differ during theft).

        Returns None if the consumer is offline (no transmission).
        """
        now = time.time()

        if self._mode == ConsumerMode.OFFLINE:
            return None

        if self._mode == ConsumerMode.STUCK_SENSOR:
            if self._stuck_reading is None:
                # Freeze the current reading
                self._stuck_reading = self._build_payload(
                    actual_power, voltage, pf, now
                )
            # Return the same frozen values every time (but update timestamp)
            frozen = self._stuck_reading.copy()
            frozen["timestamp"] = datetime.now(timezone.utc).isoformat()
            return frozen

        if self._mode == ConsumerMode.THEFT_BYPASS:
            # The meter only reports (1 - bypass_pct) of the actual power
            reported_power = actual_power * (1.0 - self._bypass_pct)
            return self._build_payload(reported_power, voltage, pf, now)

        if self._mode == ConsumerMode.POWER_SPIKE:
            spiked_power = actual_power * self._spike_multiplier
            return self._build_payload(spiked_power, voltage, pf, now)

        # NORMAL mode — report accurately
        return self._build_payload(actual_power, voltage, pf, now)

    def _build_payload(
        self, power: float, voltage: float, pf: float, now: float
    ) -> Dict[str, Any]:
        """Build a telemetry payload dictionary."""
        current = power / (voltage * pf) if (voltage * pf) > 0 else 0.0
        frequency = 50.0 + random.uniform(
            -self.FREQUENCY_JITTER, self.FREQUENCY_JITTER
        )

        # Update cumulative energy
        if self._last_publish_time is not None:
            dt_hours = (now - self._last_publish_time) / 3600.0
            self._cumulative_energy_wh += power * dt_hours
        self._last_publish_time = now

        return {
            "device_id": self.device_id,
            "voltage": round(voltage, 2),
            "current": round(current, 3),
            "power": round(power, 2),
            "energy": round(self._cumulative_energy_wh, 2),
            "power_factor": round(pf, 3),
            "frequency": round(frequency, 2),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # ── Telemetry generation & publishing ───────────────────────

    def generate_reading(self) -> Optional[Dict[str, Any]]:
        """
        Generate a single consumer telemetry reading.

        Returns None if the consumer is in OFFLINE mode.
        The actual power is always tracked (for feeder aggregation)
        even if the meter under-reports it.
        """
        # Step 1: Compute the TRUE load
        actual_power = self._compute_actual_load()
        self._actual_power_w = actual_power

        # Step 2: Generate sensor values
        voltage = self.NOMINAL_VOLTAGE + random.uniform(
            -self.VOLTAGE_JITTER, self.VOLTAGE_JITTER
        )
        pf = random.uniform(*self.PF_RANGE)

        # Step 3: Apply behavioral mode (may alter reported values)
        reading = self._apply_mode_to_reading(actual_power, voltage, pf)
        if reading is not None:
            self._reading_count += 1

        return reading

    async def publish_reading(self) -> Optional[Dict[str, Any]]:
        """Generate and publish a consumer reading to MQTT."""
        reading = self.generate_reading()

        if reading is None:
            logger.info(f"📵 {self.device_id} is OFFLINE — no transmission")
            return None

        if self.mqtt_client:
            try:
                await self.mqtt_client.publish(
                    self.mqtt_topic,
                    json.dumps(reading),
                    qos=0,
                )
                mode_tag = f"[{self._mode.value.upper()}]" if self._mode != ConsumerMode.NORMAL else ""
                logger.info(
                    f"📤 {self.device_id} {mode_tag} published: "
                    f"V={reading['voltage']}V | I={reading['current']}A | "
                    f"P={reading['power']}W (actual={self._actual_power_w:.1f}W)"
                )
            except Exception as e:
                logger.error(f"❌ {self.device_id} publish failed: {e}")
        else:
            logger.debug(f"📋 {self.device_id} reading (no MQTT): {json.dumps(reading)}")

        return reading

    # ── Diagnostics ─────────────────────────────────────────────

    @property
    def status(self) -> Dict[str, Any]:
        """Return current consumer simulation state."""
        return {
            "device_id": self.device_id,
            "mode": self._mode.value,
            "actual_power_w": round(self._actual_power_w, 2),
            "bypass_pct": self._bypass_pct if self._mode == ConsumerMode.THEFT_BYPASS else None,
            "spike_multiplier": self._spike_multiplier if self._mode == ConsumerMode.POWER_SPIKE else None,
            "cumulative_energy_wh": round(self._cumulative_energy_wh, 2),
            "reading_count": self._reading_count,
            "zone_id": self.zone_id,
            "is_transmitting": self._mode != ConsumerMode.OFFLINE,
        }
