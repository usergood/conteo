'use client';

import { createContext, useCallback, useContext, useEffect, useMemo, useReducer, useState } from 'react';
import { api } from '@/lib/api';
import { I18nContext, translate } from '@/lib/i18n';
import { useTheme } from '@/lib/theme';
import { initialState, isLocked, reducer } from '@/state/reducer';
import type { Action, AppState, Screen } from '@/state/types';
import { LoginScreen } from '@/components/screens/Login';
import { SettingsScreen } from '@/components/screens/Settings';
import { SourcesScreen } from '@/components/screens/Sources';
import { CloseScreen } from '@/components/screens/Close';
import { ForecastScreen } from '@/components/screens/Forecast';
import { MonthsScreen } from '@/components/screens/Months';
import { ShareScreen } from '@/components/screens/Share';

interface AppContextValue {
  state: AppState;
  dispatch: React.Dispatch<Action>;
  reload: () => Promise<void>;
  notify: (msg: string) => void;
}

export const AppContext = createContext<AppContextValue>({
  state: initialState,
  dispatch: () => {},
  reload: async () => {},
  notify: () => {},
});

export const useApp = () => useContext(AppContext);

const NAV: Screen[] = ['forecast', 'sources', 'close', 'months', 'share', 'settings'];

const LANG_SYMBOL: Record<string, string> = { en: '🇬🇧', es: '🇪🇸' };

export function App() {
  const [state, dispatch] = useReducer(reducer, initialState);
  const [loading, setLoading] = useState(true);
  const [notice, setNotice] = useState('');
  const { theme, cycleTheme } = useTheme();

  const reload = useCallback(async () => {
    try {
      const payload = await api.hydrate();
      dispatch({ type: 'HYDRATE', payload });
    } catch {
      dispatch({ type: 'LOGOUT' });
    }
  }, []);

  useEffect(() => {
    reload().finally(() => setLoading(false));
  }, [reload]);

  const notify = useCallback((msg: string) => {
    setNotice(msg);
    window.setTimeout(() => setNotice(''), 3500);
  }, []);

  const logout = useCallback(async () => {
    try {
      await api.logout();
    } finally {
      dispatch({ type: 'LOGOUT' });
    }
  }, []);

  const toggleLang = useCallback(async () => {
    const next = state.user?.language === 'en' ? 'es' : 'en';
    dispatch({ type: 'SET_LANG', lang: next });
    try {
      await api.saveLanguage(next);
    } catch {
      /* non-fatal */
    }
  }, [state.user?.language]);

  const tValue = useMemo(
    () => ({
      lang: (state.user?.language ?? 'en') as 'en' | 'es',
      t: (key: string, vars?: Record<string, string | number>) =>
        translate((state.user?.language ?? 'en') as 'en' | 'es', key, vars),
    }),
    [state.user?.language],
  );

  const locked = isLocked(state);
  const screen = state.screen;

  if (loading) return <main className="app"><div className="meta">…</div></main>;

  return (
    <AppContext.Provider value={{ state, dispatch, reload, notify }}>
      <I18nContext.Provider value={tValue}>
        <header className="appbar">
          <div>
            <div className="title">{tValue.t('app.title')}</div>
            {state.user && <div className="who">{state.user.email}</div>}
          </div>
          <span className="spacer" />
          {notice && <span className="meta">{notice}</span>}
          {state.user && (
            <>
              <button className="iconbtn" onClick={toggleLang}>{LANG_SYMBOL[tValue.lang] ?? tValue.lang.toUpperCase()}</button>
              <button className="iconbtn" onClick={cycleTheme}>{theme === 'dark' ? '☀️' : '🌙'}</button>
              <button className="iconbtn" onClick={logout}>{tValue.t('common.logout')}</button>
            </>
          )}
        </header>

        {screen !== 'login' && (
          <nav className="nav">
            {NAV.map((s) => (
              <button
                key={s}
                className={screen === s ? 'active' : ''}
                disabled={locked && s !== 'settings'}
                onClick={() => dispatch({ type: 'SET_SCREEN', screen: s })}
              >
                {tValue.t(s)}
              </button>
            ))}
          </nav>
        )}

        <main className="app">
          {screen === 'login' && <LoginScreen />}
          {screen === 'settings' && <SettingsScreen />}
          {screen === 'sources' && <SourcesScreen />}
          {screen === 'close' && <CloseScreen />}
          {screen === 'forecast' && <ForecastScreen />}
          {screen === 'months' && <MonthsScreen />}
          {screen === 'share' && <ShareScreen />}
        </main>
      </I18nContext.Provider>
    </AppContext.Provider>
  );
}
