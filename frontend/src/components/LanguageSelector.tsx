'use client';

import { useEffect, useRef, useState } from 'react';
import { LANGUAGES, type Language } from '@/lib/i18n';
import { FlagIcon } from '@/components/FlagIcon';

/**
 * Custom language dropdown (ticket 8): shows `flag + code` for every available
 * language, rendered at all times (including pre-login). `name` backs
 * aria-label/title so screen readers and tooltips read the full language name.
 */
export function LanguageSelector({ lang, onChange }: { lang: Language; onChange: (next: Language) => void }) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const current = LANGUAGES.find((l) => l.code === lang) ?? LANGUAGES[0];

  useEffect(() => {
    const onMouseDown = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', onMouseDown);
    return () => document.removeEventListener('mousedown', onMouseDown);
  }, []);

  return (
    <div className="langsel" ref={ref}>
      <button
        className="iconbtn langsel-trigger"
        aria-label={current.name}
        aria-haspopup="listbox"
        aria-expanded={open}
        onClick={() => setOpen((o) => !o)}
      >
        <FlagIcon code={current.code} /> {current.code.toUpperCase()}
      </button>
      {open && (
        <ul className="langsel-menu" role="listbox" aria-label="Language">
          {LANGUAGES.map((l) => (
            <li key={l.code} role="option" aria-selected={l.code === lang}>
              <button
                className="langsel-row"
                aria-label={l.name}
                title={l.name}
                onClick={() => {
                  onChange(l.code);
                  setOpen(false);
                }}
              >
                <FlagIcon code={l.code} /> {l.code.toUpperCase()}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
