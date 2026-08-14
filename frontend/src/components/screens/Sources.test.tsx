import { afterEach, describe, expect, it } from 'vitest';
import { render, screen, fireEvent, cleanup } from '@testing-library/react';
import { AppContext } from '@/components/App';
import { I18nContext } from '@/lib/i18n';
import { SourcesScreen } from '@/components/screens/Sources';
import type { AppState } from '@/state/types';

afterEach(cleanup);

const t = (key: string, vars?: Record<string, string | number>) => {
  const dict: Record<string, string> = {
    'settings.title.new': 'Bank & tax settings',
    'sources.bank.missing': 'Add your Bank & tax settings first',
    'settings.save.cont': 'Save & continue →',
    'sources.empty.title': 'No income sources yet',
    'sources.empty.sub': 'Add your first income source',
    'sources.add': 'Add income source',
  };
  let s = dict[key] ?? key;
  if (vars) for (const k in vars) s = s.split(`{${k}}`).join(String(vars[k]));
  return s;
};

const i18n = { lang: 'en' as const, t };

function baseState(over: Partial<AppState>): AppState {
  return {
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
    screen: 'sources',
    selectedSourceId: null,
    monthTab: 'mine',
    monthFilters: { source: 'all', year: 'all', month: 'all', q: '' },
    ...over,
  };
}

function renderSources(state: AppState) {
  return render(
    <I18nContext.Provider value={i18n}>
      <AppContext.Provider value={{ state, dispatch: () => {}, reload: async () => {}, notify: () => {} }}>
        <SourcesScreen />
      </AppContext.Provider>
    </I18nContext.Provider>,
  );
}

describe('SourcesScreen bank banner (ticket 07)', () => {
  it('shows the explanation banner with a visible action when bank is null', () => {
    renderSources(baseState({ bank: null, sources: [] }));
    expect(screen.getByText('Bank & tax settings')).toBeInTheDocument();
    expect(screen.getByText('Add your Bank & tax settings first')).toBeInTheDocument();
    const add = screen.getByRole('button', { name: 'Add income source' });
    expect(add).toBeEnabled();
    const goSettings = screen.getByRole('button', { name: 'Save & continue →' });
    expect(goSettings).toBeInTheDocument();
  });

  it('does not show the banner when bank exists', () => {
    renderSources(
      baseState({
        bank: { currency: 'MXN', fixedFee: 320, convPct: 3, taxPct: 2 },
        sources: [],
      }),
    );
    expect(screen.queryByText('Add your Bank & tax settings first')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Add income source' })).toBeInTheDocument();
  });

  it('the empty-state Add action navigates to settings when bank is null', () => {
    const dispatch = (action: unknown) => {
      lastAction = action;
    };
    let lastAction: unknown = null;
    render(
      <I18nContext.Provider value={i18n}>
        <AppContext.Provider value={{ state: baseState({ bank: null, sources: [] }), dispatch, reload: async () => {}, notify: () => {} }}>
          <SourcesScreen />
        </AppContext.Provider>
      </I18nContext.Provider>,
    );
    fireEvent.click(screen.getByRole('button', { name: 'Add income source' }));
    expect(lastAction).toEqual({ type: 'SET_SCREEN', screen: 'settings' });
  });
});
