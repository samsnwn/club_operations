import { type FormEvent, useCallback, useEffect, useState } from 'react';

import { ApiError } from './api';
import {
  createUser,
  listUsers,
  resetUserPassword,
  updateUser,
  type CurrentUser,
  type Role,
  type StaffUser,
} from './auth';

type Props = {
  currentUser: CurrentUser;
  onAuthProblem: () => void;
};

const ALL_ROLES: Role[] = ['owner', 'admin', 'staff'];

export function StaffPanel({ currentUser, onAuthProblem }: Props) {
  const [users, setUsers] = useState<StaffUser[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<Role>('staff');
  const [resetFor, setResetFor] = useState<number | null>(null);
  const [resetPassword, setResetPassword] = useState('');

  const roleOptions =
    currentUser.role === 'owner' ? ALL_ROLES : ['staff' as Role];

  const fail = useCallback(
    (caught: unknown, fallback: string) => {
      if (caught instanceof ApiError && caught.status === 401) {
        onAuthProblem();
        return;
      }
      if (
        caught instanceof ApiError &&
        caught.status === 403 &&
        caught.message === 'Password change required'
      ) {
        onAuthProblem();
        return;
      }
      setError(caught instanceof Error ? caught.message : fallback);
    },
    [onAuthProblem],
  );

  const load = useCallback(async () => {
    try {
      setUsers(await listUsers());
    } catch (caught) {
      fail(caught, 'Unable to load accounts');
    }
  }, [fail]);

  useEffect(() => {
    void Promise.resolve().then(load);
  }, [load]);

  const canManage = (target: StaffUser) => {
    if (target.username === currentUser.username) return false;
    return (
      currentUser.role === 'owner' ||
      (currentUser.role === 'admin' && target.role === 'staff')
    );
  };

  const create = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setBusy(true);
    setError('');
    setNotice('');
    try {
      const created = await createUser({
        username: username.trim(),
        password,
        role,
      });
      setUsers((current) =>
        [...current, created].sort((a, b) =>
          a.username.localeCompare(b.username),
        ),
      );
      setUsername('');
      setPassword('');
      setNotice(
        `Created ${created.username}. They must choose a new password at first sign-in.`,
      );
    } catch (caught) {
      fail(caught, 'Unable to create the account');
    } finally {
      setBusy(false);
    }
  };

  const patch = async (
    id: number,
    payload: { role?: Role; is_active?: boolean },
  ) => {
    setBusy(true);
    setError('');
    setNotice('');
    try {
      const updated = await updateUser(id, payload);
      setUsers((current) =>
        current.map((user) => (user.id === updated.id ? updated : user)),
      );
      setNotice(`Updated ${updated.username}. Existing sessions were revoked.`);
    } catch (caught) {
      fail(caught, 'Unable to update the account');
    } finally {
      setBusy(false);
    }
  };

  const reset = async (
    event: FormEvent<HTMLFormElement>,
    id: number,
    username: string,
  ) => {
    event.preventDefault();
    setBusy(true);
    setError('');
    setNotice('');
    try {
      await resetUserPassword(id, resetPassword);
      setResetFor(null);
      setResetPassword('');
      setUsers((current) =>
        current.map((user) =>
          user.id === id ? { ...user, must_change_password: true } : user,
        ),
      );
      setNotice(
        `Reset the password for ${username}. They must choose a new one at next sign-in.`,
      );
    } catch (caught) {
      fail(caught, 'Unable to reset the password');
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="staff-panel" aria-label="Staff accounts">
      <div className="staff-intro">
        <h2>Internal accounts</h2>
        <p>
          {currentUser.role === 'owner'
            ? 'Owners manage every account. New accounts get a temporary password and must change it at first sign-in.'
            : 'Admins manage staff accounts. New accounts get a temporary password and must change it at first sign-in.'}
        </p>
      </div>

      <form className="staff-create" onSubmit={(event) => void create(event)}>
        <label>
          Username
          <input
            required
            maxLength={32}
            value={username}
            onChange={(event) => setUsername(event.target.value)}
          />
        </label>
        <label>
          Temporary password
          <input
            type="password"
            autoComplete="new-password"
            minLength={12}
            required
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </label>
        <label>
          Role
          <select
            value={role}
            onChange={(event) => setRole(event.target.value as Role)}
          >
            {roleOptions.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </label>
        <button type="submit" disabled={busy}>
          Create account
        </button>
      </form>

      {error ? (
        <p className="form-error" role="alert">
          {error}
        </p>
      ) : (
        <p className="status" role="status">
          {notice}
        </p>
      )}

      <ul className="staff-list">
        {users.map((user) => (
          <li key={user.id} className="staff-row">
            <div className="staff-identity">
              <strong>{user.username}</strong>
              <span className="staff-role">{user.role}</span>
              <span
                className={`status-badge ${user.is_active ? '' : 'inactive'}`}
              >
                {user.is_active ? 'active' : 'inactive'}
              </span>
              {user.must_change_password && (
                <span className="staff-note">must change password</span>
              )}
              {user.created_by && (
                <span className="staff-note">created by {user.created_by}</span>
              )}
            </div>
            {canManage(user) && (
              <div className="staff-actions">
                {currentUser.role === 'owner' && (
                  <select
                    aria-label={`Role for ${user.username}`}
                    value={user.role}
                    disabled={busy}
                    onChange={(event) =>
                      void patch(user.id, {
                        role: event.target.value as Role,
                      })
                    }
                  >
                    {ALL_ROLES.map((option) => (
                      <option key={option} value={option}>
                        {option}
                      </option>
                    ))}
                  </select>
                )}
                <button
                  type="button"
                  className="secondary"
                  disabled={busy}
                  onClick={() =>
                    void patch(user.id, { is_active: !user.is_active })
                  }
                >
                  {user.is_active ? 'Deactivate' : 'Activate'}
                </button>
                <button
                  type="button"
                  className="secondary"
                  disabled={busy}
                  onClick={() =>
                    setResetFor(resetFor === user.id ? null : user.id)
                  }
                >
                  Reset password
                </button>
              </div>
            )}
            {resetFor === user.id && canManage(user) && (
              <form
                className="reset-form"
                onSubmit={(event) => void reset(event, user.id, user.username)}
              >
                <input
                  type="password"
                  autoComplete="new-password"
                  minLength={12}
                  required
                  placeholder="New temporary password"
                  value={resetPassword}
                  onChange={(event) => setResetPassword(event.target.value)}
                />
                <button type="submit" disabled={busy}>
                  Set password
                </button>
              </form>
            )}
          </li>
        ))}
        {users.length === 0 && (
          <li className="empty-state">No accounts loaded.</li>
        )}
      </ul>
    </section>
  );
}
