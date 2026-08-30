"use client";

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
  List,
  ListItem,
  ListItemText,
  Divider,
} from '@mui/material';
import {
  Security as ShieldIcon,
  OnlinePrediction as IngestionIcon,
  Timeline as LineIcon,
} from '@mui/icons-material';
import RiskGauge from '@/components/charts/RiskGauge';
import AnomalyTimeline from '@/components/charts/AnomalyTimeline';
import { api } from '@/lib/api';
import { useApi } from '@/hooks/useApi';
import { RiskScore, Telemetry } from '@/lib/types';
import { themeConfig } from '@/theme/theme';

export default function RiskPage() {
  const { data: rankingData, loading, mutate } = useApi(api.getRiskRanking);
  const [selectedDeviceId, setSelectedDeviceId] = useState<string>('');
  const [selectedRisk, setSelectedRisk] = useState<RiskScore | null>(null);
  const [timelineData, setTimelineData] = useState<Array<{ timestamp: string; power: number; anomalyScore: number }>>([]);
  const [timelineLoading, setTimelineLoading] = useState<boolean>(false);

  // Set default selected device
  useEffect(() => {
    if (rankingData && rankingData.rankings.length > 0 && !selectedDeviceId) {
      setSelectedDeviceId(rankingData.rankings[0].device_id);
    }
  }, [rankingData, selectedDeviceId]);

  // Fetch telemetry/details for selected device to populate timeline chart
  useEffect(() => {
    const fetchRiskDetails = async () => {
      if (!selectedDeviceId || !rankingData) return;
      
      const r = rankingData.rankings.find((item) => item.device_id === selectedDeviceId);
      if (r) setSelectedRisk(r);

      setTimelineLoading(true);
      try {
        const telemetry = await api.getHistoricalTelemetry(selectedDeviceId);
        
        // Compile data for AnomalyTimeline
        const compiled = telemetry.map((t: Telemetry) => ({
          timestamp: t.timestamp,
          power: t.power,
          anomalyScore: t.anomaly_score || 0,
        }));
        setTimelineData(compiled);
      } catch (err) {
        console.error(err);
      } finally {
        setTimelineLoading(false);
      }
    };
    
    fetchRiskDetails();
  }, [selectedDeviceId, rankingData]);

  const getRiskLevelColor = (level: string) => {
    switch (level) {
      case 'critical':
        return 'error';
      case 'high':
        return 'warning';
      case 'medium':
        return 'info';
      default:
        return 'success';
    }
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      {/* Title */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 800, color: 'text.primary', mb: 1 }}>
          KAVACH Risk Ranking
        </Typography>
        <Typography variant="body2" sx={{ color: 'text.secondary', fontWeight: 600 }}>
          Composite inspection prioritization score computed across all 5 telemetry audit dimensions.
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Left Side: Priority Risk Ranking List */}
        <Grid item xs={12} lg={7}>
          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ fontWeight: 700, mb: 2 }}>
                🎯 Prioritized Field Inspection Ranking
              </Typography>
              
              {loading ? (
                <LinearProgress />
              ) : (
                <TableContainer component={Paper} sx={{ border: 'none', boxShadow: 'none' }}>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Rank</TableCell>
                        <TableCell>Device ID</TableCell>
                        <TableCell align="right">Composite Score</TableCell>
                        <TableCell align="right">Risk Level</TableCell>
                        <TableCell align="right">Energy Dev (%)</TableCell>
                        <TableCell align="right">Trust Check</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {rankingData?.rankings.map((row, index) => (
                        <TableRow
                          key={row.id}
                          hover
                          selected={row.device_id === selectedDeviceId}
                          onClick={() => setSelectedDeviceId(row.device_id)}
                          sx={{ cursor: 'pointer' }}
                        >
                          <TableCell sx={{ fontWeight: 700 }}>#{index + 1}</TableCell>
                          <TableCell sx={{ color: themeConfig.primary, fontWeight: 700 }}>
                            {row.device_id}
                          </TableCell>
                          <TableCell align="right" sx={{ fontWeight: 700 }}>
                            {row.overall_score.toFixed(1)}
                          </TableCell>
                          <TableCell align="right">
                            <Chip
                              label={row.risk_level.toUpperCase()}
                              color={getRiskLevelColor(row.risk_level)}
                              size="small"
                              sx={{ fontWeight: 800, fontSize: '0.65rem' }}
                            />
                          </TableCell>
                          <TableCell align="right">
                            {row.energy_balance_score.toFixed(0)}%
                          </TableCell>
                          <TableCell align="right">
                            <Chip
                              label={row.device_trust_score >= 80 ? 'VALID' : 'ALERT'}
                              color={row.device_trust_score >= 80 ? 'success' : 'error'}
                              variant="outlined"
                              size="small"
                              sx={{ fontWeight: 700, fontSize: '0.65rem' }}
                            />
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Right Side: Composite Score Breakdown & Audit timeline */}
        <Grid item xs={12} lg={5}>
          {selectedRisk && (
            <Card sx={{ height: '100%' }}>
              <CardContent sx={{ p: 3 }}>
                <Typography variant="h6" sx={{ fontWeight: 800, mb: 1, color: themeConfig.primary }}>
                  🛡️ Risk Audit Breakdown
                </Typography>
                <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block', mb: 2 }}>
                  Inspecting Target: <strong style={{ color: '#fff' }}>{selectedRisk.device_id}</strong>
                </Typography>

                <Divider sx={{ mb: 3 }} />

                <Grid container spacing={2} alignItems="center" sx={{ mb: 3 }}>
                  <Grid item xs={12} sm={6}>
                    <RiskGauge score={selectedRisk.overall_score} />
                  </Grid>
                  
                  <Grid item xs={12} sm={6}>
                    <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 1 }}>
                      Engine Weights Score
                    </Typography>
                    
                    <List sx={{ bgcolor: 'rgba(0,0,0,0.1)', borderRadius: 2, p: 1 }}>
                      <ListItem disablePadding sx={{ py: 0.5, px: 1, display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="caption">Energy Imbalance</Typography>
                        <Typography variant="body2" sx={{ fontWeight: 700 }}>
                          {selectedRisk.energy_balance_score}/100
                        </Typography>
                      </ListItem>
                      <ListItem disablePadding sx={{ py: 0.5, px: 1, display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="caption">AI Autoencoder Anomaly</Typography>
                        <Typography variant="body2" sx={{ fontWeight: 700 }}>
                          {selectedRisk.ai_anomaly_score}/100
                        </Typography>
                      </ListItem>
                      <ListItem disablePadding sx={{ py: 0.5, px: 1, display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="caption">Meter Health</Typography>
                        <Typography variant="body2" sx={{ fontWeight: 700 }}>
                          {selectedRisk.meter_health_score}/100
                        </Typography>
                      </ListItem>
                      <ListItem disablePadding sx={{ py: 0.5, px: 1, display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="caption">Device cryptographic Trust</Typography>
                        <Typography variant="body2" sx={{ fontWeight: 700 }}>
                          {selectedRisk.device_trust_score}/100
                        </Typography>
                      </ListItem>
                      <ListItem disablePadding sx={{ py: 0.5, px: 1, display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="caption">Comm Reliability</Typography>
                        <Typography variant="body2" sx={{ fontWeight: 700 }}>
                          {selectedRisk.comm_reliability_score}/100
                        </Typography>
                      </ListItem>
                    </List>
                  </Grid>
                </Grid>

                <Divider sx={{ mb: 3 }} />

                <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 2 }}>
                  🤖 ML Load Profile & Anomaly Timeline
                </Typography>
                
                {timelineLoading ? (
                  <LinearProgress />
                ) : (
                  <AnomalyTimeline data={timelineData} />
                )}
              </CardContent>
            </Card>
          )}
        </Grid>
      </Grid>
    </Box>
  );
}
