"""
KAVACHGRID 3.0 — Energy Balance Engine Unit Tests
Phase 6: Tests for unaccounted energy detection

Tests:
    1. Perfect balance → score 0, no alert
    2. Minor imbalance (below threshold) → score > 0, no alert
    3. Low imbalance → low alert
    4. Medium imbalance → medium alert
    5. High imbalance → high alert
    6. Critical imbalance → critical alert
    7. Negative imbalance (consumers > feeder) → clamped to 0
    8. No feeder data → returns None
    9. No consumer data → returns None
    10. Per-consumer deviation scoring
    11. Score normalization stays within 0-100
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from app.engines.energy_balance import (
    EnergyBalanceEngine,
    EnergyBalanceResult,
    TECHNICAL_LOSS_PERCENT,
    ALERT_THRESHOLD_LOW,
    ALERT_THRESHOLD_MEDIUM,
    ALERT_THRESHOLD_HIGH,
    ALERT_THRESHOLD_CRITICAL,
    MIN_FEEDER_POWER,
)


@pytest.fixture
def engine():
    """Create a fresh engine instance for each test."""
    return EnergyBalanceEngine()


class TestComputeBalance:
    """Test the core _compute_balance method directly."""

    def test_perfect_balance(self, engine):
        """When consumers + loss == feeder, score should be 0."""
        feeder = 1000.0
        expected_loss = feeder * TECHNICAL_LOSS_PERCENT  # 50W
        consumers_total = feeder - expected_loss  # 950W

        result = engine._compute_balance(
            feeder_power=feeder,
            total_consumer_power=consumers_total,
            consumer_breakdown={"H1": 475.0, "H2": 475.0},
            zone_id="ZONE-A",
            timestamp=datetime.now(timezone.utc),
        )

        assert result.unaccounted_power == pytest.approx(0.0, abs=0.1)
        assert result.imbalance_score == pytest.approx(0.0, abs=0.1)
        assert result.severity is None  # No alert

    def test_minor_imbalance_below_threshold(self, engine):
        """5% imbalance should produce a score but no alert (below 10%)."""
        feeder = 2000.0
        # Consumers use only 1800W, loss = 100W → 100W unaccounted (5%)
        consumers_total = 1800.0

        result = engine._compute_balance(
            feeder_power=feeder,
            total_consumer_power=consumers_total,
            consumer_breakdown={"H1": 900.0, "H2": 900.0},
            zone_id="ZONE-A",
            timestamp=datetime.now(timezone.utc),
        )

        assert result.unaccounted_power > 0
        assert result.imbalance_score > 0
        assert result.severity is None  # Below ALERT_THRESHOLD_LOW (10%)

    def test_low_severity_alert(self, engine):
        """12% imbalance should trigger a low alert."""
        feeder = 2000.0
        # 12% of 2000 = 240W unaccounted
        expected_loss = feeder * TECHNICAL_LOSS_PERCENT
        consumers_total = feeder - expected_loss - 240.0

        result = engine._compute_balance(
            feeder_power=feeder,
            total_consumer_power=consumers_total,
            consumer_breakdown={"H1": consumers_total},
            zone_id="ZONE-A",
            timestamp=datetime.now(timezone.utc),
        )

        assert result.severity == "low"

    def test_medium_severity_alert(self, engine):
        """20% imbalance should trigger a medium alert."""
        feeder = 2000.0
        expected_loss = feeder * TECHNICAL_LOSS_PERCENT
        unaccounted_target = feeder * 0.20  # 400W
        consumers_total = feeder - expected_loss - unaccounted_target

        result = engine._compute_balance(
            feeder_power=feeder,
            total_consumer_power=consumers_total,
            consumer_breakdown={"H1": consumers_total},
            zone_id="ZONE-A",
            timestamp=datetime.now(timezone.utc),
        )

        assert result.severity == "medium"

    def test_high_severity_alert(self, engine):
        """30% imbalance should trigger a high alert."""
        feeder = 2000.0
        expected_loss = feeder * TECHNICAL_LOSS_PERCENT
        unaccounted_target = feeder * 0.30
        consumers_total = feeder - expected_loss - unaccounted_target

        result = engine._compute_balance(
            feeder_power=feeder,
            total_consumer_power=consumers_total,
            consumer_breakdown={"H1": consumers_total},
            zone_id="ZONE-A",
            timestamp=datetime.now(timezone.utc),
        )

        assert result.severity == "high"

    def test_critical_severity_alert(self, engine):
        """45% imbalance should trigger a critical alert."""
        feeder = 2000.0
        expected_loss = feeder * TECHNICAL_LOSS_PERCENT
        unaccounted_target = feeder * 0.45
        consumers_total = feeder - expected_loss - unaccounted_target

        result = engine._compute_balance(
            feeder_power=feeder,
            total_consumer_power=consumers_total,
            consumer_breakdown={"H1": consumers_total},
            zone_id="ZONE-A",
            timestamp=datetime.now(timezone.utc),
        )

        assert result.severity == "critical"

    def test_negative_imbalance_clamped(self, engine):
        """If consumers report MORE than feeder, unaccounted should be 0."""
        feeder = 1000.0
        consumers_total = 1200.0  # More than feeder!

        result = engine._compute_balance(
            feeder_power=feeder,
            total_consumer_power=consumers_total,
            consumer_breakdown={"H1": 600.0, "H2": 600.0},
            zone_id="ZONE-A",
            timestamp=datetime.now(timezone.utc),
        )

        assert result.unaccounted_power == 0.0
        assert result.imbalance_score == 0.0
        assert result.severity is None

    def test_score_never_exceeds_100(self, engine):
        """Even with 100% loss, score should cap at 100."""
        feeder = 2000.0
        consumers_total = 0.0  # No consumer readings at all

        result = engine._compute_balance(
            feeder_power=feeder,
            total_consumer_power=consumers_total,
            consumer_breakdown={},
            zone_id="ZONE-A",
            timestamp=datetime.now(timezone.utc),
        )

        assert result.imbalance_score <= 100.0

    def test_result_to_dict_serialization(self, engine):
        """Verify the result can be serialized to a dict for JSONB storage."""
        result = engine._compute_balance(
            feeder_power=2000.0,
            total_consumer_power=1500.0,
            consumer_breakdown={"H1": 800.0, "H2": 700.0},
            zone_id="ZONE-A",
            timestamp=datetime.now(timezone.utc),
        )

        d = result.to_dict()
        assert "feeder_power_w" in d
        assert "total_consumer_power_w" in d
        assert "unaccounted_power_w" in d
        assert "imbalance_score" in d
        assert "consumer_breakdown" in d
        assert isinstance(d["consumer_breakdown"], dict)


class TestClassifySeverity:
    """Test the severity classification thresholds."""

    def test_below_all_thresholds(self, engine):
        assert engine._classify_severity(0.05) is None

    def test_low_threshold(self, engine):
        assert engine._classify_severity(ALERT_THRESHOLD_LOW) == "low"

    def test_medium_threshold(self, engine):
        assert engine._classify_severity(ALERT_THRESHOLD_MEDIUM) == "medium"

    def test_high_threshold(self, engine):
        assert engine._classify_severity(ALERT_THRESHOLD_HIGH) == "high"

    def test_critical_threshold(self, engine):
        assert engine._classify_severity(ALERT_THRESHOLD_CRITICAL) == "critical"

    def test_exact_boundary_low(self, engine):
        """At exactly 10%, should trigger low."""
        assert engine._classify_severity(0.10) == "low"

    def test_just_below_low(self, engine):
        """At 9.99%, should NOT trigger."""
        assert engine._classify_severity(0.099) is None
