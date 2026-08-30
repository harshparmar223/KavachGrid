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
  const { data: feederHistory } = useApi(() => api.getHistoricalTelemetry('feeder_01'));
  const { data: m101History } = useApi(() => api.getHistoricalTelemetry('meter_101'));
  const { data: m102History } = useApi(() => api.getHistoricalTelemetry('meter_102'));
  const { data: m103History } = useApi(() => api.getHistoricalTelemetry('meter_103'));

  const { lastTelemetry, latestAlert, deviceStatuses } = useWebSocket();

  const [alerts, setAlerts] = useState<Alert[]>(mockAlerts);
  const [liveTelemetry, setLiveTelemetry] = useState<Telemetry[]>([]);

  // Initialize alerts
  useEffect(() => {
    if (initialAlerts && initialAlerts.length > 0) {
      setAlerts(initialAlerts);
    }
  }, [initialAlerts]);

  // Handle incoming live alerts
  useEffect(() => {
    if (latestAlert) {
      setAlerts((prev) => {
        // Prevent duplicate alerts in listing
        if (prev.some((a) => a.id === latestAlert.id)) return prev;
        return [latestAlert, ...prev].slice(0, 8);
      });
    }
  }, [latestAlert]);

  // Handle incoming live telemetry
  useEffect(() => {
    if (lastTelemetry) {
      setLiveTelemetry((prev) => {
        const filtered = prev.filter((t) => t.device_id !== lastTelemetry.device_id);
        return [lastTelemetry, ...filtered].slice(0, 10);
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

  // Compile energy balance history chart data
  const compileChartData = () => {
    const fHist = feederHistory && feederHistory.length > 0 ? feederHistory : mockTelemetry['feeder_01'] || [];
    const m1Hist = m101History && m101History.length > 0 ? m101History : mockTelemetry['meter_101'] || [];
    const m2Hist = m102History && m102History.length > 0 ? m102History : mockTelemetry['meter_102'] || [];
    const m3Hist = m103History && m103History.length > 0 ? m103History : mockTelemetry['meter_103'] || [];

    const dataLength = Math.min(
      fHist.length,
      m1Hist.length,
      m2Hist.length,
      m3Hist.length
    );

    if (dataLength === 0) return [];

    return Array.from({ length: dataLength }).map((_, i) => {
      const feeder = fHist[i];
      const m101 = m1Hist[i];
      const m102 = m2Hist[i];
      const m103 = m3Hist[i];

      // Sum of consumers
      const consumersSum = Number((m101.power + m102.power + m103.power).toFixed(2));
      const feederPower = Number(feeder.power.toFixed(2));
      const loss = Number(Math.max(0, feederPower - consumersSum).toFixed(2));

      return {
        timestamp: feeder.timestamp,
        feederPower,
        consumerPower: consumersSum,
        loss,
      };
    });
  };

  const chartData = compileChartData();

  // Metrics calculations
  const displayDevices = devices && devices.length > 0 ? devices : mockDevices;
  const onlineCount = displayDevices.filter((d) => deviceStatuses[d.device_id] === 'online' || d.status === 'online').length;
  const totalCount = displayDevices.length;

  // Calculate current power draw and imbalance
  const currentFeederPower = chartData.length > 0 ? chartData[chartData.length - 1].feederPower : 18.5;
  const currentConsumerPower = chartData.length > 0 ? chartData[chartData.length - 1].consumerPower : 12.8;
  const currentLoss = Number(Math.max(0, currentFeederPower - currentConsumerPower).toFixed(2));
  const currentLossPercent = Number(((currentLoss / currentFeederPower) * 100).toFixed(1));

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
                      <TableCell align="right">Current (A)</TableCell>
                      <TableCell align="right">Power (kW)</TableCell>
                      <TableCell align="right">Frequency (Hz)</TableCell>
                      <TableCell align="right">Power Factor</TableCell>
                      <TableCell align="right">Trust Score</TableCell>
                      <TableCell align="right">Timestamp</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {liveTelemetry.length === 0 ? (
                      // Show defaults from mock latest telemetry
                      devices?.slice(0, 5).map((device) => {
                        const readings = mockTelemetry[device.device_id];
                        const baseData = readings && readings.length > 0
                          ? readings[readings.length - 1]
                          : { voltage: 230, current: 5, power: 1.15, frequency: 50.00, power_factor: 0.98, trust_score: 99, timestamp: new Date().toISOString() };

                        return (
                          <TableRow key={device.device_id}>
                            <TableCell component="th" scope="row" sx={{ fontWeight: 700, color: themeConfig.primary }}>
                              {device.device_id}
                            </TableCell>
                            <TableCell align="right">{baseData.voltage}</TableCell>
                            <TableCell align="right">{baseData.current}</TableCell>
                            <TableCell align="right">{baseData.power}</TableCell>
                            <TableCell align="right">{baseData.frequency || 50.00}</TableCell>
                            <TableCell align="right">{baseData.power_factor || 0.98}</TableCell>
                            <TableCell align="right">
                              <Chip
                                label={`${baseData.trust_score}%`}
                                size="small"
                                color={baseData.trust_score && baseData.trust_score >= 80 ? 'success' : 'warning'}
                                sx={{ fontWeight: 700 }}
                              />
                            </TableCell>
                            <TableCell align="right">
                              {new Date(baseData.timestamp).toLocaleTimeString()}
                            </TableCell>
                          </TableRow>
                        );
                      })
                    ) : (
                      liveTelemetry.map((t) => (
                        <TableRow key={t.id}>
                          <TableCell component="th" scope="row" sx={{ fontWeight: 700, color: themeConfig.primary }}>
                            {t.device_id}
                          </TableCell>
                          <TableCell align="right">{t.voltage}</TableCell>
                          <TableCell align="right">{t.current}</TableCell>
                          <TableCell align="right">{t.power}</TableCell>
                          <TableCell align="right">{t.frequency || 50.00}</TableCell>
                          <TableCell align="right">{t.power_factor || 0.98}</TableCell>
                          <TableCell align="right">
                            <Chip
                              label={`${t.trust_score || 99}%`}
                              size="small"
                              color={t.trust_score && t.trust_score >= 80 ? 'success' : 'warning'}
                              sx={{ fontWeight: 700 }}
                            />
                          </TableCell>
                          <TableCell align="right">
                            {new Date(t.timestamp).toLocaleTimeString()}
                          </TableCell>
                        </TableRow>
                      ))
                    )}
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
