"""
KAVACHGRID 3.0 — Simulator Package

Software-based node simulator for SIH demonstrations.
Enables full demo without physical ESP32 hardware.

Exports:
    - VirtualFeeder: Simulates the Distribution Transformer feeder
    - VirtualConsumer: Simulates household smart meters (H1–H4)
    - ScenarioEngine: Orchestrates the 6 SIH demo scenarios
    - SCENARIOS: Dictionary of available scenario configurations
"""

from simulator.virtual_feeder import VirtualFeeder
from simulator.virtual_consumer import VirtualConsumer
from simulator.scenario_engine import ScenarioEngine, SCENARIOS

__all__ = [
    "VirtualFeeder",
    "VirtualConsumer",
    "ScenarioEngine",
    "SCENARIOS",
]
