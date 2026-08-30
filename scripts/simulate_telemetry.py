#!/usr/bin/env python3
"""
KAVACHGRID 3.0 — Telemetry Simulator CLI
Phase 15: One-command runner for SIH demo scenarios

Publishes simulated MQTT telemetry from a virtual feeder + 4 consumers.
Supports both MQTT mode (requires Mosquitto) and HTTP mode (direct API calls).

Usage:
    # Interactive menu
    python scripts/simulate_telemetry.py

    # Run a specific scenario
    python scripts/simulate_telemetry.py --scenario theft --duration 120

    # Run without MQTT (direct HTTP POST to FastAPI)
    python scripts/simulate_telemetry.py --scenario normal --mode http

    # List all scenarios
    python scripts/simulate_telemetry.py --list

    # Dry-run (print to console, no MQTT/HTTP)
    python scripts/simulate_telemetry.py --scenario theft --mode dry
"""

import argparse
import asyncio
import json
import logging
import os
import signal
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from simulator.virtual_feeder import VirtualFeeder
from simulator.virtual_consumer import VirtualConsumer
from simulator.scenario_engine import ScenarioEngine, SCENARIOS

# ── Logging setup ───────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(name)-35s │ %(levelname)-7s │ %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("kavachgrid.simulator.cli")

# Reduce noise from external libraries
logging.getLogger("paho.mqtt").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)


# ── MQTT Client Adapter ────────────────────────────────────────

