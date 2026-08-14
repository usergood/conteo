'use client';

import { useState } from 'react';
import { api } from '@/lib/api';
import { useI18n } from '@/lib/i18n';
import type { IncomeSource, Project } from '@/state/types';
import { useApp } from '@/components/App';

type View = { kind: 'list' } | { kind: 'form'; source?: IncomeSource } | { kind: 'project'; source: IncomeSource };

function commissionOf(source: IncomeSource, project: Project): number {
  if (source.commissionMode === 'pct') return (project.value * source.commissionValue) / 100;
  if (source.commissionMode === 'flat') return source.commissionValue;
  return 0;
}

export function SourcesScreen() {
  const { t } = useI18n();
  const { state, reload } = useApp();
  const [view, setView] = useState<View>({ kind: 'list' });

  if (view.kind === 'form') {
    return <SourceForm initial={view.source} onDone={() => { setView({ kind: 'list' }); reload(); }} />;
  }
  if (view.kind === 'project') {
    return <ProjectView source={view.source} onBack={() => setView({ kind: 'list' })} />;
  }

  if (state.sources.length === 0) {
    return (
      <div className="panel">
        <div className="empty">
          <div className="big">🏷️</div>
          <h3>{t('sources.empty.title')}</h3>
          <p className="meta">{t('sources.empty.sub')}</p>
          <button className="btn primary" onClick={() => setView({ kind: 'form' })}>{t('sources.add')}</button>
        </div>
      </div>
    );
  }

  return (
    <div>
      {state.sources.map((s) => (
        <div key={s.id} className="card" onClick={() => setView({ kind: 'project', source: s })}>
          <div className="headrow">
            <h3>{s.name} <span className="tag accent">{s.currency}</span></h3>
            <div className="btns">
              <button className="iconbtn" onClick={(e) => { e.stopPropagation(); setView({ kind: 'form', source: s }); }}>
                {t('sources.edit')}
              </button>
              {!s.active && <span className="tag warn">inactive</span>}
            </div>
          </div>
          <p className="meta" style={{ margin: '4px 0' }}>
            {s.fixedSalary
              ? `${t('sources.salary.has')} ${fmtF(s.fixedSalary)} ${s.currency}`
              : t('sources.salary.none')}{' · '}
            {s.commissionMode === 'pct'
              ? `${s.commissionValue}%`
              : s.commissionMode === 'flat'
                ? `${fmtF(s.commissionValue)} ${s.currency}/proj`
                : t('sources.comm.disp.none')}
          </p>
          <p className="meta">{state.projects.filter((p) => p.sourceId === s.id).length} {t('sources.projects')}</p>
        </div>
      ))}
      <button className="btn" style={{ width: '100%' }} onClick={() => setView({ kind: 'form' })}>+ {t('sources.add')}</button>
    </div>
  );
}

function SourceForm({ initial, onDone }: { initial?: IncomeSource; onDone: () => void }) {
  const { t } = useI18n();
  const isEdit = !!initial;
  const [name, setName] = useState(initial?.name ?? '');
  const [currency, setCurrency] = useState(initial?.currency ?? 'USD');
  const [salary, setSalary] = useState(initial?.fixedSalary ?? 0);
  const [mode, setMode] = useState<'none' | 'pct' | 'flat'>(initial?.commissionMode ?? 'none');
  const [value, setValue] = useState(initial?.commissionValue ?? 0);
  const [err, setErr] = useState('');
  const { notify, dispatch } = useApp();

  const save = async () => {
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
      onDone();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    }
  };

  return (
    <div className="panel">
      <h3>{isEdit ? t('sources.edit.title') : t('sources.add.title')}</h3>
      <p className="meta">{isEdit ? t('sources.edit.hint') : t('sources.add.sub')}</p>
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
        <input type="number" step="any" value={salary} onChange={(e) => setSalary(e.target.valueAsNumber || 0)} placeholder={t('sources.salary.placeholder')} />
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
          <input type="number" step="any" value={value} onChange={(e) => setValue(e.target.valueAsNumber || 0)} />
        </div>
      )}
      {err && <div className="error">{err}</div>}
      <div className="btns">
        <button className="btn" onClick={onDone}>{t('sources.cancel')}</button>
        <button className="btn primary" onClick={save}>{isEdit ? t('sources.save.changes') : t('sources.save')}</button>
      </div>
    </div>
  );
}

