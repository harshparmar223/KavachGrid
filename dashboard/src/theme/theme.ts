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
          backgroundColor: themeConfig.surface,
          backgroundImage: 'none',
          border: `1px solid ${themeConfig.border}`,
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          boxShadow: '0 4px 20px 0 rgba(0, 0, 0, 0.25)',
          '&:hover': {
            transform: 'translateY(-2px)',
            borderColor: themeConfig.primary,
            boxShadow: `0 4px 25px 0 rgba(0, 212, 255, 0.15)`,
          },
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
