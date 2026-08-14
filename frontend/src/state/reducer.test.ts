import { describe, expect, it } from 'vitest';
import { reducer, initialState, myClosedMonths, visibleMonths, isLocked, guideUnlocks } from './reducer';
import type { AppState } from './types';

function seeded(): AppState {
  return reducer(initialState, {
    type: 'HYDRATE',
    payload: {
      user: { sub: 'u1', email: 'you@example.com', displayName: 'You', avatarUrl: null, language: 'en', guideStatus: 'done' },
      bank: { currency: 'MXN', fixedFee: 320, convPct: 3, taxPct: 2 },
      sources: [
        { id: 's1', name: 'US company', currency: 'USD', fixedSalary: 5000, commissionMode: 'pct', commissionValue: 10, active: true },
        { id: 's2', name: 'Swedish co', currency: 'SEK', fixedSalary: 0, commissionMode: 'none', commissionValue: 0, active: true },
      ],
      projects: [
        { id: 'p1', sourceId: 's1', name: 'Website redesign', value: 8000, assigned: '2026-08-01', estEnd: '2026-09-12', approval: null, settledMonth: null },
      ],
      settlements: [],
      sharesByMe: [],
      sharesWithMe: [],
      months: [
        { id: 'm-jun', year: 2026, monthNum: 6, netTotal: 91480.25, sourceCount: 1, sources: ['US company'] },
        { id: 'm-jul', year: 2026, monthNum: 7, netTotal: 107263.8, sourceCount: 1, sources: ['US company'] },
      ],
      sharedMonths: [
        { id: 'sm1', owner: 'alex@gmail.com', source: 'Sketchy Studio', currency: 'USD', year: 2026, monthNum: 5, netAfterTax: 81250 },
        { id: 'sm2', owner: 'alex@gmail.com', source: 'Sketchy Studio', currency: 'USD', year: 2026, monthNum: 6, netAfterTax: 64230.75 },
      ],
      fx: { base: 'USD', rates: { USD: 1, MXN: 17.06, SEK: 9.56 }, fetchedAt: '2026-08-13T10:00:00Z', stale: false },
    },
  });
}

describe('appReducer', () => {
  it('guide is locked only while guide_status is pending, independent of bank', () => {
    const pendingNoBank = reducer(initialState, { type: 'LOGIN_SUCCESS', user: { sub: 'u1', email: 'you@example.com', displayName: 'You', avatarUrl: null, language: 'en', guideStatus: 'pending' } });
    expect(isLocked(pendingNoBank)).toBe(true);
    // bank absent, but nav is still unlocked — screen is not forced
    const pendingBank = reducer(pendingNoBank, { type: 'HYDRATE', payload: {
      user: { sub: 'u1', email: 'you@example.com', displayName: 'You', avatarUrl: null, language: 'en', guideStatus: 'pending' },
      bank: { currency: 'MXN', fixedFee: 320, convPct: 3, taxPct: 2 },
      sources: [], projects: [], settlements: [], sharesByMe: [], sharesWithMe: [], months: [], sharedMonths: [], fx: null,
    } });
    expect(isLocked(pendingBank)).toBe(true);
  });

  it('guide is unlocked once guide_status is done, even without bank', () => {
    const doneNoBank = reducer(initialState, { type: 'HYDRATE', payload: {
      user: { sub: 'u1', email: 'you@example.com', displayName: 'You', avatarUrl: null, language: 'en', guideStatus: 'done' },
      bank: null,
      sources: [], projects: [], settlements: [], sharesByMe: [], sharesWithMe: [], months: [], sharedMonths: [], fx: null,
    } });
    expect(isLocked(doneNoBank)).toBe(false);
  });

  it('LOGIN_SUCCESS then HYDRATE with bank unlocks and lands on sources (empty state)', () => {
    const logged = reducer(initialState, { type: 'LOGIN_SUCCESS', user: { sub: 'u1', email: 'you@example.com', displayName: 'You', avatarUrl: null, language: 'en', guideStatus: 'pending' } });
    const state = reducer(logged, { type: 'HYDRATE', payload: {
      user: { sub: 'u1', email: 'you@example.com', displayName: 'You', avatarUrl: null, language: 'en', guideStatus: 'done' },
      bank: { currency: 'MXN', fixedFee: 320, convPct: 3, taxPct: 2 },
      sources: [], projects: [], settlements: [], sharesByMe: [], sharesWithMe: [], months: [], sharedMonths: [], fx: null,
    } });
    expect(isLocked(state)).toBe(false);
    expect(state.screen).toBe('sources');
  });

  it('SET_SCREEN navigates', () => {
    const state = reducer(seeded(), { type: 'SET_SCREEN', screen: 'sources' });
    expect(state.screen).toBe('sources');
  });

  it('SAVE_BANK first-run routes to sources and stores bank', () => {
    const state = reducer(initialState, { type: 'SAVE_BANK', firstTime: true, bank: { currency: 'MXN', fixedFee: 320, convPct: 3, taxPct: 2 } });
    expect(state.bank?.fixedFee).toBe(320);
    expect(state.screen).toBe('sources');
  });

  it('ADD_SOURCE appends and selects the new source', () => {
    const state = reducer(seeded(), { type: 'ADD_SOURCE', source: { id: 's3', name: 'UX Collective', currency: 'USD', fixedSalary: 0, commissionMode: 'flat', commissionValue: 600, active: true } });
    expect(state.sources).toHaveLength(3);
    expect(state.selectedSourceId).toBe('s3');
  });

  it('EDIT_SOURCE updates in place', () => {
    const state = reducer(seeded(), { type: 'EDIT_SOURCE', source: { id: 's1', name: 'US company LLC', currency: 'USD', fixedSalary: 5000, commissionMode: 'flat', commissionValue: 600, active: true } });
    const s = state.sources.find((x) => x.id === 's1')!;
    expect(s.name).toBe('US company LLC');
    expect(s.commissionMode).toBe('flat');
  });

  it('CLOSE_MONTH appends a settlement', () => {
    const state = reducer(seeded(), { type: 'CLOSE_MONTH', settlement: {
      id: 'st1', sourceId: 's1', month: '2026-08', typedMxn: 86500, transfers: 1,
      fixedSalaryForeign: 5000, commissionForeign: 800, foreignPaid: 5800, grossMxn: 89505, derivedRate: 15.4319, tax: 1730, netAfterTax: 84770, paidProjectIds: ['p1'], commissionBreakdown: [{ id: 'p1', name: 'Website redesign', commissionForeign: 800 }],
    } });
    expect(state.settlements).toHaveLength(1);
    expect(state.settlements[0].netAfterTax).toBe(84770);
  });

  it('SET_LANG switches the per-user language', () => {
    const state = reducer(reducer(initialState, { type: 'LOGIN_SUCCESS', user: { sub: 'u1', email: 'x@y.com', displayName: 'X', avatarUrl: null, language: 'en', guideStatus: 'done' } }), { type: 'SET_LANG', lang: 'es' });
    expect(state.user?.language).toBe('es');
  });

  it('SET_GUIDE_STATUS updates the user flag (ticket 10)', () => {
    const logged = reducer(initialState, { type: 'LOGIN_SUCCESS', user: { sub: 'u1', email: 'x@y.com', displayName: 'X', avatarUrl: null, language: 'en', guideStatus: 'pending' } });
    const state = reducer(logged, { type: 'SET_GUIDE_STATUS', guideStatus: 'done' });
    expect(state.user?.guideStatus).toBe('done');
  });
});

