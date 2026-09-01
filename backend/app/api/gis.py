"""
KavachGrid — GIS API Router
Author: Abhishek
Endpoints: /api/v1/gis/topology, /api/v1/gis/heatmap
"""
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.schemas.gis import GISTopologyResponse, GISHeatmapPoint
from app.services.gis_service import gis_service

router = APIRouter(prefix="/gis", tags=["GIS & Geospatial"])


@router.get(
    "/topology",
    response_model=GISTopologyResponse,
    summary="Get full grid geospatial electrical topology",
)
async def get_grid_topology(db: Session = Depends(get_db)):
    """Returns Substation Feeder coords, consumer poles, and line connection statuses."""
    return gis_service.get_grid_topology(db)


@router.get(
    "/heatmap",
    response_model=List[GISHeatmapPoint],
    summary="Get risk and theft density heatmap points",
)
async def get_risk_heatmap(db: Session = Depends(get_db)):
    """Returns weighted coordinates (0.0 to 1.0) for Leaflet/Mapbox thermal loss overlays."""
    return gis_service.get_risk_heatmap(db)
