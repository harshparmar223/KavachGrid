// KAVACHGRID 3.0 — Progressive Localization Page
// Phase 12: Complete implementation
'use client';

import React, { useState } from 'react';
import {
  Grid,
  Box,
  Typography,
  Card,
  CardContent,
  Chip,
  Button,
  TextField,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  Divider,
} from '@mui/material';
import {
  Troubleshoot as InvestIcon,
  AddModerator as ShieldIcon,
  CheckCircle as AckIcon,
} from '@mui/icons-material';
import { api } from '@/lib/api';
import { useApi } from '@/hooks/useApi';
import { LocalizationResult } from '@/lib/types';
import { themeConfig } from '@/theme/theme';

export default function LocalizationPage() {
  const { data: results, loading, mutate } = useApi(api.getLocalization);
  const [selectedResult, setSelectedResult] = useState<LocalizationResult | null>(null);
  
  // Edit notes state
  const [openModal, setOpenModal] = useState<boolean>(false);
  const [status, setStatus] = useState<string>('pending');
  const [notes, setNotes] = useState<string>('');

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
      mutate(); // Reload data
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

  return (
    <Box sx={{ flexGrow: 1 }}>
      {/* Title */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 800, color: 'text.primary', mb: 1 }}>
          Progressive Localization
        </Typography>
        <Typography variant="body2" sx={{ color: 'text.secondary', fontWeight: 600 }}>
          Pinpoint suspicious distribution segments and line branches using branch-level current transformer monitoring.
        </Typography>
      </Box>

      {loading ? (
        <LinearProgress />
      ) : !results || results.length === 0 ? (
        <Typography variant="body1" sx={{ color: 'text.secondary', py: 4, textAlign: 'center' }}>
          No suspect localization results found.
        </Typography>
      ) : (
        <Grid container spacing={3}>
          {/* Left Column: Suspect Zones */}
          <Grid item xs={12} md={6}>
            <Typography variant="h6" sx={{ fontWeight: 700, mb: 2 }}>
              📍 Identified Suspect Segments
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
              {results.map((res) => (
                <Card
                  key={res.id}
                  onClick={() => setSelectedResult(res)}
                  sx={{
                    cursor: 'pointer',
                    borderColor: selectedResult?.id === res.id ? themeConfig.primary : themeConfig.border,
                    boxShadow: selectedResult?.id === res.id ? `0 0 15px rgba(0, 212, 255, 0.15)` : 'none',
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
                        <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block' }}>
                          ESTIMATED GRID ENERGY LOSS
                        </Typography>
                        <Typography variant="h6" sx={{ fontWeight: 800 }}>
                          {res.estimated_loss_kwh} kWh
                        </Typography>
                      </Grid>
                      <Grid item xs={6}>
                        <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block' }}>
                          LOCALIZATION CONFIDENCE
                        </Typography>
                        <Typography variant="h6" sx={{ fontWeight: 800, color: 'success.main' }}>
                          {res.confidence}%
                        </Typography>
                      </Grid>
                    </Grid>

                    <Divider sx={{ mb: 2 }} />

                    <Typography variant="body2" sx={{ color: 'text.secondary', mb: 2, lineClamp: 2 }}>
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
                      sx={{ borderColor: themeConfig.border, '&:hover': { borderColor: themeConfig.primary } }}
                    >
                      Update Investigation
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </Box>
          </Grid>

          {/* Right Column: Suspect Devices & Recommendation detail */}
          <Grid item xs={12} md={6}>
            {selectedResult ? (
              <Card sx={{ position: 'sticky', top: 110 }}>
                <CardContent sx={{ p: 3 }}>
                  <Typography variant="h6" sx={{ fontWeight: 800, mb: 1, color: themeConfig.primary }}>
                    📋 Suspect Candidates Breakdown
                  </Typography>
                  <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block', mb: 3 }}>
                    Auditing nodes connected downstream of Branch segment <strong style={{ color: '#fff' }}>{selectedResult.zone_id}</strong>
                  </Typography>

                  <List sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    {selectedResult.suspect_devices.map((device, idx) => (
                      <ListItem
                        key={idx}
                        sx={{
                          flexDirection: 'column',
                          alignItems: 'flex-start',
                          bgcolor: 'rgba(255, 255, 255, 0.01)',
                          border: `1px solid ${themeConfig.border}`,
                          borderRadius: 2,
                          p: 2,
                        }}
                      >
                        <Box sx={{ display: 'flex', width: '100%', justifyContent: 'space-between', alignItems: 'center', mb: 1.5 }}>
                          <Typography variant="body1" sx={{ fontWeight: 700, color: 'text.primary' }}>
                            Candidate Meter: {device.device_id}
                          </Typography>
                          <Chip
                            label={`Suspicion: ${device.suspicion_score}%`}
                            color={device.suspicion_score >= 80 ? 'error' : 'warning'}
                            size="small"
                            sx={{ fontWeight: 700, fontSize: '0.7rem' }}
                          />
                        </Box>
                        
                        <Typography variant="body2" sx={{ color: 'text.secondary', mb: 1.5 }}>
                          <strong>Deduction Reason:</strong> {device.reason}
                        </Typography>
                        
                        <Box
                          sx={{
                            width: '100%',
                            p: 1.5,
                            bgcolor: 'rgba(124, 77, 255, 0.05)',
                            borderLeft: `3px solid ${themeConfig.secondary}`,
                            borderRadius: '0 4px 4px 0',
                          }}
                        >
                          <Typography variant="caption" sx={{ color: themeConfig.secondary, fontWeight: 700, display: 'block', mb: 0.5 }}>
                            RECOMMENDED INSPECTION ACTION
                          </Typography>
                          <Typography variant="body2" sx={{ fontWeight: 600 }}>
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
                  Select a suspect segment on the left to show candidate meters.
                </Typography>
              </Box>
            )}
          </Grid>
        </Grid>
      )}

      {/* Edit Investigation Modal */}
      <Dialog open={openModal} onClose={() => setOpenModal(false)} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ fontWeight: 800 }}>Update Investigation Logs</DialogTitle>
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
          <Button onClick={handleSaveStatus} variant="contained" color="primary">
            Save Status
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
