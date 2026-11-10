import { useCallback, useEffect, useState } from 'react';

import { ApiError, request } from './api';

type Invoice = {
  id: number;
  source: string;
  status: string;
  confidence: number;
  created_at: string;
  suggestions: Record<string, string | number>;
  supplier_guess: string | null;
};

type QueueResponse = { count: number; items: Invoice[] };
type InvoiceDetail = Invoice & { extracted_text: string | null };
type ReviewValues = Record<string, string>;

const reviewFields = [
  ['supplier', 'Supplier'],
  ['invoice_number', 'Invoice number'],
  ['invoice_date', 'Invoice date'],
  ['due_date', 'Due date'],
  ['net', 'Net'],
  ['vat', 'VAT'],
  ['gross', 'Gross'],
  ['category', 'Category'],
  ['payment_method', 'Payment method'],
  ['description', 'Description'],
] as const;

type Props = {
  onAuthProblem: () => void;
};

const amountFields = new Set(['net', 'vat', 'gross']);

/** Maps invoice-service statuses onto the badge palette (docs/design-system.md). */
function statusTone(status: string) {
  if (status === 'needs_attention') return 'badge-warning';
  if (status === 'confirmed' || status === 'exported') return 'badge-success';
  if (status === 'rejected' || status === 'failed') return 'badge-danger';
  return 'badge-info';
}

function confidenceLevel(confidence: number) {
  if (confidence < 0.5) return 'low';
  if (confidence >= 0.85) return 'high';
  return 'medium';
}

