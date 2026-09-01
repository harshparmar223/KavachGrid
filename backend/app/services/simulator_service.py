"""
KavachGrid — Grid Simulator Service
Provides real-time interactive simulation of Feeder, Consumer smart meters,
theft injections, sensor failures, and live telemetry generation.
"""

import asyncio
import logging
from datetime import datetime, timezone
import random
from typing import Dict, List, Optional, Any

from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.models import Device, Telemetry, Alert
from app.engines.energy_balance import energy_balance_engine
from app.engines.meter_health import meter_health_engine
from app.engines.ai_anomaly import ai_anomaly_engine
from app.engines.risk_engine import kavach_risk_engine
from app.engines.localization import localization_engine
from app.api.websocket import ws_manager

logger = logging.getLogger("kavachgrid.simulator")

SCENARIOS = {
    1: {
        "id": 1,
        "name": "Normal Balanced Grid",
        "description": "All 4 consumer households consume legitimate power. Grid is balanced (<5% line loss).",
        "severity": "normal",
        "active_theft": False,
    },
    2: {
        "id": 2,
        "name": "Single Consumer Theft (H2 Bypass)",
        "description": "House H2 activates a 75% bypass tap. Feeder load stays high while H2 reports only ~500W.",
        "severity": "critical",
        "active_theft": True,
        "target_device": "CONSUMER-H2",
    },
    3: {
        "id": 3,
        "name": "Meter Sensor Fault (H3 Stuck 0W)",
        "description": "House H3 sensor freezes at 0W. Meter Health Engine flags as Sensor Fault (Zero False Accusation).",
        "severity": "warning",
        "active_theft": False,
        "target_device": "CONSUMER-H3",
    },
    4: {
        "id": 4,
        "name": "Legitimate Load Surge (H1 Peak)",
        "description": "House H1 turns on heavy appliances (~4500W). Feeder scales proportionally, no false alarm.",
        "severity": "info",
        "active_theft": False,
    },
    5: {
        "id": 5,
        "name": "Communication Dropout (H4 Offline)",
        "description": "House H4 drops offline. Firmware buffers data locally while comm reliability drops.",
        "severity": "warning",
        "active_theft": False,
        "target_device": "CONSUMER-H4",
    },
    6: {
        "id": 6,
        "name": "Multi-Node Coordinated Theft (H2 + H4)",
        "description": "Both H2 and H4 steal simultaneously. Localization engine ranks both at top of suspect leaderboard.",
        "severity": "critical",
        "active_theft": True,
        "target_devices": ["CONSUMER-H2", "CONSUMER-H4"],
    },
}


class NodeState:
    def __init__(self, device_id: str, name: str, device_type: str, base_load: float = 2000.0):
        self.device_id = device_id
        self.name = name
        self.device_type = device_type
        self.base_load = base_load
        self.mode = "normal"  # normal, theft_bypass, stuck_sensor, offline, power_spike
        self.actual_power = base_load
        self.reported_power = base_load
        self.voltage = 230.0
        self.current = base_load / 230.0
        self.power_factor = 0.98
        self.frequency = 50.0
        self.status = "online"


