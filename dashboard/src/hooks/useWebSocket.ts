// KAVACHGRID 3.0 — WebSocket Hook. Phase 12.
import { useState, useEffect, useRef } from 'react';
import { Telemetry, Alert, RiskScore, Device } from '@/lib/types';
import { mockDevices, mockTelemetry, mockAlerts, mockRiskRanking } from '@/lib/api';

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws/dashboard';

export function useWebSocket() {
  const [connected, setConnected] = useState(false);
  const [lastTelemetry, setLastTelemetry] = useState<Telemetry | null>(null);
  const [latestAlert, setLatestAlert] = useState<Alert | null>(null);
  const [latestRisk, setLatestRisk] = useState<RiskScore | null>(null);
  const [deviceStatuses, setDeviceStatuses] = useState<Record<string, 'online' | 'offline' | 'warning'>>({});
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    // Initialize statuses
    const initialStatuses: Record<string, 'online' | 'offline' | 'warning'> = {};
    mockDevices.forEach(d => {
      initialStatuses[d.device_id] = d.status;
    });
    setDeviceStatuses(initialStatuses);

    // Setup real WebSocket connection
    const connect = () => {
      try {
        const ws = new WebSocket(WS_URL);
        wsRef.current = ws;

        ws.onopen = () => {
          console.log('⚡ Connected to KAVACHGRID WS');
          setConnected(true);
          if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
          }
        };

        ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            const { event: eventName, data } = message;

            switch (eventName) {
              case 'telemetry_update':
                setLastTelemetry(data as Telemetry);
                break;
              case 'alert_created':
                setLatestAlert(data as Alert);
                break;
              case 'risk_updated':
                setLatestRisk(data as RiskScore);
                break;
              case 'device_status':
                const payload = data as { device_id: string; status: 'online' | 'offline' | 'warning' };
                setDeviceStatuses(prev => ({
                  ...prev,
                  [payload.device_id]: payload.status,
                }));
                break;
              default:
                break;
            }
          } catch (err) {
            console.error('Error parsing WS message:', err);
          }
        };

        ws.onclose = () => {
          setConnected(false);
          // Try reconnecting after 5 seconds
          reconnectTimeoutRef.current = setTimeout(connect, 5000);
        };

        ws.onerror = () => {
          ws.close();
        };
      } catch (err) {
        setConnected(false);
        reconnectTimeoutRef.current = setTimeout(connect, 5000);
      }
    };

    connect();

    // Fallback simulation timer: if not connected, simulate live MQTT updates
    const simulationInterval = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) return;

      // Simulate a random telemetry update
      const deviceKeys = Object.keys(mockTelemetry);
      const randomDevice = deviceKeys[Math.floor(Math.random() * deviceKeys.length)];
      const readings = mockTelemetry[randomDevice];
      if (readings && readings.length > 0) {
        const baseReading = readings[readings.length - 1];
        
        // Add random fluctuation
        const simulatedReading: Telemetry = {
          ...baseReading,
          id: `sim-${Date.now()}`,
          voltage: Number((baseReading.voltage + (Math.random() - 0.5) * 1.5).toFixed(2)),
          current: Number(Math.max(0.1, baseReading.current + (Math.random() - 0.5) * 0.4).toFixed(2)),
          power: Number(Math.max(0.02, baseReading.power + (Math.random() - 0.5) * 0.1).toFixed(2)),
          timestamp: new Date().toISOString(),
        };

        setLastTelemetry(simulatedReading);
      }

      // Simulate occasional risk updates
      if (Math.random() > 0.7) {
        const rankings = mockRiskRanking.rankings;
        const randomRisk = { ...rankings[Math.floor(Math.random() * rankings.length)] };
        randomRisk.overall_score = Math.max(0, Math.min(100, Math.round(randomRisk.overall_score + (Math.random() - 0.5) * 4)));
        setLatestRisk(randomRisk);
      }

      // Simulate occasional status changes
      if (Math.random() > 0.9) {
        const d = mockDevices[Math.floor(Math.random() * mockDevices.length)];
        const statuses: ('online' | 'offline' | 'warning')[] = ['online', 'warning'];
        const newStatus = statuses[Math.floor(Math.random() * statuses.length)];
        setDeviceStatuses(prev => ({
          ...prev,
          [d.device_id]: newStatus,
        }));
      }

      // Simulate occasional new alert
      if (Math.random() > 0.95) {
        const newAlert: Alert = {
          id: `sim-alert-${Date.now()}`,
          device_id: 'meter_102',
          alert_type: 'anomaly',
          severity: 'medium',
          title: 'Load Shift Alert',
          message: 'Telemetry engine flagged load imbalance in Sector 4 branch line.',
          details: {},
          acknowledged: false,
          acknowledged_by: null,
          acknowledged_at: null,
          created_at: new Date().toISOString(),
        };
        setLatestAlert(newAlert);
      }
    }, 4000);

    return () => {
      if (wsRef.current) wsRef.current.close();
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      clearInterval(simulationInterval);
    };
  }, []);

  return { connected, lastTelemetry, latestAlert, latestRisk, deviceStatuses };
}
