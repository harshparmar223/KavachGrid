#!/usr/bin/env python3
"""
KAVACHGRID 3.0 — SIH Demo Scenario Runner
Phase 15: One-command demo for judges

A simplified entry point that runs scenarios sequentially for judges.
For full control, use simulate_telemetry.py instead.

Usage:
    python scripts/demo_scenarios.py              # Interactive menu
    python scripts/demo_scenarios.py 2             # Run scenario 2 (theft)
    python scripts/demo_scenarios.py 0             # Run ALL scenarios sequentially

Scenarios:
    1 - Normal operation
    2 - Electricity theft simulation
    3 - Meter failure
    4 - Communication failure
    5 - Abnormal consumption
    6 - Localization workflow
    0 - Run all scenarios sequentially
"""

import asyncio
import os
import sys

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from simulator.virtual_feeder import VirtualFeeder
from simulator.virtual_consumer import VirtualConsumer
from simulator.scenario_engine import ScenarioEngine, SCENARIOS


# Map scenario number → key
SCENARIO_NUMBER_MAP = {s["number"]: k for k, s in SCENARIOS.items()}
SCENARIO_ORDER = ["normal", "theft", "meter_failure", "comm_drop", "power_spike", "localization"]


async def run_demo(scenario_number: int, duration: float = 60.0) -> None:
    """Run a single scenario or all scenarios sequentially."""

    # Use dry-run client (console only) — no MQTT dependency
    class ConsoleClient:
        async def publish(self, topic, payload, qos=0):
            import json
            data = json.loads(payload)
            dev = data.get("device_id", "?")
            pwr = data.get("power", 0)
            print(f"  📋 [{topic}] {dev}: P={pwr:.1f}W V={data.get('voltage', 0)}V")

    client = ConsoleClient()

    feeder = VirtualFeeder(mqtt_client=client)
    consumers = {
        f"CONSUMER-H{i}": VirtualConsumer(f"CONSUMER-H{i}", mqtt_client=client)
        for i in range(1, 5)
    }
    engine = ScenarioEngine(feeder, consumers)

    if scenario_number == 0:
        # Run ALL scenarios sequentially
        print("\n🎬 Running ALL 6 scenarios sequentially...\n")
        for key in SCENARIO_ORDER:
            s = SCENARIOS[key]
            print(f"\n{'─'*50}")
            print(f"  ▶️  Scenario {s['number']}: {s['name']}")
            print(f"{'─'*50}")
            await engine.run_scenario(key, duration=duration, interval=5.0)
            print()
        print("\n✅ All scenarios completed!")
    else:
        key = SCENARIO_NUMBER_MAP.get(scenario_number)
        if not key:
            print(f"❌ Invalid scenario number: {scenario_number}")
            print(f"   Valid: 0 (all), 1-6")
            return
        await engine.run_scenario(key, duration=duration, interval=5.0)


def main():
    if len(sys.argv) > 1:
        try:
            num = int(sys.argv[1])
        except ValueError:
            print(f"❌ Invalid argument: '{sys.argv[1]}'. Expected a number 0-6.")
            return
    else:
        # Interactive
        print("\n⚡ KAVACHGRID 3.0 — Quick Demo Runner")
        print("─" * 40)
        for key, s in SCENARIOS.items():
            print(f"  [{s['number']}] {s['name']}")
        print(f"  [0] Run ALL scenarios")
        print()

        try:
            num = int(input("Select scenario [0-6]: ").strip())
        except (ValueError, KeyboardInterrupt):
            print("\nExiting.")
            return

    duration = float(sys.argv[2]) if len(sys.argv) > 2 else 60.0
    asyncio.run(run_demo(num, duration))


if __name__ == "__main__":
    main()
