import { type FormEvent, useState } from 'react';

import { ApiError } from './api';
import { changePassword, type CurrentUser } from './auth';

type Props = {
  user: CurrentUser;
  forced?: boolean;
  onChanged: (user: CurrentUser) => void;
  onSignOut: () => void;
};

export function ChangePassword({
  user,
  forced = false,
  onChanged,
  onSignOut,
}: Props) {
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [repeatPassword, setRepeatPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [done, setDone] = useState(false);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (newPassword !== repeatPassword) {
      setError('The new passwords do not match');
      return;
    }
    setBusy(true);
    setError('');
    try {
      await changePassword(currentPassword, newPassword);
      setDone(true);
      onChanged({ ...user, must_change_password: false });
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.message
          : 'Unable to change the password',
      );
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="auth-card" aria-label="Change password">
      <p className="eyebrow">Blue Velvet · Phase 0.5</p>
      <h1>{forced ? 'Choose a new password' : 'Change password'}</h1>
      <p className="auth-hint">
        {forced
          ? 'Your account was created with a temporary password. Choose your own before continuing.'
          : `Signed in as ${user.username}. Other devices will be signed out.`}
      </p>
      <form className="auth-form" onSubmit={(event) => void submit(event)}>
        <label>
          Current password
          <input
            type="password"
            autoComplete="current-password"
            required
            value={currentPassword}
            onChange={(event) => setCurrentPassword(event.target.value)}
          />
        </label>
        <label>
          New password
          <input
            type="password"
            autoComplete="new-password"
            minLength={12}
            required
            value={newPassword}
            onChange={(event) => setNewPassword(event.target.value)}
          />
        </label>
        <label>
          Repeat new password
          <input
            type="password"
            autoComplete="new-password"
            minLength={12}
            required
            value={repeatPassword}
            onChange={(event) => setRepeatPassword(event.target.value)}
          />
        </label>
        <p className="auth-hint">At least 12 characters.</p>
        <button type="submit" disabled={busy || done}>
          {busy ? 'Saving…' : done ? 'Password changed' : 'Change password'}
        </button>
        {forced && (
          <button type="button" className="secondary" onClick={onSignOut}>
            Sign out
          </button>
        )}
      </form>
      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}
    </section>
  );
}
