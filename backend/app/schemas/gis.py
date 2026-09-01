"""
KavachGrid — GIS & Geospatial Pydantic Schemas
Author: Abhishek
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class GISNode(BaseModel):
    """Represents a physical device on the map."""

    id: str
    device_id: str
    name: str
    device_type: str  # 'feeder', 'consumer', 'localization'
    latitude: float
    longitude: float
    status: str
    zone_id: Optional[str] = "ZONE-A"
    risk_score: float = 0.0
    power_kw: float = 0.0


class GISLineSegment(BaseModel):
    """Represents an electrical cable connecting two nodes."""

    from_node: str
    to_node: str
    from_coords: List[float]  # [latitude, longitude]
    to_coords: List[float]  # [latitude, longitude]
    loss_status: str  # 'normal', 'warning', 'theft_suspect'
    power_flow_kw: float = 0.0


class GISTopologyResponse(BaseModel):
    """Complete distribution network topology."""

    center: List[float] = [28.6139, 77.2090]
    zoom: int = 16
    total_nodes: int
    nodes: List[GISNode]
    lines: List[GISLineSegment]


class GISHeatmapPoint(BaseModel):
    """Weighted geographic coordinate for loss density heatmap."""

    latitude: float
    longitude: float
    weight: float = Field(
        ..., ge=0.0, le=1.0, description="Normalized risk (0.0 to 1.0)"
    )
    device_id: str
    risk_level: str
    power_loss_kw: float = 0.0
