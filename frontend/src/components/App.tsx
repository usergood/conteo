'use client';

import { createContext, useCallback, useContext, useEffect, useMemo, useReducer, useRef, useState } from 'react';
import { api } from '@/lib/api';
import { I18nContext, isLanguage, resolveLanguage, translate, type Language } from '@/lib/i18n';
import { useTheme } from '@/lib/theme';
import { initialState, reducer } from '@/state/reducer';
import type { Action, AppState, Screen } from '@/state/types';
import { LanguageSelector } from '@/components/LanguageSelector';
import { InstallButton } from '@/components/InstallButton';
import { SetupGuide } from '@/components/SetupGuide';
import { LoginScreen } from '@/components/screens/Login';
import { SettingsScreen } from '@/components/screens/Settings';
import { SourcesScreen } from '@/components/screens/Sources';
import { CloseScreen } from '@/components/screens/Close';
import { ForecastScreen } from '@/components/screens/Forecast';
import { MonthsScreen } from '@/components/screens/Months';
import { ShareScreen } from '@/components/screens/Share';
import { CfdiScreen } from '@/components/screens/Cfdi';
import { TaxScreen } from '@/components/screens/Tax';

interface AppContextValue {
  state: AppState;
  dispatch: React.Dispatch<Action>;
  reload: () => Promise<void>;
  notify: (msg: string) => void;
  openGuide: () => void;
}

export const AppContext = createContext<AppContextValue>({
  state: initialState,
  dispatch: () => {},
  reload: async () => {},
  notify: () => {},
  openGuide: () => {},
});

export const useApp = () => useContext(AppContext);

const NAV: { screen: Screen; icon: string }[] = [
  { screen: 'forecast', icon: '📈' },
  { screen: 'sources', icon: '🏢' },
  { screen: 'close', icon: '💰' },
  { screen: 'months', icon: '🗓️' },
  { screen: 'cfdi', icon: '📄' },
  { screen: 'tax', icon: '🧾' },
  { screen: 'share', icon: '🔗' },
  { screen: 'settings', icon: '⚙️' },
];

const LANG_STORAGE_KEY = 'conteo-language';

export function App() {
  const [state, dispatch] = useReducer(reducer, initialState);
  const [loading, setLoading] = useState(true);
  const [notice, setNotice] = useState('');
  const [defaultLang, setDefaultLang] = useState<Language>('en');
  const [appVersion, setAppVersion] = useState('');
  const [guideOpen, setGuideOpen] = useState(false);
  const autoOpenedRef = useRef(false);
  const { theme, cycleTheme } = useTheme();

  useEffect(() => {
    api
      .authConfig()
      .then((cfg) => {
        if (isLanguage(cfg.defaultLanguage)) setDefaultLang(cfg.defaultLanguage);
        if (cfg.version) setAppVersion(cfg.version);
      })
      .catch(() => {
        /* default 'en' */
      });
  }, []);

  // Auto-open the setup guide once for new users (guide_status === 'pending').
  useEffect(() => {
    if (state.user?.guideStatus === 'pending' && !autoOpenedRef.current) {
      autoOpenedRef.current = true;
      setGuideOpen(true);
    }
  }, [state.user?.guideStatus]);

  const openGuide = useCallback(() => setGuideOpen(true), []);

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

  if (loading) {
    return (
      <div className="splash">
        <img src="/conteo.svg" className="splash-logo" alt="Conteo" />
        <div className="splash-dots"><span /><span /><span /></div>
        {appVersion && <div className="splash-version">v{appVersion}</div>}
      </div>
    );
  }

  return (
    <AppContext.Provider value={{ state, dispatch, reload, notify, openGuide }}>
      <I18nContext.Provider value={tValue}>
        <header className="appbar">
          <img src="/conteo.svg" className="logo" alt="Conteo" />
          <div>
            <div className="title">
              {tValue.t('app.title')}
              {appVersion && <span className="version-badge">v{appVersion}</span>}
            </div>
            {state.user && <div className="who">{state.user.email}</div>}
          </div>
          <span className="spacer" />
          {notice && <span className="meta">{notice}</span>}
          <InstallButton />
          <LanguageSelector lang={lang} onChange={selectLang} />
          <button className="iconbtn" onClick={cycleTheme}>{theme === 'dark' ? '☀️' : '🌙'}</button>
          {state.user && (
            <button className="iconbtn" onClick={logout}>{tValue.t('common.logout')}</button>
          )}
        </header>

        <div className="page-shell">
          {screen !== 'login' && (
            <nav className="nav">
              {NAV.map(({ screen: s, icon }) => (
                <button
                  key={s}
                  className={screen === s ? 'active' : ''}
                  onClick={() => dispatch({ type: 'SET_SCREEN', screen: s })}
                >
                  <span className="nav-ico">{icon}</span>
                  <span className="nav-label">{tValue.t(s)}</span>
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
            {screen === 'cfdi' && <CfdiScreen />}
            {screen === 'tax' && <TaxScreen />}
          </main>
        </div>

        <SetupGuide open={guideOpen} onClose={() => setGuideOpen(false)} />
      </I18nContext.Provider>
    </AppContext.Provider>
  );
}
