"use client";

import React, { useState, useEffect } from 'react';
import {
  Grid,
  Box,
  Typography,
  Card,
  CardContent,
  TextField,
  MenuItem,
  Button,
  ButtonGroup,
  Chip,
  Divider,
  List,
  ListItem,
  ListItemText,
  LinearProgress,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Search as SearchIcon,
  SettingsBackupRestore as RebootIcon,
  Tune as QueryIcon,
} from '@mui/icons-material';
import DeviceCard from '@/components/cards/DeviceCard';
import { api } from '@/lib/api';
import { useApi } from '@/hooks/useApi';
import { Device, Telemetry } from '@/lib/types';
import { themeConfig } from '@/theme/theme';

export default function DevicesPage() {
  const { data: devices, loading, mutate } = useApi(api.getDevices);
  const [selectedDeviceId, setSelectedDeviceId] = useState<string>('');
  const [selectedDevice, setSelectedDevice] = useState<Device | null>(null);
  const [deviceTelemetry, setDeviceTelemetry] = useState<Telemetry[]>([]);
  const [telemetryLoading, setTelemetryLoading] = useState<boolean>(false);

  // Filters state
  const [search, setSearch] = useState<string>('');
  const [filterType, setFilterType] = useState<string>('all');
  const [filterStatus, setFilterStatus] = useState<string>('all');

  // Trigger telemetry fetch when device selection changes
  useEffect(() => {
    if (devices && devices.length > 0 && !selectedDeviceId) {
      setSelectedDeviceId(devices[0].device_id);
    }
  }, [devices, selectedDeviceId]);

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

  // Handle remote edge device commands
  const handleDeviceCommand = (command: string) => {
    alert(`Remote Command Sent: "${command}" to target device "${selectedDeviceId}" via secure MQTT kavachgrid/commands/${selectedDeviceId}`);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online':
        return 'success.main';
      case 'warning':
        return 'warning.main';
      default:
        return 'text.secondary';
    }
  };

  // Filter device list
  const filteredDevices = devices
    ? devices.filter((device) => {
        const matchesSearch =
          device.device_id.toLowerCase().includes(search.toLowerCase()) ||
          device.name.toLowerCase().includes(search.toLowerCase()) ||
          (device.location && device.location.toLowerCase().includes(search.toLowerCase()));

        const matchesType = filterType === 'all' || device.device_type === filterType;
        const matchesStatus = filterStatus === 'all' || device.status === filterStatus;

        return matchesSearch && matchesType && matchesStatus;
      })
    : [];

  const latestRead = deviceTelemetry.length > 0 ? deviceTelemetry[deviceTelemetry.length - 1] : null;

  return (
    <Box sx={{ flexGrow: 1 }}>
      {/* Title */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 800, color: 'text.primary', mb: 1 }}>
            Smart Nodes Directory
          </Typography>
          <Typography variant="body2" sx={{ color: 'text.secondary', fontWeight: 600 }}>
            List, filter, configure, and inspect registered grid edge nodes and meters.
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<RefreshIcon />}
          onClick={mutate}
          sx={{ bgcolor: 'rgba(0, 212, 255, 0.1)', color: 'primary.main', border: `1px solid ${themeConfig.primary}`, '&:hover': { bgcolor: 'rgba(0, 212, 255, 0.2)' } }}
        >
          Refresh Directory
        </Button>
      </Box>

      {/* Filter and Content Grid */}
      <Grid container spacing={3}>
        {/* Left Side: Filter and List */}
        <Grid item xs={12} md={7} lg={8}>
          {/* Filter Bar */}
          <Card sx={{ mb: 3 }}>
            <CardContent sx={{ p: 2 }}>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    size="small"
                    variant="outlined"
                    placeholder="Search by ID, name, location..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    InputProps={{
                      startAdornment: <SearchIcon sx={{ color: 'text.secondary', mr: 1 }} />,
                    }}
                  />
                </Grid>
                <Grid item xs={6} sm={3}>
                  <TextField
                    select
                    fullWidth
                    size="small"
                    variant="outlined"
                    label="Type"
                    value={filterType}
                    onChange={(e) => setFilterType(e.target.value)}
                  >
                    <MenuItem value="all">All Types</MenuItem>
                    <MenuItem value="feeder">Substation Feeder</MenuItem>
                    <MenuItem value="consumer">Consumer Meter</MenuItem>
                    <MenuItem value="localization">Localization CT</MenuItem>
                  </TextField>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <TextField
                    select
                    fullWidth
                    size="small"
                    variant="outlined"
                    label="Status"
                    value={filterStatus}
                    onChange={(e) => setFilterStatus(e.target.value)}
                  >
                    <MenuItem value="all">All Statuses</MenuItem>
                    <MenuItem value="online">Online</MenuItem>
                    <MenuItem value="warning">Warning</MenuItem>
                    <MenuItem value="offline">Offline</MenuItem>
                  </TextField>
                </Grid>
              </Grid>
            </CardContent>
          </Card>

          {/* Devices Grid List */}
          {loading ? (
            <LinearProgress />
          ) : filteredDevices.length === 0 ? (
            <Typography variant="body1" sx={{ color: 'text.secondary', py: 4, textAlign: 'center' }}>
              No devices match the active search criteria.
            </Typography>
          ) : (
            <Grid container spacing={3.2}>
              {filteredDevices.map((device) => (
                <Grid item xs={12} sm={6} key={device.id}>
                  <DeviceCard
                    device={device}
                    onSelect={setSelectedDeviceId}
                    selected={device.device_id === selectedDeviceId}
                  />
                </Grid>
              ))}
            </Grid>
          )}
        </Grid>

        {/* Right Side: Active Selection Details & Telemetry */}
        <Grid item xs={12} md={5} lg={4}>
          {selectedDevice && (
            <Card sx={{ position: 'sticky', top: 110 }}>
              <CardContent sx={{ p: 3 }}>
                <Typography variant="h6" sx={{ fontWeight: 800, mb: 1, color: themeConfig.primary }}>
                  🔍 Node Inspector
                </Typography>
                <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block', mb: 2 }}>
                  Selected Target: <strong style={{ color: '#fff' }}>{selectedDevice.device_id}</strong>
                </Typography>
                
                <Divider sx={{ mb: 2 }} />

                {/* Device Metadata */}
                <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 1 }}>
                  Properties
                </Typography>
                <List sx={{ bgcolor: 'rgba(0,0,0,0.1)', borderRadius: 1, p: 1, mb: 3 }}>
                  <ListItem disablePadding sx={{ py: 0.5, px: 1 }}>
                    <ListItemText primary="Name" secondary={selectedDevice.name} />
                  </ListItem>
                  <ListItem disablePadding sx={{ py: 0.5, px: 1 }}>
                    <ListItemText primary="Zone" secondary={selectedDevice.zone_id || 'N/A'} />
                  </ListItem>
                  <ListItem disablePadding sx={{ py: 0.5, px: 1 }}>
                    <ListItemText primary="Hardware Address" secondary="ESP32 (0x7F2C0)" />
                  </ListItem>
                  <ListItem disablePadding sx={{ py: 0.5, px: 1 }}>
                    <ListItemText
                      primary="API Authentication Key"
                      secondary={
                        <code style={{ fontSize: '0.75rem', color: themeConfig.secondary }}>
                          {selectedDevice.api_key}
                        </code>
                      }
                    />
                  </ListItem>
                </List>

                {/* Latest Telemetry readings */}
                <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 1 }}>
                  Electrical Parameters
                </Typography>
                {telemetryLoading ? (
                  <LinearProgress />
                ) : latestRead ? (
                  <Grid container spacing={1} sx={{ mb: 3 }}>
                    <Grid item xs={6}>
                      <Box sx={{ p: 1.5, bgcolor: 'rgba(255,255,255,0.01)', border: `1px solid ${themeConfig.border}`, borderRadius: 1 }}>
                        <Typography variant="caption" sx={{ color: 'text.secondary' }}>VOLTAGE</Typography>
                        <Typography variant="body1" sx={{ fontWeight: 700 }}>{latestRead.voltage} V</Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={6}>
                      <Box sx={{ p: 1.5, bgcolor: 'rgba(255,255,255,0.01)', border: `1px solid ${themeConfig.border}`, borderRadius: 1 }}>
                        <Typography variant="caption" sx={{ color: 'text.secondary' }}>CURRENT</Typography>
                        <Typography variant="body1" sx={{ fontWeight: 700 }}>{latestRead.current} A</Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={6}>
                      <Box sx={{ p: 1.5, bgcolor: 'rgba(255,255,255,0.01)', border: `1px solid ${themeConfig.border}`, borderRadius: 1 }}>
                        <Typography variant="caption" sx={{ color: 'text.secondary' }}>POWER</Typography>
                        <Typography variant="body1" sx={{ fontWeight: 700 }}>{latestRead.power} kW</Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={6}>
                      <Box sx={{ p: 1.5, bgcolor: 'rgba(255,255,255,0.01)', border: `1px solid ${themeConfig.border}`, borderRadius: 1 }}>
                        <Typography variant="caption" sx={{ color: 'text.secondary' }}>FREQ</Typography>
                        <Typography variant="body1" sx={{ fontWeight: 700 }}>{latestRead.frequency || 50.0} Hz</Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={12}>
                      <Box sx={{ p: 1.5, bgcolor: 'rgba(255,255,255,0.01)', border: `1px solid ${themeConfig.border}`, borderRadius: 1, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Box>
                          <Typography variant="caption" sx={{ color: 'text.secondary' }}>TRUST VALIDATION</Typography>
                          <Typography variant="body2" sx={{ fontWeight: 700 }}>Trust Index Score</Typography>
                        </Box>
                        <Chip
                          label={`${latestRead.trust_score || 99}%`}
                          color={latestRead.trust_score && latestRead.trust_score >= 80 ? 'success' : 'warning'}
                          sx={{ fontWeight: 700 }}
                        />
                      </Box>
                    </Grid>
                  </Grid>
                ) : (
                  <Typography variant="body2" sx={{ color: 'text.secondary', py: 2 }}>
                    No active stream telemetry.
                  </Typography>
                )}

                {/* Remote command buttons */}
                <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 1 }}>
                  Remote Control Commands
                </Typography>
                <ButtonGroup fullWidth variant="outlined" color="primary">
                  <Button
                    startIcon={<QueryIcon />}
                    onClick={() => handleDeviceCommand('QUERY_CONFIG')}
                    sx={{ borderColor: themeConfig.border, '&:hover': { borderColor: themeConfig.primary } }}
                  >
                    Query Config
                  </Button>
                  <Button
                    startIcon={<RebootIcon />}
                    onClick={() => handleDeviceCommand('REBOOT_NODE')}
                    color="warning"
                    sx={{ borderColor: themeConfig.border, '&:hover': { borderColor: 'warning.main' } }}
                  >
                    Reboot Node
                  </Button>
                </ButtonGroup>
              </CardContent>
            </Card>
          )}
        </Grid>
      </Grid>
    </Box>
  );
}