describe('guideUnlocks (ticket 10)', () => {
  const withUser = reducer(initialState, { type: 'LOGIN_SUCCESS', user: { sub: 'u1', email: 'x@y.com', displayName: 'X', avatarUrl: null, language: 'en', guideStatus: 'pending' } });

  it('bank is always unlocked; income needs a bank; project needs a source', () => {
    expect(guideUnlocks(withUser)).toEqual({ bank: true, income: false, project: false });
  });

  it('income unlocks once bank settings exist', () => {
    const s = reducer(withUser, { type: 'SAVE_BANK', firstTime: true, bank: { currency: 'MXN', fixedFee: 320, convPct: 3, taxPct: 2 } });
    expect(guideUnlocks(s)).toEqual({ bank: true, income: true, project: false });
  });

  it('project unlocks once at least one income source exists', () => {
    const s = reducer(withUser, { type: 'ADD_SOURCE', source: { id: 's1', name: 'US company', currency: 'USD', fixedSalary: 0, commissionMode: 'none', commissionValue: 0, active: true } });
    expect(guideUnlocks(s).project).toBe(true);
  });
});

describe('myClosedMonths', () => {
  it('returns recorded months plus the current month once every active source is closed', () => {
    const state = reducer(seeded(), { type: 'CLOSE_MONTH', settlement: {
      id: 'st1', sourceId: 's1', month: '2026-08', typedMxn: 86500, transfers: 1, fixedSalaryForeign: 5000, commissionForeign: 800, foreignPaid: 5800, grossMxn: 89505, derivedRate: 15.4319, tax: 1730, netAfterTax: 84770, paidProjectIds: ['p1'], commissionBreakdown: [{ id: 'p1', name: 'Website redesign', commissionForeign: 800 }],
    } });
    const partial = reducer(state, { type: 'CLOSE_MONTH', settlement: {
      id: 'st2', sourceId: 's2', month: '2026-08', typedMxn: 0, transfers: 1, fixedSalaryForeign: 0, commissionForeign: 0, foreignPaid: 0, grossMxn: null, derivedRate: null, tax: 0, netAfterTax: 0, paidProjectIds: [], commissionBreakdown: [],
    } });
    const months = myClosedMonths(partial, 2026, 8);
    expect(months.map((m) => m.monthNum)).toEqual([6, 7, 8]);
    expect(months[2].netTotal).toBe(84770);
    expect(months[2].sourceCount).toBe(2);
    expect(months[2].sources).toEqual(['US company', 'Swedish co']);
  });

  it('does not append the current month while a source is still open', () => {
    const months = myClosedMonths(seeded(), 2026, 8);
    expect(months.map((m) => m.monthNum)).toEqual([6, 7]);
  });
});

describe('visibleMonths', () => {
  const withShared = reducer(seeded(), { type: 'SET_MONTH_TAB', tab: 'shared' });

  it('mine tab filters by source, year, month and freetext', () => {
    const s = reducer(seeded(), { type: 'SET_MONTH_FILTERS', filters: { year: '2026', month: '6', q: 'US company' } });
    expect(visibleMonths(s).map((m) => m.id)).toEqual(['m-jun']);
  });

  it('freetext search matches the month label', () => {
    const s = reducer(seeded(), { type: 'SET_MONTH_FILTERS', filters: { q: 'Jul' } });
    expect(visibleMonths(s).map((m) => m.id)).toEqual(['m-jul']);
  });

  it('shared tab matches source and owner and returns shared rows', () => {
    const s = reducer(withShared, { type: 'SET_MONTH_FILTERS', filters: { q: 'Sketchy' } });
    expect(visibleMonths(s).map((m) => m.id)).toEqual(['sm1', 'sm2']);
  });

  it('no matches returns empty', () => {
    const s = reducer(seeded(), { type: 'SET_MONTH_FILTERS', filters: { q: 'zzz-nothing' } });
    expect(visibleMonths(s)).toEqual([]);
  });
});