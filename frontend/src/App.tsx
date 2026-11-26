import { useCallback, useEffect, useState } from 'react';

import './App.css';
import { ApiError, isServerUnreachable } from './api';
import { logout, me, type CurrentUser } from './auth';
import { ChangePassword } from './ChangePassword';
import { useOnline } from './connectivity';
import { InvoiceWorkspace } from './InvoiceWorkspace';
import { Login } from './Login';
import { StaffPanel } from './StaffPanel';
import { Crest, Sign, Wordmark } from './ui/Brand';
import { OfflineBar, OfflineScreen } from './ui/Offline';
import { ThemeToggle } from './ui/ThemeToggle';

type View = 'invoices' | 'staff' | 'password';
type EffectiveView = View | 'home';

function App() {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [checking, setChecking] = useState(true);
  const [view, setView] = useState<View>('invoices');
  const [notice, setNotice] = useState('');
  const [unreachable, setUnreachable] = useState(false);
  const online = useOnline();

  const runSessionCheck = useCallback((isActive: () => boolean) => {
    me()
      .then((current) => {
        if (isActive()) setUser(current);
      })
      .catch((caught: unknown) => {
        if (!isActive()) return;
        if (isServerUnreachable(caught)) {
          setUnreachable(true);
        } else if (!(caught instanceof ApiError && caught.status === 401)) {
          setNotice('Unable to check the session. Please reload the page.');
        }
      })
      .finally(() => {
        if (isActive()) setChecking(false);
      });
  }, []);

  useEffect(() => {
    let active = true;
    runSessionCheck(() => active);
    return () => {
      active = false;
    };
  }, [runSessionCheck]);

  const retrySessionCheck = () => {
    setUnreachable(false);
    setChecking(true);
    runSessionCheck(() => true);
  };

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
      <main className="auth-layout">
        <p className="status" role="status">
          Checking session…
        </p>
      </main>
    );
  }

  if (!user && unreachable) {
    return (
      <main className="auth-layout">
        <OfflineScreen onRetry={retrySessionCheck} />
      </main>
    );
  }

  if (!user) {
    return (
      <main className="auth-layout">
        <Login onLogin={setUser} />
        {notice && (
          <p className="alert alert-danger" role="alert">
            {notice}
          </p>
        )}
      </main>
    );
  }

  if (user.must_change_password) {
    return (
      <main className="auth-layout">
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
    <div className="app-shell">
      {!online && <OfflineBar />}
      <Sign className="app-sign">
        <div className="app-sign-brand">
          <Crest />
          <div>
            <Wordmark className="app-sign-wordmark" />
            <span className="app-sign-tagline">Club operations</span>
          </div>
        </div>
        <nav className="nav-tabs app-nav" aria-label="Sections">
          {canReviewInvoices && (
            <button
              type="button"
              className="nav-tab"
              aria-current={effectiveView === 'invoices' ? 'page' : undefined}
              onClick={() => setView('invoices')}
            >
              Invoices
            </button>
          )}
          {canManageStaff && (
            <button
              type="button"
              className="nav-tab"
              aria-current={effectiveView === 'staff' ? 'page' : undefined}
              onClick={() => setView('staff')}
            >
              Staff
            </button>
          )}
          <button
            type="button"
            className="nav-tab"
            aria-current={effectiveView === 'password' ? 'page' : undefined}
            onClick={() => setView('password')}
          >
            Password
          </button>
        </nav>
        <div className="app-account">
          <span className="app-account-name">
            {user.username}
            <span>{user.role}</span>
          </span>
          <ThemeToggle />
          <button
            type="button"
            className="nav-tab"
            onClick={() => void signOut()}
          >
            Sign out
          </button>
        </div>
      </Sign>

      <main className="app-main">
        <header className="page-header">
          <p className="eyebrow">Phase 0.5</p>
          <h1>{heading.title}</h1>
          <p className="text-muted">{heading.description}</p>
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
    </div>
  );
}

export default App;
