import { RouterProvider } from '@tanstack/react-router';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

import './App.css';
import { ApiError, isServerUnreachable } from './api';
import { logout, me, type CurrentUser } from './auth';
import { router } from './router';
import { SessionContext } from './session';
import { OfflineScreen } from './ui/Offline';

function App() {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [checking, setChecking] = useState(true);
  const [notice, setNotice] = useState('');
  const [unreachable, setUnreachable] = useState(false);

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

  // Sign-out goes to a plain /login; any other loss of the user lets the
  // guards send the browser to /login?redirect=<current page>.
  const signingOut = useRef(false);

  const signOut = useCallback(async () => {
    try {
      await logout();
    } catch {
      // Clearing local state is enough; the session will expire on its own.
    }
    signingOut.current = true;
    setUser(null);
    setNotice('');
  }, []);

  // The router only runs once the session check is done, so its guards never
  // see a user who is still being checked.
  const routed = !checking && !(!user && unreachable);

  // Re-run the route guards whenever the user changes (sign-in, sign-out,
  // expired session, password change).
  useEffect(() => {
    if (!routed) return;
    if (signingOut.current) {
      signingOut.current = false;
      void router.navigate({ to: '/login' });
    } else {
      void router.invalidate();
    }
  }, [user, routed]);

  const session = useMemo(
    () => ({
      user,
      notice,
      setUser,
      onAuthProblem: handleAuthProblem,
      signOut: () => void signOut(),
    }),
    [user, notice, handleAuthProblem, signOut],
  );

  if (checking) {
    return (
      <main className="auth-layout">
        <p className="status" role="status">
          Checking session…
        </p>
      </main>
    );
  }

  if (!routed) {
    return (
      <main className="auth-layout">
        <OfflineScreen onRetry={retrySessionCheck} />
      </main>
    );
  }

  return (
    <SessionContext value={session}>
      <RouterProvider router={router} context={{ user }} />
    </SessionContext>
  );
}

export default App;
