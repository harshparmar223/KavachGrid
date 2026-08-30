'use client';

import React from 'react';
import Link from 'next/link';
import { Box, Typography, Button } from '@mui/material';

export default function NotFound() {
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
      <Typography variant="h3" sx={{ fontWeight: 800, mb: 1, color: '#00e5ff' }}>
        404
      </Typography>
      <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
        Page Not Found
      </Typography>
      <Typography variant="body2" sx={{ color: 'text.secondary', mb: 3 }}>
        The requested grid investigation view does not exist.
      </Typography>
      <Button
        component={Link}
        href="/"
        variant="contained"
        color="primary"
        sx={{ borderRadius: 2, textTransform: 'none', px: 3, py: 1 }}
      >
        Return to Overview
      </Button>
    </Box>
  );
}
