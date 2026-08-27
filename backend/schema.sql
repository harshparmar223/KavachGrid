-- ============================================
-- KAVACHGRID 3.0 — Database Schema
-- PostgreSQL 15
-- Run: psql -U kavach_admin -d kavachgrid -f schema.sql
-- ============================================

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- 1. Users
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username        VARCHAR(50) UNIQUE NOT NULL,
    email           VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name       VARCHAR(100) NOT NULL,
    role            VARCHAR(20) NOT NULL DEFAULT 'viewer'
                    CHECK (role IN ('admin', 'operator', 'investigator', 'viewer')),
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_login_at   TIMESTAMPTZ
);

-- ============================================
-- 2. Devices
-- ============================================
CREATE TABLE IF NOT EXISTS devices (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    device_id       VARCHAR(50) UNIQUE NOT NULL,
    device_type     VARCHAR(20) NOT NULL
                    CHECK (device_type IN ('feeder', 'consumer', 'localization')),
    name            VARCHAR(100) NOT NULL,
    location        VARCHAR(255),
    latitude        DOUBLE PRECISION,
    longitude       DOUBLE PRECISION,
    api_key         VARCHAR(255) NOT NULL,
    status          VARCHAR(20) NOT NULL DEFAULT 'offline'
                    CHECK (status IN ('online', 'offline', 'warning')),
    zone_id         VARCHAR(50),
    metadata        JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen_at    TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_devices_zone ON devices (zone_id);

-- ============================================
-- 3. Telemetry (High-Volume)
-- ============================================
CREATE TABLE IF NOT EXISTS telemetry (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    device_id       VARCHAR(50) NOT NULL REFERENCES devices(device_id) ON DELETE CASCADE,
    voltage         DOUBLE PRECISION NOT NULL,
    current         DOUBLE PRECISION NOT NULL,
    power           DOUBLE PRECISION NOT NULL,
    energy          DOUBLE PRECISION NOT NULL,
    power_factor    DOUBLE PRECISION,
    frequency       DOUBLE PRECISION,
    trust_score     DOUBLE PRECISION,
    anomaly_score   DOUBLE PRECISION,
    raw_payload     JSONB,
    timestamp       TIMESTAMPTZ NOT NULL,
    received_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_telemetry_device_time ON telemetry (device_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_telemetry_timestamp ON telemetry (timestamp DESC);

-- ============================================
-- 4. Alerts
-- ============================================
CREATE TABLE IF NOT EXISTS alerts (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    device_id       VARCHAR(50) REFERENCES devices(device_id) ON DELETE SET NULL,
    alert_type      VARCHAR(30) NOT NULL
                    CHECK (alert_type IN ('energy_imbalance', 'anomaly', 'meter_health',
                                          'device_trust', 'communication', 'localization')),
    severity        VARCHAR(10) NOT NULL
                    CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    title           VARCHAR(200) NOT NULL,
    message         TEXT NOT NULL,
    details         JSONB,
    acknowledged    BOOLEAN NOT NULL DEFAULT FALSE,
    acknowledged_by UUID REFERENCES users(id) ON DELETE SET NULL,
    acknowledged_at TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_alerts_device ON alerts (device_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_unacked ON alerts (acknowledged, severity);

-- ============================================
-- 5. Risk Scores
-- ============================================
CREATE TABLE IF NOT EXISTS risk_scores (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    device_id               VARCHAR(50) NOT NULL REFERENCES devices(device_id) ON DELETE CASCADE,
    overall_score           DOUBLE PRECISION NOT NULL,
    energy_balance_score    DOUBLE PRECISION NOT NULL,
    ai_anomaly_score        DOUBLE PRECISION NOT NULL,
    meter_health_score      DOUBLE PRECISION NOT NULL,
    device_trust_score      DOUBLE PRECISION NOT NULL,
    comm_reliability_score  DOUBLE PRECISION NOT NULL,
    risk_level              VARCHAR(10) NOT NULL
                            CHECK (risk_level IN ('low', 'medium', 'high', 'critical')),
    details                 JSONB,
    calculated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_risk_device_time ON risk_scores (device_id, calculated_at DESC);
CREATE INDEX IF NOT EXISTS idx_risk_level ON risk_scores (risk_level, overall_score DESC);

-- ============================================
-- 6. Localization Results
-- ============================================
CREATE TABLE IF NOT EXISTS localization_results (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    zone_id             VARCHAR(50) NOT NULL,
    confidence          DOUBLE PRECISION NOT NULL,
    priority            VARCHAR(10) NOT NULL
                        CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    estimated_loss_kwh  DOUBLE PRECISION,
    suspect_devices     JSONB NOT NULL DEFAULT '[]',
    investigation_notes TEXT,
    status              VARCHAR(20) NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending', 'investigating', 'resolved', 'false_alarm')),
    resolved_by         UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_localization_zone ON localization_results (zone_id);

-- ============================================
-- 7. Audit Logs
-- ============================================
CREATE TABLE IF NOT EXISTS audit_logs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID REFERENCES users(id) ON DELETE SET NULL,
    action          VARCHAR(50) NOT NULL,
    resource_type   VARCHAR(30) NOT NULL,
    resource_id     VARCHAR(50),
    details         JSONB,
    ip_address      VARCHAR(45),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_logs (user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_resource ON audit_logs (resource_type, resource_id);

-- ============================================
-- Done
-- ============================================
-- Total: 7 tables, 12 indexes, 10 check constraints
