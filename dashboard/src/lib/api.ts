// KAVACHGRID 3.0 — API Client. Phase 12.
import axios from 'axios';
import {
  Device,
  Telemetry,
  Alert,
  AlertSummary,
  RiskScore,
  RiskRanking,
  LocalizationResult,
} from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
const httpClient = axios.create({ timeout: 2500 });

// ---------- Mock Data Store (Fallback) ----------
export const mockDevices: Device[] = [
  {
    id: 'd1',
    device_id: 'feeder_01',
    device_type: 'feeder',
    name: 'Feeder Transformer A',
    location: 'Substation A, Sector 4',
    latitude: 28.6139,
    longitude: 77.2090,
    api_key: 'key_feeder_01',
    status: 'online',
    zone_id: 'zone_A',
    metadata: { capacity_kva: 500, install_year: 2022 },
    created_at: new Date(Date.now() - 30 * 24 * 3600 * 1000).toISOString(),
    updated_at: new Date().toISOString(),
    last_seen_at: new Date().toISOString(),
  },
  {
    id: 'd2',
    device_id: 'meter_101',
    device_type: 'consumer',
    name: 'Consumer Block A - Apt 101',
    location: 'Apartment 101, Block A, Sector 4',
    latitude: 28.6145,
    longitude: 77.2105,
    api_key: 'key_meter_101',
    status: 'online',
    zone_id: 'zone_A',
    metadata: { phase: 'single', max_load_kw: 10 },
    created_at: new Date(Date.now() - 30 * 24 * 3600 * 1000).toISOString(),
    updated_at: new Date().toISOString(),
    last_seen_at: new Date().toISOString(),
  },
  {
    id: 'd3',
    device_id: 'meter_102',
    device_type: 'consumer',
    name: 'Consumer Block A - Apt 102',
    location: 'Apartment 102, Block A, Sector 4',
    latitude: 28.6130,
    longitude: 77.2110,
    api_key: 'key_meter_102',
    status: 'warning',
    zone_id: 'zone_A',
    metadata: { phase: 'single', max_load_kw: 10 },
    created_at: new Date(Date.now() - 30 * 24 * 3600 * 1000).toISOString(),
    updated_at: new Date().toISOString(),
    last_seen_at: new Date().toISOString(),
  },
  {
    id: 'd4',
    device_id: 'meter_103',
    device_type: 'consumer',
    name: 'Commercial Shop 103',
    location: 'Shop 103, Market Complex, Sector 4',
    latitude: 28.6150,
    longitude: 77.2075,
    api_key: 'key_meter_103',
    status: 'warning',
    zone_id: 'zone_A',
    metadata: { phase: 'three', max_load_kw: 30 },
    created_at: new Date(Date.now() - 30 * 24 * 3600 * 1000).toISOString(),
    updated_at: new Date().toISOString(),
    last_seen_at: new Date().toISOString(),
  },
  {
    id: 'd5',
    device_id: 'meter_104',
    device_type: 'consumer',
    name: 'Consumer Block A - Apt 104',
    location: 'Apartment 104, Block A, Sector 4',
    latitude: 28.6120,
    longitude: 77.2085,
    api_key: 'key_meter_104',
    status: 'online',
    zone_id: 'zone_A',
    metadata: { phase: 'single', max_load_kw: 10 },
    created_at: new Date(Date.now() - 30 * 24 * 3600 * 1000).toISOString(),
    updated_at: new Date().toISOString(),
    last_seen_at: new Date().toISOString(),
  },
  {
    id: 'd6',
    device_id: 'local_sensor_01',
    device_type: 'localization',
    name: 'Zone A Branch Monitor Pole 4',
    location: 'Pole 4, Street 12, Sector 4',
    latitude: 28.6135,
    longitude: 77.2098,
    api_key: 'key_local_sensor_01',
    status: 'online',
    zone_id: 'zone_A',
    metadata: { ct_rating: 100 },
    created_at: new Date(Date.now() - 30 * 24 * 3600 * 1000).toISOString(),
    updated_at: new Date().toISOString(),
    last_seen_at: new Date().toISOString(),
  },
];

