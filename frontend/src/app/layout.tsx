import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Conteo',
  description: 'Conteo — multi-currency income tracker and forecaster',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
