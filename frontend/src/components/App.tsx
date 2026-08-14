'use client';

import { createContext, useCallback, useContext, useEffect, useMemo, useReducer, useState } from 'react';
import { api } from '@/lib/api';
import { I18nContext, isLanguage, resolveLanguage, translate, type Language } from '@/lib/i18n';
import { useTheme } from '@/lib/theme';
import { initialState, reducer } from '@/state/reducer';
import type { Action, AppState, Screen } from '@/state/types';
import { LanguageSelector } from '@/components/LanguageSelector';
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

const LANG_STORAGE_KEY = 'conteo-language';

export function App() {
  const [state, dispatch] = useReducer(reducer, initialState);
  const [loading, setLoading] = useState(true);
  const [notice, setNotice] = useState('');
  const [defaultLang, setDefaultLang] = useState<Language>('en');
  const { theme, cycleTheme } = useTheme();

  useEffect(() => {
    api
      .authConfig()
      .then((cfg) => {
        if (isLanguage(cfg.defaultLanguage)) setDefaultLang(cfg.defaultLanguage);
      })
      .catch(() => {
        /* default 'en' */
      });
  }, []);

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

  const storedLang =
    typeof window !== 'undefined' ? window.localStorage.getItem(LANG_STORAGE_KEY) : null;
  const lang = resolveLanguage(state.user?.language, storedLang, defaultLang);

  const selectLang = useCallback(
    (next: Language) => {
      dispatch({ type: 'SET_LANG', lang: next });
      try {
        window.localStorage.setItem(LANG_STORAGE_KEY, next);
      } catch {
        /* non-fatal */
      }
      if (state.user) {
        api.saveLanguage(next).catch(() => {
          /* non-fatal */
        });
      }
    },
    [state.user],
  );

  const tValue = useMemo(
    () => ({
      lang,
      t: (key: string, vars?: Record<string, string | number>) => translate(lang, key, vars),
    }),
    [lang],
  );

  const screen = state.screen;

  if (loading) return <main className="app"><div className="meta">…</div></main>;

  return (
    <AppContext.Provider value={{ state, dispatch, reload, notify }}>
      <I18nContext.Provider value={tValue}>
        <header className="appbar">
          <img src="/conteo.svg" className="logo" alt="Conteo" />
          <div>
            <div className="title">{tValue.t('app.title')}</div>
            {state.user && <div className="who">{state.user.email}</div>}
          </div>
          <span className="spacer" />
          {notice && <span className="meta">{notice}</span>}
          <LanguageSelector lang={lang} onChange={selectLang} />
          <button className="iconbtn" onClick={cycleTheme}>{theme === 'dark' ? '☀️' : '🌙'}</button>
          {state.user && (
            <button className="iconbtn" onClick={logout}>{tValue.t('common.logout')}</button>
          )}
        </header>

        {screen !== 'login' && (
          <nav className="nav">
            {NAV.map((s) => (
              <button
                key={s}
                className={screen === s ? 'active' : ''}
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
