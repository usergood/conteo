'use client';

import { useCallback, useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { useI18n } from '@/lib/i18n';
import type { CloseSourceForm, CloseView } from '@/state/types';
import { useApp } from '@/components/App';

function currentMonth(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
}

interface Draft {
  typed: string;
  transfers: number;
  salaryOverride: string;
  paid: Set<string>;
}

function derive(typed: number, foreign: number, transfers: number, fee: number, convPct: number, taxPct: number) {
  const rate = (typed + transfers * fee) / (foreign * (1 - convPct / 100));
  const gross = foreign * rate;
  const tax = typed * (taxPct / 100);
  const netAfterTax = typed - tax;
  return { rate, gross, tax, netAfterTax };
}

export function CloseScreen() {
  const { t } = useI18n();
  const { state, dispatch, notify } = useApp();
  const [month, setMonth] = useState(currentMonth());
  const [view, setView] = useState<CloseView | null>(null);
  const [drafts, setDrafts] = useState<Record<string, Draft>>({});
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');
  const [expanded, setExpanded] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    api.closeView(month)
      .then((v) => {
        if (!alive) return;
        setView(v);
        setDrafts((prev) => {
          const next: Record<string, Draft> = {};
          for (const s of v.sources) {
            const p = prev[s.id] ?? { typed: '', transfers: 1, salaryOverride: '', paid: new Set<string>() };
            next[s.id] = { ...p, paid: new Set(p.paid) };
          }
          return next;
        });
      })
      .catch(() => { if (alive) setView(null); });
    return () => { alive = false; };
  }, [month]);

  const closeSource = useCallback(
    async (s: CloseSourceForm) => {
      const d = drafts[s.id];
      setBusy(true);
      setErr('');
      try {
        const settlement = await api.closeMonth({
          month,
          sourceId: s.id,
          typedMxn: Number(d.typed) || 0,
          transfers: d.transfers,
          paidProjectIds: Array.from(d.paid),
          fixedSalaryOverride: d.salaryOverride ? Number(d.salaryOverride) : undefined,
        });
        dispatch({ type: 'CLOSE_MONTH', settlement });
        notify(t('close.closed'));
        setView(await api.closeView(month));
      } catch (e) {
        setErr(e instanceof Error ? e.message : String(e));
      } finally {
        setBusy(false);
      }
    },
    [month, drafts, dispatch, notify, t],
  );

  const allDone = view !== null && view.sources.length === 0;

  return (
    <div>
      <div className="headrow" style={{ marginBottom: 12 }}>
        <h3>{t('close.month', { m: month })}</h3>
        <input type="month" value={month} onChange={(e) => setMonth(e.target.value)} style={{ maxWidth: 160 }} />
      </div>
      <p className="sub">{t('close.sub')}</p>
      {err && <div className="error">{err}</div>}

      {allDone && (
        <div className="panel">
          <h3>{t('close.alldone')}</h3>
          <p className="meta">{t('close.alldone.sub')}</p>
        </div>
      )}

      {view === null && !allDone && <div className="panel"><p className="meta">{t('close.empty')}</p></div>}

      {view?.sources.map((s) => {
        const d = drafts[s.id];
        if (!d) return null;
        const fixedForeign = d.salaryOverride ? Number(d.salaryOverride) || 0 : s.fixedSalary;
        const foreign = fixedForeign + s.projects.filter((p) => d.paid.has(p.id)).reduce((a, p) => a + p.commissionForeign, 0);
        const typed = Number(d.typed) || 0;
        const preview = foreign > 0 ? derive(typed, foreign, d.transfers, s.fixedFee, s.bankPct, s.taxPct) : null;
        const open = expanded === s.id;
        return (
          <div key={s.id} className="panel">
            <div className="headrow" style={{ cursor: 'pointer' }} onClick={() => setExpanded(open ? null : s.id)}>
              <h3>{s.name} <span className="tag accent">{s.currency}</span></h3>
              <span className="meta">{open ? '▾' : '▸'}</span>
            </div>
            {open && (
              <>
                {s.projects.length > 0 ? (
                  <>
                    <p className="meta">{t('close.pick')}</p>
                    {s.projects.map((p) => (
                      <label key={p.id} style={{ display: 'block', padding: '4px 0', fontSize: 14 }}>
                        <input
                          type="checkbox"
                          checked={d.paid.has(p.id)}
                          onChange={() =>
                            setDrafts((prev) => {
                              const paid = new Set(prev[s.id].paid);
                              if (paid.has(p.id)) paid.delete(p.id); else paid.add(p.id);
                              return { ...prev, [s.id]: { ...prev[s.id], paid } };
                            })
                          }
                        />{' '}
                        {p.name} — {fmtF(p.value)} {s.currency}
                        {p.commissionForeign > 0 && <span className="meta"> (+{fmtF(p.commissionForeign)} comm)</span>}
                      </label>
                    ))}
                  </>
                ) : (
                  <p className="meta">{t('close.noproj')}</p>
                )}
                {s.fixedSalary > 0 && <p className="meta" style={{ marginTop: 8 }}>{t('close.fixed', { v: fmtF(s.fixedSalary), c: s.currency })}</p>}

                <div className="field">
                  <label>{t('close.override', { c: s.currency })}</label>
                  <input type="number" step="any" value={d.salaryOverride} placeholder={String(s.fixedSalary)} onChange={(e) => setDrafts((prev) => ({ ...prev, [s.id]: { ...prev[s.id], salaryOverride: e.target.value } }))} />
                  <p className="meta">{t('close.override.hint')}</p>
                </div>
                <div className="field">
                  <label>{t('close.transfers')}</label>
                  <input type="number" min={1} value={d.transfers} onChange={(e) => setDrafts((prev) => ({ ...prev, [s.id]: { ...prev[s.id], transfers: Math.max(1, Number(e.target.value) || 1) } }))} />
                </div>
                <div className="field">
                  <label>{t('close.typed')}</label>
                  <input type="number" step="any" value={d.typed} onChange={(e) => setDrafts((prev) => ({ ...prev, [s.id]: { ...prev[s.id], typed: e.target.value } }))} />
                </div>

                {preview && foreign > 0 && (
                  <div className="panel" style={{ margin: '12px 0' }}>
                    <div className="row"><span className="k">{t('close.rate', { c: s.currency })}</span><span className="v">{fmtF(preview.rate)}</span></div>
                    <div className="row"><span className="k">{t('close.gross')}</span><span className="v">{fmtM(preview.gross)}</span></div>
                    <div className="row"><span className="k">{t('close.net')}</span><span className="v">{fmtM(typed)}</span></div>
                    <div className="row"><span className="k">{t('close.tax', { p: s.taxPct })}</span><span className="v">{fmtM(preview.tax)}</span></div>
                    <div className="row"><span className="k">{t('close.after')}</span><span className="v">{fmtM(preview.netAfterTax)}</span></div>
                  </div>
                )}

                <button className="btn primary" disabled={busy} onClick={() => closeSource(s)}>
                  {t('close.cta', { name: s.name, month })}
                </button>
              </>
            )}
          </div>
        );
      })}

      {view && view.settlements.length > 0 && (
        <div className="panel">
          <h3 style={{ marginBottom: 8 }}>{t('close.settlements')}</h3>
          {view.settlements.map((st) => (
            <div key={st.id} className="row">
              <span className="k">{state.sources.find((s) => s.id === st.sourceId)?.name ?? st.sourceId}</span>
              <span className="v">{fmtM(st.netAfterTax)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function fmtF(n: number): string {
  return n.toLocaleString(undefined, { maximumFractionDigits: 4 });
}
function fmtM(n: number): string {
  return `$ ${n.toLocaleString(undefined, { maximumFractionDigits: 2 })} MXN`;
}