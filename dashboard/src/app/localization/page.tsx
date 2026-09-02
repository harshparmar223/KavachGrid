// KAVACHGRID 3.0 — Progressive Localization Page
// Phase 12: Narrow suspicious grid areas, rank candidate meters, and track investigations.
'use client';

import React, { useState, useEffect } from 'react';
import {
  Grid,
  Box,
  Typography,
  Card,
  CardContent,
  Chip,
  Button,
  ButtonGroup,
  TextField,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  LinearProgress,
  List,
  ListItem,
  Divider,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Troubleshoot as InvestIcon,
  AddModerator as ShieldIcon,
  CheckCircle as AckIcon,
  Refresh as RefreshIcon,
  PlayArrow as TriggerIcon,
  ReportProblem as AlertIcon,
  LocationOn as PinIcon,
} from '@mui/icons-material';
import { api } from '@/lib/api';
import { useApi } from '@/hooks/useApi';
import { LocalizationResult } from '@/lib/types';
import { themeConfig } from '@/theme/theme';

export default function LocalizationPage() {
  const { data: rawResults, loading, mutate } = useApi(api.getLocalization);
  const [selectedResult, setSelectedResult] = useState<LocalizationResult | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [isScanning, setIsScanning] = useState<boolean>(false);
  
  // Edit notes state
  const [openModal, setOpenModal] = useState<boolean>(false);
  const [status, setStatus] = useState<string>('pending');
  const [notes, setNotes] = useState<string>('');

  const results = rawResults || [];

  // Default select first result
  useEffect(() => {
    if (results.length > 0 && !selectedResult) {
      setSelectedResult(results[0]);
    }
  }, [results, selectedResult]);

  const handleTriggerAnalysis = async () => {
    setIsScanning(true);
    try {
      await api.triggerLocalization();
      await mutate();
    } catch (err) {
      console.error('Failed to trigger localization:', err);
    } finally {
      setIsScanning(false);
    }
  };

  const handleOpenEdit = (res: LocalizationResult) => {
    setSelectedResult(res);
    setStatus(res.status);
    setNotes(res.investigation_notes || '');
    setOpenModal(true);
  };

  const handleSaveStatus = async () => {
    if (!selectedResult) return;
    try {
      await api.updateLocalizationStatus(selectedResult.id, status, notes);
      setOpenModal(false);
      mutate();
    } catch (err) {
      console.error(err);
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
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

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'resolved':
        return 'success';
      case 'investigating':
        return 'warning';
      case 'false_alarm':
        return 'error';
      default:
        return 'default';
    }
  };

  const filteredResults = results.filter((r) => {
    if (statusFilter === 'all') return true;
    return r.status === statusFilter;
  });

  // Keep only the latest scan per unique zone_id for summary metrics
  const uniqueZoneResults = Object.values(
    results.reduce((acc, curr) => {
      if (!acc[curr.zone_id]) acc[curr.zone_id] = curr;
      return acc;
    }, {} as Record<string, LocalizationResult>)
  );

  const totalLoss = uniqueZoneResults.reduce((sum, r) => sum + (r.estimated_loss_kwh || 0), 0);
  const criticalCount = uniqueZoneResults.filter((r) => r.priority === 'critical' || r.priority === 'high').length;
  const pendingCount = uniqueZoneResults.filter((r) => r.status === 'pending').length;

  return (
    <Box sx={{ flexGrow: 1 }}>
      {/* Header with Title & Scan Trigger */}
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 2 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 800, color: 'text.primary', mb: 0.5, display: 'flex', alignItems: 'center', gap: 1.5 }}>
            <InvestIcon sx={{ color: themeConfig.primary, fontSize: 32 }} />
            Progressive Localization
          </Typography>
          <Typography variant="body2" sx={{ color: 'text.secondary', fontWeight: 600 }}>
            Hierarchical distribution fault & energy theft localization powered by branch CT monitors and cross-meter evidence fusion.
          </Typography>
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <Tooltip title="Reload Investigations">
            <IconButton onClick={() => mutate()} sx={{ border: `1px solid ${themeConfig.border}` }}>
              <RefreshIcon sx={{ color: themeConfig.primary }} />
            </IconButton>
          </Tooltip>

          <Button
            variant="contained"
            startIcon={<TriggerIcon />}
            onClick={handleTriggerAnalysis}
            disabled={isScanning}
            sx={{
              fontWeight: 800,
              textTransform: 'none',
              borderRadius: 2,
              background: `linear-gradient(135deg, ${themeConfig.primary}, ${themeConfig.secondary})`,
              boxShadow: `0 0 15px rgba(0, 212, 255, 0.3)`,
            }}
          >
            {isScanning ? 'Analyzing Branch CTs...' : 'Run Localization Scan'}
          </Button>
        </Box>
      </Box>

      {/* Summary KPI Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ p: 2, bgcolor: 'rgba(0, 212, 255, 0.05)', border: `1px solid rgba(0, 212, 255, 0.2)` }}>
            <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 700 }}>
              LOCALIZED DISTRIBUTION ZONES
            </Typography>
            <Typography variant="h5" sx={{ fontWeight: 800, color: themeConfig.primary, mt: 0.5 }}>
              {uniqueZoneResults.length} Segments
            </Typography>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ p: 2, bgcolor: 'rgba(255, 23, 68, 0.05)', border: `1px solid rgba(255, 23, 68, 0.2)` }}>
            <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 700 }}>
              HIGH PRIORITY SUSPECTS
            </Typography>
            <Typography variant="h5" sx={{ fontWeight: 800, color: '#ff1744', mt: 0.5 }}>
              {criticalCount} Critical Cases
            </Typography>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ p: 2, bgcolor: 'rgba(255, 152, 0, 0.05)', border: `1px solid rgba(255, 152, 0, 0.2)` }}>
            <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 700 }}>
              ESTIMATED UNACCOUNTED LOSS
            </Typography>
            <Typography variant="h5" sx={{ fontWeight: 800, color: '#ff9800', mt: 0.5 }}>
              {totalLoss.toFixed(1)} kWh
            </Typography>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ p: 2, bgcolor: 'rgba(0, 230, 118, 0.05)', border: `1px solid rgba(0, 230, 118, 0.2)` }}>
            <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 700 }}>
              PENDING FIELD AUDITS
            </Typography>
            <Typography variant="h5" sx={{ fontWeight: 800, color: '#00e676', mt: 0.5 }}>
              {pendingCount} Pending
            </Typography>
          </Card>
        </Grid>
      </Grid>

      {/* Filter Tabs */}
      <Box sx={{ mb: 2.5 }}>
        <ButtonGroup size="small" variant="outlined">
          <Button
            variant={statusFilter === 'all' ? 'contained' : 'outlined'}
            onClick={() => setStatusFilter('all')}
            sx={{ fontWeight: 700, textTransform: 'none' }}
          >
            All Investigations ({results.length})
          </Button>
          <Button
            variant={statusFilter === 'pending' ? 'contained' : 'outlined'}
            onClick={() => setStatusFilter('pending')}
            sx={{ fontWeight: 700, textTransform: 'none' }}
          >
            Pending
          </Button>
          <Button
            variant={statusFilter === 'investigating' ? 'contained' : 'outlined'}
            onClick={() => setStatusFilter('investigating')}
            sx={{ fontWeight: 700, textTransform: 'none' }}
          >
            Active Field Audits
          </Button>
          <Button
            variant={statusFilter === 'resolved' ? 'contained' : 'outlined'}
            onClick={() => setStatusFilter('resolved')}
            sx={{ fontWeight: 700, textTransform: 'none' }}
          >
            Resolved
          </Button>
        </ButtonGroup>
      </Box>

      {loading || isScanning ? (
        <LinearProgress sx={{ my: 4 }} />
      ) : filteredResults.length === 0 ? (
        <Box sx={{ py: 8, textAlign: 'center', bgcolor: 'rgba(255,255,255,0.01)', border: `1px dashed ${themeConfig.border}`, borderRadius: 3 }}>
          <Typography variant="h6" sx={{ color: 'text.secondary', mb: 1, fontWeight: 700 }}>
            No suspect localization results found.
          </Typography>
          <Typography variant="body2" sx={{ color: 'text.secondary', mb: 2 }}>
            Run a localization scan to correlate branch sensor CTs with smart meters.
          </Typography>
          <Button variant="contained" onClick={handleTriggerAnalysis} sx={{ fontWeight: 800 }}>
            Run Localization Scan
          </Button>
        </Box>
      ) : (
        <Grid container spacing={3}>
          {/* Left Column: Suspect Zones */}
          <Grid item xs={12} md={6}>
            <Typography variant="h6" sx={{ fontWeight: 800, mb: 2, color: 'text.primary' }}>
              📍 Identified Suspect Segments
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
              {filteredResults.map((res) => (
                <Card
                  key={res.id}
                  onClick={() => setSelectedResult(res)}
                  sx={{
                    cursor: 'pointer',
                    borderColor: selectedResult?.id === res.id ? themeConfig.primary : themeConfig.border,
                    boxShadow: selectedResult?.id === res.id ? `0 0 18px rgba(0, 212, 255, 0.2)` : 'none',
                    transition: 'all 0.2s ease',
                  }}
                >
                  <CardContent sx={{ p: 3 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                      <Typography variant="h6" sx={{ fontWeight: 800, color: themeConfig.primary }}>
                        Segment ID: {res.zone_id}
                      </Typography>
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        <Chip
                          label={res.priority.toUpperCase()}
                          color={getPriorityColor(res.priority)}
                          size="small"
                          sx={{ fontWeight: 800, fontSize: '0.65rem' }}
                        />
                        <Chip
                          label={res.status.toUpperCase()}
                          color={getStatusColor(res.status) as any}
                          size="small"
                          sx={{ fontWeight: 800, fontSize: '0.65rem' }}
                        />
                      </Box>
                    </Box>

                    <Grid container spacing={2} sx={{ mb: 2 }}>
                      <Grid item xs={6}>
                        <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block', fontWeight: 700 }}>
                          ESTIMATED GRID LOSS
                        </Typography>
                        <Typography variant="h6" sx={{ fontWeight: 800, color: '#ff9800' }}>
                          {res.estimated_loss_kwh} kWh
                        </Typography>
                      </Grid>
                      <Grid item xs={6}>
                        <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block', fontWeight: 700 }}>
                          LOCALIZATION CONFIDENCE
                        </Typography>
                        <Typography variant="h6" sx={{ fontWeight: 800, color: '#00e676' }}>
                          {res.confidence > 1 ? res.confidence : (res.confidence * 100).toFixed(0)}%
                        </Typography>
                      </Grid>
                    </Grid>

                    <Divider sx={{ mb: 2 }} />

                    <Typography variant="body2" sx={{ color: 'text.secondary', mb: 2 }}>
                      <strong>Investigation Memo:</strong> {res.investigation_notes || 'No notes added.'}
                    </Typography>

                    <Button
                      variant="outlined"
                      size="small"
                      startIcon={<InvestIcon />}
                      onClick={(e) => {
                        e.stopPropagation();
                        handleOpenEdit(res);
                      }}
                      sx={{ borderColor: themeConfig.border, fontWeight: 700 }}
                    >
                      Update Investigation Log
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </Box>
          </Grid>

          {/* Right Column: Suspect Devices & Recommendation detail */}
          <Grid item xs={12} md={6}>
            {selectedResult ? (
              <Card sx={{ position: 'sticky', top: 100 }}>
                <CardContent sx={{ p: 3 }}>
                  <Typography variant="h6" sx={{ fontWeight: 800, mb: 0.5, color: themeConfig.primary }}>
                    📋 Suspect Candidates Breakdown
                  </Typography>
                  <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block', mb: 2.5 }}>
                    Auditing nodes connected downstream of Branch segment <strong style={{ color: '#fff' }}>{selectedResult.zone_id}</strong>
                  </Typography>

                  <List sx={{ display: 'flex', flexDirection: 'column', gap: 2, p: 0 }}>
                    {selectedResult.suspect_devices.map((device, idx) => (
                      <ListItem
                        key={idx}
                        sx={{
                          flexDirection: 'column',
                          alignItems: 'flex-start',
                          bgcolor: 'rgba(255, 255, 255, 0.02)',
                          border: `1px solid ${themeConfig.border}`,
                          borderRadius: 2,
                          p: 2,
                        }}
                      >
                        <Box sx={{ display: 'flex', width: '100%', justifyContent: 'space-between', alignItems: 'center', mb: 1.5 }}>
                          <Typography variant="body1" sx={{ fontWeight: 800, color: 'text.primary' }}>
                            Candidate Meter: {device.device_id}
                          </Typography>
                          <Chip
                            label={`Suspicion: ${device.suspicion_score}%`}
                            color={device.suspicion_score >= 80 ? 'error' : 'warning'}
                            size="small"
                            sx={{ fontWeight: 800, fontSize: '0.7rem' }}
                          />
                        </Box>
                        
                        <Typography variant="body2" sx={{ color: 'text.secondary', mb: 1.5 }}>
                          <strong>Deduction Reason:</strong> {device.reason}
                        </Typography>
                        
                        <Box
                          sx={{
                            width: '100%',
                            p: 1.5,
                            bgcolor: 'rgba(0, 212, 255, 0.05)',
                            borderLeft: `3px solid ${themeConfig.primary}`,
                            borderRadius: '0 6px 6px 0',
                          }}
                        >
                          <Typography variant="caption" sx={{ color: themeConfig.primary, fontWeight: 800, display: 'block', mb: 0.5 }}>
                            RECOMMENDED INSPECTION ACTION
                          </Typography>
                          <Typography variant="body2" sx={{ fontWeight: 600, color: '#fff' }}>
                            {device.recommended_action}
                          </Typography>
                        </Box>
                      </ListItem>
                    ))}
                  </List>
                </CardContent>
              </Card>
            ) : (
              <Box sx={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', p: 4, bgcolor: 'rgba(255,255,255,0.01)', border: `1px dashed ${themeConfig.border}`, borderRadius: 2 }}>
                <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                  Select a suspect segment on the left to inspect suspect devices.
                </Typography>
              </Box>
            )}
          </Grid>
        </Grid>
      )}

      {/* Edit Investigation Modal */}
      <Dialog open={openModal} onClose={() => setOpenModal(false)} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ fontWeight: 800, color: themeConfig.primary }}>
          📝 Update Investigation Logs
        </DialogTitle>
        <DialogContent sx={{ pt: 2 }}>
          <TextField
            select
            fullWidth
            label="Investigation Status"
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            sx={{ mb: 3, mt: 1 }}
          >
            <MenuItem value="pending">Pending Audit</MenuItem>
            <MenuItem value="investigating">Field Investigation Active</MenuItem>
            <MenuItem value="resolved">Theft Resolved / Restored</MenuItem>
            <MenuItem value="false_alarm">False Alarm / Sensor Calibration</MenuItem>
          </TextField>
          
          <TextField
            fullWidth
            multiline
            rows={4}
            label="Investigation Notes / Action Summary"
            placeholder="Record site inspection details, tampering reports, bypass wire checks, etc."
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
          />
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 3 }}>
          <Button onClick={() => setOpenModal(false)} color="inherit">
            Cancel
          </Button>
          <Button
            onClick={handleSaveStatus}
            variant="contained"
            sx={{ fontWeight: 800, background: `linear-gradient(135deg, ${themeConfig.primary}, ${themeConfig.secondary})` }}
          >
            Save Status
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
