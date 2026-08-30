// KAVACHGRID 3.0 — Root Layout
// Phase 12: Complete implementation

import React from 'react';
import type { Metadata } from 'next';
import ThemeProvider from '@/components/layout/ThemeProvider';
import Sidebar from '@/components/layout/Sidebar';
import Header from '@/components/layout/Header';
import Galaxy from '@/components/animations/Galaxy';
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
          <Box
            sx={{
              position: 'relative',
              display: 'flex',
              minHeight: '100vh',
              backgroundColor: 'background.default',
              overflow: 'hidden',
            }}
          >
            <Box sx={{ position: 'absolute', inset: 0, zIndex: 0 }}>
              <Galaxy
                focal={[0.5, 0.45]}
                rotation={[1.0, 0.25]}
                starSpeed={0.5}
                density={0.8}
                hueShift={190}
                speed={0.8}
                glowIntensity={0.28}
                saturation={0.8}
                mouseInteraction={true}
                mouseRepulsion={true}
                repulsionStrength={2.1}
                twinkleIntensity={0.5}
                rotationSpeed={0.12}
                transparent={true}
              />
            </Box>

            <Box sx={{ position: 'relative', zIndex: 1, display: 'flex', minHeight: '100vh', width: '100%' }}>
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
                  pt: '88px',
                  px: 4,
                  pb: 4,
                  width: 'calc(100% - 260px)',
                }}
              >
                {/* Header */}
                <Header />

                {/* Page Contents */}
                <Box component="main" sx={{ flexGrow: 1, position: 'relative', zIndex: 1 }}>
                  {children}
                </Box>
              </Box>
            </Box>
          </Box>
        </ThemeProvider>
      </body>
    </html>
  );
}
