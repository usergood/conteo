import type { Action, AppState, MonthSummary, SharedMonthSummary } from './types';

export const initialState: AppState = {
  user: null,
  bank: null,
  sources: [],
  projects: [],
  settlements: [],
  sharesByMe: [],
  sharesWithMe: [],
  months: [],
  sharedMonths: [],
  fx: null,
  foreignClients: [],
  screen: 'login',
  selectedSourceId: null,
  monthTab: 'mine',
  monthFilters: { source: 'all', year: 'all', month: 'all', q: '' },
};

export const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

export const monthKey = (year: number, monthNum: number) =>
  `${year}-${String(monthNum).padStart(2, '0')}`;

export function isOnboarded(state: AppState): boolean {
  return state.user !== null && state.bank !== null;
}

/**
 * Navigation is never hard-locked to Settings (ticket 07). Bank no longer gates
 * nav — it gates only Income Source creation (server 409 bank_settings_missing).
 * The flag reflects whether the first-time setup guide still needs to run.
 */
export function isLocked(state: AppState): boolean {
  return state.user?.guideStatus === 'pending';
}

/**
 * Setup-guide step unlocks (ticket 10), derived from data — not ephemeral
 * progress. Bank Settings is always unlocked; Income Source needs a bank;
 * Project needs at least one Income Source.
 */
export function guideUnlocks(state: AppState): { bank: boolean; income: boolean; project: boolean } {
  return { bank: true, income: state.bank !== null, project: state.sources.length >= 1 };
}

export function reducer(state: AppState = initialState, action: Action): AppState {
  switch (action.type) {
    case 'LOGIN_SUCCESS':
      return { ...state, user: action.user, screen: 'settings' };
    case 'LOGOUT':
      return { ...initialState, screen: 'login' };
    case 'HYDRATE': {
      const { user, bank, sources, projects, settlements, sharesByMe, sharesWithMe, months, sharedMonths, fx, foreignClients } =
        action.payload;
      const screen =
        bank === null
          ? 'settings'
          : state.bank === null && state.screen === 'settings'
            ? 'sources'
            : state.screen === 'login'
              ? 'sources'
              : state.screen;
      return {
        ...state,
        user,
        bank,
        sources,
        projects,
        settlements,
        sharesByMe,
        sharesWithMe,
        months,
        sharedMonths,
        fx,
        foreignClients: foreignClients ?? [],
        screen,
      };
    }
    case 'SAVE_BANK':
      return { ...state, bank: action.bank, screen: action.firstTime ? 'sources' : 'settings' };
    case 'ADD_SOURCE':
      return { ...state, sources: [...state.sources, action.source], selectedSourceId: action.source.id };
    case 'EDIT_SOURCE':
      return {
        ...state,
        sources: state.sources.map((s) => (s.id === action.source.id ? action.source : s)),
        selectedSourceId: action.source.id,
      };
    case 'ADD_PROJECT':
      return { ...state, projects: [...state.projects, action.project] };
    case 'EDIT_PROJECT':
      return {
        ...state,
        projects: state.projects.map((p) => (p.id === action.project.id ? action.project : p)),
      };
    case 'CLOSE_MONTH':
      return { ...state, settlements: [...state.settlements, action.settlement] };
    case 'ADD_SHARE':
      return { ...state, sharesByMe: [...state.sharesByMe, action.share] };
    case 'UPDATE_SHARE':
      if (action.list === 'byMe') {
        return {
          ...state,
          sharesByMe: state.sharesByMe.map((sh) =>
            sh.id === action.shareId ? { ...sh, status: action.status, updatedAt: new Date().toISOString() } : sh,
          ),
        };
      }
      return {
        ...state,
        sharesWithMe: state.sharesWithMe.map((sh) =>
          sh.id === action.shareId ? { ...sh, status: action.status, updatedAt: new Date().toISOString() } : sh,
        ),
      };
    case 'SET_SCREEN':
      return { ...state, screen: action.screen };
    case 'SELECT_SOURCE':
      return { ...state, selectedSourceId: action.id };
    case 'SET_LANG':
      return state.user
        ? { ...state, user: { ...state.user, language: action.lang } }
        : { ...state }; // new reference so the anonymous pick still re-renders
    case 'SET_GUIDE_STATUS':
      return state.user ? { ...state, user: { ...state.user, guideStatus: action.guideStatus } } : state;
    case 'SET_MONTH_TAB':
      return { ...state, monthTab: action.tab, monthFilters: { source: 'all', year: 'all', month: 'all', q: '' } };
    case 'SET_MONTH_FILTERS':
      return { ...state, monthFilters: { ...state.monthFilters, ...action.filters } };
    default:
      return state;
  }
}

