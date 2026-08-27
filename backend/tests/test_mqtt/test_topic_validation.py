"""
KAVACHGRID 3.0 — Unit Tests for MQTT Topic Validation
Phase 3 / Phase 14: Testing topic parsing, regex matching, and payload correlation.
"""

import pytest

from app.mqtt.topics import (
    TYPE_ALERT,
    TYPE_COMMAND,
    TYPE_CONSUMER,
    TYPE_FEEDER,
    TYPE_LOCALIZATION,
    TYPE_UNKNOWN,
    get_alert_topic,
    get_command_topic,
    get_consumer_topic,
    get_feeder_topic,
    get_localization_topic,
    validate_payload_topic_match,
    validate_topic,
)


class TestTopicValidation:
    """Test suite for topic hierarchy validation and parsing."""

    def test_valid_feeder_topics(self):
        res1 = validate_topic("kavachgrid/feeder")
        assert res1.is_valid is True
        assert res1.topic_type == TYPE_FEEDER
        assert res1.device_id == "FEEDER-01"

        res2 = validate_topic("kavachgrid/feeder/feeder-02")
        assert res2.is_valid is True
        assert res2.topic_type == TYPE_FEEDER
        assert res2.device_id == "feeder-02"

    def test_valid_consumer_topics(self):
        res1 = validate_topic("kavachgrid/meter/h1")
        assert res1.is_valid is True
        assert res1.topic_type == TYPE_CONSUMER
        assert res1.device_id == "h1"

        res2 = validate_topic("kavachgrid/meter/consumer-h2")
        assert res2.is_valid is True
        assert res2.topic_type == TYPE_CONSUMER
        assert res2.device_id == "consumer-h2"

        res3 = validate_topic("kavachgrid/consumer/h3")
        assert res3.is_valid is True
        assert res3.topic_type == TYPE_CONSUMER
        assert res3.device_id == "h3"

    def test_valid_localization_topics(self):
        res = validate_topic("kavachgrid/localization/zone1")
        assert res.is_valid is True
        assert res.topic_type == TYPE_LOCALIZATION
        assert res.zone_id == "zone1"
        assert res.device_id == "LOC-ZONE1"

        res2 = validate_topic("kavachgrid/localization/zone-a")
        assert res2.is_valid is True
        assert res2.zone_id == "zone-a"

    def test_valid_alert_topics(self):
        res1 = validate_topic("kavachgrid/alerts")
        assert res1.is_valid is True
        assert res1.topic_type == TYPE_ALERT
        assert res1.device_id is None

        res2 = validate_topic("kavachgrid/alerts/consumer-h1")
        assert res2.is_valid is True
        assert res2.topic_type == TYPE_ALERT
        assert res2.device_id == "consumer-h1"

    def test_valid_command_topics(self):
        res = validate_topic("kavachgrid/commands/feeder-01")
        assert res.is_valid is True
        assert res.topic_type == TYPE_COMMAND
        assert res.device_id == "feeder-01"

    def test_invalid_wildcards(self):
        res1 = validate_topic("kavachgrid/#")
        assert res1.is_valid is False
        assert "wildcard" in res1.error_message.lower()

        res2 = validate_topic("kavachgrid/meter/+")
        assert res2.is_valid is False
        assert "wildcard" in res2.error_message.lower()

    def test_invalid_namespace(self):
        res = validate_topic("othergrid/feeder")
        assert res.is_valid is False
        assert res.topic_type == TYPE_UNKNOWN

    def test_empty_or_malformed_topics(self):
        assert validate_topic("").is_valid is False
        assert validate_topic(None).is_valid is False
        assert validate_topic("kavachgrid/unknown/extra/levels/foo").is_valid is False

    def test_payload_topic_matching(self):
        assert validate_payload_topic_match("kavachgrid/meter/h1", "CONSUMER-H1") is True
        assert validate_payload_topic_match("kavachgrid/meter/h1", "h1") is True
        assert validate_payload_topic_match("kavachgrid/feeder", "FEEDER-01") is True
        assert validate_payload_topic_match("kavachgrid/localization/zone-a", "LOC-ZONE-A") is True

        assert validate_payload_topic_match("kavachgrid/meter/h1", "FEEDER-01") is False
        assert validate_payload_topic_match("kavachgrid/feeder", "CONSUMER-H1") is False

    def test_topic_formatters(self):
        assert get_feeder_topic() == "kavachgrid/feeder"
        assert get_feeder_topic("FEEDER-02") == "kavachgrid/feeder/feeder-02"
        assert get_consumer_topic("CONSUMER-H1") == "kavachgrid/meter/h1"
        assert get_consumer_topic("h2") == "kavachgrid/meter/h2"
        assert get_localization_topic("ZONE-A") == "kavachgrid/localization/zonea"
        assert get_alert_topic() == "kavachgrid/alerts"
        assert get_alert_topic("CONSUMER-H1") == "kavachgrid/alerts/consumer-h1"
        assert get_command_topic("FEEDER-01") == "kavachgrid/commands/feeder-01"
