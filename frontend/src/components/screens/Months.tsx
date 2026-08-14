'use client';

import { useMemo } from 'react';
import { api } from '@/lib/api';
import { useI18n } from '@/lib/i18n';
import { monthLabel, visibleMonths } from '@/state/reducer';
import type { MonthFilters } from '@/state/types';
import { useApp } from '@/components/App';

export function MonthsScreen() {
  const { t } = useI18n();
  const { state, dispatch } = useApp();
  const f = state.monthFilters;

  const mine = useMemo(() => visibleMonths(state).filter((m) => 'netTotal' in m), [state]);
  const shared = useMemo(() => visibleMonths(state).filter((m) => 'netAfterTax' in m), [state]);

  const years = useMemo(() => {
    const set = new Set<number>();
    state.months.forEach((m) => set.add(m.year));
    state.sharedMonths.forEach((m) => set.add(m.year));
    return Array.from(set).sort((a, b) => b - a);
  }, [state.months, state.sharedMonths]);

  const sources = useMemo(() => {
    const set = new Set<string>();
    state.months.forEach((m) => m.sources.forEach((s) => set.add(s)));
    state.sharedMonths.forEach((m) => set.add(m.source));
    return Array.from(set).sort();
  }, [state.months, state.sharedMonths]);

  const setFilters = (p: Partial<MonthFilters>) => dispatch({ type: 'SET_MONTH_FILTERS', filters: p });

  return (
    <div>
      <h3>{t('months.title')}</h3>
      <p className="sub">{t('months.sub')}</p>

      <div className="btns" style={{ marginBottom: 12 }}>
        <button className={state.monthTab === 'mine' ? 'btn primary' : 'btn'} onClick={() => dispatch({ type: 'SET_MONTH_TAB', tab: 'mine' })}>{t('months.mine')}</button>
        <button className={state.monthTab === 'shared' ? 'btn primary' : 'btn'} onClick={() => dispatch({ type: 'SET_MONTH_TAB', tab: 'shared' })}>{t('months.shared')}</button>
      </div>

      <div className="panel" style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'end' }}>
        <div className="field" style={{ marginBottom: 0, flex: 1, minWidth: 160 }}>
          <label>{t('months.search')}</label>
          <input type="text" value={f.q} onChange={(e) => setFilters({ q: e.target.value })} />
        </div>
        <div className="field" style={{ marginBottom: 0 }}>
          <label>{t('months.year')}</label>
          <select value={f.year} onChange={(e) => setFilters({ year: e.target.value })}>
            <option value="all">{t('months.all')}</option>
            {years.map((y) => <option key={y} value={y}>{y}</option>)}
          </select>
        </div>
        <div className="field" style={{ marginBottom: 0 }}>
          <label>{t('months.month')}</label>
          <select value={f.month} onChange={(e) => setFilters({ month: e.target.value })}>
            <option value="all">{t('months.all')}</option>
            {Array.from({ length: 12 }, (_, i) => (
              <option key={i + 1} value={i + 1}>{monthLabel({ year: 2000, monthNum: i + 1 })}</option>
            ))}
          </select>
        </div>
        <div className="field" style={{ marginBottom: 0 }}>
          <label>{t('sources.name')}</label>
          <select value={f.source} onChange={(e) => setFilters({ source: e.target.value })}>
            <option value="all">{t('months.all')}</option>
            {sources.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
      </div>

      {state.monthTab === 'mine' ? (
        mine.length === 0 ? (
          <div className="panel"><p className="meta">{t('months.empty')}</p></div>
        ) : (
          <table className="months">
            <thead>
              <tr>
                <th>{t('months.month')}</th>
                <th>{t('months.srccount', { n: '' }).trim()}</th>
                <th>{t('months.gross')}</th>
                <th>{t('months.netincome')}</th>
                <th>{t('months.tax')}</th>
                <th>{t('months.slip')}</th>
              </tr>
            </thead>
            <tbody>
              {mine.map((m) => (
                <tr key={m.id}>
                  <td>{monthLabel(m)}</td>
                  <td>{m.sourceCount} · {m.sources.join(', ')}</td>
                  <td>{fmtGross(m)}</td>
                  <td>{fmtM(m.bankNet)}</td>
                  <td>{fmtM(m.tax)}</td>
                  <td>
                    <a className="btn primary" href={api.slipUrl(m.id)} target="_blank" rel="noreferrer">{t('months.slip')}</a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )
      ) : shared.length === 0 ? (
        <div className="panel"><p className="meta">{t('months.empty')}</p></div>
      ) : (
        <table className="months">
          <thead>
            <tr>
              <th>{t('months.month')}</th>
              <th>{t('months.owner')}</th>
              <th>{t('sources.name')}</th>
              <th>{t('months.gross')}</th>
              <th>{t('months.netincome')}</th>
              <th>{t('months.tax')}</th>
              <th>{t('months.slip')}</th>
            </tr>
          </thead>
          <tbody>
            {shared.map((m) => (
              <tr key={m.id}>
                <td>{monthLabel(m)}</td>
                <td>{m.owner}</td>
                <td>{m.source} <span className="tag accent">{m.currency}</span></td>
                <td>{fmtF(m.grossForeign)} {m.currency}</td>
                <td>{fmtM(m.bankNet)}</td>
                <td>{fmtM(m.tax)}</td>
                <td>
                  <a className="btn primary" href={api.slipUrl(monthKey(m.year, m.monthNum))} target="_blank" rel="noreferrer">{t('months.slip')}</a>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

function monthKey(year: number, monthNum: number): string {
  return `${year}-${String(monthNum).padStart(2, '0')}`;
}
function fmtF(n: number): string {
  return n.toLocaleString(undefined, { maximumFractionDigits: 2 });
}
function fmtM(n: number): string {
  return `$ ${n.toLocaleString(undefined, { maximumFractionDigits: 2 })} MXN`;
}
function fmtGross(m: { grossByCurrency: Record<string, number> }): string {
  return Object.entries(m.grossByCurrency)
    .map(([cur, v]) => `${fmtF(v)} ${cur}`)
    .join(' · ');
}