// KAVACHGRID 3.0 — Root Layout
// Phase 12: Complete implementation

import React from 'react';
import type { Metadata } from 'next';
import ThemeProvider from '@/components/layout/ThemeProvider';
import Sidebar from '@/components/layout/Sidebar';
import Header from '@/components/layout/Header';
import { Box } from '@mui/material';

export const metadata: Metadata = {
  title: 'KAVACHGRID 3.0 — Smart Grid Investigation Support',
  description:
    'AI-Powered Energy Theft, Anomaly Detection, Risk Ranking & Progressive Localization System',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body style={{ margin: 0, padding: 0 }}>
        <ThemeProvider>
          <Box sx={{ display: 'flex', minHeight: '100vh', backgroundColor: 'background.default' }}>
            {/* Sidebar */}
            <Sidebar />

            {/* Main Content Wrapper */}
            <Box
              sx={{
                flexGrow: 1,
                minHeight: '100vh',
                display: 'flex',
                flexDirection: 'column',
                ml: '260px',
                pt: '88px', // Header height + padding
                px: 4,
                pb: 4,
                width: 'calc(100% - 260px)',
              }}
            >
              {/* Header */}
              <Header />

              {/* Page Contents */}
              <Box component="main" sx={{ flexGrow: 1 }}>
                {children}
              </Box>
            </Box>
          </Box>
        </ThemeProvider>
      </body>
    </html>
  );
}
