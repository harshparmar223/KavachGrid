"""
KAVACHGRID 3.0 — GIS & Geospatial Pydantic Schemas
Defines request/response structures for geospatial network topology,
GeoJSON export, and node coordinate management.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class GisNode(BaseModel):
    """Geospatial representation of a grid node with live telemetry & risk."""

    device_id: str
    name: str
    device_type: str = Field(..., description="feeder | consumer | localization")
    location: Optional[str] = None
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    zone_id: Optional[str] = None
    status: str = Field(..., description="online | offline | warning")
    
    # Live electrical telemetry
    voltage: Optional[float] = None
    current: Optional[float] = None
    power: Optional[float] = None
    power_factor: Optional[float] = None
    energy: Optional[float] = None
    
    # AI & Trust metrics
    trust_score: Optional[float] = None
    anomaly_score: Optional[float] = None
    overall_risk: Optional[float] = None
    risk_level: Optional[str] = Field("low", description="low | medium | high | critical")
    
    # Alerts
    active_alerts_count: int = 0
    last_seen_at: Optional[datetime] = None


class GisEdge(BaseModel):
    """Grid transmission/distribution line connecting physical nodes."""

    id: str
    from_node: str
    to_node: str
    from_coords: List[float] = Field(..., description="[lat, lng]")
    to_coords: List[float] = Field(..., description="[lat, lng]")
    edge_type: str = Field(..., description="feeder_to_branch | branch_to_consumer | feeder_to_consumer")
    status: str = Field("normal", description="normal | warning | critical")
    power_flow_kw: Optional[float] = None
    loss_estimated_pct: Optional[float] = None


class GisZoneSummary(BaseModel):
    """Aggregated GIS metrics per electrical distribution zone."""

    zone_id: str
    total_nodes: int
    feeder_id: Optional[str] = None
    feeder_power_kw: float = 0.0
    consumer_total_power_kw: float = 0.0
    loss_percentage: float = 0.0
    critical_nodes_count: int = 0
    center_lat: float = 28.6139
    center_lng: float = 77.2090


class GisTopologyResponse(BaseModel):
    """Full geospatial network topology dataset for Leaflet/GIS dashboard."""

    nodes: List[GisNode]
    edges: List[GisEdge]
    zones: List[GisZoneSummary]
    total_nodes: int
    center_lat: float
    center_lng: float
    generated_at: datetime


class GisLocationUpdate(BaseModel):
    """Schema for updating physical GPS coordinates of a device."""

    latitude: float = Field(..., ge=-90, le=90, description="New GPS latitude")
    longitude: float = Field(..., ge=-180, le=180, description="New GPS longitude")
    location: Optional[str] = Field(None, max_length=255, description="Human readable address/pole ID")
    zone_id: Optional[str] = Field(None, max_length=50, description="Zone identifier")


class GisGeoJsonFeature(BaseModel):
    """GeoJSON Feature representation."""

    type: str = "Feature"
    geometry: Dict[str, Any]
    properties: Dict[str, Any]


class GisGeoJsonResponse(BaseModel):
    """GeoJSON FeatureCollection compliant with RFC 7946."""

    type: str = "FeatureCollection"
    features: List[GisGeoJsonFeature]
