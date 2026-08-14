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
    'sources.edit': 'Edit',
    'sources.edit.title': 'Edit income source',
    'sources.edit.hint': 'edit hint',
    'sources.save': 'Save source',
    'sources.save.changes': 'Save changes',
    'sources.cancel': 'Cancel',
    'sources.back': '← All sources',
    'sources.add.proj': 'Add project',
    'sources.deactivate': 'Deactivate',
    'sources.deactivate.confirm': 'Deactivate {name}?',
    'sources.deactivate.done': 'Source deactivated',
    'sources.delete': 'Delete',
    'sources.delete.confirm': 'Delete {name}?',
    'sources.delete.done': 'Source deleted',
    'sources.salary.has': 'Fixed salary',
    'sources.salary.none': 'No fixed salary',
    'sources.comm.disp.none': 'no commission',
    'sources.projects': 'project(s)',
    'proj.title': 'Add project',
    'proj.sub': 'Currency inherited: {cur}.',
    'proj.name': 'Name',
    'proj.value': 'Value',
    'proj.assigned': 'Assigned date',
    'proj.end': 'Estimated end',
    'proj.approval': 'Approval date',
    'proj.save': 'Save project',
    'proj.save.changes': 'Save changes',
    'proj.cancel': 'Cancel',
    'proj.approved': 'approved {d}',
    'proj.not': 'not approved',
    'proj.comm': 'Commission: {v} ({m} MXN)',
    'proj.comm.none': 'Commission: —',
    'proj.empty': 'No projects yet.',
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
      <AppContext.Provider value={{ state, dispatch: () => {}, reload: async () => {}, notify: () => {}, openGuide: () => {} }}>
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
        <AppContext.Provider value={{ state: baseState({ bank: null, sources: [] }), dispatch, reload: async () => {}, notify: () => {}, openGuide: () => {} }}>
          <SourcesScreen />
        </AppContext.Provider>
      </I18nContext.Provider>,
    );
    fireEvent.click(screen.getByRole('button', { name: 'Add income source' }));
    expect(lastAction).toEqual({ type: 'SET_SCREEN', screen: 'settings' });
  });
});

describe('SourcesScreen project view (bug fixes)', () => {
  const withSource: AppState = baseState({
    bank: { currency: 'MXN', fixedFee: 320, convPct: 3, taxPct: 2 },
    sources: [{ id: 's1', name: 'US company', currency: 'USD', fixedSalary: 5000, commissionMode: 'none', commissionValue: 0, active: true }],
    projects: [{ id: 'p1', sourceId: 's1', name: 'Website', value: 8000, assigned: '2026-08-01', estEnd: '2026-09-12', approval: null, settledMonth: null }],
  });

  it('Edit source opens the source edit form instead of printing a key', () => {
    renderSources(withSource);
    fireEvent.click(screen.getByText('US company'));
    fireEvent.click(screen.getAllByRole('button', { name: 'Edit' })[0]);
    expect(screen.getByText('Edit income source')).toBeInTheDocument();
    // and there is an explicit Cancel back to the project view
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));
    expect(screen.getByText('← All sources')).toBeInTheDocument();
  });

  it('add project button shows a single "+ Add project" (no double plus)', () => {
    renderSources(withSource);
    fireEvent.click(screen.getByText('US company'));
    const add = screen.getByRole('button', { name: '+ Add project' });
    expect(add).toBeInTheDocument();
    expect(add.textContent).toBe('+ Add project');
  });

  it('a project card has an Edit action to set approval', () => {
    renderSources(withSource);
    fireEvent.click(screen.getByText('US company'));
    fireEvent.click(screen.getAllByRole('button', { name: 'Edit' })[1]);
    expect(screen.getByText('Edit — Website')).toBeInTheDocument();
    expect(screen.getByText('Approval date')).toBeInTheDocument();
    expect(screen.getByText('Save changes')).toBeInTheDocument();
  });
});
