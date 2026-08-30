"use client";

import React from 'react';
import { Card, CardContent, Typography, Box, Chip, Grid, Button } from '@mui/material';
import {
  Router as FeederIcon,
  Person as ConsumerIcon,
  MyLocation as LocalIcon,
  Circle as DotIcon,
} from '@mui/icons-material';
import { Device } from '@/lib/types';
import { themeConfig } from '@/theme/theme';

interface DeviceCardProps {
  device: Device;
  onSelect?: (deviceId: string) => void;
  selected?: boolean;
}

export default function DeviceCard({ device, onSelect, selected = false }: DeviceCardProps) {
  const getIcon = () => {
    switch (device.device_type) {
      case 'feeder':
        return <FeederIcon sx={{ color: themeConfig.primary }} />;
      case 'consumer':
        return <ConsumerIcon sx={{ color: themeConfig.secondary }} />;
      case 'localization':
        return <LocalIcon sx={{ color: 'warning.main' }} />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online':
        return 'success.main';
      case 'offline':
        return 'text.secondary';
      case 'warning':
        return 'warning.main';
      default:
        return 'text.secondary';
    }
  };

  return (
    <Card
      onClick={() => onSelect && onSelect(device.device_id)}
      sx={{
        cursor: onSelect ? 'pointer' : 'default',
        borderColor: selected ? themeConfig.primary : themeConfig.border,
        boxShadow: selected ? `0 0 15px rgba(0, 212, 255, 0.2)` : 'none',
        '&:hover': {
          borderColor: themeConfig.primary,
        },
      }}
    >
      <CardContent sx={{ p: 2.5, '&:last-child': { pb: 2.5 } }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {getIcon()}
            <Typography variant="body1" sx={{ fontWeight: 700, color: 'text.primary' }}>
              {device.device_id}
            </Typography>
          </Box>
          <Chip
            icon={<DotIcon sx={{ fontSize: '10px !important', color: getStatusColor(device.status) }} />}
            label={device.status.toUpperCase()}
            size="small"
            variant="outlined"
            sx={{
              borderColor: getStatusColor(device.status),
              color: getStatusColor(device.status),
              fontWeight: 700,
              fontSize: '0.65rem',
              height: 20,
              '& .MuiChip-icon': {
                color: getStatusColor(device.status),
              },
            }}
          />
        </Box>

        <Typography variant="body2" noWrap sx={{ fontWeight: 600, color: 'text.primary', mb: 0.5 }}>
          {device.name}
        </Typography>
        <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block', mb: 2 }}>
          {device.location || 'Unknown Location'}
        </Typography>

        <Grid container spacing={1} sx={{ bgcolor: 'rgba(255,255,255,0.01)', p: 1, borderRadius: 1 }}>
          <Grid item xs={6}>
            <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block' }}>
              TYPE
            </Typography>
            <Typography variant="body2" sx={{ fontWeight: 700, textTransform: 'capitalize' }}>
              {device.device_type}
            </Typography>
          </Grid>
          <Grid item xs={6}>
            <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block' }}>
              ZONE
            </Typography>
            <Typography variant="body2" sx={{ fontWeight: 700 }}>
              {device.zone_id || 'N/A'}
            </Typography>
          </Grid>
        </Grid>

        {device.last_seen_at && (
          <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block', mt: 1.5, fontSize: '0.7rem', textAlign: 'right' }}>
            Last seen: {new Date(device.last_seen_at).toLocaleTimeString()}
          </Typography>
        )}
      </CardContent>
    </Card>
  );
}
