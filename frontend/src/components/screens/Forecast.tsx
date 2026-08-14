'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { useI18n } from '@/lib/i18n';
import type { ForecastResponse } from '@/state/types';
import { useApp } from '@/components/App';

const MONTH_LABEL = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

export function ForecastScreen() {
  const { t } = useI18n();
  const { state } = useApp();
  const [data, setData] = useState<ForecastResponse | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [windowSize, setWindowSize] = useState(3);

  useEffect(() => {
    let alive = true;
    api.forecast(windowSize)
      .then((d) => { if (alive) setData(d); })
      .catch(() => { if (alive) setData(null); });
    return () => { alive = false; };
  }, [windowSize]);

  if (state.sources.length === 0) {
    return (
      <div className="panel">
        <div className="empty">
          <div className="big">📈</div>
          <h3>{t('forecast.month', { m: windowLabel() })}</h3>
          <p className="meta">{t('forecast.empty')}</p>
        </div>
      </div>
    );
  }

  if (!data || data.months.length === 0) {
    return (
      <div className="panel">
        <h3>{t('forecast.month', { m: windowLabel() })}</h3>
        <p className="meta">{t('forecast.sub')}</p>
      </div>
    );
  }

  return (
    <div>
      <div className="headrow" style={{ marginBottom: 4 }}>
        <h3>{t('forecast.month', { m: monthLabel(data.months[0].month) })}</h3>
        <span className="tag accent">{t('forecast.window', { m: `${monthLabel(data.windowStart)}–${monthLabel(data.windowEnd)}` })}</span>
      </div>
      <p className="sub">{t('forecast.sub')}</p>

      <div className="btns" style={{ marginBottom: 12 }}>
        {[3, 6, 12].map((w) => (
          <button key={w} className={`btn ${windowSize === w ? 'primary' : ''}`} onClick={() => setWindowSize(w)}>
            {w} {t('forecast.months')}
          </button>
        ))}
      </div>

      {data.months.map((m) => (
        <div key={m.month} className="panel">
          <h3 style={{ marginBottom: 8 }}>{monthLabel(m.month)}</h3>
          {m.rows.map((r) => {
            const src = state.sources.find((s) => s.id === r.sourceId);
            const fixed = src?.fixedSalary ?? 0;
            const key = `${m.month}:${r.sourceId}`;
            const isOpen = expanded === key;
            const comm = Math.max(0, r.grossForeign - fixed);
            return (
              <div key={r.sourceId} className="card static">
                <div className="headrow">
                  <h3>{r.sourceName} <span className="tag accent">{r.currency}</span></h3>
                  <div className="btns">
                    {r.rateStale && <span className="tag warn">stale</span>}
                    <button className="btn ghost" onClick={() => setExpanded(isOpen ? null : key)}>
                      {isOpen ? `▾ ${t('forecast.simple')}` : `▸ ${t('forecast.advanced')}`}
                    </button>
                  </div>
                </div>
                <div className="row"><span className="k">{t('forecast.gross.cur')}</span><span className="v">{fmtF(r.grossForeign)} {r.currency}</span></div>
                {r.grossMxn != null && <div className="row"><span className="k">{t('forecast.gross')}</span><span className="v">{fmtM(r.grossMxn)}</span></div>}
                <div className="row"><span className="k">{t('forecast.net', { p: state.bank?.convPct ?? 0, f: fmtM(state.bank?.fixedFee ?? 0) })}</span><span className="v">{r.bankNet != null ? fmtM(r.bankNet) : '—'}</span></div>
                <div className="row"><span className="k">{t('forecast.netafter', { p: state.bank?.taxPct ?? 0 })}</span><span className="v">{r.netAfterTax != null ? fmtM(r.netAfterTax) : '—'}</span></div>
                {isOpen && (
                  <div className="panel" style={{ margin: '10px 0 0', background: 'transparent' }}>
                    <p className="meta">{t('forecast.formula', { fixed: fmtF(fixed), comm: fmtF(comm), cur: r.currency })}</p>
                    {r.rateMxn != null && <p className="meta">{t('forecast.convert', { rate: fmtF(r.rateMxn), mxn: r.grossMxn != null ? fmtM(r.grossMxn) : '—' })}</p>}
                    {r.projects.length > 0 && (
                      <p className="meta">{t('forecast.feeds', { list: r.projects.map((p) => `${p.name} (${fmtF(p.commissionForeign)} ${r.currency})`).join(', ') })}</p>
                    )}
                  </div>
                )}
              </div>
            );
          })}
          <div className="panel" style={{ margin: '8px 0 0' }}>
            <div className="row"><span className="k">{t('forecast.total.net')}</span><span className="v">{fmtM(m.totals.bankNet)}</span></div>
            <div className="row"><span className="k">{t('forecast.total.after')}</span><span className="v">{fmtM(m.totals.netAfterTax)}</span></div>
          </div>
        </div>
      ))}
    </div>
  );
}

function monthLabel(key: string): string {
  const [y, m] = key.split('-').map(Number);
  return `${MONTH_LABEL[m - 1]} ${y}`;
}
function windowLabel(): string {
  return monthLabel(`${new Date().getFullYear()}-${String(new Date().getMonth() + 1).padStart(2, '0')}`);
}
function fmtF(n: number): string {
  return n.toLocaleString(undefined, { maximumFractionDigits: 2 });
}
function fmtM(n: number): string {
  return `$ ${n.toLocaleString(undefined, { maximumFractionDigits: 2 })} MXN`;
}
