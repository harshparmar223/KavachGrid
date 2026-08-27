// KAVACHGRID 3.0 — Root Layout
// Phase 12: Complete implementation

import type { Metadata } from 'next';

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
      <body>{children}</body>
    </html>
  );
}
