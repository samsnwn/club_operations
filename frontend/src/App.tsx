import { useCallback, useEffect, useState } from 'react';

import './App.css';
import { ApiError } from './api';
import { logout, me, type CurrentUser } from './auth';
import { ChangePassword } from './ChangePassword';
import { InvoiceWorkspace } from './InvoiceWorkspace';
import { Login } from './Login';
import { StaffPanel } from './StaffPanel';

type View = 'invoices' | 'staff' | 'password';
type EffectiveView = View | 'home';

function App() {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [checking, setChecking] = useState(true);
  const [view, setView] = useState<View>('invoices');
  const [notice, setNotice] = useState('');

  useEffect(() => {
    let active = true;
    me()
      .then((current) => {
        if (active) setUser(current);
      })
      .catch((caught: unknown) => {
        if (active && !(caught instanceof ApiError && caught.status === 401)) {
          setNotice('Unable to check the session. Please reload the page.');
        }
      })
      .finally(() => {
        if (active) setChecking(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const refreshSession = useCallback(async () => {
    try {
      setUser(await me());
    } catch {
      setUser(null);
    }
  }, []);

  const handleAuthProblem = useCallback(() => {
    void refreshSession();
  }, [refreshSession]);

  const signOut = async () => {
    try {
      await logout();
    } catch {
      // Clearing local state is enough; the session will expire on its own.
    }
    setUser(null);
    setView('invoices');
    setNotice('');
  };

  if (checking) {
    return (
      <main className="invoice-app">
        <p className="status">Checking session…</p>
      </main>
    );
  }

  if (!user) {
    return (
      <main className="invoice-app">
        <Login onLogin={setUser} />
        {notice && (
          <p className="form-error" role="alert">
            {notice}
          </p>
        )}
      </main>
    );
  }

  if (user.must_change_password) {
    return (
      <main className="invoice-app">
        <ChangePassword
          user={user}
          forced
          onChanged={setUser}
          onSignOut={() => void signOut()}
        />
      </main>
    );
  }

  const canReviewInvoices = user.role === 'owner' || user.role === 'admin';
  const canManageStaff = user.role === 'owner' || user.role === 'admin';

  // Staff accounts can sign in and change their own password, but must never
  // see the invoice workspace or the staff panel.
  const effectiveView: EffectiveView =
    (view === 'invoices' && !canReviewInvoices) ||
    (view === 'staff' && !canManageStaff)
      ? 'home'
      : view;

  const heading =
    effectiveView === 'staff'
      ? {
          title: 'Internal accounts',
          description: 'Create staff accounts and manage access.',
        }
      : effectiveView === 'password'
        ? {
            title: 'Change password',
            description: 'Update the password for your own account.',
          }
        : effectiveView === 'invoices'
          ? {
              title: 'Invoice review',
              description:
                'Import captured invoices, check the suggestions, and confirm what is ready for export.',
            }
          : {
              title: 'Your account',
              description:
                'Your account is active. Invoice review is limited to owners and administrators; you can change your password or sign out.',
            };

  return (
    <main className="invoice-app">
      <header className="app-header">
        <div>
          <p className="eyebrow">Blue Velvet · Phase 0.5</p>
          <h1>{heading.title}</h1>
          <p>{heading.description}</p>
        </div>
        <div className="header-actions">
          <span className="account">
            {user.username} · {user.role}
          </span>
          {canReviewInvoices && (
            <button
              type="button"
              className="secondary"
              aria-pressed={effectiveView === 'invoices'}
              onClick={() => setView('invoices')}
            >
              Invoices
            </button>
          )}
          {canManageStaff && (
            <button
              type="button"
              className="secondary"
              aria-pressed={effectiveView === 'staff'}
              onClick={() => setView('staff')}
            >
              Staff
            </button>
          )}
          <button
            type="button"
            className="secondary"
            aria-pressed={effectiveView === 'password'}
            onClick={() => setView('password')}
          >
            Change password
          </button>
          <button
            type="button"
            className="secondary"
            onClick={() => void signOut()}
          >
            Sign out
          </button>
        </div>
      </header>

      {effectiveView === 'staff' ? (
        <StaffPanel currentUser={user} onAuthProblem={handleAuthProblem} />
      ) : effectiveView === 'password' ? (
        <ChangePassword
          user={user}
          onChanged={(next) => {
            setUser(next);
            setView('invoices');
          }}
          onSignOut={() => void signOut()}
        />
      ) : effectiveView === 'invoices' ? (
        <InvoiceWorkspace onAuthProblem={handleAuthProblem} />
      ) : (
        <section className="empty-state" aria-label="Your account">
          <h2>No sections are assigned to your account yet.</h2>
          <p>
            Invoice review is limited to owners and administrators. You can
            change your password or sign out above.
          </p>
        </section>
      )}
    </main>
  );
}

export default App;
