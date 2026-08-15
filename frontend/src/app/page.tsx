'use client';

import { useEffect } from 'react';
import { App } from '@/components/App';

export default function Page() {
  useEffect(() => {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js').catch(() => {
        /* non-fatal */
      });
    }
  }, []);

  return <App />;
}
