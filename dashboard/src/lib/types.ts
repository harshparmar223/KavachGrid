// ============================================
// KAVACHGRID 3.0 — TypeScript Interfaces
// Phase 2: Updated to match database schema exactly
// ============================================

// ---------- Users ----------
export interface User {
  id: string;
  username: string;
  email: string;
  full_name: string;
  role: 'admin' | 'operator' | 'investigator' | 'viewer';
  is_active: boolean;
  created_at: string;
  last_login_at: string | null;
}

// ---------- Devices ----------
export interface Device {
  id: string;
  device_id: string;
  device_type: 'feeder' | 'consumer' | 'localization';
  name: string;
  location: string | null;
  latitude: number | null;
  longitude: number | null;
  api_key: string;
  status: 'online' | 'offline' | 'warning';
  zone_id: string | null;
  metadata: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
  last_seen_at: string | null;
}

export interface DeviceStatus {
  device_id: string;
  name: string;
  device_type: 'feeder' | 'consumer' | 'localization';
  status: 'online' | 'offline' | 'warning';
  last_seen_at: string | null;
  zone_id: string | null;
}

// ---------- Telemetry ----------
export interface Telemetry {
  id: string;
  device_id: string;
  voltage: number;
  current: number;
  power: number;
  energy: number;
  power_factor: number | null;
  frequency: number | null;
  trust_score: number | null;
  anomaly_score: number | null;
  timestamp: string;
  received_at: string;
}

export interface TelemetryBatch {
  total: number;
  page: number;
  page_size: number;
  data: Telemetry[];
}

export interface TelemetryStats {
  device_id: string;
  period_start: string;
  period_end: string;
  avg_voltage: number;
  avg_current: number;
  avg_power: number;
  total_energy: number;
  min_voltage: number;
  max_voltage: number;
  reading_count: number;
}

// ---------- Alerts ----------
export type AlertType =
  | 'energy_imbalance'
  | 'anomaly'
  | 'meter_health'
  | 'device_trust'
  | 'communication'
  | 'localization';

export type Severity = 'low' | 'medium' | 'high' | 'critical';

export interface Alert {
  id: string;
  device_id: string | null;
  alert_type: AlertType;
  severity: Severity;
  title: string;
  message: string;
  details: Record<string, unknown> | null;
  acknowledged: boolean;
  acknowledged_by: string | null;
  acknowledged_at: string | null;
  created_at: string;
}

export interface AlertSummary {
  total: number;
  unacknowledged: number;
  by_severity: Record<Severity, number>;
  by_type: Record<AlertType, number>;
}

// ---------- Risk Scores ----------
export type RiskLevel = 'low' | 'medium' | 'high' | 'critical';

export interface RiskScore {
  id: string;
  device_id: string;
  overall_score: number;
  energy_balance_score: number;
  ai_anomaly_score: number;
  meter_health_score: number;
  device_trust_score: number;
  comm_reliability_score: number;
  risk_level: RiskLevel;
  details: Record<string, unknown> | null;
  calculated_at: string;
}

export interface RiskRanking {
  rankings: RiskScore[];
  total_consumers: number;
  high_risk_count: number;
  critical_count: number;
  last_calculated: string;
}

// ---------- Localization ----------
export type InvestigationStatus = 'pending' | 'investigating' | 'resolved' | 'false_alarm';

export interface SuspectDevice {
  device_id: string;
  suspicion_score: number;
  reason: string;
  recommended_action: string;
}

export interface LocalizationResult {
  id: string;
  zone_id: string;
  confidence: number;
  priority: Severity;
  estimated_loss_kwh: number | null;
  suspect_devices: SuspectDevice[];
  investigation_notes: string | null;
  status: InvestigationStatus;
  resolved_by: string | null;
  created_at: string;
  updated_at: string;
}

// ---------- Audit Logs ----------
export interface AuditLog {
  id: string;
  user_id: string | null;
  action: string;
  resource_type: string;
  resource_id: string | null;
  details: Record<string, unknown> | null;
  ip_address: string | null;
  created_at: string;
}

// ---------- API Response Wrappers ----------
export interface ApiResponse<T> {
  data: T;
  message?: string;
}

export interface PaginatedResponse<T> {
  total: number;
  page: number;
  page_size: number;
  data: T[];
}

// ---------- WebSocket Messages ----------
export interface WsMessage {
  type: 'telemetry' | 'alert' | 'risk_update' | 'device_status';
  payload: unknown;
  timestamp: string;
}

// ---------- GIS & Geospatial Grid Topology ----------
export interface GisNode {
  device_id: string;
  name: string;
  device_type: 'feeder' | 'consumer' | 'localization';
  location: string | null;
  latitude: number;
  longitude: number;
  zone_id: string | null;
  status: 'online' | 'offline' | 'warning';
  voltage: number | null;
  current: number | null;
  power: number | null;
  power_factor: number | null;
  energy: number | null;
  trust_score: number | null;
  anomaly_score: number | null;
  overall_risk: number | null;
  risk_level: RiskLevel;
  active_alerts_count: number;
  last_seen_at: string | null;
}

export interface GisEdge {
  id: string;
  from_node: string;
  to_node: string;
  from_coords: [number, number];
  to_coords: [number, number];
  edge_type: 'feeder_to_branch' | 'branch_to_consumer' | 'feeder_to_consumer';
  status: 'normal' | 'warning' | 'critical';
  power_flow_kw: number | null;
  loss_estimated_pct: number | null;
}

export interface GisZoneSummary {
  zone_id: string;
  total_nodes: number;
  feeder_id: string | null;
  feeder_power_kw: number;
  consumer_total_power_kw: number;
  loss_percentage: number;
  critical_nodes_count: number;
  center_lat: number;
  center_lng: number;
}

export interface GisTopologyResponse {
  nodes: GisNode[];
  edges: GisEdge[];
  zones: GisZoneSummary[];
  total_nodes: number;
  center_lat: number;
  center_lng: number;
  generated_at: string;
}

export interface GisLocationUpdate {
  latitude: number;
  longitude: number;
  location?: string;
  zone_id?: string;
}




