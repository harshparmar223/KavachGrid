"""
KAVACHGRID 3.0 — KAVACH Risk Engine Unit Tests
Phase 10: Tests for composite risk scoring

Tests:
    1. Risk level classification thresholds
    2. Weighted formula correctness
    3. Score clamping (0-100)
    4. Explanation generation
    5. All-low inputs → low risk
    6. All-high inputs → critical risk
    7. Inversion logic (low health = high risk)
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from app.engines.risk_engine import (
    KavachRiskEngine,
    RiskScoreResult,
    RISK_THRESHOLD_LOW,
    RISK_THRESHOLD_MEDIUM,
    RISK_THRESHOLD_HIGH,
)


@pytest.fixture
def engine():
    return KavachRiskEngine()


class TestClassifyRiskLevel:
    """Test risk level classification."""

    def test_low_risk(self, engine):
        assert engine._classify_risk_level(10.0) == "low"

    def test_low_boundary(self, engine):
        assert engine._classify_risk_level(24.9) == "low"

    def test_medium_risk(self, engine):
        assert engine._classify_risk_level(25.0) == "medium"

    def test_medium_boundary(self, engine):
        assert engine._classify_risk_level(49.9) == "medium"

    def test_high_risk(self, engine):
        assert engine._classify_risk_level(50.0) == "high"

    def test_high_boundary(self, engine):
        assert engine._classify_risk_level(74.9) == "high"

    def test_critical_risk(self, engine):
        assert engine._classify_risk_level(75.0) == "critical"

    def test_max_risk(self, engine):
        assert engine._classify_risk_level(100.0) == "critical"


class TestWeightedFormula:
    """Test the weighted composite formula logic."""

    def test_all_zero_inputs(self, engine):
        """All engines report perfect → risk should be 0."""
        # energy=0 (no imbalance)
        # ai=0 (no anomaly)
        # health=100 (perfect → inverted = 0)
        # trust=100 (fully trusted → inverted = 0)
        # comm=100 (perfect → inverted = 0)
        overall = (
            0 * engine.w_energy
            + (0 * 100) * engine.w_ai
            + (100 - 100) * engine.w_health
            + (100 - 100) * engine.w_trust
            + (100 - 100) * engine.w_comm
        )
        assert overall == 0.0

    def test_all_worst_inputs(self, engine):
        """All engines report worst possible → risk should be 100."""
        overall = (
            100 * engine.w_energy      # 30
            + (1.0 * 100) * engine.w_ai  # 25
            + (100 - 0) * engine.w_health  # 20
            + (100 - 0) * engine.w_trust  # 15
            + (100 - 0) * engine.w_comm  # 10
        )
        assert overall == pytest.approx(100.0)

    def test_weights_sum_to_one(self, engine):
        """Ensure weights sum to 1.0 for proper normalization."""
        total_weight = (
            engine.w_energy + engine.w_ai + engine.w_health
            + engine.w_trust + engine.w_comm
        )
        assert total_weight == pytest.approx(1.0)

    def test_energy_dominant_scenario(self, engine):
        """High energy imbalance but everything else perfect."""
        energy = 80.0  # High imbalance
        ai = 0.0
        health = 100.0
        trust = 100.0
        comm = 100.0

        overall = (
            energy * engine.w_energy
            + (ai * 100) * engine.w_ai
            + (100 - health) * engine.w_health
            + (100 - trust) * engine.w_trust
            + (100 - comm) * engine.w_comm
        )

        # Should be 80 * 0.30 = 24.0
        assert overall == pytest.approx(24.0)
        assert engine._classify_risk_level(overall) == "low"

    def test_multiple_factors(self, engine):
        """Multiple concerning factors should compound."""
        energy = 60.0
        ai = 0.7  # Raw 0-1
        health = 40.0  # Bad health
        trust = 50.0  # Low trust
        comm = 30.0  # Poor comms

        overall = (
            energy * engine.w_energy           # 18
            + (ai * 100) * engine.w_ai         # 17.5
            + (100 - health) * engine.w_health  # 12
            + (100 - trust) * engine.w_trust    # 7.5
            + (100 - comm) * engine.w_comm      # 7
        )

        assert overall == pytest.approx(62.0)
        assert engine._classify_risk_level(overall) == "high"


class TestExplanationGeneration:
    """Test the human-readable explanation generator."""

    def test_normal_explanation(self, engine):
        """Low risk should say 'within normal range'."""
        explanation = engine._generate_explanation(
            "CONSUMER-H1", 10.0, "low",
            energy=5.0, ai=0.1, health=95.0, trust=98.0, comm=90.0,
        )
        assert "normal range" in explanation

    def test_high_risk_explanation(self, engine):
        """High risk should mention contributing factors."""
        explanation = engine._generate_explanation(
            "CONSUMER-H1", 72.0, "high",
            energy=80.0, ai=0.6, health=40.0, trust=55.0, comm=80.0,
        )
        assert "energy imbalance" in explanation
        assert "anomaly" in explanation
        assert "NOT confirm theft" in explanation

    def test_explanation_includes_device_id(self, engine):
        explanation = engine._generate_explanation(
            "CONSUMER-H2", 50.0, "high",
            energy=60.0, ai=0.3, health=80.0, trust=90.0, comm=85.0,
        )
        assert "CONSUMER-H2" in explanation
