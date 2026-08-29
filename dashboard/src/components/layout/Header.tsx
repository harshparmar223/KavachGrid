// KAVACHGRID 3.0 — Header. Phase 12.
'use client';

import React, { useState, useEffect } from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Box,
  IconButton,
  Badge,
  Menu,
  MenuItem,
  Avatar,
  Chip,
  Tooltip,
  Divider,
} from '@mui/material';
import {
  Notifications as NotificationsIcon,
  Wifi as WifiIcon,
  WifiOff as WifiOffIcon,
  QueryBuilder as ClockIcon,
} from '@mui/icons-material';
import { themeConfig } from '@/theme/theme';

export default function Header() {
  const [time, setTime] = useState<string>('');
  const [anchorElNotifications, setAnchorElNotifications] = useState<null | HTMLElement>(null);
  const [anchorElProfile, setAnchorElProfile] = useState<null | HTMLElement>(null);
  const [online, setOnline] = useState<boolean>(true);

  // Update clock
  useEffect(() => {
    const updateClock = () => {
      const now = new Date();
      setTime(
        now.toLocaleTimeString('en-IN', {
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
          hour12: true,
        })
      );
    };
    updateClock();
    const interval = setInterval(updateClock, 1000);
    return () => clearInterval(interval);
  }, []);

  // Listen to browser network changes
  useEffect(() => {
    const handleOnline = () => setOnline(true);
    const handleOffline = () => setOnline(false);
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return (
    <AppBar
      position="fixed"
      sx={{
        width: 'calc(100% - 260px)',
        ml: '260px',
        backgroundColor: 'rgba(10, 22, 40, 0.8)',
        backdropFilter: 'blur(12px)',
        borderBottom: `1px solid ${themeConfig.border}`,
        boxShadow: 'none',
        zIndex: 1100,
      }}
    >
      <Toolbar sx={{ justifyContent: 'space-between', px: 3, py: 1 }}>
        {/* Left Side: System Title */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="h6" sx={{ fontWeight: 700, color: 'text.primary' }}>
            Investigation Control Room
          </Typography>
          <Chip
            icon={online ? <WifiIcon sx={{ fontSize: '1rem !important' }} /> : <WifiOffIcon sx={{ fontSize: '1rem !important' }} />}
            label={online ? 'Grid Ingest Live' : 'Ingest Offline'}
            color={online ? 'success' : 'error'}
            variant="outlined"
            size="small"
            sx={{
              fontWeight: 600,
              fontSize: '0.75rem',
              '& .MuiChip-icon': {
                color: online ? 'success.main' : 'error.main',
              },
            }}
          />
        </Box>

        {/* Right Side: Clock, Alerts, Profile */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 3 }}>
          {/* Real-time Clock */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, color: 'text.secondary' }}>
            <ClockIcon fontSize="small" />
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontWeight: 600, letterSpacing: '0.05em' }}>
              {time || '00:00:00 AM'}
            </Typography>
          </Box>

          {/* Alert Bell */}
          <IconButton
            size="large"
            color="inherit"
            onClick={(e) => setAnchorElNotifications(e.currentTarget)}
            sx={{
              border: `1px solid ${themeConfig.border}`,
              borderRadius: 2,
              p: 1,
              '&:hover': {
                borderColor: themeConfig.primary,
                color: themeConfig.primary,
              },
            }}
          >
            <Badge badgeContent={3} color="error">
              <NotificationsIcon />
            </Badge>
          </IconButton>

          {/* Profile Dropdown */}
          <Tooltip title="Account profile">
            <IconButton onClick={(e) => setAnchorElProfile(e.currentTarget)} sx={{ p: 0 }}>
              <Avatar
                sx={{
                  bgcolor: themeConfig.secondary,
                  border: `2px solid ${themeConfig.primary}`,
                  fontWeight: 700,
                  fontSize: '0.9rem',
                  width: 40,
                  height: 40,
                }}
              >
                YS
              </Avatar>
            </IconButton>
          </Tooltip>

          {/* Notifications Menu */}
          <Menu
            anchorEl={anchorElNotifications}
            open={Boolean(anchorElNotifications)}
            onClose={() => setAnchorElNotifications(null)}
            PaperProps={{
              sx: {
                width: 320,
                backgroundColor: 'background.paper',
                border: `1px solid ${themeConfig.border}`,
                mt: 1.5,
                p: 1,
              },
            }}
            transformOrigin={{ horizontal: 'right', vertical: 'top' }}
            anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
          >
            <Typography variant="subtitle2" sx={{ px: 2, py: 1, fontWeight: 700 }}>
              Recent Critical Alerts
            </Typography>
            <Divider sx={{ mb: 1 }} />
            <MenuItem onClick={() => setAnchorElNotifications(null)} sx={{ borderRadius: 1, py: 1.2 }}>
              <Box>
                <Typography variant="body2" sx={{ fontWeight: 700, color: 'error.main' }}>
                  ⚠️ Energy Imbalance: Feeder-01
                </Typography>
                <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                  24.5% unaccounted loss detected in Zone-A.
                </Typography>
              </Box>
            </MenuItem>
            <MenuItem onClick={() => setAnchorElNotifications(null)} sx={{ borderRadius: 1, py: 1.2 }}>
              <Box>
                <Typography variant="body2" sx={{ fontWeight: 700, color: 'warning.main' }}>
                  🤖 ML Anomaly: Meter-104
                </Typography>
                <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                  Autoencoder flagged current spike shift.
                </Typography>
              </Box>
            </MenuItem>
            <MenuItem onClick={() => setAnchorElNotifications(null)} sx={{ borderRadius: 1, py: 1.2 }}>
              <Box>
                <Typography variant="body2" sx={{ fontWeight: 700, color: 'info.main' }}>
                  🩺 Communication Drop: Meter-202
                </Typography>
                <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                  No ping response for over 15 minutes.
                </Typography>
              </Box>
            </MenuItem>
          </Menu>

          {/* Profile Menu */}
          <Menu
            anchorEl={anchorElProfile}
            open={Boolean(anchorElProfile)}
            onClose={() => setAnchorElProfile(null)}
            PaperProps={{
              sx: {
                width: 220,
                backgroundColor: 'background.paper',
                border: `1px solid ${themeConfig.border}`,
                mt: 1.5,
                p: 1,
              },
            }}
            transformOrigin={{ horizontal: 'right', vertical: 'top' }}
            anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
          >
            <Box sx={{ px: 2, py: 1.5 }}>
              <Typography variant="body2" sx={{ fontWeight: 700, color: 'text.primary' }}>
                Yash Sharma
              </Typography>
              <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                Team Lead / Operator
              </Typography>
            </Box>
            <Divider sx={{ my: 1 }} />
            <MenuItem onClick={() => setAnchorElProfile(null)}>Profile Details</MenuItem>
            <MenuItem onClick={() => setAnchorElProfile(null)}>Settings</MenuItem>
            <Divider sx={{ my: 1 }} />
            <MenuItem onClick={() => setAnchorElProfile(null)} sx={{ color: 'error.main' }}>
              Sign Out
            </MenuItem>
          </Menu>
        </Box>
      </Toolbar>
    </AppBar>
  );
}
