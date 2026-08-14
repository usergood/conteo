'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { useI18n } from '@/lib/i18n';
import { useApp } from '@/components/App';

export function SettingsScreen() {
  const { t } = useI18n();
  const { state, dispatch, openGuide } = useApp();
  const bank = state.bank;
  const first = bank === null;
  const [fee, setFee] = useState(String(bank?.fixedFee ?? 320));
  const [pct, setPct] = useState(String(bank?.convPct ?? 0));
  const [tax, setTax] = useState(String(bank?.taxPct ?? 0));
  const [err, setErr] = useState('');

  useEffect(() => {
    if (bank) {
      setFee(String(bank.fixedFee));
      setPct(String(bank.convPct));
      setTax(String(bank.taxPct));
    } else {
      api.settingsSeed().then((seed) => {
        setFee(String(seed.fixedFee));
        setPct(String(seed.convPct));
        setTax(String(seed.taxPct));
      }).catch(() => {});
    }
  }, [bank]);

  const save = async () => {
    setErr('');
    try {
      const saved = await api.saveBank({ fixedFee: Number(fee) || 0, convPct: Number(pct) || 0, taxPct: Number(tax) || 0 });
      dispatch({ type: 'SAVE_BANK', bank: { ...saved }, firstTime: first });
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    }
  };

  return (
    <>
      <div className="panel">
        <div className="headrow">
          <div>
            <h3>{t('guide.title')}</h3>
            <p className="meta">{t('guide.sub')}</p>
          </div>
          <button className="btn primary" onClick={openGuide}>{t('settings.guide')}</button>
        </div>
      </div>
      <div className="panel">
      <h3>{first ? t('settings.title.new') : t('settings.title')}</h3>
      <p className="meta">{first ? t('settings.sub.new') : t('settings.sub')}</p>
      <div className="field">
        <label>{t('settings.currency')}</label>
        <input type="text" value={bank?.currency ?? 'MXN'} disabled />
        <div className="hint">{t('settings.currency.fixed')}</div>
      </div>
      <div className="field">
        <label>{t('settings.fee')}</label>
        <input type="number" step="any" value={fee} onChange={(e) => setFee(e.target.value)} />
        <div className="hint">{t('settings.fee.hint')}</div>
      </div>
      <div className="field">
        <label>{t('settings.pct')}</label>
        <input type="number" step="any" value={pct} onChange={(e) => setPct(e.target.value)} />
        <div className="hint">{t('settings.pct.hint')}</div>
      </div>
      <div className="field">
        <label>{t('settings.tax')}</label>
        <input type="number" step="any" value={tax} onChange={(e) => setTax(e.target.value)} />
      </div>
      {err && <div className="error">{err}</div>}
      <button className="btn primary" onClick={save}>{first ? t('settings.save.cont') : t('settings.save')}</button>
      </div>
    </>
  );
}
