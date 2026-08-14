'use client';

import { useState } from 'react';
import { api } from '@/lib/api';
import { useI18n } from '@/lib/i18n';
import type { Share } from '@/state/types';
import { useApp } from '@/components/App';

export function ShareScreen() {
  const { t } = useI18n();
  const { state, dispatch, notify } = useApp();
  const [sourceId, setSourceId] = useState(state.sources[0]?.id ?? '');
  const [email, setEmail] = useState('');
  const [err, setErr] = useState('');

  const send = async () => {
    setErr('');
    if (!sourceId) { setErr('no source'); return; }
    try {
      const share = await api.createShare(sourceId, email.trim());
      dispatch({ type: 'ADD_SHARE', share });
      notify(t('share.send'));
      setEmail('');
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    }
  };

  const act = async (list: 'byMe' | 'withMe', sh: Share, action: 'revoke' | 'dismiss' | 'undismiss') => {
    try {
      const updated =
        action === 'revoke' ? await api.revokeShare(sh.id)
        : action === 'dismiss' ? await api.dismissShare(sh.id)
        : await api.undismissShare(sh.id);
      dispatch({ type: 'UPDATE_SHARE', list, shareId: sh.id, status: updated.status });
    } catch (e) {
      notify(e instanceof Error ? e.message : String(e));
    }
  };

  return (
    <div>
      <h3>{t('share.title')}</h3>
      <p className="sub">{t('share.sub')}</p>

      {state.sources.length > 0 ? (
        <div className="panel">
          <div className="field">
            <label>{t('share.source')}</label>
            <select value={sourceId} onChange={(e) => setSourceId(e.target.value)}>
              {state.sources.map((s) => <option key={s.id} value={s.id}>{s.name} ({s.currency})</option>)}
            </select>
          </div>
          <div className="field">
            <label>{t('login.email')}</label>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder={t('share.email')} />
          </div>
          {err && <div className="error">{err}</div>}
          <button className="btn primary" onClick={send}>{t('share.send')}</button>
        </div>
      ) : (
        <div className="panel"><p className="meta">{t('close.empty')}</p></div>
      )}

      <h3 style={{ margin: '18px 0 8px' }}>{t('share.byMe')}</h3>
      {state.sharesByMe.length === 0 ? (
        <div className="panel"><p className="meta">{t('share.empty')}</p></div>
      ) : (
        state.sharesByMe.map((sh) => {
          const src = state.sources.find((s) => s.id === sh.sourceId);
          return (
            <div key={sh.id} className="card static">
              <div className="headrow">
                <div>
                  <h3>{sh.email}</h3>
                  <p className="meta">{src ? `${src.name} (${src.currency})` : sh.sourceId}</p>
                </div>
                <div className="btns">
                  {sh.status === 'pending' && <span className="tag warn">{t('share.pending.sub')}</span>}
                  {sh.status === 'active' && <span className="tag ok">{t('share.active.sub')}</span>}
                  {sh.status === 'dismissed' && <span className="tag">dismissed</span>}
                  {sh.status === 'rejected' && <span className="tag">revoked</span>}
                  {sh.status !== 'rejected' && (
                    <button className="iconbtn" onClick={() => act('byMe', sh, 'revoke')}>revoke</button>
                  )}
                </div>
              </div>
            </div>
          );
        })
      )}

      <h3 style={{ margin: '18px 0 8px' }}>{t('months.shared')}</h3>
      {state.sharesWithMe.length === 0 ? (
        <div className="panel"><p className="meta">{t('share.empty')}</p></div>
      ) : (
        state.sharesWithMe.map((sh) => (
          <div key={sh.id} className="card static">
            <div className="headrow">
              <div>
                <h3>{sh.email}</h3>
                <p className="meta">{state.sources.find((s) => s.id === sh.sourceId)?.name ?? sh.sourceId}</p>
              </div>
              <div className="btns">
                {sh.status === 'active' && <span className="tag ok">{t('share.active.sub')}</span>}
                {sh.status === 'dismissed' && <span className="tag">dismissed</span>}
                {sh.status === 'active'
                  ? <button className="iconbtn" onClick={() => act('withMe', sh, 'dismiss')}>dismiss</button>
                  : sh.status === 'dismissed'
                    ? <button className="iconbtn" onClick={() => act('withMe', sh, 'undismiss')}>undismiss</button>
                    : null}
              </div>
            </div>
          </div>
        ))
      )}
    </div>
  );
}