export function InvoiceWorkspace({ onAuthProblem }: Props) {
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [selected, setSelected] = useState<InvoiceDetail | null>(null);
  const [values, setValues] = useState<ReviewValues>({});
  const [message, setMessage] = useState('Loading review queue…');
  const [busy, setBusy] = useState(false);
  const [importing, setImporting] = useState(false);

  const fail = useCallback(
    (error: unknown, fallback: string) => {
      if (error instanceof ApiError && error.status === 401) {
        onAuthProblem();
        return;
      }
      if (
        error instanceof ApiError &&
        error.status === 403 &&
        error.message === 'Password change required'
      ) {
        onAuthProblem();
        return;
      }
      setMessage(error instanceof Error ? error.message : fallback);
    },
    [onAuthProblem],
  );

  const loadQueue = useCallback(async () => {
    try {
      const queue = await request<QueueResponse>('/invoices/queue');
      setInvoices(queue.items);
      setMessage(
        `${queue.count} invoice${queue.count === 1 ? '' : 's'} awaiting review`,
      );
    } catch (error) {
      fail(error, 'Unable to load invoices');
    }
  }, [fail]);

  useEffect(() => {
    // Same refresh as every later one, deferred a tick so the mount fetch is
    // an async continuation rather than a synchronous effect body call.
    void Promise.resolve().then(loadQueue);
  }, [loadQueue]);

  const selectInvoice = async (id: number) => {
    setBusy(true);
    try {
      const detail = await request<InvoiceDetail>(`/invoices/${id}`);
      const nextValues: ReviewValues = {};
      for (const [field] of reviewFields) {
        const value = detail.suggestions[field];
        nextValues[field] = value === undefined ? '' : String(value);
      }
      setSelected(detail);
      setValues(nextValues);
      setMessage(`Reviewing invoice #${id}`);
    } catch (error) {
      fail(error, 'Unable to load invoice');
    } finally {
      setBusy(false);
    }
  };

  const updateValue = (field: string, value: string) => {
    setValues((current) => ({ ...current, [field]: value }));
  };

  const reviewInvoice = async (action: 'confirm' | 'reject') => {
    if (!selected) return;
    setBusy(true);
    try {
      if (action === 'confirm') {
        const payload: Record<string, string | number> = {};
        for (const [field] of reviewFields) {
          const value = values[field]?.trim();
          if (!value) continue;
          if (['net', 'vat', 'gross'].includes(field)) {
            const parsed = Number(value);
            if (!Number.isFinite(parsed)) {
              setMessage(`Invalid number for ${field}`);
              return;
            }
            payload[field] = parsed;
          } else {
            payload[field] = value;
          }
        }
        await request(`/invoices/${selected.id}/confirm`, {
          method: 'POST',
          body: JSON.stringify(payload),
        });
      } else {
        await request(`/invoices/${selected.id}/reject`, { method: 'POST' });
      }
      setSelected(null);
      await loadQueue();
    } catch (error) {
      fail(error, 'Unable to save review');
    } finally {
      setBusy(false);
    }
  };

  const importInvoices = async () => {
    setBusy(true);
    setImporting(true);
    try {
      const result = await request<{ new_invoices: number }>(
        '/invoices/import',
        {
          method: 'POST',
        },
      );
      setMessage(
        `${result.new_invoices} new invoice${result.new_invoices === 1 ? '' : 's'} imported`,
      );
      await loadQueue();
    } catch (error) {
      fail(error, 'Import failed');
    } finally {
      setImporting(false);
      setBusy(false);
    }
  };

  const rejectInvoice = async (id: number) => {
    setBusy(true);
    try {
      await request(`/invoices/${id}/reject`, { method: 'POST' });
      await loadQueue();
    } catch (error) {
      fail(error, 'Unable to reject invoice');
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <div className="workspace-toolbar">
        <p className="status" role="status">
          {message}
        </p>
        <button
          type="button"
          className="btn btn-primary"
          onClick={() => void importInvoices()}
          disabled={busy}
          aria-busy={importing}
        >
          {importing ? 'Importing…' : 'Import invoices'}
        </button>
      </div>
      {selected ? (
        <section className="card review-panel" aria-label="Review invoice">
          <div className="panel-header">
            <div>
              <p className="eyebrow">
                Invoice #{selected.id} · {selected.source}
              </p>
              <h2>Check and confirm the extracted values</h2>
            </div>
            <button
              type="button"
              className="btn btn-ghost"
              onClick={() => setSelected(null)}
            >
              ← Back to queue
            </button>
          </div>
          <div className="review-grid">
            {reviewFields.map(([field, label]) => (
              <label
                className={`field ${field === 'description' ? 'wide-field' : ''}`}
                key={field}
              >
                {label}
                {field === 'description' ? (
                  <textarea
                    className="input"
                    value={values[field] ?? ''}
                    onChange={(event) => updateValue(field, event.target.value)}
                  />
                ) : (
                  <input
                    className={`input ${amountFields.has(field) ? 'numeric' : ''}`}
                    inputMode={amountFields.has(field) ? 'decimal' : undefined}
                    value={values[field] ?? ''}
                    onChange={(event) => updateValue(field, event.target.value)}
                  />
                )}
              </label>
            ))}
          </div>
          <details className="source-text">
            <summary>Show extracted source text</summary>
            <pre>{selected.extracted_text || 'No text was extracted.'}</pre>
          </details>
          <div className="original-preview">
            <h3>Original invoice</h3>
            <iframe
              title={`Original invoice ${selected.id}`}
              src={`/api/v1/invoices/${selected.id}/original`}
            />
          </div>
          <div className="review-actions">
            <button
              type="button"
              className="btn btn-danger"
              disabled={busy}
              onClick={() => void reviewInvoice('reject')}
            >
              Reject
            </button>
            <button
              type="button"
              className="btn btn-primary"
              disabled={busy}
              aria-busy={busy}
              onClick={() => void reviewInvoice('confirm')}
            >
              {busy ? 'Saving…' : 'Confirm invoice'}
            </button>
          </div>
        </section>
      ) : (
        <section className="invoice-list" aria-label="Invoices awaiting review">
          {invoices.length === 0 ? (
            <div className="empty-state">
              <h2>All caught up</h2>
              <p>No invoices are waiting for review.</p>
            </div>
          ) : (
            invoices.map((invoice) => (
              <article
                className="card card-interactive invoice-card"
                key={invoice.id}
              >
                <button
                  type="button"
                  className="invoice-select"
                  onClick={() => void selectInvoice(invoice.id)}
                >
                  <span className="invoice-summary">
                    <span className="eyebrow">
                      Invoice #{invoice.id} · {invoice.source}
                    </span>
                    <strong>
                      {invoice.supplier_guess ?? 'Supplier not recognised'}
                    </strong>
                    <span className="invoice-confidence">
                      <span
                        className="meter"
                        data-level={confidenceLevel(invoice.confidence)}
                        aria-hidden="true"
                      >
                        <span
                          style={{
                            width: `${Math.round(invoice.confidence * 100)}%`,
                          }}
                        />
                      </span>
                      <span className="numeric">
                        {Math.round(invoice.confidence * 100)}% extraction
                        confidence
                      </span>
                    </span>
                  </span>
                  <span className={`badge ${statusTone(invoice.status)}`}>
                    {invoice.status.replace('_', ' ')}
                  </span>
                </button>
                <button
                  type="button"
                  className="btn btn-danger btn-sm"
                  disabled={busy}
                  onClick={() => void rejectInvoice(invoice.id)}
                >
                  Reject
                </button>
              </article>
            ))
          )}
        </section>
      )}
    </>
  );
}
