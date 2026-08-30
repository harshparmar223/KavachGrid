"""
KAVACHGRID 3.0 — Scenario Engine
Phase 15: Demo scenario orchestrator

Orchestrates the 6 SIH demo scenarios by coordinating the VirtualFeeder
and VirtualConsumer nodes. Each scenario modifies consumer modes and
feeder parameters to demonstrate a specific detection capability.

Scenarios:
    1. Normal Operation    — All nodes healthy, grid balanced
    2. Electricity Theft   — H2 bypasses meter, feeder detects deficit
    3. Meter Failure       — H3 sensor freezes, health score drops
    4. Communication Drop  — H4 goes offline, comm reliability flags
    5. Power Spike         — H1 draws 3× sanctioned load
    6. Full Localization   — Theft + localization narrowing in ZONE-A

Usage:
    engine = ScenarioEngine(feeder, consumers, mqtt_client)
    await engine.run_scenario("theft", duration=60)
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from simulator.virtual_feeder import VirtualFeeder
from simulator.virtual_consumer import VirtualConsumer

logger = logging.getLogger("kavachgrid.simulator.scenario")


# ── Scenario Definitions ────────────────────────────────────────

SCENARIOS = {
    "normal": {
        "name": "Normal Operation",
        "description": "All nodes report accurately. Grid is balanced. Risk scores stay low.",
        "number": 1,
        "consumer_modes": {
            "CONSUMER-H1": {"mode": "normal"},
            "CONSUMER-H2": {"mode": "normal"},
            "CONSUMER-H3": {"mode": "normal"},
            "CONSUMER-H4": {"mode": "normal"},
        },
        "theft_tapping_w": 0.0,
    },
    "theft": {
        "name": "Electricity Theft (Meter Bypass)",
        "description": (
            "Consumer H2 bypasses their meter using a neutral tap. "
            "The meter under-reports by ~55%. The feeder still sees the full load, "
            "creating a 12+ kW energy deficit. AI anomaly score spikes. "
            "Risk engine ranks H2 as Suspect #1."
        ),
        "number": 2,
        "consumer_modes": {
            "CONSUMER-H1": {"mode": "normal"},
            "CONSUMER-H2": {"mode": "theft_bypass", "bypass_pct": 0.55},
            "CONSUMER-H3": {"mode": "normal"},
            "CONSUMER-H4": {"mode": "normal"},
        },
        "theft_tapping_w": 0.0,  # Feeder auto-calculates from actual vs reported
    },
    "meter_failure": {
        "name": "Meter Sensor Failure",
        "description": (
            "Consumer H3's sensor freezes (corrosion/hardware fault). "
            "The meter repeatedly reports identical readings. "
            "Meter Health Engine detects stuck readings and drops health to ~40/100. "
            "This is flagged as MAINTENANCE, NOT as theft (zero false accusation)."
        ),
        "number": 3,
        "consumer_modes": {
            "CONSUMER-H1": {"mode": "normal"},
            "CONSUMER-H2": {"mode": "normal"},
            "CONSUMER-H3": {"mode": "stuck_sensor"},
            "CONSUMER-H4": {"mode": "normal"},
        },
        "theft_tapping_w": 0.0,
    },
    "comm_drop": {
        "name": "Communication Failure",
        "description": (
            "Consumer H4 loses network connectivity (cellular dropout). "
            "The node stops transmitting entirely. "
            "Communication Reliability drops. Device status changes to OFFLINE."
        ),
        "number": 4,
        "consumer_modes": {
            "CONSUMER-H1": {"mode": "normal"},
            "CONSUMER-H2": {"mode": "normal"},
            "CONSUMER-H3": {"mode": "normal"},
            "CONSUMER-H4": {"mode": "offline"},
        },
        "theft_tapping_w": 0.0,
    },
    "power_spike": {
        "name": "Abnormal Consumption Spike",
        "description": (
            "Consumer H1 draws 2.5× their normal sanctioned load "
            "(e.g., unauthorized welding equipment or grow-lights). "
            "AI Anomaly Engine flags the unusual pattern. "
            "Reported honestly, so Energy Balance stays near zero."
        ),
        "number": 5,
        "consumer_modes": {
            "CONSUMER-H1": {"mode": "power_spike", "spike_multiplier": 2.5},
            "CONSUMER-H2": {"mode": "normal"},
            "CONSUMER-H3": {"mode": "normal"},
            "CONSUMER-H4": {"mode": "normal"},
        },
        "theft_tapping_w": 0.0,
    },
    "localization": {
        "name": "Full Localization Workflow",
        "description": (
            "Combines theft (H2 bypass) with progressive localization. "
            "The Localization Engine narrows suspects within ZONE-A, "
            "ranks candidates by confidence score, and recommends "
            "'Immediate Field Inspection' for H2."
        ),
        "number": 6,
        "consumer_modes": {
            "CONSUMER-H1": {"mode": "normal"},
            "CONSUMER-H2": {"mode": "theft_bypass", "bypass_pct": 0.60},
            "CONSUMER-H3": {"mode": "normal"},
            "CONSUMER-H4": {"mode": "normal"},
        },
        "theft_tapping_w": 0.0,
    },
}


class ScenarioEngine:
    """
    Orchestrates SIH demo scenarios by configuring consumer modes
    and coordinating the feeder-consumer publish loop.
    """

    DEFAULT_PUBLISH_INTERVAL = 5.0  # seconds between telemetry publishes

    def __init__(
        self,
        feeder: VirtualFeeder,
        consumers: Dict[str, VirtualConsumer],
        mqtt_client=None,
    ):
        self.feeder = feeder
        self.consumers = consumers
        self.mqtt_client = mqtt_client

        self._active_scenario: Optional[str] = None
        self._running: bool = False
        self._task: Optional[asyncio.Task] = None
        self._cycle_count: int = 0

        logger.info(
            f"🎮 ScenarioEngine initialized | "
            f"Feeder={feeder.device_id} | "
            f"Consumers={list(consumers.keys())}"
        )

    # ── Scenario management ─────────────────────────────────────

    @staticmethod
    def list_scenarios() -> List[Dict[str, Any]]:
        """Return list of available demo scenarios."""
        return [
            {
                "key": key,
                "number": s["number"],
                "name": s["name"],
                "description": s["description"],
            }
            for key, s in SCENARIOS.items()
        ]

    def apply_scenario(self, scenario_key: str) -> None:
        """
        Apply a scenario configuration (set consumer modes and feeder parameters).
        Does NOT start the publish loop — call run_scenario() for that.
        """
        if scenario_key not in SCENARIOS:
            raise ValueError(
                f"Unknown scenario '{scenario_key}'. "
                f"Available: {list(SCENARIOS.keys())}"
            )

        scenario = SCENARIOS[scenario_key]
        self._active_scenario = scenario_key
        self._cycle_count = 0

        logger.info(f"\n{'='*60}")
        logger.info(f"🎬 SCENARIO {scenario['number']}: {scenario['name']}")
        logger.info(f"   {scenario['description']}")
        logger.info(f"{'='*60}\n")

        # Configure each consumer
        for device_id, mode_config in scenario["consumer_modes"].items():
            if device_id in self.consumers:
                self.consumers[device_id].set_mode(**mode_config)
            else:
                logger.warning(f"⚠️ Consumer '{device_id}' not found in engine")

        # Configure feeder theft tapping
        self.feeder.set_theft_tapping(scenario["theft_tapping_w"])

    async def run_scenario(
        self,
        scenario_key: str,
        duration: float = 120.0,
        interval: float = 5.0,
    ) -> Dict[str, Any]:
        """
        Apply a scenario and run the publish loop for the given duration.

        Args:
            scenario_key: One of 'normal', 'theft', 'meter_failure', etc.
            duration: How long to run in seconds (default 120s = 2 minutes)
            interval: Seconds between each publish cycle

        Returns:
            Summary dictionary with cycle count and final states
        """
        self.apply_scenario(scenario_key)
        self._running = True

        start_time = time.time()
        end_time = start_time + duration

        logger.info(
            f"▶️  Starting scenario '{scenario_key}' for {duration:.0f}s "
            f"(interval={interval:.1f}s)"
        )

        try:
            while self._running and time.time() < end_time:
                await self._publish_cycle()
                self._cycle_count += 1

                elapsed = time.time() - start_time
                remaining = duration - elapsed
                if self._cycle_count % 5 == 0:
                    logger.info(
                        f"📊 Cycle {self._cycle_count} | "
                        f"Elapsed: {elapsed:.0f}s | Remaining: {remaining:.0f}s"
                    )

                await asyncio.sleep(interval)

        except asyncio.CancelledError:
            logger.info(f"⏹️  Scenario '{scenario_key}' cancelled")
        except KeyboardInterrupt:
            logger.info(f"⏹️  Scenario '{scenario_key}' interrupted by user")
        finally:
            self._running = False

        summary = self._generate_summary(scenario_key, start_time)
        logger.info(f"\n✅ Scenario '{scenario_key}' completed: {self._cycle_count} cycles")
        return summary

    async def run_interactive(self, interval: float = 5.0) -> None:
        """
        Run in interactive mode — publish continuously until stopped.
        Scenario can be switched on the fly via switch_scenario().
        """
        self._running = True
        logger.info(f"▶️  Interactive mode started (interval={interval:.1f}s)")

        try:
            while self._running:
                await self._publish_cycle()
                self._cycle_count += 1
                await asyncio.sleep(interval)
        except asyncio.CancelledError:
            pass
        finally:
            self._running = False
            logger.info("⏹️  Interactive mode stopped")

    def switch_scenario(self, scenario_key: str) -> None:
        """Switch scenario on the fly during interactive mode."""
        self.apply_scenario(scenario_key)
        logger.info(f"🔄 Live-switched to scenario: {scenario_key}")

    def stop(self) -> None:
        """Stop the running scenario."""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
        logger.info("⏹️  Scenario engine stopped")

    # ── Internal publish cycle ──────────────────────────────────

    async def _publish_cycle(self) -> None:
        """
        Execute one complete telemetry cycle:
        1. Each consumer generates and publishes their reading
        2. Consumer actual loads are aggregated for the feeder
        3. Feeder generates and publishes the total reading
        """
        consumer_actual_loads: Dict[str, float] = {}

        # Step 1: Publish all consumer readings
        for device_id, consumer in self.consumers.items():
            reading = await consumer.publish_reading()
            # Track actual power for feeder aggregation
            # (actual_power is what the feeder physically sees, regardless of mode)
            consumer_actual_loads[device_id] = consumer.actual_power

        # Step 2: Update feeder with true consumer loads and publish
        self.feeder.update_consumer_loads(consumer_actual_loads)
        await self.feeder.publish_reading()

    # ── Summary generation ──────────────────────────────────────

    def _generate_summary(
        self, scenario_key: str, start_time: float
    ) -> Dict[str, Any]:
        """Generate end-of-scenario summary."""
        scenario = SCENARIOS[scenario_key]
        duration = time.time() - start_time

        return {
            "scenario": scenario_key,
            "scenario_name": scenario["name"],
            "duration_seconds": round(duration, 1),
            "total_cycles": self._cycle_count,
            "feeder_status": self.feeder.status,
            "consumer_statuses": {
                did: c.status for did, c in self.consumers.items()
            },
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }

    @property
    def status(self) -> Dict[str, Any]:
        """Return current engine state."""
        return {
            "active_scenario": self._active_scenario,
            "running": self._running,
            "cycle_count": self._cycle_count,
            "feeder": self.feeder.device_id,
            "consumers": list(self.consumers.keys()),
        }
