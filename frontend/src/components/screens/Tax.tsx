'use client';

import { useCallback, useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { useI18n } from '@/lib/i18n';
import { useApp } from '@/components/App';
import type { TaxSummary } from '@/state/types';

function currentMonth(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
}

export function TaxScreen() {
  const { t } = useI18n();
  const { state } = useApp();
  const [summary, setSummary] = useState<TaxSummary | null>(null);
  const [month, setMonth] = useState(currentMonth());
  const [loading, setLoading] = useState(false);
  const [computing, setComputing] = useState(false);
  const [err, setErr] = useState('');

  const loadSummary = useCallback(async () => {
    setLoading(true);
    setErr('');
    try {
      const s = await api.getTaxSummary(month);
      setSummary(s);
    } catch (e: unknown) {
      if (e && typeof e === 'object' && 'status' in e && (e as { status: number }).status === 404) {
        setSummary(null);
      } else {
        setErr(e instanceof Error ? e.message : String(e));
      }
    } finally {
      setLoading(false);
    }
  }, [month]);

  useEffect(() => { loadSummary(); }, [loadSummary]);

  const handleCompute = useCallback(async () => {
    setComputing(true);
    setErr('');
    try {
      const s = await api.computeTaxSummary(month);
      setSummary(s);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setComputing(false);
    }
  }, [month]);

  const regimeLabel = (code: string) => {
    if (code === 'RESICO') return 'RESICO';
    if (code === 'LEGACY_2PCT') return 'Legacy 2%';
    return code;
  };

  const sourceName = (sourceId: string) =>
    state.sources.find((s) => s.id === sourceId)?.name ?? sourceId;

  return (
    <div>
      <div className="headrow" style={{ marginBottom: 12 }}>
        <h3>{t('tax.title')}</h3>
        <input type="month" value={month} onChange={(e) => setMonth(e.target.value)} style={{ maxWidth: 160 }} />
      </div>
      <p className="sub">{t('tax.sub')}</p>

      <div className="meta" style={{ marginBottom: 8 }}>
        Active regime: <strong>{regimeLabel(state.user?.taxRegime ?? 'LEGACY_2PCT')}</strong>
      </div>

      {err && <div className="error">{err}</div>}

      {loading ? (
        <div className="meta">Loading...</div>
      ) : summary ? (
        <div style={{ marginTop: 12 }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 12, marginBottom: 16 }}>
            <div className="card">
              <div className="meta">{t('tax.gross')}</div>
              <div style={{ fontSize: 18, fontWeight: 600 }}>
                ${summary.totalGrossMxn.toLocaleString(undefined, { minimumFractionDigits: 2 })} MXN
              </div>
            </div>
            <div className="card">
              <div className="meta">{t('tax.rate')}</div>
              <div style={{ fontSize: 18, fontWeight: 600 }}>
                {summary.bracketRate !== null ? `${(summary.bracketRate * 100).toFixed(2)}%` : '—'}
              </div>
            </div>
            <div className="card">
              <div className="meta">{t('tax.isr')}</div>
              <div style={{ fontSize: 18, fontWeight: 600 }}>
                ${summary.isrDue.toLocaleString(undefined, { minimumFractionDigits: 2 })} MXN
              </div>
            </div>
            <div className="card">
              <div className="meta">CFDIs</div>
              <div style={{ fontSize: 18, fontWeight: 600 }}>{summary.cfdiCount}</div>
            </div>
          </div>

          <div style={{ marginBottom: 8 }}>
            <span className="meta">Status: </span>
            <span style={{ fontWeight: 600 }}>{t(`tax.status.${summary.status}`)}</span>
            {summary.filedAt && <span className="meta"> — filed {new Date(summary.filedAt).toLocaleDateString()}</span>}
          </div>

          {summary.breakdown.length > 0 && (
            <>
              <h4>{t('tax.breakdown')}</h4>
              <table style={{ width: '100%' }}>
                <thead>
                  <tr>
                    <th>Source</th>
                    <th>Gross MXN</th>
                    <th>Tipo de cambio</th>
                  </tr>
                </thead>
                <tbody>
                  {summary.breakdown.map((item, i) => (
                    <tr key={i}>
                      <td>{sourceName(item.invoiceId)}</td>
                      <td>${item.grossMxn.toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                      <td>{item.tipoCambio?.toFixed(4) ?? '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}
        </div>
      ) : (
        <div style={{ marginTop: 12 }}>
          <p className="meta">{t('tax.empty')}</p>
          <button className="btn primary" onClick={handleCompute} disabled={computing}>
            {computing ? 'Computing...' : t('tax.compute')}
          </button>
        </div>
      )}
    </div>
  );
}
