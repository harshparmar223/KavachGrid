"""
KAVACHGRID 3.0 — Risk Score Pydantic Schemas
Phase 2: Request/Response validation models for Risk Scores

Schemas:
    - RiskScoreCreate: Engine output for storage
    - RiskScoreResponse: API response with full breakdown
    - RiskRanking: Ranked list of suspicious consumers
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class RiskScoreCreate(BaseModel):
    """Schema for storing a new risk score (from Risk Engine)."""

    device_id: str = Field(..., examples=["CONSUMER-H1"])
    overall_score: float = Field(..., ge=0, le=100, examples=[72.5])
    energy_balance_score: float = Field(
        ..., ge=0, le=100, examples=[85.0],
        description="Energy imbalance contribution (0=no imbalance, 100=severe)",
    )
    ai_anomaly_score: float = Field(
        ..., ge=0, le=1, examples=[0.73],
        description="AI autoencoder anomaly score (0=normal, 1=highly anomalous)",
    )
    meter_health_score: float = Field(
        ..., ge=0, le=100, examples=[45.0],
        description="Meter health (100=perfect health, 0=completely unhealthy)",
    )
    device_trust_score: float = Field(
        ..., ge=0, le=100, examples=[90.0],
        description="Device trust level (100=fully trusted, 0=untrusted)",
    )
    comm_reliability_score: float = Field(
        ..., ge=0, le=100, examples=[88.0],
        description="Communication reliability (100=perfect, 0=no comms)",
    )
    risk_level: str = Field(
        ...,
        pattern="^(low|medium|high|critical)$",
        examples=["high"],
    )
    details: Optional[Dict[str, Any]] = Field(
        None,
        examples=[{
            "weights": {
                "energy_balance": 0.30,
                "ai_anomaly": 0.25,
                "meter_health": 0.20,
                "device_trust": 0.15,
                "comm_reliability": 0.10,
            },
            "explanation": "High energy imbalance combined with AI anomaly detection",
        }],
    )


class RiskScoreResponse(BaseModel):
    """Schema for risk score API responses with full breakdown."""

    id: UUID
    device_id: str
    overall_score: float
    energy_balance_score: float
    ai_anomaly_score: float
    meter_health_score: float
    device_trust_score: float
    comm_reliability_score: float
    risk_level: str
    details: Optional[Dict[str, Any]] = None
    calculated_at: datetime

    model_config = {"from_attributes": True}


class RiskRanking(BaseModel):
    """Ranked list of consumers by risk score (for investigation prioritization)."""

    rankings: List[RiskScoreResponse]
    total_consumers: int
    high_risk_count: int
    critical_count: int
    last_calculated: datetime
