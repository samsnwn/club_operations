import { type FormEvent, useState } from 'react';

import { ApiError } from './api';
import { login, type CurrentUser } from './auth';

type Props = {
  onLogin: (user: CurrentUser) => void;
};

export function Login({ onLogin }: Props) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setBusy(true);
    setError('');
    try {
      onLogin(await login(username.trim(), password));
    } catch (caught) {
      setError(
        caught instanceof ApiError ? caught.message : 'Unable to sign in',
      );
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="auth-card" aria-label="Sign in">
      <p className="eyebrow">Blue Velvet · Phase 0.5</p>
      <h1>Sign in</h1>
      <p className="auth-hint">
        Internal accounts are created by an administrator. There is no
        self-registration.
      </p>
      <form className="auth-form" onSubmit={(event) => void submit(event)}>
        <label>
          Username
          <input
            autoComplete="username"
            autoFocus
            required
            value={username}
            onChange={(event) => setUsername(event.target.value)}
          />
        </label>
        <label>
          Password
          <input
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </label>
        <button type="submit" disabled={busy}>
          {busy ? 'Signing in…' : 'Sign in'}
        </button>
      </form>
      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}
    </section>
  );
}
