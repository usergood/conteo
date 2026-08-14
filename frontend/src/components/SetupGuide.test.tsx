import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent, waitFor, cleanup } from '@testing-library/react';
import { useReducer } from 'react';
import { AppContext } from '@/components/App';
import { I18nContext } from '@/lib/i18n';
import { reducer, initialState } from '@/state/reducer';
import type { AppState } from '@/state/types';
import { SetupGuide } from '@/components/SetupGuide';

vi.mock('@/lib/api', () => ({
  api: {
    saveGuideStatus: vi.fn().mockResolvedValue({ guideStatus: 'done' }),
    settingsSeed: vi.fn().mockResolvedValue({ currency: 'MXN', fixedFee: 320, convPct: 3, taxPct: 2 }),
    saveBank: vi.fn().mockResolvedValue({ currency: 'MXN', fixedFee: 320, convPct: 3, taxPct: 2 }),
    createSource: vi.fn().mockResolvedValue({ id: 's1', name: 'US company', currency: 'USD', fixedSalary: 0, commissionMode: 'none', commissionValue: 0, active: true }),
    createProject: vi.fn().mockResolvedValue({ id: 'p1', sourceId: 's1', name: 'Website', value: 1000, assigned: '2026-08-01', estEnd: '2026-09-12', approval: null, settledMonth: null }),
  },
}));

afterEach(cleanup);

const t = (key: string, vars?: Record<string, string | number>) => {
  const dict: Record<string, string> = {
    'guide.title': 'Setup guide',
    'guide.sub': 'Three quick steps.',
    'guide.bank': 'Bank Settings',
    'guide.income': 'Income Source',
    'guide.project': 'Project',
    'guide.skip': 'Skip all',
    'guide.finish': 'Finish',
    'guide.add.income': 'Add income source',
    'guide.add.project': 'Add project',
    'settings.fee': 'Fee',
    'sources.name': 'Name',
    'proj.name': 'Name',
    'proj.assigned': 'Assigned',
    'proj.end': 'End',
  };
  let s = dict[key] ?? key;
  if (vars) for (const k in vars) s = s.split(`{${k}}`).join(String(vars[k]));
  return s;
};

const i18n = { lang: 'en' as const, t };

function loggedIn(): AppState {
  return reducer(initialState, {
    type: 'LOGIN_SUCCESS',
    user: { sub: 'u1', email: 'you@example.com', displayName: 'You', avatarUrl: null, language: 'en', guideStatus: 'pending' },
  });
}

function renderGuide(state: AppState, onClose = () => {}) {
  function Harness() {
    const [s, dispatch] = useReducer(reducer, state);
    return (
      <I18nContext.Provider value={i18n}>
        <AppContext.Provider value={{ state: s, dispatch, reload: async () => {}, notify: () => {}, openGuide: () => {} }}>
          <SetupGuide open onClose={onClose} />
        </AppContext.Provider>
      </I18nContext.Provider>
    );
  }
  return render(<Harness />);
}

describe('SetupGuide (ticket 10)', () => {
  it('renders the overlay with the bank step; later steps locked until their data exists', () => {
    renderGuide(loggedIn());
    expect(screen.getByRole('dialog', { name: 'Setup guide' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '1. Bank Settings' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '2. Income Source' })).toBeDisabled();
    expect(screen.getByRole('button', { name: '3. Project' })).toBeDisabled();
    expect(screen.queryByRole('button', { name: 'Finish' })).not.toBeInTheDocument();
  });

  it('saving bank unlocks Income Source and advances; Finish becomes available (bank-only finish)', async () => {
    const { api } = await import('@/lib/api');
    const onClose = vi.fn();
    renderGuide(loggedIn(), onClose);
    fireEvent.click(screen.getByRole('button', { name: 'Add income source' }));
    // advanced to step 2 (Income), Finish now available
    expect(api.saveBank).toHaveBeenCalled();
    const finish = await screen.findByRole('button', { name: 'Finish' });
    fireEvent.click(finish);
    await waitFor(() => expect(api.saveGuideStatus).toHaveBeenCalledWith('done'));
    expect(onClose).toHaveBeenCalled();
  });

  it('Skip all persists skipped and closes', async () => {
    const { api } = await import('@/lib/api');
    const onClose = vi.fn();
    renderGuide(loggedIn(), onClose);
    fireEvent.click(screen.getByRole('button', { name: 'Skip all' }));
    await waitFor(() => expect(api.saveGuideStatus).toHaveBeenCalledWith('skipped'));
    await waitFor(() => expect(onClose).toHaveBeenCalled());
  });

  it('project step unlocks once an income source exists', () => {
    const withBank = reducer(loggedIn(), { type: 'SAVE_BANK', firstTime: true, bank: { currency: 'MXN', fixedFee: 320, convPct: 3, taxPct: 2 } });
    const withSource = reducer(withBank, { type: 'ADD_SOURCE', source: { id: 's1', name: 'US company', currency: 'USD', fixedSalary: 0, commissionMode: 'none', commissionValue: 0, active: true } });
    renderGuide(withSource);
    expect(screen.getByRole('button', { name: '2. Income Source' })).toBeEnabled();
    expect(screen.getByRole('button', { name: '3. Project' })).toBeEnabled();
  });
});
