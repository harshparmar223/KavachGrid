// KAVACHGRID 3.0 — Alert Card. Phase 12.
'use client';

import React from 'react';
import { Card, CardContent, Typography, Box, Button, Chip } from '@mui/material';
import {
  Warning as WarningIcon,
  CheckCircle as AckIcon,
  Schedule as TimeIcon,
} from '@mui/icons-material';
import { Alert } from '@/lib/types';
import { themeConfig } from '@/theme/theme';

interface AlertCardProps {
  alert: Alert;
  onAcknowledge?: (alertId: string) => void;
}

export default function AlertCard({ alert, onAcknowledge }: AlertCardProps) {
  const getSeverityColors = (severity: string) => {
    switch (severity) {
      case 'critical':
        return {
          border: 'rgba(244, 67, 54, 0.4)',
          leftBorder: '#f44336',
          bg: 'rgba(244, 67, 54, 0.04)',
          text: '#f44336',
        };
      case 'high':
        return {
          border: 'rgba(255, 152, 0, 0.4)',
          leftBorder: '#ff9800',
          bg: 'rgba(255, 152, 0, 0.04)',
          text: '#ff9800',
        };
      case 'medium':
        return {
          border: 'rgba(0, 176, 255, 0.4)',
          leftBorder: '#00b0ff',
          bg: 'rgba(0, 176, 255, 0.04)',
          text: '#00b0ff',
        };
      default:
        return {
          border: 'rgba(76, 175, 80, 0.4)',
          leftBorder: '#4caf50',
          bg: 'rgba(76, 175, 80, 0.04)',
          text: '#4caf50',
        };
    }
  };

  const colors = getSeverityColors(alert.severity);

  return (
    <Card
      sx={{
        backgroundColor: colors.bg,
        borderColor: colors.border,
        borderLeft: `5px solid ${colors.leftBorder}`,
        position: 'relative',
        '&:hover': {
          boxShadow: `0 4px 15px rgba(0, 0, 0, 0.2)`,
        },
      }}
    >
      <CardContent sx={{ p: 2.5, '&:last-child': { pb: 2.5 } }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1.5 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <WarningIcon sx={{ color: colors.text }} />
            <Typography variant="body1" sx={{ fontWeight: 700, color: 'text.primary' }}>
              {alert.title}
            </Typography>
          </Box>
          <Chip
            label={alert.severity.toUpperCase()}
            size="small"
            sx={{
              backgroundColor: colors.leftBorder,
              color: '#0a1628',
              fontWeight: 800,
              fontSize: '0.65rem',
            }}
          />
        </Box>

        <Typography variant="body2" sx={{ color: 'text.primary', mb: 2, lineHeight: 1.5 }}>
          {alert.message}
        </Typography>

        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, color: 'text.secondary' }}>
            <TimeIcon sx={{ fontSize: 16 }} />
            <Typography variant="caption" sx={{ fontWeight: 600 }} suppressHydrationWarning>
              {new Date(alert.created_at).toLocaleString()}
            </Typography>
            {alert.device_id && (
              <Typography variant="caption" sx={{ ml: 1, color: 'primary.main', fontWeight: 700 }}>
                ({alert.device_id})
              </Typography>
            )}
          </Box>

          {alert.acknowledged ? (
            <Chip
              icon={<AckIcon sx={{ fontSize: '14px !important', color: 'success.main' }} />}
              label="ACKNOWLEDGED"
              size="small"
              variant="outlined"
              color="success"
              sx={{ fontWeight: 700, fontSize: '0.65rem' }}
            />
          ) : (
            onAcknowledge && (
              <Button
                variant="outlined"
                size="small"
                onClick={() => onAcknowledge(alert.id)}
                sx={{
                  color: colors.leftBorder,
                  borderColor: colors.leftBorder,
                  py: 0.25,
                  px: 1.5,
                  fontSize: '0.75rem',
                  fontWeight: 700,
                  '&:hover': {
                    borderColor: colors.leftBorder,
                    backgroundColor: `rgba(255, 255, 255, 0.02)`,
                  },
                }}
              >
                Acknowledge
              </Button>
            )
          )}
        </Box>
      </CardContent>
    </Card>
  );
}
