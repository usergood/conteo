import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent, cleanup } from '@testing-library/react';
import { AppContext } from '@/components/App';
import { I18nContext } from '@/lib/i18n';
import { api } from '@/lib/api';
import { ForecastScreen } from '@/components/screens/Forecast';
import type { AppState, ForecastResponse } from '@/state/types';

const t = (key: string, vars?: Record<string, string | number>) => {
  const dict: Record<string, string> = {
    'forecast.month': 'Forecast — {m}',
    'forecast.window': 'window: {m}',
    'forecast.sub': 'sub',
    'forecast.months': 'months',
    'forecast.gross': 'Gross (MXN)',
    'forecast.gross.cur': 'Gross',
    'forecast.net': 'Net',
    'forecast.netafter': 'After',
    'forecast.simple': 'Simple',
    'forecast.advanced': 'Advanced',
    'forecast.formula': '= Fixed {fixed} {cur} + Commissions {comm} {cur}',
    'forecast.convert': '× rate {rate} → {mxn}',
    'forecast.feeds': 'Projects feeding this month: {list}',
    'forecast.total.net': 'Total net',
    'forecast.total.after': 'Total after',
    'forecast.empty': 'empty',
  };
  let s = dict[key] ?? key;
  if (vars) for (const k in vars) s = s.split(`{${k}}`).join(String(vars[k]));
  return s;
};

const i18n = { lang: 'en' as const, t };

const data: ForecastResponse = {
  windowStart: '2026-08',
  windowEnd: '2026-10',
  months: [
    {
      month: '2026-08',
      rows: [
        {
          sourceId: 's1', sourceName: 'US company', currency: 'USD',
          grossForeign: 5800, rateMxn: 17.06, rateStale: false,
          grossMxn: 98948, bankNet: 95680, netAfterTax: 93766.4,
          projects: [{ id: 'p1', name: 'Website', value: 8000, commissionForeign: 800, estEnd: '2026-08-20' }],
        },
        {
          sourceId: 's2', sourceName: 'Swedish co', currency: 'SEK',
          grossForeign: 1000, rateMxn: 9.56, rateStale: true,
          grossMxn: 9560, bankNet: 8950, netAfterTax: 8771,
          projects: [],
        },
      ],
      totals: { grossMxn: 108508, bankNet: 104630, netAfterTax: 102537.4 },
    },
  ],
};

function baseState(over: Partial<AppState>): AppState {
  return {
    user: { sub: 'u1', email: 'you@example.com', displayName: 'You', avatarUrl: null, language: 'en', guideStatus: 'done' },
    bank: { currency: 'MXN', fixedFee: 320, convPct: 3, taxPct: 2 },
    sources: [
      { id: 's1', name: 'US company', currency: 'USD', fixedSalary: 5000, commissionMode: 'pct', commissionValue: 10, active: true },
      { id: 's2', name: 'Swedish co', currency: 'SEK', fixedSalary: 1000, commissionMode: 'none', commissionValue: 0, active: true },
    ],
    projects: [],
    settlements: [],
    sharesByMe: [],
    sharesWithMe: [],
    months: [],
    sharedMonths: [],
    fx: null,
    screen: 'forecast',
    selectedSourceId: null,
    monthTab: 'mine',
    monthFilters: { source: 'all', year: 'all', month: 'all', q: '' },
    ...over,
  };
}

function renderForecast(state: AppState) {
  return render(
    <I18nContext.Provider value={i18n}>
      <AppContext.Provider value={{ state, dispatch: () => {}, reload: async () => {}, notify: () => {}, openGuide: () => {} }}>
        <ForecastScreen />
      </AppContext.Provider>
    </I18nContext.Provider>,
  );
}

vi.mock('@/lib/api', () => ({ api: { forecast: vi.fn() } }));

beforeEach(() => {
  vi.mocked(api.forecast).mockResolvedValue(data);
});
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe('ForecastScreen (bug fixes)', () => {
  it('always shows the gross in original currency, even when folded', async () => {
    renderForecast(baseState({}));
    const rows = await screen.findAllByText('Gross');
    expect(rows.length).toBeGreaterThan(0);
    expect(screen.getAllByText((_, el) => !!el?.textContent && /USD$/.test(el.textContent.trim())).length).toBeGreaterThan(0);
    expect(screen.getAllByText((_, el) => !!el?.textContent && /SEK$/.test(el.textContent.trim())).length).toBeGreaterThan(0);
  });

  it('has no FX-source footer', async () => {
    renderForecast(baseState({}));
    await screen.findAllByText('Gross');
    expect(screen.queryByText(/FX source/)).not.toBeInTheDocument();
  });

  it('each source row has an Advanced/Simple toggle instead of a row-wide click', async () => {
    renderForecast(baseState({}));
    const toggles = await screen.findAllByRole('button', { name: /Advanced/ });
    expect(toggles).toHaveLength(2);
    fireEvent.click(toggles[0]);
    expect(screen.getByRole('button', { name: /Simple/ })).toBeInTheDocument();
    expect(screen.getAllByRole('button', { name: /Simple/ })).toHaveLength(1);
  });

  it('expanding one source reveals only its formula and projects', async () => {
    renderForecast(baseState({}));
    const toggles = await screen.findAllByRole('button', { name: /Advanced/ });
    fireEvent.click(toggles[0]);
    expect(screen.getByText(/Website/)).toBeInTheDocument();
    expect(screen.getByText(/Commissions 800 USD/)).toBeInTheDocument();
    // only the clicked source got an expand-toggle flip
    expect(screen.getAllByRole('button', { name: /Advanced/ })).toHaveLength(1);
  });
});
