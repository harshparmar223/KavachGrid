// KAVACHGRID 3.0 — GIS Risk Map Component
// Interactive geospatial grid visualizer with live electrical power flows, risk indicators & tile controls.
'use client';

import React, { useEffect, useMemo } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, Tooltip, useMap } from 'react-leaflet';
import L from 'leaflet';
import { Box, Typography, Chip, Grid, Button, ButtonGroup } from '@mui/material';
import { themeConfig } from '@/theme/theme';
import { Device, GisEdge, GisNode } from '@/lib/types';

import 'leaflet/dist/leaflet.css';

interface RiskMapProps {
  nodes?: GisNode[];
  edges?: GisEdge[];
  devices?: Device[];
  selectedDeviceId?: string;
  onSelectDevice?: (deviceId: string) => void;
  tileTheme?: 'dark' | 'streets' | 'satellite';
}

// Sub-component to handle map center/bounds updates dynamically
function MapUpdater({
  center,
  nodes,
  selectedId,
}: {
  center: [number, number];
  nodes: GisNode[];
  selectedId?: string;
}) {
  const map = useMap();
  const initialFit = React.useRef(false);

  useEffect(() => {
    if (!initialFit.current && nodes.length > 1) {
      const bounds = L.latLngBounds(nodes.map((n) => [n.latitude, n.longitude]));
      map.fitBounds(bounds, { padding: [60, 60], maxZoom: 17 });
      initialFit.current = true;
    } else if (selectedId) {
      const selected = nodes.find((n) => n.device_id === selectedId);
      if (selected) {
        map.flyTo([selected.latitude, selected.longitude], Math.max(map.getZoom(), 16), { duration: 1.0 });
      }
    }
  }, [center, nodes, selectedId, map]);

  return null;
}