class GridSimulatorService:
    def __init__(self):
        self.is_running: bool = False
        self.current_scenario_id: int = 1
        self.tick_count: int = 0
        self.interval_seconds: float = 3.0
        self._task: Optional[asyncio.Task] = None
        
        # Initialize virtual nodes
        self.feeder = NodeState("FEEDER-01", "Substation Feeder DT-01", "feeder", base_load=9000.0)
        self.consumers: Dict[str, NodeState] = {
            "CONSUMER-H1": NodeState("CONSUMER-H1", "House H1 (Sharma)", "consumer", base_load=2400.0),
            "CONSUMER-H2": NodeState("CONSUMER-H2", "House H2 (Verma)", "consumer", base_load=2500.0),
            "CONSUMER-H3": NodeState("CONSUMER-H3", "House H3 (Patel)", "consumer", base_load=2000.0),
            "CONSUMER-H4": NodeState("CONSUMER-H4", "House H4 (Singh)", "consumer", base_load=2100.0),
        }
        
        # Rolling 30-point telemetry stream buffer for live graphs
        self.stream_history: List[Dict[str, Any]] = []

    def get_status(self) -> Dict[str, Any]:
        """Returns full simulator state, active scenario, and node parameters."""
        active_scenario = SCENARIOS.get(self.current_scenario_id, SCENARIOS[1])
        
        # Compute live energy balance metrics
        total_consumer_reported = sum(
            c.reported_power for c in self.consumers.values() if c.status == "online"
        )
        feeder_power = self.feeder.actual_power
        expected_loss = feeder_power * 0.05
        unaccounted = max(0.0, feeder_power - total_consumer_reported - expected_loss)
        deficit_pct = (unaccounted / feeder_power * 100.0) if feeder_power > 0 else 0.0
        
        return {
            "is_running": self.is_running,
            "current_scenario": active_scenario,
            "tick_count": self.tick_count,
            "interval_seconds": self.interval_seconds,
            "feeder": {
                "device_id": self.feeder.device_id,
                "name": self.feeder.name,
                "power_w": round(self.feeder.actual_power, 1),
                "voltage": round(self.feeder.voltage, 1),
                "current": round(self.feeder.current, 2),
                "power_factor": self.feeder.power_factor,
                "status": self.feeder.status,
            },
            "consumers": [
                {
                    "device_id": c.device_id,
                    "name": c.name,
                    "mode": c.mode,
                    "actual_power_w": round(c.actual_power, 1),
                    "reported_power_w": round(c.reported_power, 1),
                    "voltage": round(c.voltage, 1),
                    "current": round(c.current, 2),
                    "power_factor": c.power_factor,
                    "status": c.status,
                    "is_theft_active": (c.actual_power - c.reported_power) > 500,
                }
                for c in self.consumers.values()
            ],
            "balance": {
                "feeder_power_w": round(feeder_power, 1),
                "total_consumer_w": round(total_consumer_reported, 1),
                "technical_loss_w": round(expected_loss, 1),
                "unaccounted_w": round(unaccounted, 1),
                "deficit_pct": round(deficit_pct, 1),
                "severity": "critical" if deficit_pct > 25 else "warning" if deficit_pct > 15 else "normal",
            },
            "available_scenarios": list(SCENARIOS.values()),
        }

    def set_scenario(self, scenario_id: int):
        """Applies a preset SIH demonstration scenario."""
        if scenario_id not in SCENARIOS:
            raise ValueError(f"Invalid scenario id: {scenario_id}")
            
        self.current_scenario_id = scenario_id
        
        # Reset all nodes to normal baseline first
        for c in self.consumers.values():
            c.mode = "normal"
            c.status = "online"
            
        # Apply specific scenario modifiers
        if scenario_id == 1:
            # Normal balanced
            self.consumers["CONSUMER-H1"].base_load = 2400.0
            self.consumers["CONSUMER-H2"].base_load = 2200.0
            self.consumers["CONSUMER-H3"].base_load = 2000.0
            self.consumers["CONSUMER-H4"].base_load = 2100.0
        elif scenario_id == 2:
            # H2 Bypass Theft
            self.consumers["CONSUMER-H2"].mode = "theft_bypass"
            self.consumers["CONSUMER-H2"].base_load = 3500.0
        elif scenario_id == 3:
            # H3 Stuck Sensor
            self.consumers["CONSUMER-H3"].mode = "stuck_sensor"
        elif scenario_id == 4:
            # H1 Load Surge (clean peak)
            self.consumers["CONSUMER-H1"].mode = "power_spike"
            self.consumers["CONSUMER-H1"].base_load = 4500.0
        elif scenario_id == 5:
            # H4 Offline
            self.consumers["CONSUMER-H4"].mode = "offline"
            self.consumers["CONSUMER-H4"].status = "offline"
        elif scenario_id == 6:
            # Multi-Theft H2 + H4
            self.consumers["CONSUMER-H2"].mode = "theft_bypass"
            self.consumers["CONSUMER-H2"].base_load = 3500.0
            self.consumers["CONSUMER-H4"].mode = "theft_bypass"
            self.consumers["CONSUMER-H4"].base_load = 3000.0

        logger.info(f"Simulator switched to Scenario {scenario_id}: {SCENARIOS[scenario_id]['name']}")

    def set_node_mode(self, device_id: str, mode: str, load_w: Optional[float] = None):
        """Sets custom mode and load for a specific node."""
        if device_id in self.consumers:
            node = self.consumers[device_id]
            node.mode = mode
            if load_w is not None:
                node.base_load = load_w
            node.status = "offline" if mode == "offline" else "online"
        elif device_id == "FEEDER-01":
            if load_w is not None:
                self.feeder.base_load = load_w

    def reset(self):
        """Resets the entire grid back to default normal state."""
        self.current_scenario_id = 1
        self.tick_count = 0
        self.stream_history.clear()
        for c in self.consumers.values():
            c.mode = "normal"
            c.status = "online"
            c.base_load = 2200.0
        self.set_scenario(1)

    async def start(self):
        """Starts the background continuous simulation tick loop."""
        if self.is_running:
            return
        self.is_running = True
        self._task = asyncio.create_task(self._simulation_loop())
        logger.info("Grid Simulator worker STARTED.")

    async def stop(self):
        """Stops the background continuous simulation loop."""
        self.is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
        logger.info("Grid Simulator worker STOPPED.")

    async def _simulation_loop(self):
        """Main periodic loop simulating physical electricity and dispatching engines."""
        while self.is_running:
            try:
                self.tick_count += 1
                now = datetime.now(timezone.utc)
                now_str = now.strftime("%H:%M:%S")

                # 1. Compute physics for each consumer
                total_actual_draw = 0.0
                total_reported_draw = 0.0
                consumer_readings: Dict[str, float] = {}

                for c in self.consumers.values():
                    # Add small realistic ±2% random fluctuation
                    fluctuation = random.uniform(0.97, 1.03)
                    c.voltage = round(random.uniform(228.0, 232.0), 1)
                    c.frequency = round(random.uniform(49.95, 50.05), 2)
                    c.power_factor = round(random.uniform(0.96, 0.99), 2)

                    if c.mode == "normal":
                        c.actual_power = c.base_load * fluctuation
                        c.reported_power = c.actual_power
                        c.status = "online"
                    elif c.mode == "theft_bypass":
                        # Actual draw is high (e.g. 3500W), but meter only reports ~500W
                        c.actual_power = c.base_load * fluctuation
                        c.reported_power = round(random.uniform(450.0, 550.0), 1)
                        c.status = "online"
                    elif c.mode == "stuck_sensor":
                        c.actual_power = c.base_load * fluctuation
                        c.reported_power = 0.0  # Frozen 0W reading
                        c.status = "online"
                    elif c.mode == "power_spike":
                        c.actual_power = c.base_load * fluctuation
                        c.reported_power = c.actual_power
                        c.status = "online"
                    elif c.mode == "offline":
                        c.actual_power = c.base_load * fluctuation
                        c.reported_power = 0.0
                        c.status = "offline"

                    c.current = round(c.reported_power / (c.voltage * c.power_factor), 2) if c.reported_power > 0 else 0.0
                    
                    if c.status == "online":
                        total_reported_draw += c.reported_power
                    total_actual_draw += c.actual_power
                    consumer_readings[c.device_id] = c.reported_power

                # 2. Feeder delivers total actual draw + 5% wire line loss
                feeder_loss = total_actual_draw * 0.05
                self.feeder.actual_power = round(total_actual_draw + feeder_loss, 1)
                self.feeder.voltage = round(random.uniform(229.0, 231.5), 1)
                self.feeder.current = round(self.feeder.actual_power / (self.feeder.voltage * 0.98), 2)

                # 3. Calculate unaccounted energy deficit
                expected_loss = self.feeder.actual_power * 0.05
                unaccounted_w = max(0.0, self.feeder.actual_power - total_reported_draw - expected_loss)
                deficit_pct = round((unaccounted_w / self.feeder.actual_power * 100.0), 1) if self.feeder.actual_power > 0 else 0.0

                # 4. Append to rolling 30-point stream history for charts
                stream_point = {
                    "time": now_str,
                    "timestamp": now.isoformat(),
                    "feeder_w": round(self.feeder.actual_power, 1),
                    "consumers_sum_w": round(total_reported_draw, 1),
                    "expected_loss_w": round(expected_loss, 1),
                    "unaccounted_gap_w": round(unaccounted_w, 1),
                    "deficit_pct": deficit_pct,
                    "h1_w": round(self.consumers["CONSUMER-H1"].reported_power, 1),
                    "h2_w": round(self.consumers["CONSUMER-H2"].reported_power, 1),
                    "h3_w": round(self.consumers["CONSUMER-H3"].reported_power, 1),
                    "h4_w": round(self.consumers["CONSUMER-H4"].reported_power, 1),
                }
                self.stream_history.append(stream_point)
                if len(self.stream_history) > 30:
                    self.stream_history.pop(0)

                # 5. Ingest into database session
                db: Session = SessionLocal()
                try:
                    # Write feeder telemetry
                    feeder_tel = Telemetry(
                        device_id=self.feeder.device_id,
                        voltage=self.feeder.voltage,
                        current=self.feeder.current,
                        power=self.feeder.actual_power,
                        energy=self.feeder.actual_power * (self.tick_count * self.interval_seconds / 3600.0),
                        power_factor=self.feeder.power_factor,
                        frequency=self.feeder.frequency,
                        timestamp=now,
                    )
                    db.add(feeder_tel)

                    # Write consumer telemetry
                    for c in self.consumers.values():
                        if c.status == "online":
                            c_tel = Telemetry(
                                device_id=c.device_id,
                                voltage=c.voltage,
                                current=c.current,
                                power=c.reported_power,
                                energy=c.reported_power * (self.tick_count * self.interval_seconds / 3600.0),
                                power_factor=c.power_factor,
                                frequency=c.frequency,
                                timestamp=now,
                            )
                            db.add(c_tel)
                    db.commit()

                    # Run analytics engines on the live grid state
                    energy_balance_engine.calculate_realtime(db, zone_id="ZONE-A")
                    kavach_risk_engine.calculate_all_risks(db)
                    localization_engine.localize_zone(db, zone_id="ZONE-A")

                except Exception as e:
                    logger.error(f"Simulator DB/Engine execution error: {e}")
                    db.rollback()
                finally:
                    db.close()

                # 6. Broadcast live update to WebSockets
                await ws_manager.broadcast({
                    "event": "simulator_tick",
                    "data": {
                        "stream_point": stream_point,
                        "status": self.get_status(),
                    },
                })

                await asyncio.sleep(self.interval_seconds)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in simulator tick loop: {e}")
                await asyncio.sleep(self.interval_seconds)


# Global singleton instance
simulator_service = GridSimulatorService()