class MQTTClientAdapter:
    """
    Thin async wrapper around paho-mqtt for the simulator.
    Provides an async publish() method compatible with VirtualFeeder/Consumer.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 1883,
        username: str = "kavachgrid_backend",
        password: str = "kavachgrid",
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self._client = None
        self._connected = False

    def connect(self) -> bool:
        """Connect to the MQTT broker using paho-mqtt."""
        try:
            import paho.mqtt.client as paho_mqtt
        except ImportError:
            logger.error(
                "❌ paho-mqtt not installed. Install with:\n"
                "   pip install paho-mqtt\n"
                "   Or use --mode http or --mode dry"
            )
            return False

        try:
            self._client = paho_mqtt.Client(
                client_id="kavach-simulator",
                protocol=paho_mqtt.MQTTv311,
            )
            if self.username:
                self._client.username_pw_set(self.username, self.password)

            self._client.on_connect = self._on_connect
            self._client.on_disconnect = self._on_disconnect

            self._client.connect(self.host, self.port, keepalive=60)
            self._client.loop_start()

            # Wait for connection
            for _ in range(30):
                if self._connected:
                    break
                time.sleep(0.1)

            if not self._connected:
                logger.warning("⚠️ MQTT connection timeout — continuing anyway")

            return self._connected

        except Exception as e:
            logger.error(f"❌ MQTT connection failed: {e}")
            return False

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self._connected = True
            logger.info(f"✅ Connected to MQTT broker at {self.host}:{self.port}")
        else:
            logger.error(f"❌ MQTT connection refused (rc={rc})")

    def _on_disconnect(self, client, userdata, rc):
        self._connected = False
        if rc != 0:
            logger.warning(f"⚠️ MQTT disconnected unexpectedly (rc={rc})")

    async def publish(self, topic: str, payload: str, qos: int = 0) -> None:
        """Async-compatible publish (wraps sync paho publish)."""
        if self._client and self._connected:
            result = self._client.publish(topic, payload, qos=qos)
            result.wait_for_publish(timeout=5.0)
        else:
            logger.warning(f"📵 Not connected — skipping publish to {topic}")

    def disconnect(self) -> None:
        """Disconnect from broker."""
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()
            logger.info("🔌 MQTT disconnected")


# ── HTTP Client Adapter ────────────────────────────────────────

class HTTPClientAdapter:
    """
    Posts telemetry directly to FastAPI REST API instead of MQTT.
    Useful when Mosquitto broker is not available.
    """

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self._session = None

    async def publish(self, topic: str, payload: str, qos: int = 0) -> None:
        """Post telemetry as HTTP request to the backend API."""
        try:
            import aiohttp
        except ImportError:
            logger.error("❌ aiohttp not installed for HTTP mode. pip install aiohttp")
            return

        data = json.loads(payload)
        url = f"{self.base_url}/api/v1/telemetry"

        try:
            if self._session is None:
                self._session = aiohttp.ClientSession()

            async with self._session.post(url, json=data) as resp:
                if resp.status in (200, 201):
                    logger.debug(f"📤 HTTP POST {url} → {resp.status}")
                else:
                    body = await resp.text()
                    logger.warning(f"⚠️ HTTP POST {url} → {resp.status}: {body[:100]}")
        except Exception as e:
            logger.error(f"❌ HTTP POST failed: {e}")

    async def close(self):
        if self._session:
            await self._session.close()


# ── Dry-Run Client (Console Only) ──────────────────────────────

class DryRunClient:
    """Prints telemetry to console without any network I/O."""

    async def publish(self, topic: str, payload: str, qos: int = 0) -> None:
        data = json.loads(payload)
        dev = data.get("device_id", "?")
        pwr = data.get("power", 0)
        volt = data.get("voltage", 0)
        print(
            f"  📋 [{topic}] {dev}: "
            f"V={volt}V P={pwr}W E={data.get('energy', 0)}Wh"
        )


# ── Interactive Menu ────────────────────────────────────────────

def print_banner():
    """Print the KAVACHGRID simulator banner."""
    print("\n" + "=" * 62)
    print("  ⚡ KAVACHGRID 3.0 — Virtual Grid Simulator")
    print("  🎯 SIH Demo Scenario Engine")
    print("=" * 62)


def print_scenarios():
    """Print all available scenarios."""
    print("\n┌──────┬────────────────────────────────────────────────┐")
    print("│  #   │  Scenario                                      │")
    print("├──────┼────────────────────────────────────────────────┤")
    for key, s in SCENARIOS.items():
        num = s["number"]
        name = s["name"]
        print(f"│  {num}   │  {name:<48} │")
    print("└──────┴────────────────────────────────────────────────┘")


def interactive_menu() -> str:
    """Show interactive scenario selection menu."""
    print_scenarios()

    key_map = {str(s["number"]): k for k, s in SCENARIOS.items()}
    key_map.update({k: k for k in SCENARIOS.keys()})  # also accept key names

    while True:
        choice = input("\n🎮 Select scenario [1-6] or name (q to quit): ").strip().lower()
        if choice in ("q", "quit", "exit"):
            sys.exit(0)
        if choice in key_map:
            return key_map[choice]
        print(f"  ❌ Invalid choice '{choice}'. Try 1-6 or a scenario name.")


# ── Main Entry Point ────────────────────────────────────────────

async def main(args: argparse.Namespace) -> None:
    """Main async entry point."""
    print_banner()

    # ── Determine scenario ──────────────────────────────────────
    if args.list:
        print_scenarios()
        for key, s in SCENARIOS.items():
            print(f"\n  [{key}] {s['name']}")
            print(f"    {s['description']}")
        return

    scenario_key = args.scenario
    if not scenario_key:
        scenario_key = interactive_menu()

    if scenario_key not in SCENARIOS:
        print(f"❌ Unknown scenario: '{scenario_key}'")
        print(f"   Available: {', '.join(SCENARIOS.keys())}")
        return

    # ── Setup client adapter ────────────────────────────────────
    client = None
    if args.mode == "mqtt":
        mqtt_host = args.mqtt_host or os.getenv("MQTT_BROKER_HOST", "localhost")
        mqtt_port = args.mqtt_port or int(os.getenv("MQTT_BROKER_PORT", "1883"))
        mqtt_user = args.mqtt_user or os.getenv("MQTT_USERNAME", "kavachgrid_backend")
        mqtt_pass = args.mqtt_pass or os.getenv("MQTT_PASSWORD", "kavachgrid")

        adapter = MQTTClientAdapter(
            host=mqtt_host,
            port=mqtt_port,
            username=mqtt_user,
            password=mqtt_pass,
        )
        if not adapter.connect():
            print("\n⚠️ MQTT connection failed. Falling back to dry-run mode.")
            print("   Make sure Mosquitto is running (docker-compose up mqtt)\n")
            client = DryRunClient()
        else:
            client = adapter

    elif args.mode == "http":
        base_url = args.api_url or os.getenv("API_BASE_URL", "http://localhost:8000")
        client = HTTPClientAdapter(base_url=base_url)
        logger.info(f"🌐 Using HTTP mode → {base_url}")

    elif args.mode == "dry":
        client = DryRunClient()
        logger.info("📋 Dry-run mode — printing to console only")

    else:
        client = DryRunClient()

    # ── Create virtual nodes ────────────────────────────────────
    feeder = VirtualFeeder(mqtt_client=client, device_id="FEEDER-01")

    consumers = {
        "CONSUMER-H1": VirtualConsumer("CONSUMER-H1", mqtt_client=client, zone_id="ZONE-A"),
        "CONSUMER-H2": VirtualConsumer("CONSUMER-H2", mqtt_client=client, zone_id="ZONE-A"),
        "CONSUMER-H3": VirtualConsumer("CONSUMER-H3", mqtt_client=client, zone_id="ZONE-A"),
        "CONSUMER-H4": VirtualConsumer("CONSUMER-H4", mqtt_client=client, zone_id="ZONE-A"),
    }

    engine = ScenarioEngine(feeder, consumers, mqtt_client=client)

    # ── Handle graceful shutdown ────────────────────────────────
    shutdown_event = asyncio.Event()

    def handle_signal(sig, frame):
        print(f"\n\n⏹️  Received {signal.Signals(sig).name} — shutting down gracefully...")
        engine.stop()
        shutdown_event.set()

    signal.signal(signal.SIGINT, handle_signal)

    # ── Run the scenario ────────────────────────────────────────
    print(f"\n🚀 Running scenario: {SCENARIOS[scenario_key]['name']}")
    print(f"   Duration: {args.duration}s | Interval: {args.interval}s")
    print(f"   Mode: {args.mode.upper()}")
    print(f"   Press Ctrl+C to stop early\n")

    try:
        summary = await engine.run_scenario(
            scenario_key=scenario_key,
            duration=args.duration,
            interval=args.interval,
        )

        # ── Print summary ───────────────────────────────────────
        print("\n" + "=" * 62)
        print("  📊 SCENARIO SUMMARY")
        print("=" * 62)
        print(f"  Scenario:   {summary['scenario_name']}")
        print(f"  Duration:   {summary['duration_seconds']:.1f}s")
        print(f"  Cycles:     {summary['total_cycles']}")
        print(f"  Feeder:     {summary['feeder_status']['total_load_w']:.1f}W total load")
        print()
        for did, cs in summary["consumer_statuses"].items():
            mode_str = cs["mode"].upper()
            pwr = cs["actual_power_w"]
            tx = "✅ TX" if cs["is_transmitting"] else "❌ OFFLINE"
            print(f"  {did}: {pwr:>8.1f}W | Mode={mode_str:<15} | {tx}")
        print("=" * 62)

    except Exception as e:
        logger.error(f"❌ Scenario execution error: {e}", exc_info=True)

    finally:
        # Cleanup
        if isinstance(client, MQTTClientAdapter):
            client.disconnect()
        elif isinstance(client, HTTPClientAdapter):
            await client.close()


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="KAVACHGRID 3.0 — Virtual Grid Simulator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/simulate_telemetry.py                              # Interactive menu
  python scripts/simulate_telemetry.py --scenario theft             # Run theft scenario
  python scripts/simulate_telemetry.py --scenario normal --mode dry # Dry run (no network)
  python scripts/simulate_telemetry.py --list                       # List all scenarios
  python scripts/simulate_telemetry.py --scenario localization --duration 300
        """,
    )

    parser.add_argument(
        "--scenario", "-s",
        type=str,
        default=None,
        choices=list(SCENARIOS.keys()),
        help="Scenario to run (omit for interactive menu)",
    )
    parser.add_argument(
        "--duration", "-d",
        type=float,
        default=120.0,
        help="Duration in seconds (default: 120)",
    )
    parser.add_argument(
        "--interval", "-i",
        type=float,
        default=5.0,
        help="Publish interval in seconds (default: 5)",
    )
    parser.add_argument(
        "--mode", "-m",
        type=str,
        default="mqtt",
        choices=["mqtt", "http", "dry"],
        help="Transport mode: mqtt (default), http (direct API), dry (console only)",
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List all available scenarios and exit",
    )

    # MQTT options
    mqtt_group = parser.add_argument_group("MQTT Options")
    mqtt_group.add_argument("--mqtt-host", type=str, default=None, help="MQTT broker host")
    mqtt_group.add_argument("--mqtt-port", type=int, default=None, help="MQTT broker port")
    mqtt_group.add_argument("--mqtt-user", type=str, default=None, help="MQTT username")
    mqtt_group.add_argument("--mqtt-pass", type=str, default=None, help="MQTT password")

    # HTTP options
    http_group = parser.add_argument_group("HTTP Options")
    http_group.add_argument("--api-url", type=str, default=None, help="FastAPI base URL")

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(main(args))
