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
  GisTopologyResponse,
  GisNode,
  GisLocationUpdate,
} from './types';

const rawBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const API_BASE = rawBase.endsWith('/api/v1') ? rawBase : `${rawBase.replace(/\/+$/, '')}/api/v1`;
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

export const mockGisTopology: GisTopologyResponse = {
  nodes: [
    {
      device_id: 'feeder_01',
      name: 'Feeder Transformer A',
      device_type: 'feeder',
      location: 'Substation A, Sector 4',
      latitude: 28.6139,
      longitude: 77.2090,
      zone_id: 'zone_A',
      status: 'online',
      voltage: 231.5,
      current: 40.2,
      power: 9.3,
      power_factor: 0.95,
      energy: 1245.5,
      trust_score: 99.5,
      anomaly_score: 0.05,
      overall_risk: 10.0,
      risk_level: 'low',
      active_alerts_count: 1,
      last_seen_at: new Date().toISOString(),
    },
    {
      device_id: 'local_sensor_01',
      name: 'Zone A Branch Monitor Pole 4',
      device_type: 'localization',
      location: 'Pole 4, Street 12, Sector 4',
      latitude: 28.6135,
      longitude: 77.2098,
      zone_id: 'zone_A',
      status: 'online',
      voltage: 230.0,
      current: 28.5,
      power: 6.5,
      power_factor: 0.96,
      energy: 850.0,
      trust_score: 98.0,
      anomaly_score: 0.1,
      overall_risk: 25.0,
      risk_level: 'low',
      active_alerts_count: 0,
      last_seen_at: new Date().toISOString(),
    },
    {
      device_id: 'meter_101',
      name: 'Consumer Block A - Apt 101',
      device_type: 'consumer',
      location: 'Apartment 101, Block A, Sector 4',
      latitude: 28.6145,
      longitude: 77.2105,
      zone_id: 'zone_A',
      status: 'online',
      voltage: 228.4,
      current: 4.5,
      power: 1.02,
      power_factor: 0.98,
      energy: 312.2,
      trust_score: 99.0,
      anomaly_score: 0.02,
      overall_risk: 12.4,
      risk_level: 'low',
      active_alerts_count: 0,
      last_seen_at: new Date().toISOString(),
    },
    {
      device_id: 'meter_102',
      name: 'Consumer Block A - Apt 102',
      device_type: 'consumer',
      location: 'Apartment 102, Block A, Sector 4',
      latitude: 28.6130,
      longitude: 77.2110,
      zone_id: 'zone_A',
      status: 'warning',
      voltage: 229.1,
      current: 6.2,
      power: 1.42,
      power_factor: 0.97,
      energy: 410.8,
      trust_score: 75.0,
      anomaly_score: 0.15,
      overall_risk: 48.0,
      risk_level: 'medium',
      active_alerts_count: 1,
      last_seen_at: new Date().toISOString(),
    },
    {
      device_id: 'meter_103',
      name: 'Commercial Shop 103',
      device_type: 'consumer',
      location: 'Shop 103, Market Complex, Sector 4',
      latitude: 28.6150,
      longitude: 77.2075,
      zone_id: 'zone_A',
      status: 'warning',
      voltage: 225.1,
      current: 1.5,
      power: 0.3,
      power_factor: 0.65,
      energy: 985.4,
      trust_score: 25.0,
      anomaly_score: 0.92,
      overall_risk: 88.5,
      risk_level: 'critical',
      active_alerts_count: 1,
      last_seen_at: new Date().toISOString(),
    },
    {
      device_id: 'meter_104',
      name: 'Consumer Block A - Apt 104',
      device_type: 'consumer',
      location: 'Apartment 104, Block A, Sector 4',
      latitude: 28.6120,
      longitude: 77.2085,
      zone_id: 'zone_A',
      status: 'online',
      voltage: 230.2,
      current: 3.8,
      power: 0.87,
      power_factor: 0.98,
      energy: 290.0,
      trust_score: 99.0,
      anomaly_score: 0.03,
      overall_risk: 8.2,
      risk_level: 'low',
      active_alerts_count: 0,
      last_seen_at: new Date().toISOString(),
    },
  ],
  edges: [
    {
      id: 'edge-1',
      from_node: 'feeder_01',
      to_node: 'local_sensor_01',
      from_coords: [28.6139, 77.2090],
      to_coords: [28.6135, 77.2098],
      edge_type: 'feeder_to_branch',
      status: 'normal',
      power_flow_kw: 6.5,
      loss_estimated_pct: 1.2,
    },
    {
      id: 'edge-2',
      from_node: 'local_sensor_01',
      to_node: 'meter_101',
      from_coords: [28.6135, 77.2098],
      to_coords: [28.6145, 77.2105],
      edge_type: 'branch_to_consumer',
      status: 'normal',
      power_flow_kw: 1.02,
      loss_estimated_pct: 1.5,
    },
    {
      id: 'edge-3',
      from_node: 'local_sensor_01',
      to_node: 'meter_102',
      from_coords: [28.6135, 77.2098],
      to_coords: [28.6130, 77.2110],
      edge_type: 'branch_to_consumer',
      status: 'warning',
      power_flow_kw: 1.42,
      loss_estimated_pct: 8.5,
    },
    {
      id: 'edge-4',
      from_node: 'feeder_01',
      to_node: 'meter_103',
      from_coords: [28.6139, 77.2090],
      to_coords: [28.6150, 77.2075],
      edge_type: 'feeder_to_consumer',
      status: 'critical',
      power_flow_kw: 0.3,
      loss_estimated_pct: 35.0,
    },
    {
      id: 'edge-5',
      from_node: 'feeder_01',
      to_node: 'meter_104',
      from_coords: [28.6139, 77.2090],
      to_coords: [28.6120, 77.2085],
      edge_type: 'feeder_to_consumer',
      status: 'normal',
      power_flow_kw: 0.87,
      loss_estimated_pct: 1.0,
    },
  ],
  zones: [
    {
      zone_id: 'zone_A',
      total_nodes: 6,
      feeder_id: 'feeder_01',
      feeder_power_kw: 9.3,
      consumer_total_power_kw: 3.61,
      loss_percentage: 61.18,
      critical_nodes_count: 1,
      center_lat: 28.6139,
      center_lng: 77.2090,
    },
  ],
  total_nodes: 6,
  center_lat: 28.6139,
  center_lng: 77.2090,
  generated_at: new Date().toISOString(),
};