export const mockTelemetry: Record<string, Telemetry[]> = {
  feeder_01: Array.from({ length: 20 }).map((_, i) => ({
    id: `tf-${i}`,
    device_id: 'feeder_01',
    voltage: 231.5 + Math.sin(i / 2) * 1.5,
    current: 40.2 + Math.cos(i / 2) * 4.1,
    power: 9.3 + Math.sin(i / 2) * 0.8, // kW
    energy: 1245.5 + i * 2.5,
    power_factor: 0.95 + Math.sin(i) * 0.02,
    frequency: 49.98 + Math.cos(i) * 0.05,
    trust_score: 99.5,
    anomaly_score: 0.05,
    timestamp: new Date(Date.now() - (20 - i) * 60 * 1000).toISOString(),
    received_at: new Date(Date.now() - (20 - i) * 60 * 1000).toISOString(),
  })),
  meter_101: Array.from({ length: 20 }).map((_, i) => ({
    id: `tm1-${i}`,
    device_id: 'meter_101',
    voltage: 228.4 + Math.sin(i / 2) * 2.2,
    current: 4.5 + Math.cos(i / 3) * 0.8,
    power: 1.02 + Math.sin(i / 3) * 0.15,
    energy: 312.2 + i * 0.15,
    power_factor: 0.98,
    frequency: 50.01,
    trust_score: 99.0,
    anomaly_score: 0.02,
    timestamp: new Date(Date.now() - (20 - i) * 60 * 1000).toISOString(),
    received_at: new Date(Date.now() - (20 - i) * 60 * 1000).toISOString(),
  })),
  meter_102: Array.from({ length: 20 }).map((_, i) => ({
    id: `tm2-${i}`,
    device_id: 'meter_102',
    voltage: 229.1 + Math.sin(i / 2) * 2.0,
    current: 6.2 + Math.cos(i / 2) * 2.5,
    power: 1.42 + Math.sin(i / 2) * 0.5,
    energy: 410.8 + i * 0.22,
    power_factor: 0.97,
    frequency: 50.02,
    trust_score: 75.0, // Compromised trust
    anomaly_score: 0.15,
    timestamp: new Date(Date.now() - (20 - i) * 60 * 1000).toISOString(),
    received_at: new Date(Date.now() - (20 - i) * 60 * 1000).toISOString(),
  })),
  meter_103: Array.from({ length: 20 }).map((_, i) => {
    const isAnomalous = i > 12; // Simulated anomaly trigger
    return {
      id: `tm3-${i}`,
      device_id: 'meter_103',
      voltage: 225.1 + Math.sin(i / 2) * 4.0,
      current: isAnomalous ? 1.5 : 22.4 + Math.cos(i / 2) * 3.5, // Sudden load drop (bypass indicators)
      power: isAnomalous ? 0.3 : 5.04 + Math.cos(i / 2) * 0.8,
      energy: 985.4 + i * (isAnomalous ? 0.01 : 0.8),
      power_factor: isAnomalous ? 0.65 : 0.92, // Poor power factor during theft
      frequency: 50.02,
      trust_score: isAnomalous ? 25.0 : 95.0,
      anomaly_score: isAnomalous ? 0.92 : 0.08,
      timestamp: new Date(Date.now() - (20 - i) * 60 * 1000).toISOString(),
      received_at: new Date(Date.now() - (20 - i) * 60 * 1000).toISOString(),
    };
  }),
};

