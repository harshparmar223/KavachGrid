// KAVACHGRID 3.0 — Sidebar. Phase 12.
'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import './Sidebar.css';
import {
  Box,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Typography,
  Divider,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Router as DevicesIcon,
  Security as RiskIcon,
  TrackChanges as LocalizationIcon,
  Map as MapIcon,
  FlashOn as FlashIcon,
  Speed as SimulatorIcon,
} from '@mui/icons-material';
import { themeConfig } from '@/theme/theme';

const menuItems = [
  { text: 'Overview', icon: <DashboardIcon />, path: '/' },
  { text: 'Devices', icon: <DevicesIcon />, path: '/devices' },
  { text: 'Risk Monitoring', icon: <RiskIcon />, path: '/risk' },
  { text: 'Localization', icon: <LocalizationIcon />, path: '/localization' },
  { text: 'GIS Map', icon: <MapIcon />, path: '/map' },
  { text: 'Grid Simulator', icon: <SimulatorIcon />, path: '/simulator' },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <Box
      className="sidebar-shell"
      sx={{
        width: 260,
        height: '100vh',
        backgroundColor: 'background.paper',
        borderRight: `1px solid ${themeConfig.border}`,
        display: 'flex',
        flexDirection: 'column',
        position: 'fixed',
        left: 0,
        top: 0,
        zIndex: 1200,
      }}
    >
      {/* Brand Header */}
      <Box
        sx={{
          p: 3,
          display: 'flex',
          alignItems: 'center',
          gap: 1.5,
        }}
      >
        <FlashIcon className="brand-mark" sx={{ color: 'primary.main', fontSize: 32 }} />
        <Box>
          <Typography
            variant="h6"
            className="brand-text"
            sx={{
              fontWeight: 800,
              letterSpacing: '0.05em',
            }}
          >
            KAVACHGRID
          </Typography>
        </Box>
      </Box>

      <Divider sx={{ mx: 2 }} />

      {/* Navigation List */}
      <Box sx={{ flexGrow: 1, px: 2, py: 3 }}>
        <List sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
          {menuItems.map((item) => {
            const isActive = pathname === item.path;
            return (
              <ListItem key={item.text} disablePadding>
                <ListItemButton
                  component={Link}
                  href={item.path}
                  className={`nav-item-button ${isActive ? 'active' : ''}`}
                  sx={{
                    borderRadius: 2,
                    py: 1.2,
                    px: 2,
                    backgroundColor: isActive ? 'rgba(0, 212, 255, 0.08)' : 'transparent',
                    borderLeft: isActive ? `3px solid ${themeConfig.primary}` : '3px solid transparent',
                    color: isActive ? 'primary.main' : 'text.secondary',
                    transition: 'all 0.2s ease',
                    '&:hover': {
                      backgroundColor: 'rgba(255, 255, 255, 0.03)',
                      color: 'text.primary',
                      '& .MuiListItemIcon-root': {
                        color: themeConfig.primary,
                      },
                    },
                  }}
                >
                  <ListItemIcon
                    className="nav-icon"
                    sx={{
                      color: isActive ? 'primary.main' : 'text.secondary',
                      minWidth: 40,
                      transition: 'color 0.2s ease, transform 0.25s ease, filter 0.2s ease',
                    }}
                  >
                    {item.icon}
                  </ListItemIcon>
                  <ListItemText
                    primary={item.text}
                    primaryTypographyProps={{
                      fontSize: '0.95rem',
                      fontWeight: isActive ? 700 : 500,
                      letterSpacing: '0.02em',
                    }}
                  />
                </ListItemButton>
              </ListItem>
            );
          })}
        </List>
      </Box>

      {/* Footer Info */}
      <Box sx={{ p: 3, mt: 'auto' }}>
        <Box
          className="system-status"
          sx={{
            p: 2,
            borderRadius: 2,
            backgroundColor: 'rgba(255, 255, 255, 0.02)',
            border: `1px solid rgba(255, 255, 255, 0.05)`,
            textAlign: 'center',
          }}
        >
          <Typography variant="body2" sx={{ fontWeight: 600, color: 'text.secondary' }}>
            System Integrity
          </Typography>
          <Typography variant="caption" sx={{ color: 'success.main', fontWeight: 700, display: 'block', mt: 0.5 }}>
            ● SECURED
          </Typography>
        </Box>
      </Box>
    </Box>
  );
}
