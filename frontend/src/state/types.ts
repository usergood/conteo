export type Screen =
  | 'login'
  | 'settings'
  | 'sources'
  | 'close'
  | 'forecast'
  | 'months'
  | 'share';

export type Language = 'en' | 'es';

export type GuideStatus = 'pending' | 'skipped' | 'done';

export interface User {
  sub: string;
  email: string;
  displayName: string;
  avatarUrl: string | null;
  language: Language;
  guideStatus: GuideStatus;
}

export interface BankSettings {
  currency: string;
  fixedFee: number;
  convPct: number;
  taxPct: number;
}

export interface IncomeSource {
  id: string;
  name: string;
  currency: string;
  fixedSalary: number;
  commissionMode: 'none' | 'pct' | 'flat';
  commissionValue: number;
  active: boolean;
}

export interface Project {
  id: string;
  sourceId: string;
  name: string;
  value: number;
  assigned: string;
  estEnd: string;
  approval: string | null;
  settledMonth: string | null;
}

export interface CommissionBreakdownItem {
  id: string;
  name: string;
  commissionForeign: number;
}

export interface Settlement {
  id: string;
  sourceId: string;
  month: string;
  typedMxn: number;
  transfers: number;
  fixedSalaryForeign: number;
  commissionForeign: number;
  foreignPaid: number;
  grossMxn: number | null;
  derivedRate: number | null;
  tax: number;
  netAfterTax: number;
  paidProjectIds: string[];
  commissionBreakdown: CommissionBreakdownItem[];
}

export type ShareStatus = 'pending' | 'active' | 'dismissed' | 'rejected';

export interface Share {
  id: string;
  sourceId: string;
  email: string;
  status: ShareStatus;
  updatedAt: string;
}

export interface MonthSummary {
  id: string;
  year: number;
  monthNum: number;
  netTotal: number;
  sourceCount: number;
  sources: string[];
}

export interface SharedMonthSummary {
  id: string;
  owner: string;
  source: string;
  currency: string;
  year: number;
  monthNum: number;
  netAfterTax: number;
}

export interface FxSnapshot {
  base: string;
  rates: Record<string, number>;
  fetchedAt: string | null;
  stale: boolean;
}

export interface MonthFilters {
  source: string;
  year: string;
  month: string;
  q: string;
}

export interface HydratePayload {
  user: User;
  bank: BankSettings | null;
  sources: IncomeSource[];
  projects: Project[];
  settlements: Settlement[];
  sharesByMe: Share[];
  sharesWithMe: Share[];
  months: MonthSummary[];
  sharedMonths: SharedMonthSummary[];
  fx: FxSnapshot | null;
}

export type Action =
  | { type: 'LOGIN_SUCCESS'; user: User }
  | { type: 'LOGOUT' }
  | { type: 'HYDRATE'; payload: HydratePayload }
  | { type: 'SAVE_BANK'; bank: BankSettings; firstTime: boolean }
  | { type: 'ADD_SOURCE'; source: IncomeSource }
  | { type: 'EDIT_SOURCE'; source: IncomeSource }
  | { type: 'ADD_PROJECT'; project: Project }
  | { type: 'CLOSE_MONTH'; settlement: Settlement }
  | { type: 'ADD_SHARE'; share: Share }
  | { type: 'UPDATE_SHARE'; list: 'byMe' | 'withMe'; shareId: string; status: ShareStatus }
  | { type: 'SET_SCREEN'; screen: Screen }
  | { type: 'SELECT_SOURCE'; id: string | null }
  | { type: 'SET_LANG'; lang: Language }
  | { type: 'SET_MONTH_TAB'; tab: 'mine' | 'shared' }
  | { type: 'SET_MONTH_FILTERS'; filters: Partial<MonthFilters> };

export interface AppState {
  user: User | null;
  bank: BankSettings | null;
  sources: IncomeSource[];
  projects: Project[];
  settlements: Settlement[];
  sharesByMe: Share[];
  sharesWithMe: Share[];
  months: MonthSummary[];
  sharedMonths: SharedMonthSummary[];
  fx: FxSnapshot | null;
  screen: Screen;
  selectedSourceId: string | null;
  monthTab: 'mine' | 'shared';
  monthFilters: MonthFilters;
}

/* ------------------------------- API shapes ------------------------------- */

export interface AuthConfig {
  authMode: 'google' | 'dev';
  googleClientId: string;
  devLoginEnabled: boolean;
}

export interface SettingsSeed {
  currency: string;
  fixedFee: number;
  convPct: number;
  taxPct: number;
}

export interface ForecastProject {
  id: string;
  name: string;
  value: number;
  commissionForeign: number;
  estEnd: string;
}

export interface ForecastRow {
  sourceId: string;
  sourceName: string;
  currency: string;
  grossForeign: number;
  rateMxn: number | null;
  rateStale: boolean;
  grossMxn: number | null;
  bankNet: number | null;
  netAfterTax: number | null;
  projects: ForecastProject[];
}

export interface ForecastMonth {
  month: string;
  rows: ForecastRow[];
  totals: { grossMxn: number; bankNet: number; netAfterTax: number };
}

export interface ForecastResponse {
  windowStart: string;
  windowEnd: string;
  months: ForecastMonth[];
}

export interface CloseProject {
  id: string;
  name: string;
  value: number;
  commissionForeign: number;
}

export interface CloseSourceForm {
  id: string;
  name: string;
  currency: string;
  fixedSalary: number;
  commissionMode: 'none' | 'pct' | 'flat';
  commissionValue: number;
  bankPct: number;
  fixedFee: number;
  taxPct: number;
  projects: CloseProject[];
}

export interface CloseView {
  month: string;
  sources: CloseSourceForm[];
  settlements: Settlement[];
}
