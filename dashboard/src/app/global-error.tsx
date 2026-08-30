'use client';

import React from 'react';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html>
      <body style={{ backgroundColor: '#07111f', color: '#ffffff', fontFamily: 'sans-serif', padding: '40px', textAlign: 'center' }}>
        <h2>⚠️ System Error</h2>
        <p>{error.message || 'Critical error in KAVACHGRID interface.'}</p>
        <button
          onClick={() => reset()}
          style={{ padding: '10px 20px', background: '#00e5ff', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}
        >
          Reload Dashboard
        </button>
      </body>
    </html>
  );
}
