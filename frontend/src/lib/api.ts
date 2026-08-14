import type {
  AuthConfig,
  BankSettings,
  CloseView,
  CurrencyOption,
  ForecastResponse,
  HydratePayload,
  IncomeSource,
  Project,
  SettingsSeed,
  Settlement,
  Share,
  User,
} from '@/state/types';

export class ApiError extends Error {
  status: number;
  detail: string;
  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
    this.detail = detail;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    credentials: 'same-origin',
    ...init,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      if (typeof body.detail === 'string') detail = body.detail;
    } catch {
      /* keep statusText */
    }
    throw new ApiError(res.status, detail);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const api = {
  authConfig: () => request<AuthConfig>('/api/auth/config'),

  devLogin: (token: string, email: string, language?: string) =>
    request<{ user: User }>('/api/auth/dev-login', {
      method: 'POST',
      body: JSON.stringify({ token, email, language }),
    }),

  googleUrl: (lang?: string) =>
    request<{ url: string }>(
      `/api/auth/google-url${lang ? `?lang=${encodeURIComponent(lang)}` : ''}`,
    ),

  hydrate: () => request<HydratePayload>('/api/auth/me'),

  logout: () => request<{ ok: boolean }>('/api/auth/logout', { method: 'POST' }),

  settingsSeed: () => request<SettingsSeed>('/api/settings/seed'),

  currencies: () => request<CurrencyOption[]>('/api/settings/currencies'),

  saveBank: (bank: { currency: string; fixedFee: number; convPct: number; taxPct: number }) =>
    request<BankSettings>('/api/settings/bank', { method: 'PUT', body: JSON.stringify(bank) }),

  saveLanguage: (language: string) =>
    request<{ language: string }>('/api/settings/language', {
      method: 'PUT',
      body: JSON.stringify({ language }),
    }),

  saveGuideStatus: (guideStatus: string) =>
    request<{ guideStatus: string }>('/api/settings/guide-status', {
      method: 'PUT',
      body: JSON.stringify({ guideStatus }),
    }),

  listSources: () => request<IncomeSource[]>('/api/sources'),

  createSource: (body: Omit<IncomeSource, 'id' | 'active'>) =>
    request<IncomeSource>('/api/sources', { method: 'POST', body: JSON.stringify(body) }),

  updateSource: (id: string, body: Omit<IncomeSource, 'id' | 'active'>) =>
    request<IncomeSource>(`/api/sources/${id}`, { method: 'PUT', body: JSON.stringify(body) }),

  deactivateSource: (id: string) =>
    request<IncomeSource>(`/api/sources/${id}/deactivate`, { method: 'POST' }),

  deleteSource: (id: string) => request<{ ok: boolean; name: string }>(`/api/sources/${id}`, { method: 'DELETE' }),

  listProjects: (sourceId: string) => request<Project[]>(`/api/sources/${sourceId}/projects`),

  createProject: (
    sourceId: string,
    body: { name: string; value: number; assigned: string; estEnd: string; approval: string | null },
  ) => request<Project>(`/api/sources/${sourceId}/projects`, { method: 'POST', body: JSON.stringify(body) }),

  updateProject: (
    id: string,
    body: { name: string; value: number; assigned: string; estEnd: string; approval: string | null },
  ) => request<Project>(`/api/projects/${id}`, { method: 'PUT', body: JSON.stringify(body) }),

  deleteProject: (id: string) => request<{ ok: boolean }>(`/api/projects/${id}`, { method: 'DELETE' }),

  closeView: (month: string) => request<CloseView>(`/api/close?month=${encodeURIComponent(month)}`),

  closeMonth: (body: { month: string; sourceId: string; typedMxn: number; transfers: number; paidProjectIds: string[]; fixedSalaryOverride?: number }) =>
    request<Settlement>('/api/close', { method: 'POST', body: JSON.stringify(body) }),

  forecast: (windowSize = 3) =>
    request<ForecastResponse>(`/api/forecast?window=${windowSize}`),

  monthsMine: () => request<unknown[]>('/api/months/mine'),
  monthsShared: () => request<unknown[]>('/api/months/shared'),

  shares: () => request<{ byMe: Share[]; withMe: Share[] }>('/api/shares'),

  createShare: (sourceId: string, email: string) =>
    request<Share>('/api/shares', { method: 'POST', body: JSON.stringify({ sourceId, email }) }),

  revokeShare: (id: string) => request<Share>(`/api/shares/${id}/revoke`, { method: 'POST' }),
  dismissShare: (id: string) => request<Share>(`/api/shares/${id}/dismiss`, { method: 'POST' }),
  undismissShare: (id: string) => request<Share>(`/api/shares/${id}/undismiss`, { method: 'POST' }),

  slipUrl: (month: string) => `/api/months/${encodeURIComponent(month)}/slip`,
};
