// KAVACHGRID 3.0 — GIS Map View Page
// Phase 12: Connected to backend GIS API with live topology, power flows, risk rankings & GPS coordinator.
'use client';

import React, { useState, useEffect, useCallback } from 'react';
import dynamic from 'next/dynamic';
import {
  Grid,
  Box,
  Typography,
  Card,
  CardContent,
  Divider,
  Chip,
  List,
  ListItem,
  ListItemText,
  LinearProgress,
  Button,
  ButtonGroup,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert as MuiAlert,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import EditLocationAltIcon from '@mui/icons-material/EditLocationAlt';
import DownloadIcon from '@mui/icons-material/Download';
import LayersIcon from '@mui/icons-material/Layers';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import ElectricBoltIcon from '@mui/icons-material/ElectricBolt';
import SensorsIcon from '@mui/icons-material/Sensors';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';

import { api } from '@/lib/api';
import { GisNode, GisTopologyResponse, Telemetry } from '@/lib/types';
import { themeConfig } from '@/theme/theme';

// Dynamically import Leaflet RiskMap component to disable SSR
const RiskMap = dynamic(() => import('@/components/map/RiskMap'), {
  ssr: false,
  loading: () => (
    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', py: 8 }}>
      <Typography variant="body1" sx={{ mb: 2, color: 'text.secondary', fontWeight: 600 }}>
        Initializing GIS Canvas Engine...
      </Typography>
      <LinearProgress sx={{ width: 220 }} />
    </Box>
  ),
});

export default function MapPage() {
  const [topology, setTopology] = useState<GisTopologyResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedDeviceId, setSelectedDeviceId] = useState<string>('');
  const [selectedNode, setSelectedNode] = useState<GisNode | null>(null);
  const [deviceTelemetry, setDeviceTelemetry] = useState<Telemetry[]>([]);
  const [telemetryLoading, setTelemetryLoading] = useState<boolean>(false);
  
  // Controls & Filters
  const [zoneFilter, setZoneFilter] = useState<string>('all');
  const [riskFilter, setRiskFilter] = useState<string>('all');
  const [tileTheme, setTileTheme] = useState<'dark' | 'streets' | 'satellite'>('dark');

  // Edit Coordinates Dialog
  const [editOpen, setEditOpen] = useState<boolean>(false);
  const [editLat, setEditLat] = useState<string>('');
  const [editLng, setEditLng] = useState<string>('');
  const [editLocation, setEditLocation] = useState<string>('');
  const [editSaving, setEditSaving] = useState<boolean>(false);
  const [editMsg, setEditMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Fetch GIS topology
  const fetchTopology = useCallback(async (isInitial = false) => {
    if (isInitial) setLoading(true);
    try {
      const data = await api.getGisTopology(zoneFilter === 'all' ? undefined : zoneFilter);
      setTopology(data);
    } catch (err) {
      console.error('Failed to load GIS topology:', err);
    } finally {
      if (isInitial) setLoading(false);
    }
  }, [zoneFilter]);

  useEffect(() => {
    fetchTopology(true);
    const interval = setInterval(() => {
      fetchTopology(false);
    }, 4000);
    return () => clearInterval(interval);
  }, [fetchTopology]);

  // Set default selected device
  useEffect(() => {
    if (topology && topology.nodes.length > 0 && !selectedDeviceId) {
      const suspect = topology.nodes.find((n) => n.risk_level === 'critical' || n.status === 'warning');
      const first = suspect || topology.nodes[0];
      if (first) {
        setSelectedDeviceId(first.device_id);
      }
    }
  }, [topology, selectedDeviceId]);

  // Update selectedNode whenever selection or topology changes
  useEffect(() => {
    if (topology && selectedDeviceId) {
      const node = topology.nodes.find((n) => n.device_id === selectedDeviceId);
      setSelectedNode(node || null);
      if (node) {
        setEditLat(node.latitude.toString());
        setEditLng(node.longitude.toString());
        setEditLocation(node.location || '');
      }
    }
  }, [topology, selectedDeviceId]);

  // Fetch telemetry history for selected device
  useEffect(() => {
    const fetchTelemetry = async () => {
      if (!selectedDeviceId) return;
      setTelemetryLoading(true);
      try {
        const tel = await api.getHistoricalTelemetry(selectedDeviceId);
        setDeviceTelemetry(tel);
      } catch (err) {
        console.error(err);
      } finally {
        setTelemetryLoading(false);
      }
    };
    fetchTelemetry();
  }, [selectedDeviceId]);

  // Handle saving new coordinates
  const handleSaveCoordinates = async () => {
    if (!selectedDeviceId) return;
    const lat = parseFloat(editLat);
    const lng = parseFloat(editLng);
    if (isNaN(lat) || isNaN(lng) || lat < -90 || lat > 90 || lng < -180 || lng > 180) {
      setEditMsg({ type: 'error', text: 'Please enter valid GPS coordinates (Lat -90..90, Lng -180..180)' });
      return;
    }

    setEditSaving(true);
    setEditMsg(null);
    try {
      await api.updateDeviceCoordinates(selectedDeviceId, {
        latitude: lat,
        longitude: lng,
        location: editLocation,
      });
      setEditMsg({ type: 'success', text: 'GPS Coordinates updated successfully!' });
      setTimeout(() => {
        setEditOpen(false);
        setEditMsg(null);
        fetchTopology();
      }, 1000);
    } catch (err) {
      setEditMsg({ type: 'error', text: 'Failed to update coordinates.' });
    } finally {
      setEditSaving(false);
    }
  };

  // Export GeoJSON
  const handleExportGeoJson = async () => {
    try {
      const geojson = await api.getGisGeoJson(zoneFilter === 'all' ? undefined : zoneFilter);
      const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(geojson, null, 2));
      const downloadAnchor = document.createElement('a');
      downloadAnchor.setAttribute('href', dataStr);
      downloadAnchor.setAttribute('download', `kavachgrid_gis_${zoneFilter}_${new Date().toISOString().slice(0, 10)}.geojson`);
      document.body.appendChild(downloadAnchor);
      downloadAnchor.click();
      downloadAnchor.remove();
    } catch (err) {
      console.error('Failed to export GeoJSON:', err);
    }
  };

  // Filtered nodes
  const filteredNodes = (topology?.nodes || []).filter((n) => {
    if (riskFilter === 'critical') return n.risk_level === 'critical' || (n.anomaly_score || 0) >= 0.7;
    if (riskFilter === 'warning') return n.risk_level === 'high' || n.status === 'warning';
    if (riskFilter === 'normal') return n.risk_level === 'low' && n.status === 'online';
    return true;
  });

  const latestRead = deviceTelemetry.length > 0 ? deviceTelemetry[deviceTelemetry.length - 1] : null;
  const zoneSummary = topology?.zones?.[0];

  return (
    <Box sx={{ minHeight: 'calc(100vh - 120px)', display: 'flex', flexDirection: 'column' }}>
      {/* Top Header & Metrics Bar */}
      <Box sx={{ mb: 2.5, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 2 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 800, color: 'text.primary', mb: 0.5, display: 'flex', alignItems: 'center', gap: 1.5 }}>
            <ElectricBoltIcon sx={{ color: themeConfig.primary, fontSize: 32 }} />
            GIS Smart Grid Topology
          </Typography>
          <Typography variant="body2" sx={{ color: 'text.secondary', fontWeight: 600 }}>
            Real-time geospatial distribution grid mapping, branch loss indicators, and node telemetry.
          </Typography>
        </Box>

        {/* Action Controls */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, flexWrap: 'wrap' }}>
          {/* Zone Selector */}
          <FormControl size="small" sx={{ minWidth: 140 }}>
            <InputLabel sx={{ color: 'text.secondary', fontWeight: 600 }}>Zone</InputLabel>
            <Select
              value={zoneFilter}
              label="Zone"
              onChange={(e) => setZoneFilter(e.target.value)}
              sx={{ bgcolor: 'rgba(255,255,255,0.03)', fontWeight: 700 }}
            >
              <MenuItem value="all">All Zones</MenuItem>
              <MenuItem value="zone_A">Zone A (Sector 4)</MenuItem>
            </Select>
          </FormControl>

          {/* Risk Level Filter */}
          <ButtonGroup size="small" variant="outlined">
            <Button
              variant={riskFilter === 'all' ? 'contained' : 'outlined'}
              onClick={() => setRiskFilter('all')}
              sx={{ fontWeight: 700, textTransform: 'none' }}
            >
              All Nodes ({topology?.nodes?.length || 0})
            </Button>
            <Button
              color="error"
              variant={riskFilter === 'critical' ? 'contained' : 'outlined'}
              onClick={() => setRiskFilter('critical')}
              sx={{ fontWeight: 700, textTransform: 'none' }}
            >
              Critical ({topology?.nodes?.filter((n) => n.risk_level === 'critical').length || 0})
            </Button>
          </ButtonGroup>

          {/* Tile Layer Toggle */}
          <ButtonGroup size="small" variant="outlined">
            <Button
              variant={tileTheme === 'dark' ? 'contained' : 'outlined'}
              onClick={() => setTileTheme('dark')}
              sx={{ fontWeight: 700, fontSize: '0.75rem', textTransform: 'none' }}
            >
              Dark
            </Button>
            <Button
              variant={tileTheme === 'streets' ? 'contained' : 'outlined'}
              onClick={() => setTileTheme('streets')}
              sx={{ fontWeight: 700, fontSize: '0.75rem', textTransform: 'none' }}
            >
              Streets
            </Button>
            <Button
              variant={tileTheme === 'satellite' ? 'contained' : 'outlined'}
              onClick={() => setTileTheme('satellite')}
              sx={{ fontWeight: 700, fontSize: '0.75rem', textTransform: 'none' }}
            >
              Satellite
            </Button>
          </ButtonGroup>

          {/* Refresh & GeoJSON Export */}
          <Tooltip title="Refresh GIS Topology">
            <IconButton onClick={() => fetchTopology(true)} sx={{ border: `1px solid ${themeConfig.border}` }}>
              <RefreshIcon sx={{ color: themeConfig.primary }} />
            </IconButton>
          </Tooltip>

          <Button
            variant="outlined"
            size="small"
            startIcon={<DownloadIcon />}
            onClick={handleExportGeoJson}
            sx={{ fontWeight: 700, textTransform: 'none', borderColor: themeConfig.border }}
          >
            Export GeoJSON
          </Button>
        </Box>
      </Box>

      {/* Grid Summary Stats Bar */}
      {zoneSummary && (
        <Grid container spacing={2} sx={{ mb: 2.5 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ p: 2, bgcolor: 'rgba(0, 212, 255, 0.05)', border: `1px solid rgba(0, 212, 255, 0.2)` }}>
              <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 700 }}>
                FEEDER INFLOW (TRANSFORMER)
              </Typography>
              <Typography variant="h5" sx={{ fontWeight: 800, color: themeConfig.primary, mt: 0.5 }}>
                {zoneSummary.feeder_power_kw.toFixed(2)} kW
              </Typography>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ p: 2, bgcolor: 'rgba(0, 230, 118, 0.05)', border: `1px solid rgba(0, 230, 118, 0.2)` }}>
              <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 700 }}>
                CONSUMER LOGGED DRAW
              </Typography>
              <Typography variant="h5" sx={{ fontWeight: 800, color: '#00e676', mt: 0.5 }}>
                {zoneSummary.consumer_total_power_kw.toFixed(2)} kW
              </Typography>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ p: 2, bgcolor: zoneSummary.loss_percentage > 20 ? 'rgba(255, 23, 68, 0.05)' : 'rgba(255, 152, 0, 0.05)', border: `1px solid ${zoneSummary.loss_percentage > 20 ? 'rgba(255, 23, 68, 0.3)' : 'rgba(255, 152, 0, 0.3)'}` }}>
              <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 700 }}>
                DISTRIBUTION LINE LOSS
              </Typography>
              <Typography variant="h5" sx={{ fontWeight: 800, color: zoneSummary.loss_percentage > 20 ? 'error.main' : 'warning.main', mt: 0.5 }}>
                {zoneSummary.loss_percentage.toFixed(1)}% {zoneSummary.loss_percentage > 20 ? '⚠️ High Theft' : 'Normal'}
              </Typography>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ p: 2, bgcolor: 'rgba(255, 255, 255, 0.02)', border: `1px solid ${themeConfig.border}` }}>
              <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 700 }}>
                MAPPED NODES / HIGH RISK
              </Typography>
              <Typography variant="h5" sx={{ fontWeight: 800, color: '#fff', mt: 0.5 }}>
                {topology?.total_nodes || 0} Nodes / <span style={{ color: '#ff1744' }}>{zoneSummary.critical_nodes_count} Alert</span>
              </Typography>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Main Map + Inspector View */}
      <Box sx={{ flexGrow: 1, minHeight: 520, height: 'calc(100vh - 300px)' }}>
        {loading && !topology ? (
          <LinearProgress />
        ) : (
          <Grid container spacing={3} sx={{ height: '100%' }}>
            {/* Map Frame (Left Column) */}
            <Grid item xs={12} lg={8} sx={{ height: '100%' }}>
              <RiskMap
                nodes={filteredNodes}
                edges={topology?.edges || []}
                selectedDeviceId={selectedDeviceId}
                onSelectDevice={setSelectedDeviceId}
                tileTheme={tileTheme}
              />
            </Grid>

            {/* Selected Node Sidebar (Right Column) */}
            <Grid item xs={12} lg={4} sx={{ height: '100%', overflowY: 'auto' }}>
              {selectedNode ? (
                <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                  <CardContent sx={{ p: 3, flexGrow: 1 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                      <Box>
                        <Typography variant="h6" sx={{ fontWeight: 800, color: themeConfig.primary }}>
                          📍 Node Pin Inspector
                        </Typography>
                        <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block' }}>
                          Device ID: <strong style={{ color: '#fff' }}>{selectedNode.device_id}</strong>
                        </Typography>
                      </Box>

                      <Tooltip title="Edit Physical Coordinates">
                        <IconButton
                          size="small"
                          onClick={() => setEditOpen(true)}
                          sx={{ bgcolor: 'rgba(0, 212, 255, 0.1)', color: themeConfig.primary }}
                        >
                          <EditLocationAltIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </Box>

                    <Divider sx={{ mb: 2 }} />

                    {/* Node Overview Properties */}
                    <List sx={{ bgcolor: 'rgba(0,0,0,0.15)', borderRadius: 2, p: 1, mb: 2.5 }}>
                      <ListItem disablePadding sx={{ py: 0.5, px: 1 }}>
                        <ListItemText primary="Label" secondary={selectedNode.name} />
                      </ListItem>
                      <ListItem disablePadding sx={{ py: 0.5, px: 1 }}>
                        <ListItemText primary="Grid Type" secondary={selectedNode.device_type.toUpperCase()} />
                      </ListItem>
                      <ListItem disablePadding sx={{ py: 0.5, px: 1 }}>
                        <ListItemText primary="Zone Segment" secondary={selectedNode.zone_id || 'N/A'} />
                      </ListItem>
                      <ListItem disablePadding sx={{ py: 0.5, px: 1 }}>
                        <ListItemText
                          primary="GPS Coordinates"
                          secondary={`${selectedNode.latitude.toFixed(5)}, ${selectedNode.longitude.toFixed(5)}`}
                        />
                      </ListItem>
                      {selectedNode.location && (
                        <ListItem disablePadding sx={{ py: 0.5, px: 1 }}>
                          <ListItemText primary="Physical Address" secondary={selectedNode.location} />
                        </ListItem>
                      )}
                    </List>

                    {/* Live Electrical Telemetry */}
                    <Typography variant="subtitle2" sx={{ fontWeight: 800, mb: 1.5, display: 'flex', alignItems: 'center', gap: 1 }}>
                      <SensorsIcon sx={{ color: themeConfig.secondary, fontSize: 18 }} />
                      Real-time Electrical Telemetry
                    </Typography>

                    {telemetryLoading ? (
                      <LinearProgress />
                    ) : (
                      <Grid container spacing={1.5} sx={{ mb: 2.5 }}>
                        <Grid item xs={6}>
                          <Box sx={{ p: 1.5, bgcolor: 'rgba(255,255,255,0.01)', border: `1px solid ${themeConfig.border}`, borderRadius: 1.5 }}>
                            <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 700 }}>VOLTAGE</Typography>
                            <Typography variant="body1" sx={{ fontWeight: 800 }}>
                              {latestRead?.voltage || selectedNode.voltage || 230.0} V
                            </Typography>
                          </Box>
                        </Grid>
                        <Grid item xs={6}>
                          <Box sx={{ p: 1.5, bgcolor: 'rgba(255,255,255,0.01)', border: `1px solid ${themeConfig.border}`, borderRadius: 1.5 }}>
                            <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 700 }}>CURRENT</Typography>
                            <Typography variant="body1" sx={{ fontWeight: 800 }}>
                              {latestRead?.current || selectedNode.current || 0.0} A
                            </Typography>
                          </Box>
                        </Grid>
                        <Grid item xs={6}>
                          <Box sx={{ p: 1.5, bgcolor: 'rgba(255,255,255,0.01)', border: `1px solid ${themeConfig.border}`, borderRadius: 1.5 }}>
                            <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 700 }}>ACTIVE POWER</Typography>
                            <Typography variant="body1" sx={{ fontWeight: 800 }}>
                              {latestRead?.power || selectedNode.power || 0.0} kW
                            </Typography>
                          </Box>
                        </Grid>
                        <Grid item xs={6}>
                          <Box sx={{ p: 1.5, bgcolor: 'rgba(255,255,255,0.01)', border: `1px solid ${themeConfig.border}`, borderRadius: 1.5 }}>
                            <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 700 }}>AI ANOMALY SCORE</Typography>
                            <Typography
                              variant="body1"
                              sx={{
                                fontWeight: 800,
                                color: (selectedNode.anomaly_score || 0) >= 0.7 ? 'error.main' : 'success.main',
                              }}
                            >
                              {(selectedNode.anomaly_score || 0).toFixed(2)}
                            </Typography>
                          </Box>
                        </Grid>
                      </Grid>
                    )}

                    {/* Trust & Risk Summary Card */}
                    <Box
                      sx={{
                        p: 2,
                        bgcolor: selectedNode.risk_level === 'critical' ? 'rgba(255, 23, 68, 0.08)' : 'rgba(0, 212, 255, 0.05)',
                        border: `1px solid ${selectedNode.risk_level === 'critical' ? 'rgba(255, 23, 68, 0.3)' : 'rgba(0, 212, 255, 0.2)'}`,
                        borderRadius: 2,
                        mb: 2,
                      }}
                    >
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                        <Typography variant="body2" sx={{ fontWeight: 800 }}>
                          Risk Rating: <span style={{ textTransform: 'uppercase', color: selectedNode.risk_level === 'critical' ? '#ff1744' : '#00e676' }}>{selectedNode.risk_level}</span>
                        </Typography>
                        <Chip
                          label={`${selectedNode.trust_score ? selectedNode.trust_score.toFixed(0) : 99}% Trust`}
                          color={(selectedNode.trust_score || 99) >= 80 ? 'success' : 'error'}
                          size="small"
                          sx={{ fontWeight: 800 }}
                        />
                      </Box>
                      {selectedNode.risk_level === 'critical' && (
                        <Typography variant="caption" sx={{ color: '#ff8a80', display: 'block' }}>
                          ⚠️ Sudden load drop detected while branch sensor registers draw. Potential meter bypass!
                        </Typography>
                      )}
                    </Box>
                  </CardContent>
                </Card>
              ) : (
                <Box sx={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', p: 4, bgcolor: 'rgba(255,255,255,0.01)', border: `1px dashed ${themeConfig.border}`, borderRadius: 2 }}>
                  <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                    Select a pin on the GIS map to inspect details.
                  </Typography>
                </Box>
              )}
            </Grid>
          </Grid>
        )}
      </Box>

      {/* Edit Coordinates Dialog */}
      <Dialog open={editOpen} onClose={() => setEditOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle sx={{ fontWeight: 800, color: themeConfig.primary }}>
          📍 Edit Node GPS Coordinates
        </DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
          <Typography variant="caption" sx={{ color: 'text.secondary' }}>
            Updating location for <strong>{selectedDeviceId}</strong> ({selectedNode?.name})
          </Typography>

          {editMsg && (
            <MuiAlert severity={editMsg.type} sx={{ py: 0.5 }}>
              {editMsg.text}
            </MuiAlert>
          )}

          <TextField
            label="Latitude"
            type="number"
            value={editLat}
            onChange={(e) => setEditLat(e.target.value)}
            fullWidth
            size="small"
            inputProps={{ step: '0.0001', min: -90, max: 90 }}
          />

          <TextField
            label="Longitude"
            type="number"
            value={editLng}
            onChange={(e) => setEditLng(e.target.value)}
            fullWidth
            size="small"
            inputProps={{ step: '0.0001', min: -180, max: 180 }}
          />

          <TextField
            label="Physical Address / Pole Label"
            value={editLocation}
            onChange={(e) => setEditLocation(e.target.value)}
            fullWidth
            size="small"
          />
        </DialogContent>
        <DialogActions sx={{ p: 2 }}>
          <Button onClick={() => setEditOpen(false)} sx={{ color: 'text.secondary' }}>
            Cancel
          </Button>
          <Button
            variant="contained"
            onClick={handleSaveCoordinates}
            disabled={editSaving}
            sx={{ fontWeight: 800, background: `linear-gradient(135deg, ${themeConfig.primary}, ${themeConfig.secondary})` }}
          >
            {editSaving ? 'Saving...' : 'Update Location'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
