import { Link, Outlet, useMatches } from '@tanstack/react-router';

import { ChangePassword } from './ChangePassword';
import { useOnline } from './connectivity';
import { useSession } from './session';
import { Crest, Sign, Wordmark } from './ui/Brand';
import { OfflineBar } from './ui/Offline';
import { ThemeToggle } from './ui/ThemeToggle';

const activeTab = { 'aria-current': 'page' } as const;

/** Signed-in layout: forced password change, or the shell around a screen. */
export function AppShell() {
  const { user, setUser, signOut } = useSession();
  const online = useOnline();
  const matches = useMatches();

  // The guard keeps signed-out visitors away; this covers the render between
  // sign-out and the redirect.
  if (!user) return null;

  if (user.must_change_password) {
    return (
      <main className="auth-layout">
        <ChangePassword
          user={user}
          forced
          onChanged={setUser}
          onSignOut={signOut}
        />
      </main>
    );
  }

  const canManage = user.role === 'owner' || user.role === 'admin';
  const heading = matches.at(-1)?.staticData;

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
          {canManage && (
            <Link to="/invoices" className="nav-tab" activeProps={activeTab}>
              Invoices
            </Link>
          )}
          {canManage && (
            <Link to="/staff" className="nav-tab" activeProps={activeTab}>
              Staff
            </Link>
          )}
          <Link
            to="/account/password"
            className="nav-tab"
            activeProps={activeTab}
          >
            Password
          </Link>
        </nav>
        <div className="app-account">
          <span className="app-account-name">
            {user.username}
            <span>{user.role}</span>
          </span>
          <ThemeToggle />
          <button type="button" className="nav-tab" onClick={signOut}>
            Sign out
          </button>
        </div>
      </Sign>

      <main className="app-main">
        <header className="page-header">
          <p className="eyebrow">Phase 0.5</p>
          <h1>{heading?.title}</h1>
          <p className="text-muted">{heading?.description}</p>
        </header>

        <Outlet />
      </main>
    </div>
  );
}
