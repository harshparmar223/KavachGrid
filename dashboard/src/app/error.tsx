'use client';

import React, { useEffect } from 'react';
import { Box, Typography, Button } from '@mui/material';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error('Next.js caught client error:', error);
  }, [error]);

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '60vh',
        textAlign: 'center',
        p: 3,
      }}
    >
      <Typography variant="h5" sx={{ fontWeight: 700, mb: 1, color: '#f44336' }}>
        ⚠️ Something went wrong
      </Typography>
      <Typography variant="body2" sx={{ color: 'text.secondary', mb: 3, maxWidth: 500 }}>
        {error.message || 'An unexpected error occurred in the investigation dashboard.'}
      </Typography>
      <Button
        variant="contained"
        color="primary"
        onClick={() => reset()}
        sx={{ borderRadius: 2, textTransform: 'none', px: 3, py: 1 }}
      >
        Retry
      </Button>
    </Box>
  );
}
