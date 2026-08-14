'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { useI18n } from '@/lib/i18n';
import { useApp } from '@/components/App';

export function SettingsScreen() {
  const { t } = useI18n();
  const { state, dispatch } = useApp();
  const bank = state.bank;
  const first = bank === null;
  const [fee, setFee] = useState(bank?.fixedFee ?? 320);
  const [pct, setPct] = useState(bank?.convPct ?? 0);
  const [tax, setTax] = useState(bank?.taxPct ?? 0);
  const [err, setErr] = useState('');

  useEffect(() => {
    if (bank) {
      setFee(bank.fixedFee);
      setPct(bank.convPct);
      setTax(bank.taxPct);
    } else {
      api.settingsSeed().then((seed) => {
        setFee(seed.fixedFee);
        setPct(seed.convPct);
        setTax(seed.taxPct);
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
        <input type="number" step="any" value={fee} onChange={(e) => setFee(e.target.valueAsNumber || 0)} />
        <div className="hint">{t('settings.fee.hint')}</div>
      </div>
      <div className="field">
        <label>{t('settings.pct')}</label>
        <input type="number" step="any" value={pct} onChange={(e) => setPct(e.target.valueAsNumber || 0)} />
        <div className="hint">{t('settings.pct.hint')}</div>
      </div>
      <div className="field">
        <label>{t('settings.tax')}</label>
        <input type="number" step="any" value={tax} onChange={(e) => setTax(e.target.valueAsNumber || 0)} />
      </div>
      {err && <div className="error">{err}</div>}
      <button className="btn primary" onClick={save}>{first ? t('settings.save.cont') : t('settings.save')}</button>
    </div>
  );
}
