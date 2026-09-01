"""
KAVACHGRID 3.0 — GIS & Geospatial API Router
Phase 12: Connects smart grid topological GIS mapping, coordinates,
GeoJSON feeds, real-time power flows, and risk overlays.

Endpoints:
    GET  /api/v1/gis/topology           — Complete GIS nodes, edges, power flows, and risk stats
    GET  /api/v1/gis/geojson            — RFC 7946 GeoJSON FeatureCollection for QGIS / Leaflet
    PUT  /api/v1/gis/devices/{device_id}/coordinates — Update device GPS coordinates & zone
    GET  /api/v1/gis/stats              — High-level geospatial grid health summary
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.dependencies import get_current_user, get_db, require_role
from app.db.models import Device, Telemetry, RiskScore, Alert, User
from app.schemas.gis import (
    GisEdge,
    GisGeoJsonFeature,
    GisGeoJsonResponse,
    GisLocationUpdate,
    GisNode,
    GisTopologyResponse,
    GisZoneSummary,
)

router = APIRouter(prefix="/gis", tags=["GIS & Topology"])


@router.get(
    "/topology",
    response_model=GisTopologyResponse,
    summary="Get complete GIS grid topology with live telemetry & risk",
)
async def get_gis_topology(
    zone_id: Optional[str] = Query(None, description="Optional zone filter (e.g. zone_A)"),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """
    Fetch comprehensive geospatial grid topology:
    - Nodes with GPS coordinates, latest telemetry, trust score, AI anomaly score, and active risk level.
    - Grid distribution lines (Edges) connecting feeder -> branch sensors -> consumers.
    - Aggregated energy balance and line loss percentage per zone.
    """
    query = db.query(Device)
    if zone_id:
        query = query.filter(Device.zone_id == zone_id)
    
    # Filter devices that have coordinates or provide fallback default
    devices: List[Device] = query.all()
    
    nodes: List[GisNode] = []
    zones_map: Dict[str, Dict] = {}
    
    # Track nodes by type for topological edge creation
    feeders_by_zone: Dict[str, Device] = {}
    localization_by_zone: Dict[str, List[Device]] = {}
    consumers_by_zone: Dict[str, List[Device]] = {}

    total_lats = 0.0
    total_lngs = 0.0
    valid_coords_count = 0

    for dev in devices:
        # Default coordinates around Delhi grid center if null
        lat = dev.latitude if dev.latitude is not None else 28.6139
        lng = dev.longitude if dev.longitude is not None else 77.2090
        
        total_lats += lat
        total_lngs += lng
        valid_coords_count += 1

        zid = dev.zone_id or "default_zone"
        if zid not in zones_map:
            zones_map[zid] = {
                "zone_id": zid,
                "total_nodes": 0,
                "feeder_id": None,
                "feeder_power_kw": 0.0,
                "consumer_total_power_kw": 0.0,
                "critical_nodes_count": 0,
                "lats": [],
                "lngs": [],
            }
        zones_map[zid]["total_nodes"] += 1
        zones_map[zid]["lats"].append(lat)
        zones_map[zid]["lngs"].append(lng)

        # Get latest telemetry reading
        latest_tel = (
            db.query(Telemetry)
            .filter(Telemetry.device_id == dev.device_id)
            .order_by(desc(Telemetry.timestamp))
            .first()
        )

        # Get latest risk score
        latest_risk = (
            db.query(RiskScore)
            .filter(RiskScore.device_id == dev.device_id)
            .order_by(desc(RiskScore.calculated_at))
            .first()
        )

        # Count active unacknowledged alerts
        active_alerts_cnt = (
            db.query(Alert)
            .filter(Alert.device_id == dev.device_id, Alert.acknowledged == False)  # noqa: E712
            .count()
        )

        # Extract values
        v = latest_tel.voltage if latest_tel else None
        c = latest_tel.current if latest_tel else None
        raw_p = latest_tel.power if latest_tel else None
        
        # Normalize power to kW (if telemetry is reported in Watts > 50W, convert to kW)
        p = round(raw_p / 1000.0, 3) if (raw_p is not None and raw_p > 50.0) else (round(raw_p, 3) if raw_p is not None else None)
        
        pf = latest_tel.power_factor if latest_tel else None
        e = latest_tel.energy if latest_tel else None
        trust = latest_tel.trust_score if latest_tel else (dev.device_metadata or {}).get("trust_score", 99.0)
        anomaly = latest_tel.anomaly_score if latest_tel else 0.0
        
        risk_level = "low"
        overall_risk = 0.0
        if latest_risk:
            risk_level = latest_risk.risk_level or "low"
            overall_risk = latest_risk.overall_score or 0.0
        elif (anomaly is not None and anomaly >= 0.7) or dev.status == "warning":
            risk_level = "critical" if (anomaly is not None and anomaly >= 0.7) else "high"
            overall_risk = 88.5 if (anomaly is not None and anomaly >= 0.7) else 65.0
        elif (anomaly is not None and anomaly >= 0.3) or (trust is not None and trust < 80.0):
            risk_level = "medium"
            overall_risk = 45.0
        else:
            risk_level = "low"
            overall_risk = round((anomaly or 0.0) * 25.0 + ((100.0 - (trust or 99.0)) * 0.2), 1)

        # Dynamic online status check (if seen within last 5 minutes)
        node_status = dev.status
        if latest_tel and latest_tel.timestamp:
            delta = (datetime.now(timezone.utc) - latest_tel.timestamp.replace(tzinfo=timezone.utc)).total_seconds()
            if delta < 300:
                node_status = "warning" if risk_level in ["high", "critical"] else "online"

        if risk_level in ["high", "critical"]:
            zones_map[zid]["critical_nodes_count"] += 1

        if dev.device_type == "feeder":
            feeders_by_zone[zid] = dev
            zones_map[zid]["feeder_id"] = dev.device_id
            if p is not None:
                zones_map[zid]["feeder_power_kw"] += p
        elif dev.device_type == "localization":
            localization_by_zone.setdefault(zid, []).append(dev)
        else:
            consumers_by_zone.setdefault(zid, []).append(dev)
            if p is not None:
                zones_map[zid]["consumer_total_power_kw"] += p

        nodes.append(
            GisNode(
                device_id=dev.device_id,
                name=dev.name,
                device_type=dev.device_type,
                location=dev.location,
                latitude=lat,
                longitude=lng,
                zone_id=dev.zone_id,
                status=node_status,
                voltage=v,
                current=c,
                power=p,
                power_factor=pf,
                energy=e,
                trust_score=trust,
                anomaly_score=anomaly,
                overall_risk=overall_risk,
                risk_level=risk_level,
                active_alerts_count=active_alerts_cnt,
                last_seen_at=dev.last_seen_at,
            )
        )

    # Construct Topological Edges (Lines between nodes)
    edges: List[GisEdge] = []
    edge_idx = 1

    for zid, f_dev in feeders_by_zone.items():
        f_lat = f_dev.latitude if f_dev.latitude is not None else 28.6139
        f_lng = f_dev.longitude if f_dev.longitude is not None else 77.2090
        
        loc_nodes = localization_by_zone.get(zid, [])
        cons_nodes = consumers_by_zone.get(zid, [])

        if loc_nodes:
            # Feeder -> Localization Sensors
            for loc in loc_nodes:
                l_lat = loc.latitude if loc.latitude is not None else 28.6135
                l_lng = loc.longitude if loc.longitude is not None else 77.2098
                edges.append(
                    GisEdge(
                        id=f"edge-{edge_idx}",
                        from_node=f_dev.device_id,
                        to_node=loc.device_id,
                        from_coords=[f_lat, f_lng],
                        to_coords=[l_lat, l_lng],
                        edge_type="feeder_to_branch",
                        status="warning" if loc.status == "warning" else "normal",
                        power_flow_kw=15.0,
                    )
                )
                edge_idx += 1

                # Localization Sensor -> Consumers in proximity
                for cons in cons_nodes:
                    c_lat = cons.latitude if cons.latitude is not None else 28.6145
                    c_lng = cons.longitude if cons.longitude is not None else 77.2105
                    is_bad = cons.status == "warning"
                    edges.append(
                        GisEdge(
                            id=f"edge-{edge_idx}",
                            from_node=loc.device_id,
                            to_node=cons.device_id,
                            from_coords=[l_lat, l_lng],
                            to_coords=[c_lat, c_lng],
                            edge_type="branch_to_consumer",
                            status="critical" if is_bad else "normal",
                            power_flow_kw=1.5,
                            loss_estimated_pct=30.0 if is_bad else 2.5,
                        )
                    )
                    edge_idx += 1
        else:
            # Direct Feeder -> Consumers
            for cons in cons_nodes:
                c_lat = cons.latitude if cons.latitude is not None else 28.6145
                c_lng = cons.longitude if cons.longitude is not None else 77.2105
                is_bad = cons.status == "warning"
                edges.append(
                    GisEdge(
                        id=f"edge-{edge_idx}",
                        from_node=f_dev.device_id,
                        to_node=cons.device_id,
                        from_coords=[f_lat, f_lng],
                        to_coords=[c_lat, c_lng],
                        edge_type="feeder_to_consumer",
                        status="critical" if is_bad else "normal",
                        power_flow_kw=2.0,
                        loss_estimated_pct=25.0 if is_bad else 1.8,
                    )
                )
                edge_idx += 1

    # Calculate Zone Summaries
    zone_summaries: List[GisZoneSummary] = []
    for zid, zdata in zones_map.items():
        f_p = zdata["feeder_power_kw"]
        c_p = zdata["consumer_total_power_kw"]
        loss_pct = 0.0
        if f_p > 0 and f_p >= c_p:
            loss_pct = round(((f_p - c_p) / f_p) * 100.0, 2)
        elif f_p == 0 and c_p > 0:
            loss_pct = 0.0

        c_lat = sum(zdata["lats"]) / len(zdata["lats"]) if zdata["lats"] else 28.6139
        c_lng = sum(zdata["lngs"]) / len(zdata["lngs"]) if zdata["lngs"] else 77.2090

        zone_summaries.append(
            GisZoneSummary(
                zone_id=zid,
                total_nodes=zdata["total_nodes"],
                feeder_id=zdata["feeder_id"],
                feeder_power_kw=round(f_p, 2),
                consumer_total_power_kw=round(c_p, 2),
                loss_percentage=loss_pct,
                critical_nodes_count=zdata["critical_nodes_count"],
                center_lat=c_lat,
                center_lng=c_lng,
            )
        )

    center_lat = (total_lats / valid_coords_count) if valid_coords_count > 0 else 28.6139
    center_lng = (total_lngs / valid_coords_count) if valid_coords_count > 0 else 77.2090

    return GisTopologyResponse(
        nodes=nodes,
        edges=edges,
        zones=zone_summaries,
        total_nodes=len(nodes),
        center_lat=center_lat,
        center_lng=center_lng,
        generated_at=datetime.now(timezone.utc),
    )


@router.get(
    "/geojson",
    response_model=GisGeoJsonResponse,
    summary="Export GIS smart grid layer in standard GeoJSON format",
)
async def get_gis_geojson(
    zone_id: Optional[str] = Query(None, description="Optional zone filter"),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """
    Returns RFC 7946 compliant GeoJSON FeatureCollection:
    - Points: Feeder substations, branch sensors, smart meters with properties
    - LineStrings: Electrical topology wires connecting grid hierarchy
    """
    topology = await get_gis_topology(zone_id=zone_id, db=db, _current_user=_current_user)
    
    features: List[GisGeoJsonFeature] = []

    # Node Points
    for node in topology.nodes:
        feature = GisGeoJsonFeature(
            type="Feature",
            geometry={
                "type": "Point",
                "coordinates": [node.longitude, node.latitude],
            },
            properties={
                "device_id": node.device_id,
                "name": node.name,
                "device_type": node.device_type,
                "zone_id": node.zone_id,
                "status": node.status,
                "voltage": node.voltage,
                "current": node.current,
                "power_kw": node.power,
                "trust_score": node.trust_score,
                "anomaly_score": node.anomaly_score,
                "risk_level": node.risk_level,
                "active_alerts": node.active_alerts_count,
            },
        )
        features.append(feature)

    # Edge LineStrings
    for edge in topology.edges:
        feature = GisGeoJsonFeature(
            type="Feature",
            geometry={
                "type": "LineString",
                "coordinates": [
                    [edge.from_coords[1], edge.from_coords[0]],  # [lng, lat]
                    [edge.to_coords[1], edge.to_coords[0]],
                ],
            },
            properties={
                "edge_id": edge.id,
                "from_node": edge.from_node,
                "to_node": edge.to_node,
                "edge_type": edge.edge_type,
                "status": edge.status,
                "power_flow_kw": edge.power_flow_kw,
                "loss_estimated_pct": edge.loss_estimated_pct,
            },
        )
        features.append(feature)

    return GisGeoJsonResponse(type="FeatureCollection", features=features)


@router.put(
    "/devices/{device_id}/coordinates",
    response_model=GisNode,
    summary="Update GPS coordinates and location metadata for a device",
    dependencies=[Depends(require_role("operator"))],
)
async def update_device_coordinates(
    device_id: str,
    data: GisLocationUpdate,
    db: Session = Depends(get_db),
):
    """Update latitude, longitude, and physical installation location for GIS mapping."""
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device '{device_id}' not found",
        )

    device.latitude = data.latitude
    device.longitude = data.longitude
    if data.location is not None:
        device.location = data.location
    if data.zone_id is not None:
        device.zone_id = data.zone_id
    
    device.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(device)

    # Return updated node representation
    return GisNode(
        device_id=device.device_id,
        name=device.name,
        device_type=device.device_type,
        location=device.location,
        latitude=device.latitude,
        longitude=device.longitude,
        zone_id=device.zone_id,
        status=device.status,
        trust_score=99.0,
        risk_level="low" if device.status == "online" else "warning",
    )


@router.get(
    "/stats",
    summary="Get GIS network health and coverage statistics",
)
async def get_gis_stats(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """Returns geospatial operational metrics, mapped node count, and high-risk clusters."""
    total_devices = db.query(Device).count()
    mapped_devices = (
        db.query(Device)
        .filter(Device.latitude.isnot(None), Device.longitude.isnot(None))
        .count()
    )
    feeders_count = db.query(Device).filter(Device.device_type == "feeder").count()
    consumers_count = db.query(Device).filter(Device.device_type == "consumer").count()
    loc_count = db.query(Device).filter(Device.device_type == "localization").count()

    return {
        "total_devices": total_devices,
        "mapped_devices": mapped_devices,
        "unmapped_devices": total_devices - mapped_devices,
        "coverage_percentage": round((mapped_devices / total_devices * 100.0), 1) if total_devices > 0 else 100.0,
        "device_breakdown": {
            "feeders": feeders_count,
            "consumers": consumers_count,
            "localization_nodes": loc_count,
        },
    }
