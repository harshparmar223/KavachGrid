// KAVACHGRID 3.0 — GIS Risk Map. Phase 12.
'use client';

import React, { useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet';
import L from 'leaflet';
import { Box, Typography, Chip, Grid } from '@mui/material';
import { themeConfig } from '@/theme/theme';
import { Device } from '@/lib/types';

import 'leaflet/dist/leaflet.css';

interface RiskMapProps {
  devices: Device[];
  onSelectDevice?: (deviceId: string) => void;
}

export default function RiskMap({ devices, onSelectDevice }: RiskMapProps) {
  
  // Custom Leaflet CSS overrides for marker icons
  useEffect(() => {
    // Inject custom pulse style for map pins
    const style = document.createElement('style');
    style.innerHTML = `
      .pulse-feeder {
        background: #00d4ff;
        border: 2px solid #ffffff;
        border-radius: 50%;
        box-shadow: 0 0 12px #00d4ff;
      }
      .pulse-consumer-green {
        background: #4caf50;
        border: 2px solid #ffffff;
        border-radius: 50%;
        box-shadow: 0 0 8px #4caf50;
      }
      .pulse-consumer-warning {
        background: #ff9800;
        border: 2px solid #ffffff;
        border-radius: 50%;
        box-shadow: 0 0 10px #ff9800;
        animation: map-pulse 1.5s infinite;
      }
      .pulse-consumer-critical {
        background: #f44336;
        border: 2px solid #ffffff;
        border-radius: 50%;
        box-shadow: 0 0 14px #f44336;
        animation: map-pulse 1s infinite alternate;
      }
      .pulse-localization {
        background: #ffb74d;
        border: 2px solid #ffffff;
        border-radius: 50%;
        box-shadow: 0 0 10px #ffb74d;
      }
      @keyframes map-pulse {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(255, 152, 0, 0.7); }
        70% { transform: scale(1.1); box-shadow: 0 0 0 10px rgba(255, 152, 0, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(255, 152, 0, 0); }
      }
    `;
    document.head.appendChild(style);
    return () => {
      document.head.removeChild(style);
    };
  }, []);

  // Create custom Leaflet div icons
  const createMarkerIcon = (type: string, status: string) => {
    let className = 'pulse-consumer-green';
    if (type === 'feeder') {
      className = 'pulse-feeder';
    } else if (type === 'localization') {
      className = 'pulse-localization';
    } else if (status === 'warning') {
      className = 'pulse-consumer-warning';
    } else if (status === 'offline') {
      className = 'pulse-consumer-warning';
    }
    
    // Critical risk indicator based on mock data IDs
    if (status === 'warning' && type === 'consumer') {
      className = 'pulse-consumer-critical';
    }

    return L.divIcon({
      className: className,
      iconSize: type === 'feeder' ? [18, 18] : [12, 12],
      iconAnchor: type === 'feeder' ? [9, 9] : [6, 6],
    });
  };

  const center: [number, number] = [28.6139, 77.2090]; // Delhi center coordinates

  // Generate connection polylines
  const feeder = devices.find((d) => d.device_type === 'feeder');
  const connections = devices
    .filter((d) => d.device_type === 'consumer' && d.latitude && d.longitude && feeder?.latitude && feeder?.longitude)
    .map((c) => ({
      from: [feeder!.latitude!, feeder!.longitude!] as [number, number],
      to: [c.latitude!, c.longitude!] as [number, number],
      status: c.status,
    }));

  return (
    <Box
      sx={{
        width: '100%',
        height: '100%',
        borderRadius: 3,
        overflow: 'hidden',
        border: `1px solid ${themeConfig.border}`,
        position: 'relative',
        backgroundColor: '#0a1628',
      }}
    >
      <MapContainer
        center={center}
        zoom={16}
        scrollWheelZoom={true}
        style={{ width: '100%', height: '100%' }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        />

        {/* Polylines for electric grid connectivity */}
        {connections.map((conn, idx) => (
          <Polyline
            key={idx}
            positions={[conn.from, conn.to]}
            color={
              conn.status === 'warning'
                ? themeConfig.error
                : themeConfig.secondary
            }
            weight={conn.status === 'warning' ? 3 : 2}
            opacity={0.65}
            dashArray={conn.status === 'warning' ? '6, 6' : undefined}
          />
        ))}

        {/* Device Markers */}
        {devices
          .filter((d) => d.latitude !== null && d.longitude !== null)
          .map((device) => (
            <Marker
              key={device.device_id}
              position={[device.latitude!, device.longitude!]}
              icon={createMarkerIcon(device.device_type, device.status)}
              eventHandlers={{
                click: () => onSelectDevice && onSelectDevice(device.device_id),
              }}
            >
              <Popup>
                <Box sx={{ p: 1, minWidth: 200, color: '#ccd6f6' }}>
                  <Typography variant="subtitle2" sx={{ fontWeight: 700, color: themeConfig.primary, mb: 0.5 }}>
                    {device.device_id}
                  </Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600, mb: 1, color: '#fff' }}>
                    {device.name}
                  </Typography>
                  <Grid container spacing={1} sx={{ mb: 1.5 }}>
                    <Grid item xs={6}>
                      <Typography variant="caption" sx={{ color: '#8892b0', display: 'block' }}>
                        TYPE
                      </Typography>
                      <Typography variant="caption" sx={{ fontWeight: 700, textTransform: 'uppercase' }}>
                        {device.device_type}
                      </Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="caption" sx={{ color: '#8892b0', display: 'block' }}>
                        STATUS
                      </Typography>
                      <Typography
                        variant="caption"
                        sx={{
                          fontWeight: 700,
                          color:
                            device.status === 'online'
                              ? 'success.main'
                              : 'warning.main',
                        }}
                      >
                        {device.status.toUpperCase()}
                      </Typography>
                    </Grid>
                  </Grid>

                  <Chip
                    label="Select for analytics"
                    size="small"
                    color="primary"
                    variant="outlined"
                    sx={{
                      width: '100%',
                      fontWeight: 700,
                      cursor: 'pointer',
                      fontSize: '0.7rem',
                    }}
                    onClick={() => onSelectDevice && onSelectDevice(device.device_id)}
                  />
                </Box>
              </Popup>
            </Marker>
          ))}
      </MapContainer>
    </Box>
  );
}
