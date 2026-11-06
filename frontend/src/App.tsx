import { useCallback, useEffect, useState } from 'react';
import './App.css';

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

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`/api/v1${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json() as Promise<T>;
}

function App() {
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [selected, setSelected] = useState<InvoiceDetail | null>(null);
  const [values, setValues] = useState<ReviewValues>({});
  const [message, setMessage] = useState('Loading review queue…');
  const [busy, setBusy] = useState(false);
  const [importing, setImporting] = useState(false);

  const loadQueue = useCallback(async () => {
    try {
      const queue = await request<QueueResponse>('/invoices/queue');
      setInvoices(queue.items);
      setMessage(
        `${queue.count} invoice${queue.count === 1 ? '' : 's'} awaiting review`,
      );
    } catch (error) {
      setMessage(
        error instanceof Error ? error.message : 'Unable to load invoices',
      );
    }
  }, []);

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
      setMessage(
        error instanceof Error ? error.message : 'Unable to load invoice',
      );
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
      setMessage(
        error instanceof Error ? error.message : 'Unable to save review',
      );
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
      setMessage(error instanceof Error ? error.message : 'Import failed');
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
      setMessage(
        error instanceof Error ? error.message : 'Unable to reject invoice',
      );
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="invoice-app">
      <header className="app-header">
        <div>
          <p className="eyebrow">Blue Velvet · Phase 0.5</p>
          <h1>Invoice review</h1>
          <p>
            Import captured invoices, check the suggestions, and confirm what is
            ready for export.
          </p>
        </div>
        <button
          type="button"
          onClick={() => void importInvoices()}
          disabled={busy}
        >
          {importing ? 'Importing…' : 'Import invoices'}
        </button>
      </header>
      <p className="status" role="status">
        {message}
      </p>
      {selected ? (
        <section className="review-panel" aria-label="Review invoice">
          <div className="panel-header">
            <div>
              <p className="eyebrow">
                Invoice #{selected.id} · {selected.source}
              </p>
              <h2>Check and confirm the extracted values</h2>
            </div>
            <button
              type="button"
              className="secondary"
              onClick={() => setSelected(null)}
            >
              Back to queue
            </button>
          </div>
          <div className="review-grid">
            {reviewFields.map(([field, label]) => (
              <label
                className={field === 'description' ? 'wide-field' : ''}
                key={field}
              >
                {label}
                {field === 'description' ? (
                  <textarea
                    value={values[field] ?? ''}
                    onChange={(event) => updateValue(field, event.target.value)}
                  />
                ) : (
                  <input
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
              className="secondary"
              disabled={busy}
              onClick={() => void reviewInvoice('reject')}
            >
              Reject
            </button>
            <button
              type="button"
              disabled={busy}
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
              No invoices are waiting for review.
            </div>
          ) : (
            invoices.map((invoice) => (
              <article className="invoice-card" key={invoice.id}>
                <button
                  type="button"
                  className="invoice-select"
                  onClick={() => void selectInvoice(invoice.id)}
                >
                  <span>
                    <span className="eyebrow">
                      Invoice #{invoice.id} · {invoice.source}
                    </span>
                    <strong>
                      {invoice.supplier_guess ?? 'Supplier not recognised'}
                    </strong>
                    <span>
                      {Math.round(invoice.confidence * 100)}% extraction
                      confidence
                    </span>
                  </span>
                  <span className={`status-badge ${invoice.status}`}>
                    {invoice.status.replace('_', ' ')}
                  </span>
                </button>
                <button
                  type="button"
                  className="secondary"
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
    </main>
  );
}

export default App;