export const mockAlerts: Alert[] = [
  {
    id: 'a1',
    device_id: 'feeder_01',
    alert_type: 'energy_imbalance',
    severity: 'high',
    title: 'High Distribution Imbalance Detected',
    message: 'Transformer Feeder A reports 18.5 kW input, but total logged consumer draw is only 12.8 kW (30.8% loss).',
    details: { feeder_load_kw: 18.5, consumer_load_kw: 12.8, loss_percentage: 30.8 },
    acknowledged: false,
    acknowledged_by: null,
    acknowledged_at: null,
    created_at: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
  },
  {
    id: 'a2',
    device_id: 'meter_103',
    alert_type: 'anomaly',
    severity: 'critical',
    title: 'Severe Consumption Anomaly (AI Flagged)',
    message: 'Autoencoder flagged a 94.0% sudden drop in power consumption despite voltage remaining stable. Potential meter bypass.',
    details: { anomaly_score: 0.92, voltage: 226.1, power_prev_kw: 5.1, power_curr_kw: 0.3 },
    acknowledged: false,
    acknowledged_by: null,
    acknowledged_at: null,
    created_at: new Date(Date.now() - 25 * 60 * 1000).toISOString(),
  },
  {
    id: 'a3',
    device_id: 'meter_102',
    alert_type: 'device_trust',
    severity: 'medium',
    title: 'Device Signature / Hash Discrepancy',
    message: 'Telemetry payload verification failed. Cryptographic signature does not match device private key registered in Trust Engine.',
    details: { client_ip: '192.168.1.102', validation_error: 'signature_mismatch' },
    acknowledged: false,
    acknowledged_by: null,
    acknowledged_at: null,
    created_at: new Date(Date.now() - 45 * 60 * 1000).toISOString(),
  },
];

export const mockAlertSummary: AlertSummary = {
  total: 3,
  unacknowledged: 3,
  by_severity: { low: 0, medium: 1, high: 1, critical: 1 },
  by_type: {
    energy_imbalance: 1,
    anomaly: 1,
    device_trust: 1,
    meter_health: 0,
    communication: 0,
    localization: 0,
  },
};

export const mockRiskRanking: RiskRanking = {
  rankings: [
    {
      id: 'r1',
      device_id: 'meter_103',
      overall_score: 88.5,
      energy_balance_score: 95.0,
      ai_anomaly_score: 92.0,
      meter_health_score: 90.0,
      device_trust_score: 95.0,
      comm_reliability_score: 70.0,
      risk_level: 'critical',
      details: { suspect_reason: 'Sudden load drop + bad power factor' },
      calculated_at: new Date().toISOString(),
    },
    {
      id: 'r2',
      device_id: 'meter_102',
      overall_score: 48.0,
      energy_balance_score: 30.0,
      ai_anomaly_score: 15.0,
      meter_health_score: 20.0,
      device_trust_score: 95.0,
      comm_reliability_score: 80.0,
      risk_level: 'medium',
      details: { suspect_reason: 'Signature mismatch warnings' },
      calculated_at: new Date().toISOString(),
    },
    {
      id: 'r3',
      device_id: 'meter_101',
      overall_score: 12.4,
      energy_balance_score: 10.0,
      ai_anomaly_score: 5.0,
      meter_health_score: 8.0,
      device_trust_score: 0.0,
      comm_reliability_score: 99.0,
      risk_level: 'low',
      details: {},
      calculated_at: new Date().toISOString(),
    },
    {
      id: 'r4',
      device_id: 'meter_104',
      overall_score: 8.2,
      energy_balance_score: 5.0,
      ai_anomaly_score: 2.0,
      meter_health_score: 10.0,
      device_trust_score: 0.0,
      comm_reliability_score: 99.0,
      risk_level: 'low',
      details: {},
      calculated_at: new Date().toISOString(),
    },
  ],
  total_consumers: 4,
  high_risk_count: 0,
  critical_count: 1,
  last_calculated: new Date().toISOString(),
};

export const mockLocalization: LocalizationResult[] = [
  {
    id: 'loc-01',
    zone_id: 'zone_A',
    confidence: 94.2,
    priority: 'critical',
    estimated_loss_kwh: 124.5,
    suspect_devices: [
      {
        device_id: 'meter_103',
        suspicion_score: 96.5,
        reason: 'Consumption dropped 95% while line branch monitor CT detects active draw.',
        recommended_action: 'Send investigator to check for physical bypass at main terminal.',
      },
      {
        device_id: 'meter_102',
        suspicion_score: 52.4,
        reason: 'Compromised trust signature telemetry reported nearby on same branch line.',
        recommended_action: 'Audit meter firmware integrity and check connections.',
      },
    ],
    investigation_notes: 'Branch monitoring pole CT indicates active load in street 12, but consumer meter 103 reports almost zero consumption.',
    status: 'pending',
    resolved_by: null,
    created_at: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
    updated_at: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
  },
];

