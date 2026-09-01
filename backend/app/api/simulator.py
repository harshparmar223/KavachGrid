"""
KavachGrid — Grid Simulator API Router
Endpoints to control the interactive grid simulator, trigger SIH demo scenarios,
inject live thefts, and stream real-time physics telemetry.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.simulator_service import simulator_service, SCENARIOS

router = APIRouter(prefix="/simulator", tags=["Virtual Grid Simulator"])


class SetNodeModeRequest(BaseModel):
    mode: str = Field(..., description="Behavioral mode: 'normal', 'theft_bypass', 'stuck_sensor', 'offline', 'power_spike'")
    load_w: Optional[float] = Field(None, description="Optional custom base load in Watts")


@router.get("/status", summary="Get current simulation status, active scenario, and node telemetry")
async def get_simulator_status() -> Dict[str, Any]:
    """Returns the full live state of all nodes, active scenarios, and energy balance metrics."""
    return simulator_service.get_status()


@router.get("/telemetry/stream", summary="Get rolling 30-point time-series history for live charts")
async def get_stream_history() -> List[Dict[str, Any]]:
    """Returns the last 30 simulation ticks for instantaneous graph hydration on page load."""
    return simulator_service.stream_history


@router.post("/start", summary="Start the continuous simulation telemetry loop")
async def start_simulator() -> Dict[str, Any]:
    """Starts generating physical electrical telemetry every 3 seconds."""
    await simulator_service.start()
    return {"message": "Grid simulator started successfully", "status": simulator_service.get_status()}


@router.post("/stop", summary="Pause/Stop the simulation telemetry loop")
async def stop_simulator() -> Dict[str, Any]:
    """Pauses the simulation telemetry worker."""
    await simulator_service.stop()
    return {"message": "Grid simulator stopped successfully", "status": simulator_service.get_status()}


@router.post("/scenario/{scenario_id}", summary="Activate a pre-built SIH demo scenario")
async def apply_scenario(scenario_id: int) -> Dict[str, Any]:
    """Applies a preset demonstration scenario (1: Normal, 2: H2 Theft, 3: H3 Fault, 4: Surge, 5: Offline, 6: Multi-Theft)."""
    if scenario_id not in SCENARIOS:
        raise HTTPException(status_code=400, detail=f"Invalid scenario ID {scenario_id}. Choose between 1 and 6.")
    
    simulator_service.set_scenario(scenario_id)
    # If not already running, auto-start on scenario selection for instant demo experience
    if not simulator_service.is_running:
        await simulator_service.start()
        
    return {
        "message": f"Scenario {scenario_id} ({SCENARIOS[scenario_id]['name']}) activated",
        "status": simulator_service.get_status(),
    }


@router.post("/node/{device_id}/mode", summary="Set custom behavioral mode and wattage for a specific node")
async def set_node_mode(device_id: str, request: SetNodeModeRequest) -> Dict[str, Any]:
    """Manually customize any specific smart meter's operating behavior and load."""
    valid_devices = list(simulator_service.consumers.keys()) + ["FEEDER-01"]
    if device_id not in valid_devices:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found in simulator grid.")
    
    simulator_service.set_node_mode(device_id, request.mode, request.load_w)
    return {
        "message": f"Node {device_id} mode updated to {request.mode}",
        "status": simulator_service.get_status(),
    }


@router.post("/reset", summary="Reset grid back to standard normal baseline")
async def reset_simulator() -> Dict[str, Any]:
    """Clears all faults and bypasses, resetting the entire grid to normal operation."""
    simulator_service.reset()
    return {"message": "Grid simulator reset to normal baseline", "status": simulator_service.get_status()}
