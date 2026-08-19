'use client';

import { useCallback, useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { useI18n } from '@/lib/i18n';
import { useApp } from '@/components/App';
import type { CFDIInvoice, ForeignClient, IncomeSource } from '@/state/types';

function currentMonth(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
}

function statusColor(s: string): string {
  if (s === 'stamped') return 'var(--green)';
  if (s === 'cancelled') return 'var(--red)';
  return 'var(--muted)';
}

function formatDate(iso: string): string {
  try { return new Date(iso).toLocaleDateString(); } catch { return iso; }
}

export function CfdiScreen() {
  const { t } = useI18n();
  const { state, notify } = useApp();
  const [invoices, setInvoices] = useState<CFDIInvoice[]>([]);
  const [foreignClients, setForeignClients] = useState<ForeignClient[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterMonth, setFilterMonth] = useState(currentMonth());
  const [showCreate, setShowCreate] = useState(false);
  const [previewXml, setPreviewXml] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');

  const foreignSources = state.sources.filter(
    (s) => s.active && s.foreignClientId,
  );

  const loadData = useCallback(async () => {
    try {
      const [inv, fc] = await Promise.all([
        api.listCfdiInvoices(filterMonth || undefined),
        api.listForeignClients(),
      ]);
      setInvoices(inv);
      setForeignClients(fc);
    } catch {
      /* non-fatal */
    } finally {
      setLoading(false);
    }
  }, [filterMonth]);

  useEffect(() => { loadData(); }, [loadData]);

  const handlePreview = useCallback(async (id: string) => {
    setBusy(true);
    setErr('');
    try {
      const { xml } = await api.previewCfdiInvoice(id);
      setPreviewXml(xml);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }, []);

  const handleStamp = useCallback(async (id: string) => {
    setBusy(true);
    setErr('');
    try {
      await api.stampCfdiInvoice(id);
      notify(t('cfdi.status.stamped'));
      loadData();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }, [loadData, notify, t]);

  const handleCancel = useCallback(async (id: string) => {
    if (!window.confirm('Cancel this CFDI?')) return;
    setBusy(true);
    setErr('');
    try {
      await api.cancelCfdiInvoice(id);
      notify(t('cfdi.cancel'));
      loadData();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }, [loadData, notify, t]);

  const handleDelete = useCallback(async (id: string) => {
    if (!window.confirm('Delete this draft?')) return;
    setBusy(true);
    setErr('');
    try {
      await api.cancelCfdiInvoice(id);
      loadData();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }, [loadData]);

  const sourceName = (sourceId: string) =>
    state.sources.find((s) => s.id === sourceId)?.name ?? sourceId;

  const clientName = (fcId: string) =>
    foreignClients.find((fc) => fc.id === fcId)?.legalName ?? fcId;

  return (
    <div>
      <div className="headrow" style={{ marginBottom: 12 }}>
        <h3>{t('cfdi.title')}</h3>
        <input type="month" value={filterMonth} onChange={(e) => setFilterMonth(e.target.value)} style={{ maxWidth: 160 }} />
      </div>
      <p className="sub">{t('cfdi.sub')}</p>
      {err && <div className="error">{err}</div>}

      {foreignSources.length === 0 && !loading && (
        <div className="empty-state">
          <p>{t('cfdi.empty')}</p>
        </div>
      )}

      {foreignSources.length > 0 && (
        <button className="btn primary" onClick={() => setShowCreate(!showCreate)} disabled={busy}>
          {t('cfdi.create')}
        </button>
      )}

      {showCreate && (
        <CreateInvoiceForm
          sources={foreignSources}
          clients={foreignClients}
          month={filterMonth}
          onCancel={() => setShowCreate(false)}
          onCreated={() => { setShowCreate(false); loadData(); }}
        />
      )}

      {loading ? (
        <div className="meta">Loading...</div>
      ) : (
        <table style={{ width: '100%', marginTop: 12 }}>
          <thead>
            <tr>
              <th>Source</th>
              <th>Client</th>
              <th>Month</th>
              <th>Total</th>
              <th>Currency</th>
              <th>Payment</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {invoices.map((inv) => (
              <tr key={inv.id}>
                <td>{sourceName(inv.sourceId)}</td>
                <td>{clientName(inv.foreignClientId)}</td>
                <td>{inv.month}</td>
                <td>{inv.total.toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                <td>{inv.moneda}</td>
                <td>{inv.metodoPago}</td>
                <td>
                  <span style={{ color: statusColor(inv.status), fontWeight: 600 }}>
                    {t(`cfdi.status.${inv.status}`)}
                  </span>
                </td>
                <td>
                  {inv.status === 'draft' && (
                    <>
                      <button className="btn small" onClick={() => handlePreview(inv.id)} disabled={busy}>
                        {t('cfdi.preview')}
                      </button>{' '}
                      <button className="btn small primary" onClick={() => handleStamp(inv.id)} disabled={busy}>
                        {t('cfdi.stamp')}
                      </button>{' '}
                      <button className="btn small danger" onClick={() => handleDelete(inv.id)} disabled={busy}>
                        {t('cfdi.delete')}
                      </button>
                    </>
                  )}
                  {inv.status === 'stamped' && (
                    <button className="btn small danger" onClick={() => handleCancel(inv.id)} disabled={busy}>
                      {t('cfdi.cancel')}
                    </button>
                  )}
                </td>
              </tr>
            ))}
            {invoices.length === 0 && (
              <tr><td colSpan={8} className="meta">No invoices for this month.</td></tr>
            )}
          </tbody>
        </table>
      )}

      {previewXml && (
        <div className="modal-backdrop" onClick={() => setPreviewXml(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h4>CFDI XML Preview</h4>
            <pre style={{ maxHeight: 400, overflow: 'auto', fontSize: 12, background: 'var(--bg-subtle)', padding: 8, borderRadius: 4 }}>
              {previewXml}
            </pre>
            <div style={{ marginTop: 8, display: 'flex', gap: 8 }}>
              <button className="btn" onClick={() => { navigator.clipboard.writeText(previewXml); notify('Copied!'); }}>
                Copy
              </button>
              <button className="btn" onClick={() => setPreviewXml(null)}>
                {t('common.close')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/* ---- Create invoice form (inline) ---- */

function CreateInvoiceForm({
  sources,
  clients,
  month,
  onCancel,
  onCreated,
}: {
  sources: IncomeSource[];
  clients: ForeignClient[];
  month: string;
  onCancel: () => void;
  onCreated: () => void;
}) {
  const { t } = useI18n();
  const [sourceId, setSourceId] = useState(sources[0]?.id ?? '');
  const [amountMxn, setAmountMxn] = useState('');
  const [tipoCambio, setTipoCambio] = useState('');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');

  const selectedSource = sources.find((s) => s.id === sourceId);
  const fcId = selectedSource?.foreignClientId ?? '';
  const fc = clients.find((c) => c.id === fcId);

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sourceId || !fcId || !amountMxn) return;
    setBusy(true);
    setErr('');
    try {
      await api.createCfdiInvoice({
        sourceId,
        foreignClientId: fcId,
        month,
        amountMxn: Number(amountMxn),
        tipoCambio: tipoCambio ? Number(tipoCambio) : undefined,
        currencyOption: fc?.currencyOption ?? 'USD',
      });
      onCreated();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }, [sourceId, fcId, month, amountMxn, tipoCambio, fc, onCreated]);

  return (
    <form onSubmit={handleSubmit} style={{ marginTop: 12, padding: 12, border: '1px solid var(--border)', borderRadius: 6 }}>
      {err && <div className="error">{err}</div>}
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'end' }}>
        <label style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <span className="meta">Source</span>
          <select value={sourceId} onChange={(e) => setSourceId(e.target.value)}>
            {sources.map((s) => (
              <option key={s.id} value={s.id}>{s.name} ({s.currency})</option>
            ))}
          </select>
        </label>
        <label style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <span className="meta">Client</span>
          <input type="text" value={fc?.legalName ?? ''} disabled readOnly style={{ width: 160 }} />
        </label>
        <label style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <span className="meta">Amount (MXN)</span>
          <input type="number" value={amountMxn} onChange={(e) => setAmountMxn(e.target.value)} required min="0" step="0.01" />
        </label>
        {fc?.currencyOption === 'USD' && (
          <label style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <span className="meta">Tipo de cambio</span>
            <input type="number" value={tipoCambio} onChange={(e) => setTipoCambio(e.target.value)} step="0.0001" placeholder="Banxico rate" />
          </label>
        )}
        <button type="submit" className="btn primary" disabled={busy}>{t('cfdi.create')}</button>
        <button type="button" className="btn" onClick={onCancel}>{t('sources.cancel')}</button>
      </div>
    </form>
  );
}
