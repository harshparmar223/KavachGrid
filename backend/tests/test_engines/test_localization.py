"""
KAVACHGRID 3.0 — Progressive Localization Engine Unit Tests
Phase 11: Tests for investigation area narrowing

Tests:
    1. Priority assignment thresholds
    2. Suspect reason generation
    3. Action recommendation logic
    4. Confidence calculation components
    5. Suspicion score formula
"""

import pytest
from unittest.mock import MagicMock
from datetime import datetime, timezone

from app.engines.localization import (
    LocalizationEngine,
    SuspectAnalysis,
    MIN_IMBALANCE_THRESHOLD,
    PRIORITY_CRITICAL_CONFIDENCE,
    PRIORITY_HIGH_CONFIDENCE,
    PRIORITY_MEDIUM_CONFIDENCE,
)


@pytest.fixture
def engine():
    return LocalizationEngine()


class TestPriorityAssignment:
    """Test investigation priority assignment."""

    def test_critical_priority(self, engine):
        # High confidence + high loss
        priority = engine._assign_priority(confidence=0.9, estimated_loss_kwh=5.0)
        assert priority == "critical"

    def test_high_priority(self, engine):
        priority = engine._assign_priority(confidence=0.7, estimated_loss_kwh=2.0)
        assert priority == "high"

    def test_medium_priority(self, engine):
        priority = engine._assign_priority(confidence=0.55, estimated_loss_kwh=2.0)
        assert priority == "medium"

    def test_low_priority(self, engine):
        priority = engine._assign_priority(confidence=0.2, estimated_loss_kwh=0.1)
        assert priority == "low"

    def test_high_loss_boosts_priority(self, engine):
        """Even moderate confidence with very high loss should boost priority."""
        priority = engine._assign_priority(confidence=0.5, estimated_loss_kwh=10.0)
        # 0.5 * 0.7 + 1.0 * 0.3 = 0.65 → high
        assert priority == "high"


class TestSuspectReasonGeneration:
    """Test human-readable suspect reason generation."""

    def test_high_risk_high_deviation(self, engine):
        reason = engine._generate_suspect_reason("H1", risk_score=80.0, energy_deviation=60.0, suspicion=72.0)
        assert "high composite risk" in reason
        assert "significant energy" in reason

    def test_moderate_factors(self, engine):
        reason = engine._generate_suspect_reason("H2", risk_score=50.0, energy_deviation=30.0, suspicion=42.0)
        assert "elevated" in reason
        assert "moderate energy" in reason

    def test_low_suspicion(self, engine):
        reason = engine._generate_suspect_reason("H3", risk_score=10.0, energy_deviation=5.0, suspicion=8.0)
        assert "normal parameters" in reason.lower() or "Low suspicion" in reason

    def test_reason_always_returns_string(self, engine):
        reason = engine._generate_suspect_reason("H4", risk_score=0.0, energy_deviation=0.0, suspicion=0.0)
        assert isinstance(reason, str)
        assert len(reason) > 0


class TestActionRecommendation:
    """Test investigation action recommendations."""

    def test_immediate_inspection(self, engine):
        assert engine._recommend_action(80.0) == "immediate_field_inspection"

    def test_field_inspection(self, engine):
        assert engine._recommend_action(55.0) == "field_inspection"

    def test_enhanced_monitoring(self, engine):
        assert engine._recommend_action(35.0) == "enhanced_monitoring"

    def test_routine_monitoring(self, engine):
        assert engine._recommend_action(10.0) == "routine_monitoring"

    def test_boundary_75(self, engine):
        assert engine._recommend_action(75.0) == "immediate_field_inspection"

    def test_boundary_50(self, engine):
        assert engine._recommend_action(50.0) == "field_inspection"

    def test_boundary_30(self, engine):
        assert engine._recommend_action(30.0) == "enhanced_monitoring"


class TestSuspectAnalysis:
    """Test the SuspectAnalysis data class."""

    def test_to_suspect_device_conversion(self):
        analysis = SuspectAnalysis(
            device_id="CONSUMER-H1",
            suspicion_score=72.456,
            risk_score=65.0,
            energy_deviation=45.0,
            reason="High risk + energy gap",
            recommended_action="field_inspection",
        )

        sd = analysis.to_suspect_device()
        assert sd.device_id == "CONSUMER-H1"
        assert sd.suspicion_score == 72.46  # Rounded to 2 decimal places
        assert sd.reason == "High risk + energy gap"
        assert sd.recommended_action == "field_inspection"


class TestConfidenceCalculation:
    """Test confidence score components."""

    def test_high_imbalance_high_spread(self, engine):
        """High imbalance + clear standout suspect → high confidence."""
        mock_balance = MagicMock()
        mock_balance.unaccounted_power = 800.0

        suspects = [
            SuspectAnalysis("H1", 85.0, 80.0, 70.0, "r", "a"),
            SuspectAnalysis("H2", 20.0, 15.0, 10.0, "r", "a"),
            SuspectAnalysis("H3", 10.0, 10.0, 5.0, "r", "a"),
        ]

        consumers = [MagicMock(), MagicMock(), MagicMock()]

        confidence = engine._calculate_confidence(mock_balance, suspects, consumers)
        assert confidence > 0.6  # Should be fairly high

    def test_low_imbalance(self, engine):
        """Low imbalance → low confidence."""
        mock_balance = MagicMock()
        mock_balance.unaccounted_power = 50.0

        suspects = [
            SuspectAnalysis("H1", 40.0, 30.0, 25.0, "r", "a"),
            SuspectAnalysis("H2", 35.0, 25.0, 20.0, "r", "a"),
        ]

        consumers = [MagicMock(), MagicMock()]

        confidence = engine._calculate_confidence(mock_balance, suspects, consumers)
        assert confidence < 0.5  # Should be lower

    def test_confidence_bounded_zero_to_one(self, engine):
        """Confidence should always be between 0 and 1."""
        mock_balance = MagicMock()
        mock_balance.unaccounted_power = 10000.0

        suspects = [
            SuspectAnalysis("H1", 99.0, 95.0, 90.0, "r", "a"),
            SuspectAnalysis("H2", 5.0, 5.0, 5.0, "r", "a"),
        ]

        consumers = [MagicMock(), MagicMock()]

        confidence = engine._calculate_confidence(mock_balance, suspects, consumers)
        assert 0.0 <= confidence <= 1.0
