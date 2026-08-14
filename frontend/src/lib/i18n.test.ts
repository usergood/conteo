import { describe, expect, it } from 'vitest';
import { LANGUAGES, resolveLanguage, isLanguage, type Language } from './i18n';

describe('LANGUAGES (ticket 8)', () => {
  it('is a single extensible array with code/name/flag', () => {
    expect(LANGUAGES.map((l) => l.code)).toEqual(['en', 'es']);
    for (const l of LANGUAGES) {
      expect(l.code).toBeTruthy();
      expect(l.name).toBeTruthy();
      expect(l.flag).toBeTruthy();
    }
  });

  it('English carries the GB flag (GB never surfaces as text)', () => {
    const en = LANGUAGES.find((l) => l.code === 'en')!;
    expect(en.flag).toBe('🇬🇧');
    expect(en.name).toBe('English');
  });

  it('derives the Language type from the array', () => {
    const codes = LANGUAGES.map((l) => l.code) as Language[];
    expect(isLanguage('en')).toBe(true);
    expect(isLanguage('es')).toBe(true);
    expect(isLanguage('fr')).toBe(false);
    expect(isLanguage('GB')).toBe(false);
  });
});

describe('resolveLanguage precedence (ticket 8)', () => {
  it('user.language wins over storage and default', () => {
    expect(resolveLanguage('es', 'en', 'en')).toBe('es');
  });

  it('localStorage wins over the default', () => {
    expect(resolveLanguage(undefined, 'es', 'en')).toBe('es');
  });

  it('default is used when nothing is stored', () => {
    expect(resolveLanguage(undefined, null, 'es')).toBe('es');
  });

  it('falls back to en for unknown values', () => {
    expect(resolveLanguage(undefined, null, 'xx')).toBe('en');
    expect(resolveLanguage('xx', null, null)).toBe('en');
  });
});
