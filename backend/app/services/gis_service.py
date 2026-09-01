"""
KavachGrid — GIS Service
Author: Abhishek
Fetches device coordinates, cross-references risk scores, and builds grid lines.
"""
from typing import List
from sqlalchemy.orm import Session
from app.db.models import Device, RiskScore, Telemetry
from app.schemas.gis import (
    GISTopologyResponse,
    GISNode,
    GISLineSegment,
    GISHeatmapPoint,
)


class GISService:
    @staticmethod
    def get_grid_topology(db: Session) -> GISTopologyResponse:
        """Queries all devices and dynamically constructs electrical topology lines."""
        devices = db.query(Device).all()
        nodes = []
        feeder_coords = [28.6139, 77.2090]
        feeder_id = "FEEDER-01"

        for dev in devices:
            # Fallback coordinates if null
            lat = dev.latitude if dev.latitude is not None else 28.6139
            lng = dev.longitude if dev.longitude is not None else 77.2090

            # Get latest risk score from RiskScore table
            latest_risk = (
                db.query(RiskScore)
                .filter(RiskScore.device_id == dev.device_id)
                .order_by(RiskScore.calculated_at.desc())
                .first()
            )
            risk_val = latest_risk.overall_score if latest_risk else 10.0

            if dev.device_type == "feeder":
                feeder_coords = [lat, lng]
                feeder_id = dev.device_id

            nodes.append(
                GISNode(
                    id=str(dev.id),
                    device_id=dev.device_id,
                    name=dev.name or dev.device_id,
                    device_type=dev.device_type,
                    latitude=lat,
                    longitude=lng,
                    status=dev.status or "online",
                    zone_id=dev.zone_id or "ZONE-A",
                    risk_score=risk_val,
                    power_kw=1.2,
                )
            )

        # Build electrical connection lines from Feeder -> Consumers
        lines = []
        for node in nodes:
            if node.device_type != "feeder":
                # If risk score > 75%, mark line as theft_suspect (turns red on map)
                line_status = (
                    "theft_suspect" if node.risk_score > 75 else "normal"
                )
                lines.append(
                    GISLineSegment(
                        from_node=feeder_id,
                        to_node=node.device_id,
                        from_coords=feeder_coords,
                        to_coords=[node.latitude, node.longitude],
                        loss_status=line_status,
                        power_flow_kw=node.power_kw,
                    )
                )

        return GISTopologyResponse(
            center=feeder_coords,
            zoom=16,
            total_nodes=len(nodes),
            nodes=nodes,
            lines=lines,
        )

    @staticmethod
    def get_risk_heatmap(db: Session) -> List[GISHeatmapPoint]:
        """Returns weighted geographic points for loss heatmaps."""
        devices = (
            db.query(Device).filter(Device.device_type == "consumer").all()
        )
        heatmap_points = []

        for dev in devices:
            lat = dev.latitude if dev.latitude is not None else 28.6139
            lng = dev.longitude if dev.longitude is not None else 77.2090

            latest_risk = (
                db.query(RiskScore)
                .filter(RiskScore.device_id == dev.device_id)
                .order_by(RiskScore.calculated_at.desc())
                .first()
            )
            score = latest_risk.overall_score if latest_risk else 15.0
            weight = round(min(1.0, max(0.0, score / 100.0)), 2)
            level = latest_risk.risk_level if latest_risk else "low"

            heatmap_points.append(
                GISHeatmapPoint(
                    latitude=lat,
                    longitude=lng,
                    weight=weight,
                    device_id=dev.device_id,
                    risk_level=level,
                    power_loss_kw=round(weight * 2.5, 2),
                )
            )

        return heatmap_points


gis_service = GISService()
