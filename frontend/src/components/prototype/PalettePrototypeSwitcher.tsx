'use client';

import { useCallback, useEffect, useState } from 'react';

/* PROTOTYPE (throwaway) — switcher for wayfinding ticket: "Prototype candidate
   color themes to choose". Two independent dimensions, set as attributes on
   <html> so palette-prototype.css overrides apply:
     - palette: [data-palette] A|B|C  (from docs/research/color-scheme.md)
     - header:  [data-header]  grad|surface|accent|deep
   Both ride in the URL (?palette=&header=) so a choice is shareable and
   reload-stable. Dev-gated so it never ships. */

const PALETTES = [
  { key: 'A', name: 'A · Linen & Dusk' },
  { key: 'B', name: 'B · Stone & Plum' },
  { key: 'C', name: 'C · Dawn & Midnight' },
] as const;

const HEADERS = [
  { key: 'grad', name: 'gradient' },
  { key: 'surface', name: 'surface' },
  { key: 'accent', name: 'accent' },
  { key: 'deep', name: 'deep bar' },
  { key: 'topbar', name: 'rounded topbar' },
] as const;

const NAVS = [
  { key: 'tabs', name: 'tabs (top)' },
  { key: 'sidebar', name: 'sidebar (left)' },
] as const;

function param(key: string): string | null {
  if (typeof window === 'undefined') return null;
  return new URLSearchParams(window.location.search).get(key);
}
function inList<T extends { key: string }>(list: readonly T[], v: string | null, def: string): string {
  return v && list.some((x) => x.key === v) ? v : def;
}
function setParam(key: string, value: string) {
  const url = new URL(window.location.href);
  url.searchParams.set(key, value);
  window.history.replaceState({}, '', url.toString());
}

export function PalettePrototypeSwitcher() {
  const [palette, setPalette] = useState('B');
  const [header, setHeader] = useState('grad');
  const [nav, setNav] = useState('tabs');

  useEffect(() => {
    setPalette(inList(PALETTES, param('palette'), 'B'));
    setHeader(inList(HEADERS, param('header'), 'topbar'));
    setNav(inList(NAVS, param('nav'), 'tabs'));
  }, []);

  useEffect(() => {
    document.documentElement.dataset.palette = palette;
  }, [palette]);

  useEffect(() => {
    document.documentElement.dataset.header = header;
  }, [header]);

  useEffect(() => {
    document.documentElement.dataset.nav = nav;
  }, [nav]);

  const cycle = useCallback((list: readonly { key: string }[], current: string, dir: 1 | -1) => {
    const idx = list.findIndex((x) => x.key === current);
    return list[(idx + dir + list.length) % list.length].key;
  }, []);

  const onPalette = useCallback((dir: 1 | -1) => {
    setPalette((prev) => {
      const next = cycle(PALETTES, prev, dir);
      setParam('palette', next);
      return next;
    });
  }, [cycle]);

  const onHeader = useCallback((dir: 1 | -1) => {
    setHeader((prev) => {
      const next = cycle(HEADERS, prev, dir);
      setParam('header', next);
      return next;
    });
  }, [cycle]);

  const onNav = useCallback((dir: 1 | -1) => {
    setNav((prev) => {
      const next = cycle(NAVS, prev, dir);
      setParam('nav', next);
      return next;
    });
  }, [cycle]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement | null;
      const tag = target?.tagName;
      if (tag === 'INPUT' || tag === 'TEXTAREA' || target?.isContentEditable) return;
      if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
        const dir = e.key === 'ArrowLeft' ? -1 : 1;
        if (e.shiftKey) onHeader(dir);
        else onPalette(dir);
      } else if (e.key.toLowerCase() === 'n') {
        onNav(e.shiftKey ? -1 : 1);
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onHeader, onPalette, onNav]);

  if (process.env.NODE_ENV === 'production') return null;

  const p = PALETTES.find((x) => x.key === palette) ?? PALETTES[0];
  const h = HEADERS.find((x) => x.key === header) ?? HEADERS[0];
  const n = NAVS.find((x) => x.key === nav) ?? NAVS[0];

  return (
    <div style={{ ...pillStyle, flexDirection: 'column', alignItems: 'stretch', gap: 6, width: 320 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <span style={{ opacity: 0.6, fontSize: 12, width: 52 }}>PALETTE</span>
        <button aria-label="previous palette" onClick={() => onPalette(-1)} style={btnStyle}>‹</button>
        <span style={{ fontWeight: 600, whiteSpace: 'nowrap', flex: 1, textAlign: 'center' }}>{p.name}</span>
        <button aria-label="next palette" onClick={() => onPalette(1)} style={btnStyle}>›</button>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <span style={{ opacity: 0.6, fontSize: 12, width: 52 }}>HEADER</span>
        <button aria-label="previous header" onClick={() => onHeader(-1)} style={btnStyle}>‹</button>
        <span style={{ fontWeight: 600, whiteSpace: 'nowrap', flex: 1, textAlign: 'center' }}>{h.name}</span>
        <button aria-label="next header" onClick={() => onHeader(1)} style={btnStyle}>›</button>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <span style={{ opacity: 0.6, fontSize: 12, width: 52 }}>NAV</span>
        <button aria-label="previous nav" onClick={() => onNav(-1)} style={btnStyle}>‹</button>
        <span style={{ fontWeight: 600, whiteSpace: 'nowrap', flex: 1, textAlign: 'center' }}>{n.name}</span>
        <button aria-label="next nav" onClick={() => onNav(1)} style={btnStyle}>›</button>
      </div>
      <div style={{ opacity: 0.5, fontSize: 11, textAlign: 'center' }}>←/→ palette · shift+←/→ header · N nav · resize to see mobile</div>
    </div>
  );
}

const pillStyle: React.CSSProperties = {
  position: 'fixed',
  bottom: 16,
  left: '50%',
  transform: 'translateX(-50%)',
  zIndex: 9999,
  background: '#111',
  color: '#fff',
  borderRadius: 14,
  padding: '10px 16px',
  boxShadow: '0 4px 20px rgba(0,0,0,0.35)',
  fontFamily: 'system-ui, sans-serif',
  fontSize: 14,
  border: '1px solid rgba(255,255,255,0.2)',
};

const btnStyle: React.CSSProperties = {
  background: 'transparent',
  color: '#fff',
  border: 'none',
  cursor: 'pointer',
  fontSize: 18,
  lineHeight: 1,
  padding: '0 4px',
  borderRadius: 6,
};