// ---------- Typed API Client ----------
export const api = {
  baseUrl: API_BASE,

  // GIS & Topology
  async getGisTopology(zoneId?: string): Promise<GisTopologyResponse> {
    try {
      const url = zoneId ? `${API_BASE}/gis/topology?zone_id=${encodeURIComponent(zoneId)}` : `${API_BASE}/gis/topology`;
      const res = await httpClient.get(url);
      return res.data;
    } catch {
      if (zoneId) {
        return {
          ...mockGisTopology,
          nodes: mockGisTopology.nodes.filter((n) => n.zone_id === zoneId),
          zones: mockGisTopology.zones.filter((z) => z.zone_id === zoneId),
        };
      }
      return mockGisTopology;
    }
  },

  async getGisGeoJson(zoneId?: string): Promise<any> {
    try {
      const url = zoneId ? `${API_BASE}/gis/geojson?zone_id=${encodeURIComponent(zoneId)}` : `${API_BASE}/gis/geojson`;
      const res = await httpClient.get(url);
      return res.data;
    } catch {
      return {
        type: 'FeatureCollection',
        features: mockGisTopology.nodes.map((n) => ({
          type: 'Feature',
          geometry: { type: 'Point', coordinates: [n.longitude, n.latitude] },
          properties: { ...n },
        })),
      };
    }
  },

  async updateDeviceCoordinates(
    deviceId: string,
    data: GisLocationUpdate
  ): Promise<GisNode> {
    try {
      const res = await httpClient.put(`${API_BASE}/gis/devices/${deviceId}/coordinates`, data);
      return res.data;
    } catch {
      const node = mockGisTopology.nodes.find((n) => n.device_id === deviceId);
      if (node) {
        node.latitude = data.latitude;
        node.longitude = data.longitude;
        if (data.location) node.location = data.location;
        if (data.zone_id) node.zone_id = data.zone_id;
      }
      const dev = mockDevices.find((d) => d.device_id === deviceId);
      if (dev) {
        dev.latitude = data.latitude;
        dev.longitude = data.longitude;
        if (data.location) dev.location = data.location;
        if (data.zone_id) dev.zone_id = data.zone_id;
      }
      return node || (mockGisTopology.nodes[0] as GisNode);
    }
  },

  async getGisStats(): Promise<any> {
    try {
      const res = await httpClient.get(`${API_BASE}/gis/stats`);
      return res.data;
    } catch {
      return {
        total_devices: mockDevices.length,
        mapped_devices: mockDevices.filter((d) => d.latitude && d.longitude).length,
        coverage_percentage: 100.0,
        device_breakdown: {
          feeders: mockDevices.filter((d) => d.device_type === 'feeder').length,
          consumers: mockDevices.filter((d) => d.device_type === 'consumer').length,
          localization_nodes: mockDevices.filter((d) => d.device_type === 'localization').length,
        },
      };
    }
  },


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

  async triggerLocalization(): Promise<LocalizationResult[]> {
    try {
      const res = await httpClient.post(`${API_BASE}/localization/trigger`);
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

  // Grid Simulator Controls
  async getSimulatorStatus(): Promise<any> {
    try {
      const res = await httpClient.get(`${API_BASE}/simulator/status`);
      return res.data;
    } catch {
      return {
        is_running: true,
        current_scenario: { id: 1, name: 'Normal Balanced Grid', description: 'Clean baseline grid with <5% loss.', active_theft: false },
        tick_count: 42,
        feeder: { device_id: 'FEEDER-01', name: 'Substation Feeder DT-01', power_w: 9450, voltage: 230.1, current: 41.8, power_factor: 0.98, status: 'online' },
        consumers: [
          { device_id: 'CONSUMER-H1', name: 'House H1 (Sharma)', mode: 'normal', actual_power_w: 2400, reported_power_w: 2400, voltage: 230, current: 10.5, power_factor: 0.98, status: 'online', is_theft_active: false },
          { device_id: 'CONSUMER-H2', name: 'House H2 (Verma)', mode: 'normal', actual_power_w: 2200, reported_power_w: 2200, voltage: 230, current: 9.6, power_factor: 0.98, status: 'online', is_theft_active: false },
          { device_id: 'CONSUMER-H3', name: 'House H3 (Patel)', mode: 'normal', actual_power_w: 2000, reported_power_w: 2000, voltage: 230, current: 8.7, power_factor: 0.98, status: 'online', is_theft_active: false },
          { device_id: 'CONSUMER-H4', name: 'House H4 (Singh)', mode: 'normal', actual_power_w: 2100, reported_power_w: 2100, voltage: 230, current: 9.2, power_factor: 0.98, status: 'online', is_theft_active: false },
        ],
        balance: { feeder_power_w: 9450, total_consumer_w: 8700, technical_loss_w: 472.5, unaccounted_w: 277.5, deficit_pct: 2.9, severity: 'normal' },
        available_scenarios: [
          { id: 1, name: 'Normal Balanced Grid', description: 'All 4 consumers consume legitimate power (<5% loss).', severity: 'normal', active_theft: false },
          { id: 2, name: 'Single Consumer Theft (H2 Bypass)', description: 'House H2 bypasses 75% load. Deficit spikes.', severity: 'critical', active_theft: true, target_device: 'CONSUMER-H2' },
          { id: 3, name: 'Meter Sensor Fault (H3 Stuck 0W)', description: 'House H3 sensor freezes. Health engine generates Maintenance Ticket.', severity: 'warning', active_theft: false, target_device: 'CONSUMER-H3' },
          { id: 4, name: 'Legitimate Load Surge (H1 Peak)', description: 'House H1 surges to 4.5kW. Feeder scales, no false alarm.', severity: 'info', active_theft: false },
          { id: 5, name: 'Communication Dropout (H4 Offline)', description: 'House H4 drops offline. Ring buffer buffers locally.', severity: 'warning', active_theft: false, target_device: 'CONSUMER-H4' },
          { id: 6, name: 'Multi-Node Coordinated Theft (H2 + H4)', description: 'H2 and H4 steal simultaneously. Localization ranks both top.', severity: 'critical', active_theft: true },
        ],
      };
    }
  },

  async getSimulatorStream(): Promise<any[]> {
    try {
      const res = await httpClient.get(`${API_BASE}/simulator/telemetry/stream`);
      return res.data;
    } catch {
      // Generate realistic 15-point baseline buffer
      const now = Date.now();
      return Array.from({ length: 15 }).map((_, i) => {
        const t = new Date(now - (14 - i) * 3000);
        return {
          time: t.toTimeString().split(' ')[0],
          feeder_w: 9450 + Math.sin(i) * 120,
          consumers_sum_w: 8700 + Math.sin(i) * 100,
          expected_loss_w: 472.5,
          unaccounted_gap_w: 277.5,
          deficit_pct: 2.9,
          h1_w: 2400 + Math.random() * 50,
          h2_w: 2200 + Math.random() * 50,
          h3_w: 2000 + Math.random() * 50,
          h4_w: 2100 + Math.random() * 50,
        };
      });
    }
  },

  async startSimulator(): Promise<any> {
    try {
      const res = await httpClient.post(`${API_BASE}/simulator/start`);
      return res.data;
    } catch {
      return { status: 'running' };
    }
  },

  async stopSimulator(): Promise<any> {
    try {
      const res = await httpClient.post(`${API_BASE}/simulator/stop`);
      return res.data;
    } catch {
      return { status: 'stopped' };
    }
  },

  async setSimulatorScenario(scenarioId: number): Promise<any> {
    try {
      const res = await httpClient.post(`${API_BASE}/simulator/scenario/${scenarioId}`);
      return res.data;
    } catch {
      return { scenario: scenarioId };
    }
  },

  async setNodeMode(deviceId: string, mode: string, loadW?: number): Promise<any> {
    try {
      const res = await httpClient.post(`${API_BASE}/simulator/node/${deviceId}/mode`, { mode, load_w: loadW });
      return res.data;
    } catch {
      return { deviceId, mode };
    }
  },

  async resetSimulator(): Promise<any> {
    try {
      const res = await httpClient.post(`${API_BASE}/simulator/reset`);
      return res.data;
    } catch {
      return { status: 'reset' };
    }
  },
};

