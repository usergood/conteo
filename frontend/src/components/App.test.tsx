import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent, waitFor, cleanup } from '@testing-library/react';
import { App } from '@/components/App';

vi.mock('@/lib/api', () => ({
  api: {
    hydrate: vi.fn().mockRejectedValue(new Error('no session')),
    authConfig: vi.fn().mockResolvedValue({
      authMode: 'dev',
      googleClientId: '',
      devLoginEnabled: true,
      defaultLanguage: 'es',
    }),
    logout: vi.fn().mockResolvedValue({ ok: true }),
    saveLanguage: vi.fn().mockResolvedValue({ language: 'es' }),
    settingsSeed: vi.fn().mockResolvedValue({ currency: 'MXN', fixedFee: 320, convPct: 3, taxPct: 2 }),
    saveGuideStatus: vi.fn().mockResolvedValue({ guideStatus: 'done' }),
    saveBank: vi.fn(),
    googleUrl: vi.fn(),
    devLogin: vi.fn(),
  },
}));

beforeEach(() => {
  window.localStorage.clear();
  window.matchMedia = vi.fn().mockReturnValue({
    matches: false,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
  }) as unknown as typeof window.matchMedia;
});

afterEach(() => {
  cleanup();
  window.localStorage.clear();
});

describe('App language selector (ticket 8)', () => {
  it('renders the selector before sign-in', async () => {
    render(<App />);
    expect(await screen.findByRole('button', { name: 'Español' })).toBeInTheDocument();
  });

  it('applies the server default when nothing is stored', async () => {
    render(<App />);
    expect(await screen.findByRole('button', { name: 'Español' })).toHaveTextContent('🇪🇸 ES');
  });

  it('localStorage pick wins over the server default', async () => {
    window.localStorage.setItem('conteo-language', 'en');
    render(<App />);
    expect(await screen.findByRole('button', { name: 'English' })).toHaveTextContent('🇬🇧 EN');
  });

  it('an anonymous pick updates the trigger immediately and persists to localStorage', async () => {
    render(<App />);
    const trigger = await screen.findByRole('button', { name: 'Español' });
    fireEvent.click(trigger);
    fireEvent.click(await screen.findByRole('button', { name: 'English' }));
    await waitFor(() => expect(screen.getByRole('button', { name: 'English' })).toHaveTextContent('🇬🇧 EN'));
    expect(window.localStorage.getItem('conteo-language')).toBe('en');
  });

  it('auto-opens the setup guide once for a pending user (ticket 10)', async () => {
    const { api } = await import('@/lib/api');
    vi.mocked(api.hydrate).mockResolvedValueOnce({
      user: { sub: 'u1', email: 'you@example.com', displayName: 'You', avatarUrl: null, language: 'en', guideStatus: 'pending' },
      bank: null,
      sources: [],
      projects: [],
      settlements: [],
      sharesByMe: [],
      sharesWithMe: [],
      months: [],
      sharedMonths: [],
      fx: null,
    });
    render(<App />);
    expect(await screen.findByRole('dialog', { name: 'Setup guide' })).toBeInTheDocument();
  });
});
