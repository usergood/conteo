'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { useI18n } from '@/lib/i18n';
import { guideUnlocks } from '@/state/reducer';
import type { GuideStatus } from '@/state/types';
import { useApp } from '@/components/App';

/**
 * 3-step setup guide (ticket 10). An overlay over any open screen — never a
 * separate screen, no outside-click close, no X close. Exits are Skip all and
 * Finish. Step 2 (Income Source) unlocks once Bank Settings exist; step 3
 * (Project) once at least one Income Source exists. Finish is available from
 * step 2, so a bank-only setup is a valid finish.
 */
export function SetupGuide({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { t } = useI18n();
  const { state, dispatch } = useApp();
  const [step, setStep] = useState(0);
  const unlocks = guideUnlocks(state);
  const stepList = [
    { key: 'guide.bank', on: unlocks.bank },
    { key: 'guide.income', on: unlocks.income },
    { key: 'guide.project', on: unlocks.project },
  ];

  useEffect(() => {
    if (open) setStep(0);
  }, [open]);

  if (!open) return null;

  const persist = async (guideStatus: 'done' | 'skipped') => {
    try {
      const res = await api.saveGuideStatus(guideStatus);
      dispatch({ type: 'SET_GUIDE_STATUS', guideStatus: res.guideStatus as GuideStatus });
    } finally {
      onClose();
    }
  };

  return (
    <div className="guide-backdrop">
      <div className="guide" role="dialog" aria-modal="true" aria-label={t('guide.title')}>
        <div className="guide-head">
          <h3>{t('guide.title')}</h3>
          <p className="meta">{t('guide.sub')}</p>
          <div className="guide-steps">
            {stepList.map((s, i) => (
              <button
                key={s.key}
                className={i === step ? 'active' : ''}
                disabled={!s.on}
                onClick={() => s.on && setStep(i)}
              >
                {i + 1}. {t(s.key)}
              </button>
            ))}
          </div>
        </div>

        <div className="guide-body">
          {step === 0 && <BankStep onAdvance={() => setStep(1)} />}
          {step === 1 && <SourceStep onAdvance={() => setStep(2)} />}
          {step === 2 && <ProjectStep />}
        </div>

        <div className="guide-actions">
          <button className="btn ghost" onClick={() => persist('skipped')}>{t('guide.skip')}</button>
          {step >= 1 && <button className="btn primary" onClick={() => persist('done')}>{t('guide.finish')}</button>}
        </div>
      </div>
    </div>
  );
}

function BankStep({ onAdvance }: { onAdvance: () => void }) {
  const { t } = useI18n();
  const { state, dispatch } = useApp();
  const bank = state.bank;
  const [fee, setFee] = useState(String(bank?.fixedFee ?? 320));
  const [pct, setPct] = useState(String(bank?.convPct ?? 0));
  const [tax, setTax] = useState(String(bank?.taxPct ?? 0));
  const [err, setErr] = useState('');

  const save = async () => {
    setErr('');
    try {
      const saved = await api.saveBank({ fixedFee: Number(fee) || 0, convPct: Number(pct) || 0, taxPct: Number(tax) || 0 });
      dispatch({ type: 'SAVE_BANK', bank: { ...saved }, firstTime: bank === null });
      onAdvance();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    }
  };

  return (
    <>
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
      </div>
      <div className="field">
        <label>{t('settings.tax')}</label>
        <input type="number" step="any" value={tax} onChange={(e) => setTax(e.target.value)} />
      </div>
      {err && <div className="error">{err}</div>}
      <button className="btn primary" onClick={save}>{t('guide.add.income')}</button>
    </>
  );
}

function SourceStep({ onAdvance }: { onAdvance: () => void }) {
  const { t } = useI18n();
  const { dispatch } = useApp();
  const [name, setName] = useState('');
  const [currency, setCurrency] = useState('USD');
  const [salary, setSalary] = useState('0');
  const [mode, setMode] = useState<'none' | 'pct' | 'flat'>('none');
  const [value, setValue] = useState('0');
  const [err, setErr] = useState('');

  const save = async () => {
    setErr('');
    try {
      const created = await api.createSource({
        name: name.trim(),
        currency: currency.trim().toUpperCase(),
        fixedSalary: Number(salary) || 0,
        commissionMode: mode,
        commissionValue: mode === 'none' ? 0 : Number(value) || 0,
      });
      dispatch({ type: 'ADD_SOURCE', source: created });
      onAdvance();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    }
  };

  return (
    <>
      <div className="field">
        <label>{t('sources.name')}</label>
        <input type="text" value={name} onChange={(e) => setName(e.target.value)} />
      </div>
      <div className="field">
        <label>{t('sources.currency')}</label>
        <input type="text" value={currency} onChange={(e) => setCurrency(e.target.value)} />
      </div>
      <div className="field">
        <label>{t('sources.salary')}</label>
        <input type="number" step="any" value={salary} onChange={(e) => setSalary(e.target.value)} placeholder={t('sources.salary.placeholder')} />
      </div>
      <div className="field">
        <label>{t('sources.comm.mode')}</label>
        <select value={mode} onChange={(e) => setMode(e.target.value as 'none' | 'pct' | 'flat')}>
          <option value="none">{t('sources.comm.none')}</option>
          <option value="pct">{t('sources.comm.pct')}</option>
          <option value="flat">{t('sources.comm.flat')}</option>
        </select>
      </div>
      {mode !== 'none' && (
        <div className="field">
          <label>{mode === 'pct' ? t('sources.comm.value.pct') : t('sources.comm.value.flat')}</label>
          <input type="number" step="any" value={value} onChange={(e) => setValue(e.target.value)} />
        </div>
      )}
      {err && <div className="error">{err}</div>}
      <button className="btn primary" onClick={save}>{t('guide.add.project')}</button>
    </>
  );
}

function ProjectStep() {
  const { t } = useI18n();
  const { state, dispatch } = useApp();
  const source = state.sources[0];
  const [name, setName] = useState('');
  const [value, setValue] = useState('');
  const [assigned, setAssigned] = useState(new Date().toISOString().slice(0, 10));
  const [end, setEnd] = useState(addWeeks(new Date().toISOString().slice(0, 10), 6));
  const [err, setErr] = useState('');

  if (!source) {
    return <p className="meta">{t('sources.empty.sub')}</p>;
  }

  const save = async () => {
    setErr('');
    try {
      const created = await api.createProject(source.id, {
        name: name.trim() || 'Project',
        value: Number(value) || 0,
        assigned,
        estEnd: end,
        approval: null,
      });
      dispatch({ type: 'ADD_PROJECT', project: created });
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    }
  };

  return (
    <>
      <div className="field">
        <label>{t('proj.name')}</label>
        <input type="text" value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Website redesign" />
      </div>
      <div className="field">
        <label>{t('proj.value')} ({source.currency})</label>
        <input type="number" step="any" value={value} onChange={(e) => setValue(e.target.value)} />
      </div>
      <div className="field">
        <label>{t('proj.assigned')}</label>
        <input type="date" value={assigned} onChange={(e) => setAssigned(e.target.value)} />
      </div>
      <div className="field">
        <label>{t('proj.end')}</label>
        <input type="date" value={end} onChange={(e) => setEnd(e.target.value)} />
      </div>
      {err && <div className="error">{err}</div>}
      <button className="btn" onClick={save}>{t('guide.add.project')}</button>
    </>
  );
}

function addWeeks(iso: string, weeks: number): string {
  const d = new Date(`${iso}T00:00:00`);
  d.setDate(d.getDate() + weeks * 7);
  return d.toISOString().slice(0, 10);
}
