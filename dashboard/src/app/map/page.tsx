// KAVACHGRID 3.0 — GIS Map View Page
// Phase 12: Complete implementation
'use client';

import React, { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';
import { Grid, Box, Typography, Card, CardContent, Divider, Chip, List, ListItem, ListItemText, LinearProgress } from '@mui/material';
import { api } from '@/lib/api';
import { useApi } from '@/hooks/useApi';
import { Device, Telemetry } from '@/lib/types';
import { themeConfig } from '@/theme/theme';

// Dynamically import Leaflet RiskMap component to disable SSR
const RiskMap = dynamic(() => import('@/components/map/RiskMap'), {
  ssr: false,
  loading: () => (
    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', py: 8 }}>
      <Typography variant="body1" sx={{ mb: 2, color: 'text.secondary', fontWeight: 600 }}>
        Loading GIS Canvas Engine...
      </Typography>
      <LinearProgress sx={{ width: 200 }} />
    </Box>
  ),
});

export default function MapPage() {
  const { data: devices, loading } = useApi(api.getDevices);
  const [selectedDeviceId, setSelectedDeviceId] = useState<string>('');
  const [selectedDevice, setSelectedDevice] = useState<Device | null>(null);
  const [deviceTelemetry, setDeviceTelemetry] = useState<Telemetry[]>([]);
  const [telemetryLoading, setTelemetryLoading] = useState<boolean>(false);

  // Set default selected device
  useEffect(() => {
    if (devices && devices.length > 0 && !selectedDeviceId) {
      // Find a consumer with coordinates to default highlight
      const consumer = devices.find((d) => d.device_type === 'consumer' && d.latitude);
      if (consumer) setSelectedDeviceId(consumer.device_id);
    }
  }, [devices, selectedDeviceId]);

  // Fetch telemetry/details for selected device
  useEffect(() => {
    const fetchDetails = async () => {
      if (!selectedDeviceId) return;
      setTelemetryLoading(true);
      try {
        const dev = await api.getDevice(selectedDeviceId);
        setSelectedDevice(dev);
        const tel = await api.getHistoricalTelemetry(selectedDeviceId);
        setDeviceTelemetry(tel);
      } catch (err) {
        console.error(err);
      } finally {
        setTelemetryLoading(false);
      }
    };
    fetchDetails();
  }, [selectedDeviceId]);

  const latestRead = deviceTelemetry.length > 0 ? deviceTelemetry[deviceTelemetry.length - 1] : null;

  return (
    <Box sx={{ height: 'calc(100vh - 120px)', display: 'flex', flexDirection: 'column' }}>
      {/* Title */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 800, color: 'text.primary', mb: 1 }}>
          GIS Map View
        </Typography>
        <Typography variant="body2" sx={{ color: 'text.secondary', fontWeight: 600 }}>
          Geospatial visualization of smart grid topology, node statuses, and real-time current/voltage parameters.
        </Typography>
      </Box>

      {/* Map Content */}
      <Box sx={{ flexGrow: 1, minHeight: 0 }}>
        {loading ? (
          <LinearProgress />
        ) : (
          <Grid container spacing={3} sx={{ height: '100%' }}>
            {/* Map Frame (Left Column) */}
            <Grid item xs={12} lg={8} sx={{ height: '100%' }}>
              <RiskMap devices={devices || []} onSelectDevice={setSelectedDeviceId} />
            </Grid>

            {/* Selected Node Sidebar (Right Column) */}
            <Grid item xs={12} lg={4} sx={{ height: '100%', overflowY: 'auto' }}>
              {selectedDevice ? (
                <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                  <CardContent sx={{ p: 3, flexGrow: 1 }}>
                    <Typography variant="h6" sx={{ fontWeight: 800, mb: 1, color: themeConfig.primary }}>
                      📍 Map Pin Inspector
                    </Typography>
                    <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block', mb: 2 }}>
                      Device ID: <strong style={{ color: '#fff' }}>{selectedDevice.device_id}</strong>
                    </Typography>

                    <Divider sx={{ mb: 2.5 }} />

                    {/* Metadata list */}
                    <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 1.5 }}>
                      Device Properties
                    </Typography>
                    <List sx={{ bgcolor: 'rgba(0,0,0,0.1)', borderRadius: 2, p: 1, mb: 3 }}>
                      <ListItem disablePadding sx={{ py: 0.5, px: 1 }}>
                        <ListItemText primary="Label" secondary={selectedDevice.name} />
                      </ListItem>
                      <ListItem disablePadding sx={{ py: 0.5, px: 1 }}>
                        <ListItemText primary="Type" secondary={selectedDevice.device_type.toUpperCase()} />
                      </ListItem>
                      <ListItem disablePadding sx={{ py: 0.5, px: 1 }}>
                        <ListItemText primary="Zone Segment" secondary={selectedDevice.zone_id || 'N/A'} />
                      </ListItem>
                      <ListItem disablePadding sx={{ py: 0.5, px: 1 }}>
                        <ListItemText primary="Address / GPS" secondary={`${selectedDevice.latitude?.toFixed(4)}, ${selectedDevice.longitude?.toFixed(4)}`} />
                      </ListItem>
                    </List>

                    <Divider sx={{ mb: 2.5 }} />

                    {/* Telemetry Stats */}
                    <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 1.5 }}>
                      Electrical Ingest Readings
                    </Typography>
                    
                    {telemetryLoading ? (
                      <LinearProgress />
                    ) : latestRead ? (
                      <Grid container spacing={1.5}>
                        <Grid item xs={6}>
                          <Box sx={{ p: 1.5, bgcolor: 'rgba(255,255,255,0.01)', border: `1px solid ${themeConfig.border}`, borderRadius: 1.5 }}>
                            <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 600 }}>VOLTAGE</Typography>
                            <Typography variant="body1" sx={{ fontWeight: 800 }}>{latestRead.voltage} V</Typography>
                          </Box>
                        </Grid>
                        <Grid item xs={6}>
                          <Box sx={{ p: 1.5, bgcolor: 'rgba(255,255,255,0.01)', border: `1px solid ${themeConfig.border}`, borderRadius: 1.5 }}>
                            <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 600 }}>CURRENT</Typography>
                            <Typography variant="body1" sx={{ fontWeight: 800 }}>{latestRead.current} A</Typography>
                          </Box>
                        </Grid>
                        <Grid item xs={6}>
                          <Box sx={{ p: 1.5, bgcolor: 'rgba(255,255,255,0.01)', border: `1px solid ${themeConfig.border}`, borderRadius: 1.5 }}>
                            <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 600 }}>POWER DRAW</Typography>
                            <Typography variant="body1" sx={{ fontWeight: 800 }}>{latestRead.power} kW</Typography>
                          </Box>
                        </Grid>
                        <Grid item xs={6}>
                          <Box sx={{ p: 1.5, bgcolor: 'rgba(255,255,255,0.01)', border: `1px solid ${themeConfig.border}`, borderRadius: 1.5 }}>
                            <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 600 }}>ANOMALY SCORE</Typography>
                            <Typography variant="body1" sx={{ fontWeight: 800, color: (latestRead.anomaly_score || 0) >= 0.7 ? 'error.main' : 'success.main' }}>
                              {(latestRead.anomaly_score || 0).toFixed(2)}
                            </Typography>
                          </Box>
                        </Grid>
                        <Grid item xs={12}>
                          <Box sx={{ p: 1.5, bgcolor: 'rgba(255,255,255,0.01)', border: `1px solid ${themeConfig.border}`, borderRadius: 1.5, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <Typography variant="body2" sx={{ fontWeight: 700 }}>Zero Trust Validation</Typography>
                            <Chip
                              label={`${latestRead.trust_score || 99}% Secure`}
                              color={(latestRead.trust_score || 99) >= 80 ? 'success' : 'warning'}
                              sx={{ fontWeight: 800 }}
                            />
                          </Box>
                        </Grid>
                      </Grid>
                    ) : (
                      <Typography variant="body2" sx={{ color: 'text.secondary', py: 2 }}>
                        No active telemetry from selected node.
                      </Typography>
                    )}
                  </CardContent>
                </Card>
              ) : (
                <Box sx={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', p: 4, bgcolor: 'rgba(255,255,255,0.01)', border: `1px dashed ${themeConfig.border}`, borderRadius: 2 }}>
                  <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                    Select a pin on the map to inspect telemetry.
                  </Typography>
                </Box>
              )}
            </Grid>
          </Grid>
        )}
      </Box>
    </Box>
  );
}
