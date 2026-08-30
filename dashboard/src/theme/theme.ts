export const KAVACH_COLORS = {
  primary: {
    cyanLight: '#00f2fe',
    cyan: '#4facfe',
  },
  background: {
    deep1: '#0b132b',
    deep2: '#1c2541',
  },
  severity: {
    critical: '#ef4444',
    high: '#f97316',
    medium: '#f59e0b',
    normal: '#10b981',
  },
};

export const applyThemeVariables = (isDark = true) => {
  const root = typeof document !== 'undefined' ? document.documentElement : null;
  if (!root) return;
  const colors = KAVACH_COLORS;
  root.style.setProperty('--kg-primary-cyan', colors.primary.cyan);
  root.style.setProperty('--kg-primary-cyan-light', colors.primary.cyanLight);
  root.style.setProperty('--kg-bg-deep', isDark ? colors.background.deep1 : '#ffffff');
  root.style.setProperty('--kg-bg-surface', isDark ? colors.background.deep2 : '#f6f8fb');
  root.style.setProperty('--kg-text', isDark ? '#e6eef8' : '#0b132b');
  root.style.setProperty('--kg-critical', colors.severity.critical);
  root.style.setProperty('--kg-high', colors.severity.high);
  root.style.setProperty('--kg-medium', colors.severity.medium);
  root.style.setProperty('--kg-normal', colors.severity.normal);
};

export default KAVACH_COLORS;
// KAVACHGRID 3.0 — MUI Theme Customization
// Phase 12: Complete implementation

import { createTheme } from '@mui/material/styles';

export const themeConfig = {
  primary: '#00d4ff', // Electric cyan
  secondary: '#7c4dff', // Purple/Violet
  background: '#0a1628', // Deep navy
  surface: '#112240', // Navy card surface
  surfaceHover: '#1d3056', // Hover card surface
  border: '#233554', // Border color
  textPrimary: '#ccd6f6', // Light grayish blue
  textSecondary: '#8892b0', // Dim grayish blue
  warning: '#ff9800',
  error: '#f44336',
  success: '#4caf50',
  info: '#00b0ff',
};

export const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: themeConfig.primary,
      contrastText: '#0a1628',
    },
    secondary: {
      main: themeConfig.secondary,
    },
    background: {
      default: themeConfig.background,
      paper: themeConfig.surface,
    },
    text: {
      primary: themeConfig.textPrimary,
      secondary: themeConfig.textSecondary,
    },
    warning: {
      main: themeConfig.warning,
    },
    error: {
      main: themeConfig.error,
    },
    success: {
      main: themeConfig.success,
    },
    info: {
      main: themeConfig.info,
    },
    divider: themeConfig.border,
  },
  typography: {
    fontFamily: [
      'Outfit',
      'Inter',
      '-apple-system',
      'BlinkMacSystemFont',
      '"Segoe UI"',
      'Roboto',
      '"Helvetica Neue"',
      'Arial',
      'sans-serif',
    ].join(','),
    h1: {
      fontWeight: 700,
      letterSpacing: '-0.02em',
    },
    h2: {
      fontWeight: 700,
      letterSpacing: '-0.01em',
    },
    h3: {
      fontWeight: 600,
    },
    h4: {
      fontWeight: 600,
    },
    h5: {
      fontWeight: 600,
    },
    h6: {
      fontWeight: 600,
    },
    subtitle1: {
      letterSpacing: '0.01em',
    },
    body1: {
      lineHeight: 1.6,
    },
    body2: {
      lineHeight: 1.5,
    },
  },
  shape: {
    borderRadius: 12,
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          backgroundColor: themeConfig.background,
          color: themeConfig.textPrimary,
          scrollbarColor: '#233554 #0a1628',
          '&::-webkit-scrollbar': {
            width: '8px',
            height: '8px',
          },
          '&::-webkit-scrollbar-track': {
            background: '#0a1628',
          },
          '&::-webkit-scrollbar-thumb': {
            background: '#233554',
            borderRadius: '4px',
          },
          '&::-webkit-scrollbar-thumb:hover': {
            background: '#00d4ff',
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          position: 'relative',
          overflow: 'hidden',
          borderRadius: 18,
          background: 'linear-gradient(180deg, rgba(17, 34, 64, 0.92) 0%, rgba(8, 18, 33, 0.96) 100%)',
          border: '1px solid rgba(255, 255, 255, 0.12)',
          backdropFilter: 'blur(18px)',
          WebkitBackdropFilter: 'blur(18px)',
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.08), 0 18px 40px rgba(0, 0, 0, 0.28)',
          '&::before': {
            content: '""',
            position: 'absolute',
            inset: 0,
            borderRadius: 'inherit',
            background: 'linear-gradient(130deg, rgba(255,255,255,0.14) 0%, rgba(255,255,255,0.02) 18%, transparent 42%, rgba(79, 172, 254, 0.18) 68%, transparent 100%)',
            pointerEvents: 'none',
            opacity: 0.9,
          },
          '&::after': {
            content: '""',
            position: 'absolute',
            inset: 1,
            borderRadius: 'inherit',
            background: 'linear-gradient(135deg, rgba(255,255,255,0.06), rgba(255,255,255,0.01) 35%, rgba(79,172,254,0.08) 100%)',
            pointerEvents: 'none',
          },
          '&:hover': {
            transform: 'translateY(-2px)',
            borderColor: 'rgba(0, 212, 255, 0.6)',
            boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.1), 0 24px 48px rgba(0, 212, 255, 0.12)',
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          background: 'linear-gradient(180deg, rgba(17, 34, 64, 0.9) 0%, rgba(10, 18, 31, 0.96) 100%)',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.06), 0 18px 40px rgba(0, 0, 0, 0.2)',
          backdropFilter: 'blur(14px)',
          WebkitBackdropFilter: 'blur(14px)',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 600,
          borderRadius: 8,
          padding: '6px 16px',
        },
        containedPrimary: {
          '&:hover': {
            boxShadow: '0 0 15px rgba(0, 212, 255, 0.4)',
          },
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          borderBottom: `1px solid ${themeConfig.border}`,
        },
        head: {
          fontWeight: 700,
          backgroundColor: '#0c1a30',
        },
      },
    },
  },
});
