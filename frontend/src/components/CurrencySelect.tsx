'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import { api } from '@/lib/api';

/**
 * Searchable currency dropdown (ticket 15). Rows show `Code — Name` from the
 * canonical list served by GET /api/settings/currencies. The list is fetched
 * once and cached module-wide (no refetch on every screen visit or form open).
 * Mirrors the LanguageSelector custom-dropdown pattern.
 */
export interface CurrencyOption {
  code: string;
  name: string;
}

let cachePromise: Promise<CurrencyOption[]> | null = null;

function loadCurrencies(): Promise<CurrencyOption[]> {
  if (!cachePromise) {
    cachePromise = api.currencies().catch((e) => {
      cachePromise = null;
      throw e;
    });
  }
  return cachePromise;
}

export function CurrencySelect({
  value,
  onChange,
  ariaLabel,
}: {
  value: string;
  onChange: (code: string) => void;
  ariaLabel?: string;
}) {
  const [open, setOpen] = useState(false);
  const [list, setList] = useState<CurrencyOption[]>([]);
  const [query, setQuery] = useState('');
  const [error, setError] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadCurrencies()
      .then(setList)
      .catch(() => setError(true));
  }, []);

  useEffect(() => {
    const onMouseDown = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', onMouseDown);
    return () => document.removeEventListener('mousedown', onMouseDown);
  }, []);

  const current = list.find((c) => c.code === value);
  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return list;
    return list.filter((c) => c.code.toLowerCase().includes(q) || c.name.toLowerCase().includes(q));
  }, [list, query]);

  return (
    <div className="currency" ref={ref}>
      <button
        type="button"
        className="currency-trigger"
        aria-label={ariaLabel}
        aria-haspopup="listbox"
        aria-expanded={open}
        onClick={() => setOpen((o) => !o)}
      >
        {current ? `${current.code} — ${current.name}` : value || '…'}
      </button>
      {open && (
        <div className="currency-menu" role="listbox" aria-label={ariaLabel}>
          <input
            className="currency-search"
            type="text"
            autoFocus
            value={query}
            placeholder="Search…"
            onChange={(e) => setQuery(e.target.value)}
          />
          <ul className="currency-list">
            {error && <li className="currency-empty">Failed to load currencies</li>}
            {!error && filtered.length === 0 && <li className="currency-empty">No match</li>}
            {!error &&
              filtered.map((c) => (
                <li key={c.code} role="option" aria-selected={c.code === value}>
                  <button
                    className="currency-row"
                    onClick={() => {
                      onChange(c.code);
                      setOpen(false);
                      setQuery('');
                    }}
                  >
                    <span className="currency-code">{c.code}</span>
                    <span className="currency-name">{c.name}</span>
                  </button>
                </li>
              ))}
          </ul>
        </div>
      )}
    </div>
  );
}