function ProjectView({ source, onBack }: { source: IncomeSource; onBack: () => void }) {
  const { t } = useI18n();
  const { state, reload, notify } = useApp();
  const [adding, setAdding] = useState(false);
  const projects = state.projects.filter((p) => p.sourceId === source.id);
  const rateMxn = state.fx?.rates[source.currency] ?? null;

  const remove = async (p: Project) => {
    try {
      await api.deleteProject(p.id);
      await reload();
    } catch (e) {
      notify(e instanceof Error ? e.message : String(e));
    }
  };

  const deactivate = async () => {
    if (!window.confirm(t('sources.deactivate.confirm', { name: source.name }))) return;
    try {
      await api.deactivateSource(source.id);
      notify(t('sources.deactivate.done'));
      onBack();
      await reload();
    } catch (e) {
      notify(e instanceof Error ? e.message : String(e));
    }
  };

  const removeSource = async () => {
    if (!window.confirm(t('sources.delete.confirm', { name: source.name }))) return;
    try {
      await api.deleteSource(source.id);
      notify(t('sources.delete.done'));
      onBack();
      await reload();
    } catch (e) {
      notify(e instanceof Error ? e.message : String(e));
    }
  };

  return (
    <div className="panel">
      <button className="btn ghost" style={{ padding: '2px 0' }} onClick={onBack}>{t('sources.back')}</button>
      <div className="headrow">
        <h3>{source.name} <span className="tag accent">{source.currency}</span></h3>
        <div className="btns">
          {source.active ? (
            <button className="iconbtn" onClick={deactivate}>{t('sources.deactivate')}</button>
          ) : (
            <span className="tag warn">inactive</span>
          )}
          <button className="iconbtn" onClick={() => notify('source.edit')}>{t('sources.edit')}</button>
          {!source.active && <button className="iconbtn" onClick={removeSource}>✕ {t('sources.delete')}</button>}
        </div>
      </div>
      <p className="meta">
        {source.fixedSalary
          ? `${t('sources.salary.has')} ${fmtF(source.fixedSalary)} ${source.currency}`
          : t('sources.salary.none')}{' · '}
        {source.commissionMode === 'pct'
          ? `${source.commissionValue}%`
          : source.commissionMode === 'flat'
            ? `${fmtF(source.commissionValue)} ${source.currency}/proj`
            : t('sources.comm.disp.none')}
      </p>

      {projects.length === 0 && (
        <div className="empty">
          <div className="big">➕</div>
          <p className="meta">{t('proj.empty')}</p>
        </div>
      )}
      {projects.map((p) => {
        const comm = commissionOf(source, p);
        return (
          <div key={p.id} className="card static">
            <div className="headrow">
              <h3>{p.name}</h3>
              <div className="btns">
                {p.approval ? <span className="tag ok">{t('proj.approved', { d: p.approval })}</span> : <span className="tag warn">{t('proj.not')}</span>}
                {!p.settledMonth && <button className="iconbtn" onClick={() => remove(p)}>✕</button>}
              </div>
            </div>
            <p className="meta">
              {t('proj.value')} {fmtF(p.value)} {source.currency} · {t('proj.assigned')} {p.assigned} · {t('proj.end')} {p.estEnd}
            </p>
            <p className="meta">
              {comm > 0
                ? t('proj.comm', { v: `${fmtF(comm)} ${source.currency}`, m: rateMxn ? fmtF(comm * rateMxn) : '—' })
                : t('proj.comm.none')}
            </p>
          </div>
        );
      })}
      {adding ? (
        <ProjectForm source={source} onDone={() => { setAdding(false); reload(); }} onCancel={() => setAdding(false)} />
      ) : (
        <button className="btn" style={{ width: '100%' }} onClick={() => setAdding(true)}>+ {t('sources.add.proj')}</button>
      )}
    </div>
  );
}

function addWeeks(iso: string, weeks: number): string {
  const d = new Date(`${iso}T00:00:00`);
  d.setDate(d.getDate() + weeks * 7);
  return d.toISOString().slice(0, 10);
}

function ProjectForm({ source, onDone, onCancel }: { source: IncomeSource; onDone: () => void; onCancel: () => void }) {
  const { t } = useI18n();
  const [name, setName] = useState('');
  const [value, setValue] = useState(0);
  const [assigned, setAssigned] = useState(new Date().toISOString().slice(0, 10));
  const [end, setEnd] = useState(addWeeks(new Date().toISOString().slice(0, 10), 6));
  const [approval, setApproval] = useState('');
  const [err, setErr] = useState('');
  const { notify, dispatch } = useApp();

  const save = async () => {
    setErr('');
    try {
      const created = await api.createProject(source.id, {
        name: name.trim() || 'Project',
        value: Number(value) || 0,
        assigned,
        estEnd: end,
        approval: approval || null,
      });
      dispatch({ type: 'ADD_PROJECT', project: created });
      notify(t('proj.save'));
      onDone();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    }
  };

  return (
    <div className="panel" style={{ marginTop: 12 }}>
      <h3>{t('proj.title')}</h3>
      <p className="meta">{t('proj.sub', { cur: source.currency })}</p>
      <div className="field"><label>{t('proj.name')}</label><input type="text" value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Website redesign" /></div>
      <div className="field"><label>{t('proj.value')} ({source.currency})</label><input type="number" step="any" value={value} onChange={(e) => setValue(e.target.valueAsNumber || 0)} /></div>
      <div className="field"><label>{t('proj.assigned')}</label><input type="date" value={assigned} onChange={(e) => setAssigned(e.target.value)} /></div>
      <div className="field"><label>{t('proj.end')}</label><input type="date" value={end} onChange={(e) => setEnd(e.target.value)} /></div>
      <div className="field"><label>{t('proj.approval')}</label><input type="date" value={approval} onChange={(e) => setApproval(e.target.value)} /></div>
      {err && <div className="error">{err}</div>}
      <div className="btns">
        <button className="btn" onClick={onCancel}>{t('proj.cancel')}</button>
        <button className="btn primary" onClick={save}>{t('proj.save')}</button>
      </div>
    </div>
  );
}

function fmtF(n: number): string {
  return n.toLocaleString(undefined, { maximumFractionDigits: 2 });
}