"use client";

import React from 'react';
import { Box, Typography } from '@mui/material';
import { themeConfig } from '@/theme/theme';

interface RiskGaugeProps {
  score: number;
}

export default function RiskGauge({ score }: RiskGaugeProps) {
  const normalizedScore = Math.max(0, Math.min(100, score));

  // Determine colors and labels
  const getRiskCategory = (val: number) => {
    if (val >= 75) return { label: 'CRITICAL', color: themeConfig.error, glow: 'rgba(244, 67, 54, 0.4)' };
    if (val >= 50) return { label: 'HIGH', color: themeConfig.warning, glow: 'rgba(255, 152, 0, 0.4)' };
    if (val >= 25) return { label: 'MEDIUM', color: '#00b0ff', glow: 'rgba(0, 176, 255, 0.4)' };
    return { label: 'LOW', color: themeConfig.success, glow: 'rgba(76, 175, 80, 0.4)' };
  };

  const risk = getRiskCategory(normalizedScore);

  // SVG parameters
  const radius = 70;
  const strokeWidth = 14;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (normalizedScore / 100) * circumference;

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        position: 'relative',
        py: 2,
      }}
    >
      <Box sx={{ position: 'relative', width: 170, height: 170 }}>
        {/* SVG Gauge */}
        <svg width="100%" height="100%" viewBox="0 0 170 170" style={{ transform: 'rotate(-90deg)' }}>
          {/* Background Track */}
          <circle
            cx="85"
            cy="85"
            r={radius}
            fill="transparent"
            stroke="rgba(255, 255, 255, 0.05)"
            strokeWidth={strokeWidth}
          />
          {/* Foreground Arc */}
          <circle
            cx="85"
            cy="85"
            r={radius}
            fill="transparent"
            stroke={risk.color}
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            style={{
              transition: 'stroke-dashoffset 0.8s ease-in-out',
              filter: `drop-shadow(0 0 6px ${risk.color})`,
            }}
          />
        </svg>

        {/* Center Labels */}
        <Box
          sx={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Typography
            variant="h3"
            sx={{
              fontWeight: 800,
              fontFamily: 'monospace',
              color: 'text.primary',
              lineHeight: 1,
            }}
          >
            {normalizedScore}
          </Typography>
          <Typography
            variant="caption"
            sx={{
              fontWeight: 800,
              letterSpacing: '0.08em',
              color: risk.color,
              mt: 0.5,
              textShadow: `0 0 4px ${risk.glow}`,
            }}
          >
            {risk.label}
          </Typography>
        </Box>
      </Box>
      <Typography variant="body2" sx={{ color: 'text.secondary', fontWeight: 600, mt: 1 }}>
        Composite Risk Rating
      </Typography>
    </Box>
  );
}
