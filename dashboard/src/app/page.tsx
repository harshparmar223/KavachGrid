// KAVACHGRID 3.0 — Overview Dashboard Page
// Phase 12: Complete implementation
'use client';

import React, { useState, useEffect } from 'react';
import {
  Grid,
  Box,
  Typography,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  LinearProgress,
} from '@mui/material';
import {
  FlashOn as PowerIcon,
  Warning as AlertIcon,
  Router as RouterIcon,
  Timeline as ChartIcon,
} from '@mui/icons-material';
import dynamic from 'next/dynamic';
import MetricCard from '@/components/cards/MetricCard';
import AlertCard from '@/components/cards/AlertCard';
import FoldText from '@/components/animations/FoldText';

const EnergyChart = dynamic(() => import('@/components/charts/EnergyChart'), { ssr: false });
import { api, mockTelemetry, mockAlerts, mockDevices } from '@/lib/api';
import { useApi } from '@/hooks/useApi';
import { useWebSocket } from '@/hooks/useWebSocket';
import { Alert, Telemetry } from '@/lib/types';
import { themeConfig } from '@/theme/theme';

export default function HomePage() {
  const { data: devices, loading: devicesLoading } = useApi(api.getDevices);
  const { data: initialAlerts, loading: alertsLoading } = useApi(api.getAlerts);
  const { data: initialTelemetry } = useApi(api.getLatestTelemetry);
  const { data: feederHistory } = useApi(() => api.getHistoricalTelemetry('FEEDER-01'));
  const { data: m101History } = useApi(() => api.getHistoricalTelemetry('CONSUMER-H1'));
  const { data: m102History } = useApi(() => api.getHistoricalTelemetry('CONSUMER-H2'));
  const { data: m103History } = useApi(() => api.getHistoricalTelemetry('CONSUMER-H3'));

  const { lastTelemetry, latestAlert, deviceStatuses } = useWebSocket();

  const [alerts, setAlerts] = useState<Alert[]>(mockAlerts);
  const [telemetryMap, setTelemetryMap] = useState<Record<string, Telemetry>>({});

  // Initialize alerts
  useEffect(() => {
    if (initialAlerts && initialAlerts.length > 0) {
      setAlerts(initialAlerts);
    }
  }, [initialAlerts]);

  // Initialize latest telemetry from backend
  useEffect(() => {
    if (initialTelemetry && initialTelemetry.length > 0) {
      const map: Record<string, Telemetry> = {};
      initialTelemetry.forEach((t) => {
        const id = t.device_id;
        map[id] = t;
        map[id.toLowerCase()] = t;
        map[id.toUpperCase()] = t;
        if (id === 'CONSUMER-01' || id === 'meter_101') map['CONSUMER-H1'] = t;
        if (id === 'CONSUMER-02' || id === 'meter_102') map['CONSUMER-H2'] = t;
        if (id === 'CONSUMER-03' || id === 'meter_103') map['CONSUMER-H3'] = t;
      });
      setTelemetryMap((prev) => ({ ...map, ...prev }));
    }
  }, [initialTelemetry]);

  // Handle incoming live alerts
  useEffect(() => {
    if (latestAlert) {
      setAlerts((prev) => {
        if (prev.some((a) => a.id === latestAlert.id)) return prev;
        return [latestAlert, ...prev].slice(0, 8);
      });
    }
  }, [latestAlert]);

  // Helper to convert power to kW consistently
  const toKw = (p: number | undefined | null): number => {
    if (p === undefined || p === null) return 0;
    const num = Number(p);
    if (isNaN(num)) return 0;
    // Sensor sends Watts (e.g. 238W - 10000W). If > 20.0, convert to kW; if <= 20.0, it's already in kW (e.g. 9.3 kW)
    return num > 20.0 ? num / 1000.0 : num;
  };

  // Compile a single energy balance point from the current telemetry map
  const computeEnergyBalancePoint = (map: Record<string, Telemetry>, timestamp?: string) => {
    const now = Date.now();

    // Check if live hardware feeder is actively transmitting in current session (within last 2 minutes)
    const feederTele = map['FEEDER-01'] || map['feeder-01'];
    const isFeederLive = feederTele && (now - new Date(feederTele.timestamp || feederTele.received_at || 0).getTime() < 120000);

    const hwConsumerKeys = ['CONSUMER-H1', 'CONSUMER-H2', 'CONSUMER-H3', 'CONSUMER-H4'];
    const mockConsumerKeys = ['meter_101', 'meter_102', 'meter_103', 'meter_104'];

    // Find active live consumer nodes transmitting within the last 2 minutes
    const activeLiveConsumers = hwConsumerKeys.filter((k) => {
      const dev = map[k] || map[k.toLowerCase()] || map[k.toUpperCase()];
      if (!dev) return false;
      const ageMs = now - new Date(dev.timestamp || dev.received_at || 0).getTime();
      return ageMs < 120000;
    });

    const countedDevices = new Set<string>();
    let totalConsumerKw = 0;

    if (activeLiveConsumers.length > 0) {
      // ONLY sum the currently active live hardware nodes (e.g. House 1, House 2)
      for (const key of activeLiveConsumers) {
        const dev = map[key] || map[key.toLowerCase()] || map[key.toUpperCase()];
        if (dev && !countedDevices.has(dev.device_id.toUpperCase())) {
          countedDevices.add(dev.device_id.toUpperCase());
          totalConsumerKw += toKw(dev.power);
        }
      }
    } else {
      // If no live hardware is active, check fallback mock devices
      for (const key of mockConsumerKeys) {
        const dev = map[key] || map[key.toLowerCase()] || map[key.toUpperCase()];
        if (dev && !countedDevices.has(dev.device_id.toUpperCase())) {
          countedDevices.add(dev.device_id.toUpperCase());
          totalConsumerKw += toKw(dev.power);
        }
      }
      if (totalConsumerKw === 0) totalConsumerKw = 0.080;
    }

    // Feeder input power:
    // If real Feeder node is live, use it. Otherwise, compute feeder power as consumer load + distribution technical loss.
    let feederKw = 0;
    if (isFeederLive && feederTele) {
      feederKw = toKw(feederTele.power);
    } else if (activeLiveConsumers.length > 0) {
      feederKw = totalConsumerKw * 1.05 + 0.005;
    } else {
      const fallbackFeeder = map['feeder_01'] || map['FEEDER_01'];
      feederKw = fallbackFeeder ? toKw(fallbackFeeder.power) : totalConsumerKw * 1.05 + 0.005;
    }

    const lossKw = Math.max(0, feederKw - totalConsumerKw);

    return {
      timestamp: timestamp || new Date().toISOString(),
      feederPower: Number(feederKw.toFixed(3)),
      consumerPower: Number(totalConsumerKw.toFixed(3)),
      loss: Number(lossKw.toFixed(3)),
    };
  };

  // Start with 15 baseline points so the chart renders instantly
  const [chartData, setChartData] = useState<Array<{
    timestamp: string;
    feederPower: number;
    consumerPower: number;
    loss: number;
  }>>(() => {
    const now = Date.now();
    return Array.from({ length: 15 }).map((_, i) => ({
      timestamp: new Date(now - (14 - i) * 3000).toISOString(),
      feederPower: 0.100,
      consumerPower: 0.080,
      loss: 0.020,
    }));
  });

  // Handle incoming live telemetry over WebSocket and update real-time chart
  useEffect(() => {
    if (lastTelemetry) {
      const key = lastTelemetry.device_id;
      const updatedMap: Record<string, Telemetry> = {
        ...telemetryMap,
        [key]: lastTelemetry,
        [key.toUpperCase()]: lastTelemetry,
        [key.toLowerCase()]: lastTelemetry,
      };
      if (key === 'CONSUMER-H1' || key === 'CONSUMER-01' || key === 'meter_101' || key.toLowerCase().includes('house1')) {
        updatedMap['CONSUMER-H1'] = lastTelemetry;
        updatedMap['CONSUMER-01'] = lastTelemetry;
        updatedMap['meter_101'] = lastTelemetry;
      }
      if (key === 'CONSUMER-H2' || key === 'CONSUMER-02' || key === 'meter_102' || key.toLowerCase().includes('house2')) {
        updatedMap['CONSUMER-H2'] = lastTelemetry;
        updatedMap['CONSUMER-02'] = lastTelemetry;
        updatedMap['meter_102'] = lastTelemetry;
      }
      if (key === 'CONSUMER-H3' || key === 'CONSUMER-03' || key === 'meter_103' || key.toLowerCase().includes('house3')) {
        updatedMap['CONSUMER-H3'] = lastTelemetry;
        updatedMap['CONSUMER-03'] = lastTelemetry;
        updatedMap['meter_103'] = lastTelemetry;
      }
      if (key === 'FEEDER-01' || key === 'FEEDER-1' || key === 'feeder_01') {
        updatedMap['FEEDER-01'] = lastTelemetry;
        updatedMap['FEEDER-1'] = lastTelemetry;
        updatedMap['feeder_01'] = lastTelemetry;
      }

      setTelemetryMap(updatedMap);

      // Append new real-time point to chartData
      const newPoint = computeEnergyBalancePoint(updatedMap, lastTelemetry.timestamp || new Date().toISOString());
      setChartData((prev) => {
        const base = prev.length > 0 ? prev : [];
        return [...base.slice(-29), newPoint];
      });
    }
  }, [lastTelemetry]);

  // Helper to acknowledge alerts locally
  const handleAcknowledge = async (id: string) => {
    await api.acknowledgeAlert(id);
    setAlerts((prev) =>
      prev.map((a) => (a.id === id ? { ...a, acknowledged: true } : a))
    );
  };

  // Metrics calculations (filter out localization branch sensors from overview meters)
  const allDevices = devices && devices.length > 0 ? devices : mockDevices;
  const displayDevices = allDevices.filter(
    (d) =>
      d.device_type !== 'localization' &&
      !d.device_id.toUpperCase().includes('LOC-') &&
      !d.device_id.toUpperCase().includes('ZONE')
  );
  const onlineCount = displayDevices.filter((d) => deviceStatuses[d.device_id] === 'online' || d.status === 'online').length;
  const totalCount = displayDevices.length;

  // Calculate current power draw and imbalance
  const latestPoint = chartData.length > 0 ? chartData[chartData.length - 1] : null;
  const currentFeederPower = latestPoint ? latestPoint.feederPower : 3.36;
  const currentConsumerPower = latestPoint ? latestPoint.consumerPower : 2.45;
  const currentLoss = Number(Math.max(0, currentFeederPower - currentConsumerPower).toFixed(3));
  const currentLossPercent = currentFeederPower > 0 ? Number(((currentLoss / currentFeederPower) * 100).toFixed(1)) : 0;

  return (
    <Box sx={{ flexGrow: 1 }}>
      {/* Title */}
      <Box sx={{ mb: 4 }}>
        <Box className="kavachgrid-hero">
          <FoldText
            text="KAVACHGRID"
            splitBy="char"
            hinge="top"
            trigger="mount"
            duration={0.8}
            stagger={0.04}
            ease="power3.out"
            perspective={900}
            creaseShading={0.55}
            fontSize="clamp(2.5rem, 4vw, 5rem)"
            fontWeight={900}
            color="#f5f7ff"
            style={{
              display: 'inline-block',
              lineHeight: 1,
              letterSpacing: '0.08em',
            }}
          />
          <Typography variant="body2" sx={{ color: 'text.secondary', fontWeight: 600, letterSpacing: '0.14em', textTransform: 'uppercase' }}>
            Smart Grid Investigation Support
          </Typography>
        </Box>
        <Typography variant="body2" sx={{ color: 'text.secondary', fontWeight: 600 }}>
          Real-time smart grid validation status & anomaly assessment dashboard.
        </Typography>
      </Box>

      {/* KPI Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Grid Unaccounted Loss"
            value={`${currentLossPercent}%`}
            icon={<PowerIcon sx={{ color: themeConfig.primary }} />}
            trend={4.2}
            trendText="vs yesterday"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Active System Alarms"
            value={alerts.filter((a) => !a.acknowledged).length}
            icon={<AlertIcon sx={{ color: themeConfig.error }} />}
            iconBgColor="rgba(244, 67, 54, 0.1)"
            subtext="Unresolved alerts pending"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Nodes Ingest Status"
            value={`${onlineCount} / ${totalCount}`}
            icon={<RouterIcon sx={{ color: themeConfig.success }} />}
            iconBgColor="rgba(76, 175, 80, 0.1)"
            subtext="Smart meters connected"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Active Loss Power"
            value={`${currentLoss} kW`}
            icon={<ChartIcon sx={{ color: themeConfig.secondary }} />}
            iconBgColor="rgba(124, 77, 255, 0.1)"
            subtext={`Feeder total: ${currentFeederPower} kW`}
          />
        </Grid>
      </Grid>

      {/* Main Grid Charts and Alerts */}
      <Grid container spacing={3}>
        {/* Left Column: Energy Balance Chart */}
        <Grid item xs={12} lg={8}>
          <Card sx={{ height: '100%', background: 'linear-gradient(180deg, rgba(17, 34, 64, 0.9) 0%, rgba(7, 17, 31, 0.96) 100%)' }}>
            <CardContent sx={{ p: 3, position: 'relative', zIndex: 1 }}>
              <Typography variant="h6" sx={{ fontWeight: 700, mb: 1 }}>
                ⚡ Energy Balance (Real-Time Grid Flow)
              </Typography>
              <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block', mb: 3, fontWeight: 500 }}>
                Compares input power at Substation Feeder vs cumulative load across downstream consumer nodes.
              </Typography>
              
              {chartData.length === 0 ? (
                <Box sx={{ width: '100%', py: 8 }}>
                  <Typography variant="body2" sx={{ textAlign: 'center', mb: 2, color: 'text.secondary' }}>
                    Loading electrical telemetry stream...
                  </Typography>
                  <LinearProgress />
                </Box>
              ) : (
                <EnergyChart data={chartData} />
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Right Column: Recent Alerts Feed */}
        <Grid item xs={12} lg={4}>
          <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column', background: 'linear-gradient(180deg, rgba(17, 34, 64, 0.9) 0%, rgba(7, 17, 31, 0.96) 100%)' }}>
            <CardContent sx={{ p: 3, flexGrow: 1, display: 'flex', flexDirection: 'column', position: 'relative', zIndex: 1 }}>
              <Typography variant="h6" sx={{ fontWeight: 700, mb: 2 }}>
                🚨 Control Room Alerts Feed
              </Typography>

              {alerts.length === 0 && alertsLoading ? (
                <LinearProgress />
              ) : alerts.length === 0 ? (
                <Typography variant="body2" sx={{ color: 'text.secondary', py: 4, textAlign: 'center' }}>
                  No active grid alerts detected.
                </Typography>
              ) : (
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, maxHeight: 380, overflowY: 'auto', pr: 1 }}>
                  {alerts.slice(0, 3).map((alert) => (
                    <AlertCard key={alert.id} alert={alert} onAcknowledge={handleAcknowledge} />
                  ))}
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Bottom Column: Real-Time Grid Telemetry Feed */}
        <Grid item xs={12}>
          <Card sx={{ mt: 1 }}>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ fontWeight: 700, mb: 2 }}>
                📡 Live Ingest Stream (Latest Telemetry)
              </Typography>
              <TableContainer component={Paper} sx={{ border: 'none', boxShadow: 'none' }}>
                <Table sx={{ minWidth: 650 }}>
                  <TableHead>
                    <TableRow>
                      <TableCell>Device ID</TableCell>
                      <TableCell align="right">Voltage (V)</TableCell>
                      <TableCell align="right">Current</TableCell>
                      <TableCell align="right">Power (kW)</TableCell>
                      <TableCell align="right">Frequency (Hz)</TableCell>
                      <TableCell align="right">Power Factor</TableCell>
                      <TableCell align="right">Trust Score</TableCell>
                      <TableCell align="right">Timestamp</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {displayDevices.map((device) => {
                      const liveData =
                        telemetryMap[device.device_id] ||
                        telemetryMap[device.device_id.toUpperCase()] ||
                        telemetryMap[device.device_id.toLowerCase()];

                      const mockReadings = mockTelemetry[device.device_id] || mockTelemetry[device.device_id.toLowerCase()];
                      const baseData = liveData || (mockReadings && mockReadings.length > 0 ? mockReadings[mockReadings.length - 1] : null);

                      const v = baseData ? Number(baseData.voltage).toFixed(1) : '230.0';
                      const rawCurrent = baseData ? Number(baseData.current) : 0.0;
                      // Display in mA for small loads (< 1.0A) or in A for larger loads
                      const iDisplay = rawCurrent > 0 && rawCurrent < 1.0 
                        ? `${(rawCurrent * 1000).toFixed(1)} mA` 
                        : `${rawCurrent.toFixed(2)} A`;
                      const rawP = baseData ? Number(baseData.power) : 0.0;
                      // Sensor sends Watts if > 20.0 (e.g. 238 W -> 0.238 kW). Otherwise already in kW (e.g. 9.3 kW).
                      const pKw = rawP > 20.0 ? (rawP / 1000.0).toFixed(3) : (rawP > 0 ? rawP.toFixed(3) : '0.000');
                      const freq = baseData?.frequency ? Number(baseData.frequency).toFixed(2) : '50.00';
                      const pf = baseData?.power_factor ? Number(baseData.power_factor).toFixed(2) : '0.98';
                      const trust = baseData?.trust_score !== undefined ? Number(baseData.trust_score).toFixed(0) : '99';
                      const timeStr = baseData ? new Date(baseData.timestamp).toLocaleTimeString() : 'Just now';

                      return (
                        <TableRow key={device.device_id} sx={{ '&:hover': { bgcolor: 'rgba(255,255,255,0.03)' } }}>
                          <TableCell component="th" scope="row" sx={{ fontWeight: 700, color: themeConfig.primary }}>
                            {device.device_id}
                          </TableCell>
                          <TableCell align="right">{v}</TableCell>
                          <TableCell align="right">{iDisplay}</TableCell>
                          <TableCell align="right">{pKw}</TableCell>
                          <TableCell align="right">{freq}</TableCell>
                          <TableCell align="right">{pf}</TableCell>
                          <TableCell align="right">
                            <Chip
                              label={`${trust}%`}
                              size="small"
                              color={Number(trust) >= 80 ? 'success' : 'warning'}
                              sx={{ fontWeight: 700 }}
                            />
                          </TableCell>
                          <TableCell align="right" suppressHydrationWarning>{timeStr}</TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}
