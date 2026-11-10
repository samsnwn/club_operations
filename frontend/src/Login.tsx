import { type FormEvent, useState } from 'react';

import { ApiError, isServerUnreachable } from './api';
import { login, type CurrentUser } from './auth';
import { Crest, Sign, Wordmark } from './ui/Brand';

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
      if (isServerUnreachable(caught)) {
        setError(
          "Can't reach the server. Check your connection and try again.",
        );
      } else {
        setError(
          caught instanceof ApiError ? caught.message : 'Unable to sign in',
        );
      }
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="auth-stack" aria-label="Sign in">
      <Sign className="auth-sign">
        <Crest />
        <Wordmark className="auth-wordmark" />
        <span className="auth-tagline">Club operations</span>
      </Sign>
      <div className="card auth-card">
        <h1>Sign in</h1>
        <p className="auth-hint">
          Use the account your manager created for you.
        </p>
        <form className="auth-form" onSubmit={(event) => void submit(event)}>
          <label className="field">
            Username
            <input
              className="input"
              autoComplete="username"
              autoFocus
              required
              value={username}
              onChange={(event) => setUsername(event.target.value)}
            />
          </label>
          <label className="field">
            Password
            <input
              className="input"
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </label>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={busy}
            aria-busy={busy}
          >
            {busy ? 'Signing in…' : 'Sign in'}
          </button>
        </form>
        {error && (
          <p className="alert alert-danger form-error" role="alert">
            {error}
          </p>
        )}
      </div>
    </section>
  );
}