export default function RiskMap({
  nodes,
  edges,
  devices,
  selectedDeviceId,
  onSelectDevice,
  tileTheme = 'dark',
}: RiskMapProps) {

  // Consolidate devices into standardized GisNodes
  const mapNodes: GisNode[] = useMemo(() => {
    if (nodes && nodes.length > 0) return nodes;
    if (devices && devices.length > 0) {
      return devices
        .filter((d) => d.latitude !== null && d.longitude !== null)
        .map((d) => ({
          device_id: d.device_id,
          name: d.name,
          device_type: d.device_type,
          location: d.location,
          latitude: d.latitude!,
          longitude: d.longitude!,
          zone_id: d.zone_id,
          status: d.status,
          voltage: 230.0,
          current: d.device_type === 'feeder' ? 40.0 : 4.0,
          power: d.device_type === 'feeder' ? 9.2 : 0.9,
          power_factor: 0.98,
          energy: 1000.0,
          trust_score: 99.0,
          anomaly_score: d.status === 'warning' ? 0.85 : 0.05,
          overall_risk: d.status === 'warning' ? 88.0 : 10.0,
          risk_level: d.status === 'warning' ? 'critical' : 'low',
          active_alerts_count: d.status === 'warning' ? 1 : 0,
          last_seen_at: d.last_seen_at,
        }));
    }
    return [];
  }, [nodes, devices]);

  // Consolidate edges
  const mapEdges: GisEdge[] = useMemo(() => {
    if (edges && edges.length > 0) return edges;
    const feeder = mapNodes.find((d) => d.device_type === 'feeder');
    if (!feeder) return [];
    return mapNodes
      .filter((c) => c.device_type !== 'feeder')
      .map((c, i) => ({
        id: `auto-edge-${i}`,
        from_node: feeder.device_id,
        to_node: c.device_id,
        from_coords: [feeder.latitude, feeder.longitude] as [number, number],
        to_coords: [c.latitude, c.longitude] as [number, number],
        edge_type: c.device_type === 'localization' ? 'feeder_to_branch' : 'feeder_to_consumer',
        status: (c.risk_level === 'critical' || c.status === 'warning') ? 'critical' : 'normal',
        power_flow_kw: c.power || 1.2,
        loss_estimated_pct: (c.risk_level === 'critical' || c.status === 'warning') ? 32.0 : 1.5,
      }));
  }, [edges, mapNodes]);

  // Inject CSS animations for glowing GIS markers
  useEffect(() => {
    const styleId = 'kavachgrid-leaflet-styles';
    if (!document.getElementById(styleId)) {
      const style = document.createElement('style');
      style.id = styleId;
      style.innerHTML = `
        .pulse-feeder {
          background: #00d4ff;
          border: 2.5px solid #ffffff;
          border-radius: 50%;
          box-shadow: 0 0 16px #00d4ff;
          animation: feeder-glow 2s infinite ease-in-out;
        }
        .pulse-localization {
          background: #ffb74d;
          border: 2px solid #ffffff;
          border-radius: 50%;
          box-shadow: 0 0 12px #ffb74d;
        }
        .pulse-consumer-green {
          background: #00e676;
          border: 2px solid #ffffff;
          border-radius: 50%;
          box-shadow: 0 0 8px #00e676;
        }
        .pulse-consumer-warning {
          background: #ff9800;
          border: 2px solid #ffffff;
          border-radius: 50%;
          box-shadow: 0 0 12px #ff9800;
          animation: map-pulse 1.5s infinite;
        }
        .pulse-consumer-critical {
          background: #ff1744;
          border: 2.5px solid #ffffff;
          border-radius: 50%;
          box-shadow: 0 0 18px #ff1744;
          animation: critical-pulse 0.9s infinite alternate;
        }
        .selected-pin {
          outline: 3px solid #00d4ff;
          outline-offset: 3px;
        }
        @keyframes feeder-glow {
          0%, 100% { box-shadow: 0 0 10px #00d4ff; }
          50% { box-shadow: 0 0 24px #00d4ff; }
        }
        @keyframes map-pulse {
          0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(255, 152, 0, 0.7); }
          70% { transform: scale(1.15); box-shadow: 0 0 0 10px rgba(255, 152, 0, 0); }
          100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(255, 152, 0, 0); }
        }
        @keyframes critical-pulse {
          0% { transform: scale(1); box-shadow: 0 0 10px #ff1744; }
          100% { transform: scale(1.3); box-shadow: 0 0 25px #ff1744, 0 0 35px rgba(255, 23, 68, 0.5); }
        }
        .dark-tiles .leaflet-tile {
          filter: brightness(0.55) invert(1) contrast(2.8) hue-rotate(200deg) saturate(0.35) brightness(0.85);
        }
        .leaflet-popup-content-wrapper {
          background: #0f1c32 !important;
          border: 1px solid rgba(0, 212, 255, 0.3) !important;
          border-radius: 12px !important;
          color: #fff !important;
          backdrop-filter: blur(10px);
        }
        .leaflet-popup-tip {
          background: #0f1c32 !important;
        }
      `;
      document.head.appendChild(style);
    }
  }, []);

  // Marker icon builder
  const createMarkerIcon = (node: GisNode, isSelected: boolean) => {
    let className = 'pulse-consumer-green';
    if (node.device_type === 'feeder') {
      className = 'pulse-feeder';
    } else if (node.device_type === 'localization') {
      className = 'pulse-localization';
    } else if (node.risk_level === 'critical' || (node.anomaly_score || 0) >= 0.7) {
      className = 'pulse-consumer-critical';
    } else if (node.risk_level === 'high' || node.status === 'warning') {
      className = 'pulse-consumer-warning';
    }

    if (isSelected) {
      className += ' selected-pin';
    }

    const size = node.device_type === 'feeder' ? 22 : node.device_type === 'localization' ? 16 : 14;
    return L.divIcon({
      className: className,
      iconSize: [size, size],
      iconAnchor: [size / 2, size / 2],
    });
  };

  // Center coordinate
  const centerNode = mapNodes.find((n) => n.device_id === selectedDeviceId);
  const mapCenter: [number, number] = centerNode
    ? [centerNode.latitude, centerNode.longitude]
    : mapNodes.length > 0
    ? [mapNodes[0].latitude, mapNodes[0].longitude]
    : [28.6139, 77.2090];

  // Tile URL based on theme (100% free, full zoom support, no watermarks, no missing tiles)
  const tileUrl =
    tileTheme === 'satellite'
      ? 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
      : 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';

  const tileAttribution =
    tileTheme === 'satellite'
      ? 'Tiles &copy; Esri &mdash; Earthstar Geographics'
      : '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors';

  return (
    <Box
      className={tileTheme === 'dark' ? 'dark-tiles' : ''}
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
        center={mapCenter}
        zoom={16}
        maxZoom={19}
        scrollWheelZoom={true}
        style={{ width: '100%', height: '100%' }}
      >
        <MapUpdater center={mapCenter} nodes={mapNodes} selectedId={selectedDeviceId} />

        <TileLayer
          attribution={tileAttribution}
          url={tileUrl}
          maxZoom={19}
        />

        {/* Polylines for electric grid connectivity & power flow */}
        {mapEdges.map((edge) => {
          const isCritical = edge.status === 'critical';
          const isWarning = edge.status === 'warning';
          const strokeColor = isCritical
            ? '#ff1744'
            : isWarning
            ? '#ff9800'
            : '#00d4ff';

          return (
            <Polyline
              key={edge.id}
              positions={[edge.from_coords, edge.to_coords]}
              pathOptions={{
                color: strokeColor,
                weight: isCritical ? 3.5 : 2,
                opacity: isCritical ? 0.9 : 0.6,
                dashArray: isCritical ? '6, 6' : isWarning ? '4, 4' : undefined,
              }}
            >
              <Tooltip sticky>
                <Box sx={{ p: 0.5 }}>
                  <Typography variant="caption" sx={{ fontWeight: 800, color: strokeColor, display: 'block' }}>
                    {edge.edge_type.replace(/_/g, ' ').toUpperCase()}
                  </Typography>
                  <Typography variant="caption" sx={{ color: '#fff', display: 'block' }}>
                    Flow: <strong>{edge.power_flow_kw?.toFixed(2) || '0.00'} kW</strong>
                  </Typography>
                  {edge.loss_estimated_pct !== null && (
                    <Typography variant="caption" sx={{ color: isCritical ? '#ff1744' : '#00e676', display: 'block' }}>
                      Loss: <strong>{edge.loss_estimated_pct?.toFixed(1)}%</strong>
                    </Typography>
                  )}
                </Box>
              </Tooltip>
            </Polyline>
          );
        })}

        {/* Node Markers */}
        {mapNodes.map((node) => {
          const isSelected = selectedDeviceId === node.device_id;
          return (
            <Marker
              key={node.device_id}
              position={[node.latitude, node.longitude]}
              icon={createMarkerIcon(node, isSelected)}
              eventHandlers={{
                click: () => onSelectDevice && onSelectDevice(node.device_id),
              }}
            >
              <Popup>
                <Box sx={{ p: 1, minWidth: 220 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.5 }}>
                    <Typography variant="subtitle2" sx={{ fontWeight: 800, color: themeConfig.primary }}>
                      {node.device_id}
                    </Typography>
                    <Chip
                      label={node.device_type.toUpperCase()}
                      size="small"
                      sx={{
                        height: 18,
                        fontSize: '0.65rem',
                        fontWeight: 800,
                        bgcolor: 'rgba(0, 212, 255, 0.15)',
                        color: themeConfig.primary,
                      }}
                    />
                  </Box>

                  <Typography variant="body2" sx={{ fontWeight: 700, mb: 1, color: '#fff' }}>
                    {node.name}
                  </Typography>

                  <Grid container spacing={1} sx={{ mb: 1.5 }}>
                    <Grid item xs={6}>
                      <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block' }}>
                        POWER DRAW
                      </Typography>
                      <Typography variant="caption" sx={{ fontWeight: 800, color: '#fff' }}>
                        {node.power !== null && node.power !== undefined ? `${node.power.toFixed(2)} kW` : 'N/A'}
                      </Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block' }}>
                        VOLTAGE
                      </Typography>
                      <Typography variant="caption" sx={{ fontWeight: 800, color: '#fff' }}>
                        {node.voltage !== null && node.voltage !== undefined ? `${node.voltage.toFixed(1)} V` : 'N/A'}
                      </Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block' }}>
                        RISK STATUS
                      </Typography>
                      <Typography
                        variant="caption"
                        sx={{
                          fontWeight: 800,
                          color:
                            node.risk_level === 'critical'
                              ? 'error.main'
                              : node.risk_level === 'medium' || node.status === 'warning'
                              ? 'warning.main'
                              : 'success.main',
                        }}
                      >
                        {(node.risk_level || node.status).toUpperCase()}
                      </Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block' }}>
                        TRUST SCORE
                      </Typography>
                      <Typography variant="caption" sx={{ fontWeight: 800, color: '#00d4ff' }}>
                        {node.trust_score ? `${node.trust_score.toFixed(0)}%` : '99%'}
                      </Typography>
                    </Grid>
                  </Grid>

                  <Button
                    variant="contained"
                    size="small"
                    fullWidth
                    sx={{
                      fontWeight: 800,
                      textTransform: 'none',
                      fontSize: '0.75rem',
                      borderRadius: 1.5,
                      background: `linear-gradient(135deg, ${themeConfig.primary}, ${themeConfig.secondary})`,
                    }}
                    onClick={() => onSelectDevice && onSelectDevice(node.device_id)}
                  >
                    Inspect Node Telemetry
                  </Button>
                </Box>
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>
    </Box>
  );
}