// ---------- Typed API Client ----------
export const api = {
  baseUrl: API_BASE,

  // Devices
  async getDevices(): Promise<Device[]> {
    try {
      const res = await httpClient.get(`${API_BASE}/devices`);
      return res.data;
    } catch {
      return mockDevices;
    }
  },

  async getDevice(deviceId: string): Promise<Device> {
    try {
      const res = await httpClient.get(`${API_BASE}/devices/${deviceId}`);
      return res.data;
    } catch {
      return mockDevices.find((d) => d.device_id === deviceId) || mockDevices[0];
    }
  },

  // Telemetry
  async getLatestTelemetry(): Promise<Telemetry[]> {
    try {
      const res = await httpClient.get(`${API_BASE}/telemetry/latest`);
      return res.data;
    } catch {
      return Object.keys(mockTelemetry).map((k) => mockTelemetry[k][mockTelemetry[k].length - 1]);
    }
  },

  async getHistoricalTelemetry(deviceId: string): Promise<Telemetry[]> {
    try {
      const res = await httpClient.get(`${API_BASE}/telemetry/${deviceId}`);
      return res.data.data || res.data;
    } catch {
      return mockTelemetry[deviceId] || mockTelemetry['meter_101'] || [];
    }
  },

  // Alerts
  async getAlerts(): Promise<Alert[]> {
    try {
      const res = await httpClient.get(`${API_BASE}/alerts`);
      return res.data;
    } catch {
      return mockAlerts;
    }
  },

  async getAlertSummary(): Promise<AlertSummary> {
    try {
      const res = await httpClient.get(`${API_BASE}/alerts/summary`);
      return res.data;
    } catch {
      return mockAlertSummary;
    }
  },

  async acknowledgeAlert(alertId: string): Promise<any> {
    try {
      const res = await httpClient.put(`${API_BASE}/alerts/${alertId}/acknowledge`);
      return res.data;
    } catch {
      const alert = mockAlerts.find((a) => a.id === alertId);
      if (alert) {
        alert.acknowledged = true;
        alert.acknowledged_at = new Date().toISOString();
        alert.acknowledged_by = 'operator-01';
      }
      return { status: 'success', alert_id: alertId };
    }
  },

  // Risk Scores
  async getRiskRanking(): Promise<RiskRanking> {
    try {
      const res = await httpClient.get(`${API_BASE}/risk/ranking`);
      return res.data;
    } catch {
      return mockRiskRanking;
    }
  },

  async getRiskBreakdown(deviceId: string): Promise<RiskScore> {
    try {
      const res = await httpClient.get(`${API_BASE}/risk/${deviceId}`);
      return res.data;
    } catch {
      return (
        mockRiskRanking.rankings.find((r) => r.device_id === deviceId) ||
        mockRiskRanking.rankings[0]
      );
    }
  },

  // Localization
  async getLocalization(): Promise<LocalizationResult[]> {
    try {
      const res = await httpClient.get(`${API_BASE}/localization`);
      return res.data;
    } catch {
      return mockLocalization;
    }
  },

  async updateLocalizationStatus(resultId: string, status: string, notes: string): Promise<any> {
    try {
      const res = await httpClient.put(`${API_BASE}/localization/${resultId}`, { status, investigation_notes: notes });
      return res.data;
    } catch {
      const result = mockLocalization.find((l) => l.id === resultId);
      if (result) {
        result.status = status as any;
        result.investigation_notes = notes;
        result.updated_at = new Date().toISOString();
      }
      return { status: 'success', result_id: resultId };
    }
  },
};
