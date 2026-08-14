'use client';

import { forwardRef, useEffect, useImperativeHandle, useState } from 'react';
import { api } from '@/lib/api';
import { useI18n } from '@/lib/i18n';
import type { BankSettings, IncomeSource, Project } from '@/state/types';
import { useApp } from '@/components/App';

export interface SaveHandle {
  /** Persists the form. Resolves true on success, false on failure. */
  save: () => Promise<boolean>;
}

export function addWeeks(iso: string, weeks: number): string {
  const d = new Date(`${iso}T00:00:00`);
  d.setDate(d.getDate() + weeks * 7);
  return d.toISOString().slice(0, 10);
}

/**
 * Shared form field components (ticket 10). The Bank Settings / Income Source
 * / Project screens and the setup-guide overlay both compose these, so the two
 * write to exactly the same data via the same api calls + reducer actions and
 * can never drift apart. Each exposes `save()` through a ref so the caller
 * owns its own button/label.
 */

export const BankFields = forwardRef<SaveHandle, { initial?: BankSettings | null }>(function BankFields(
  { initial },
  ref,
) {
  const { t } = useI18n();
  const { dispatch } = useApp();
  const [fee, setFee] = useState(String(initial?.fixedFee ?? 320));
  const [pct, setPct] = useState(String(initial?.convPct ?? 0));
  const [tax, setTax] = useState(String(initial?.taxPct ?? 0));
  const [err, setErr] = useState('');

  useEffect(() => {
    if (initial) {
      setFee(String(initial.fixedFee));
      setPct(String(initial.convPct));
      setTax(String(initial.taxPct));
    } else {
      api.settingsSeed().then((seed) => {
        setFee(String(seed.fixedFee));
        setPct(String(seed.convPct));
        setTax(String(seed.taxPct));
      }).catch(() => {});
    }
  }, [initial]);

  useImperativeHandle(ref, () => ({
    save: async () => {
      setErr('');
      try {
        const saved = await api.saveBank({ fixedFee: Number(fee) || 0, convPct: Number(pct) || 0, taxPct: Number(tax) || 0 });
        dispatch({ type: 'SAVE_BANK', bank: { ...saved }, firstTime: !initial });
        return true;
      } catch (e) {
        setErr(e instanceof Error ? e.message : String(e));
        return false;
      }
    },
  }));

  return (
    <>
      <div className="field">
        <label>{t('settings.currency')}</label>
        <input type="text" value={initial?.currency ?? 'MXN'} disabled />
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
    </>
  );
});

export const SourceFields = forwardRef<SaveHandle, { initial?: IncomeSource }>(function SourceFields(
  { initial },
  ref,
) {
  const { t } = useI18n();
  const { notify, dispatch } = useApp();
  const isEdit = !!initial;
  const [name, setName] = useState(initial?.name ?? '');
  const [currency, setCurrency] = useState(initial?.currency ?? 'USD');
  const [salary, setSalary] = useState(String(initial?.fixedSalary ?? 0));
  const [mode, setMode] = useState<'none' | 'pct' | 'flat'>(initial?.commissionMode ?? 'none');
  const [value, setValue] = useState(String(initial?.commissionValue ?? 0));
  const [err, setErr] = useState('');

  useImperativeHandle(ref, () => ({
    save: async () => {
      setErr('');
      try {
        const body = {
          name: name.trim(),
          currency: currency.trim().toUpperCase(),
          fixedSalary: Number(salary) || 0,
          commissionMode: mode,
          commissionValue: mode === 'none' ? 0 : Number(value) || 0,
        };
        if (isEdit && initial) {
          const updated = await api.updateSource(initial.id, body);
          dispatch({ type: 'EDIT_SOURCE', source: updated });
        } else {
          const created = await api.createSource(body);
          dispatch({ type: 'ADD_SOURCE', source: created });
        }
        notify(isEdit ? t('sources.save.changes') : t('sources.save'));
        return true;
      } catch (e) {
        setErr(e instanceof Error ? e.message : String(e));
        return false;
      }
    },
  }));

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
    </>
  );
});

export const ProjectFields = forwardRef<SaveHandle, { source: IncomeSource; initial?: Project }>(
  function ProjectFields({ source, initial }, ref) {
    const { t } = useI18n();
    const { notify, dispatch } = useApp();
    const isEdit = !!initial;
    const [name, setName] = useState(initial?.name ?? '');
    const [value, setValue] = useState(initial ? String(initial.value) : '');
    const [assigned, setAssigned] = useState(initial?.assigned ?? new Date().toISOString().slice(0, 10));
    const [end, setEnd] = useState(initial?.estEnd ?? addWeeks(new Date().toISOString().slice(0, 10), 6));
    const [approval, setApproval] = useState(initial?.approval ?? '');
    const [err, setErr] = useState('');

    useImperativeHandle(ref, () => ({
      save: async () => {
        setErr('');
        try {
          const body = {
            name: name.trim() || 'Project',
            value: Number(value) || 0,
            assigned,
            estEnd: end,
            approval: approval || null,
          };
          if (isEdit && initial) {
            const updated = await api.updateProject(initial.id, body);
            dispatch({ type: 'EDIT_PROJECT', project: updated });
          } else {
            const created = await api.createProject(source.id, body);
            dispatch({ type: 'ADD_PROJECT', project: created });
          }
          notify(isEdit ? t('proj.save.changes') : t('proj.save'));
          return true;
        } catch (e) {
          setErr(e instanceof Error ? e.message : String(e));
          return false;
        }
      },
    }));

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
        <div className="field">
          <label>{t('proj.approval')}</label>
          <input type="date" value={approval} onChange={(e) => setApproval(e.target.value)} />
        </div>
        {err && <div className="error">{err}</div>}
      </>
    );
  },
);
