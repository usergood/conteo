'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { useI18n } from '@/lib/i18n';
import type { AuthConfig } from '@/state/types';
import { useApp } from '@/components/App';

export function LoginScreen() {
  const { t, lang } = useI18n();
  const { dispatch, reload } = useApp();
  const [config, setConfig] = useState<AuthConfig | null>(null);
  const [token, setToken] = useState('demo-token');
  const [email, setEmail] = useState('you@example.com');
  const [err, setErr] = useState('');

  useEffect(() => {
    api.authConfig().then(setConfig).catch(() => setConfig(null));
  }, []);

  const devLogin = async () => {
    setErr('');
    try {
      const { user } = await api.devLogin(token.trim(), email.trim(), lang);
      dispatch({ type: 'LOGIN_SUCCESS', user });
      await reload();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    }
  };

  const googleLogin = async () => {
    setErr('');
    try {
      const { url } = await api.googleUrl(lang);
      window.location.href = url;
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    }
  };

  return (
    <div className="panel">
<div className="empty">
          <img src="/conteo.svg" className="login-logo" alt="Conteo" />
          <h3>{t('login.title')}</h3>
        {config?.authMode === 'google' ? (
          <>
            <p className="meta">Google Sign-In · scopes: openid email profile</p>
            <button className="btn primary" onClick={googleLogin}>{t('login.google')}</button>
          </>
        ) : (
          <>
            <p className="meta">{t('login.dev.sub')}</p>
            <div className="field">
              <label>{t('login.token')}</label>
              <input type="text" value={token} onChange={(e) => setToken(e.target.value)} />
            </div>
            <div className="field">
              <label>{t('login.email')}</label>
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
            </div>
            {err && <div className="error">{err}</div>}
            <button className="btn primary" onClick={devLogin}>{t('login.submit')}</button>
          </>
        )}
      </div>
    </div>
  );
}