export const monthLabel = (m: { year: number; monthNum: number }) =>
  `${MONTHS[m.monthNum - 1]} ${m.year}`;

/**
 * "My closed months": recorded closed months, plus the current month auto-
 * appended once every active source has a settlement for it (prototype
 * myClosedMonths()). The synthetic row aggregates that month's settlements.
 */
export function myClosedMonths(state: AppState, currentYear: number, currentMonthNum: number): MonthSummary[] {
  const list = [...state.months];
  const active = state.sources.filter((s) => s.active);
  if (active.length === 0) return list;
  const key = monthKey(currentYear, currentMonthNum);
  const settled = state.settlements.filter((s) => s.month === key);
  const settledIds = new Set(settled.map((s) => s.sourceId));
  const allClosed = active.every((s) => settledIds.has(s.id));
  // Skip the synthetic row when the backend already lists this month as fully
  // closed (its id is a real 'YYYY-MM' key). The synthetic 'm-YYYY-MM' id broke
  // the slip link (invalid_month) — never surface it for a known month.
  const alreadyListed = list.some((m) => m.year === currentYear && m.monthNum === currentMonthNum);
  if (allClosed && !alreadyListed) {
    const sources = active.map((s) => s.name);
    const grossByCurrency: Record<string, number> = {};
    let bankNet = 0;
    let tax = 0;
    for (const st of settled) {
      const cur = state.sources.find((s) => s.id === st.sourceId)?.currency ?? '';
      grossByCurrency[cur] = (grossByCurrency[cur] ?? 0) + st.foreignPaid;
      bankNet += st.typedMxn;
      tax += st.tax;
    }
    list.push({
      id: `m-${key}`,
      year: currentYear,
      monthNum: currentMonthNum,
      netTotal: settled.reduce((a, s) => a + s.netAfterTax, 0),
      sourceCount: active.length,
      sources,
      grossByCurrency,
      bankNet,
      tax,
    });
  }
  return list;
}

export function visibleMonths(
  state: AppState,
  now: { year: number; monthNum: number } = { year: new Date().getFullYear(), monthNum: new Date().getMonth() + 1 },
): (MonthSummary | SharedMonthSummary)[] {
  const f = state.monthFilters;
  const mine = state.monthTab === 'mine';
  const base = mine ? myClosedMonths(state, now.year, now.monthNum) : state.sharedMonths;
  const q = f.q.toLowerCase();

  return base.filter((m) => {
    if (mine) {
      const row = m as MonthSummary;
      if (f.source !== 'all' && !row.sources.includes(f.source)) return false;
      if (f.year !== 'all' && row.year !== Number(f.year)) return false;
      if (f.month !== 'all' && row.monthNum !== Number(f.month)) return false;
      if (q) {
        const hay = `${row.sources.join(' ')} ${monthLabel(row)}`.toLowerCase();
        if (!hay.includes(q)) return false;
      }
    } else {
      const row = m as SharedMonthSummary;
      if (f.source !== 'all' && row.source !== f.source) return false;
      if (f.year !== 'all' && row.year !== Number(f.year)) return false;
      if (f.month !== 'all' && row.monthNum !== Number(f.month)) return false;
      if (q) {
        const hay = `${row.source} ${row.owner} ${monthLabel(row)}`.toLowerCase();
        if (!hay.includes(q)) return false;
      }
    }
    return true;
  });
}