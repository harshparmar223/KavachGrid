// KAVACHGRID 3.0 — Anomaly Timeline. Phase 12.
'use client';

import React from 'react';
import { ResponsiveContainer, ComposedChart, Line, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
import { Box, Typography } from '@mui/material';
import { themeConfig } from '@/theme/theme';

interface AnomalyTimelineProps {
  data: Array<{
    timestamp: string;
    power: number;
    anomalyScore: number;
  }>;
}

export default function AnomalyTimeline({ data }: AnomalyTimelineProps) {
  const formatXAxis = (tickItem: string) => {
    try {
      const d = new Date(tickItem);
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
      return tickItem;
    }
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <Box
          sx={{
            bgcolor: 'background.paper',
            border: `1px solid ${themeConfig.border}`,
            p: 2,
            borderRadius: 2,
            boxShadow: '0 4px 20px rgba(0,0,0,0.3)',
          }}
        >
          <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block', mb: 1, fontWeight: 600 }}>
            {new Date(label).toLocaleString()}
          </Typography>
          <Typography variant="body2" sx={{ color: 'secondary.main', fontWeight: 700, mb: 0.5 }}>
            🔌 Active Load: {payload[0].value} kW
          </Typography>
          <Typography variant="body2" sx={{ color: 'error.main', fontWeight: 800 }}>
            🤖 AI Anomaly Score: {payload[1].value} ({payload[1].value >= 0.7 ? 'Critical Anomaly' : 'Normal'})
          </Typography>
        </Box>
      );
    }
    return null;
  };

  return (
    <Box sx={{ width: '100%', height: 300 }}>
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart
          data={data}
          margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke={themeConfig.border} opacity={0.5} />
          
          <XAxis
            dataKey="timestamp"
            tickFormatter={formatXAxis}
            stroke={themeConfig.textSecondary}
            style={{ fontSize: '0.75rem' }}
          />
          
          {/* Left Y-Axis for Active Power */}
          <YAxis
            yAxisId="left"
            label={{ value: 'Active Power (kW)', angle: -90, position: 'insideLeft', offset: 10, fill: themeConfig.textSecondary, fontSize: '0.8rem' }}
            stroke={themeConfig.textSecondary}
            style={{ fontSize: '0.75rem' }}
          />

          {/* Right Y-Axis for Anomaly Score */}
          <YAxis
            yAxisId="right"
            orientation="right"
            domain={[0, 1]}
            label={{ value: 'AI Anomaly Score', angle: 90, position: 'insideRight', offset: 10, fill: themeConfig.textSecondary, fontSize: '0.8rem' }}
            stroke={themeConfig.textSecondary}
            style={{ fontSize: '0.75rem' }}
          />

          <Tooltip content={<CustomTooltip />} />
          
          <Legend
            verticalAlign="top"
            height={36}
            iconType="circle"
            wrapperStyle={{ fontSize: '0.8rem', fontWeight: 600 }}
          />

          <Line
            yAxisId="left"
            type="monotone"
            name="Active Power (kW)"
            dataKey="power"
            stroke={themeConfig.secondary}
            strokeWidth={2.5}
            dot={{ r: 3, fill: themeConfig.secondary }}
            activeDot={{ r: 5 }}
          />
          
          <Bar
            yAxisId="right"
            name="AI Anomaly Score"
            dataKey="anomalyScore"
            barSize={20}
            fill={themeConfig.error}
            opacity={0.45}
            radius={[4, 4, 0, 0]}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </Box>
  );
}
