// Route screens. Each wraps an existing component with the session it needs;
// router.tsx decides which one shows.

import { Link, useNavigate } from '@tanstack/react-router';

import { ChangePassword } from './ChangePassword';
import { InvoiceWorkspace } from './InvoiceWorkspace';
import { Login } from './Login';
import { useSession } from './session';
import { StaffPanel } from './StaffPanel';
import { Crest, Sign, Wordmark } from './ui/Brand';

export function LoginScreen() {
  const { notice, setUser } = useSession();
  // Once the user is set, the /login guard sends them on to the validated
  // ?redirect= target.
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

export function InvoicesScreen() {
  const { onAuthProblem } = useSession();
  return <InvoiceWorkspace onAuthProblem={onAuthProblem} />;
}

export function StaffScreen() {
  const { user, onAuthProblem } = useSession();
  if (!user) return null;
  return <StaffPanel currentUser={user} onAuthProblem={onAuthProblem} />;
}

export function AccountScreen() {
  return (
    <section className="empty-state" aria-label="Your account">
      <h2>No sections are assigned to your account yet.</h2>
      <p>
        Invoice review is limited to owners and administrators. You can change
        your password or sign out above.
      </p>
    </section>
  );
}

export function PasswordScreen() {
  const { user, setUser, signOut } = useSession();
  const navigate = useNavigate();
  if (!user) return null;
  return (
    <ChangePassword
      user={user}
      onChanged={(next) => {
        setUser(next);
        void navigate({ to: '/' });
      }}
      onSignOut={signOut}
    />
  );
}

export function NotFoundScreen() {
  return (
    <main className="auth-layout">
      <section className="auth-stack" aria-label="Page not found">
        <Sign className="auth-sign">
          <Crest />
          <Wordmark className="auth-wordmark" />
          <span className="auth-tagline">Club operations</span>
        </Sign>
        <div className="card auth-card">
          <h1>Page not found</h1>
          <p className="auth-hint">This page doesn't exist.</p>
          <p>
            <Link to="/">Go to the start page</Link>
          </p>
        </div>
      </section>
    </main>
  );
}
