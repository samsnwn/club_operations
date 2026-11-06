# Initial Architecture Skeleton

This repository uses a modular-monolith direction with separate frontend and backend workspaces.

## Planned top-level structure

- `frontend/` — React + TypeScript + Vite PWA
- `backend/` — FastAPI backend (`/api/v1`)
- `infra/` — deployment and environment scaffolding (Docker Compose, HTTPS setup)
- `docs/` — product, architecture, milestones, and implementation notes

## Data and integration direction

- Backend is source of truth for operational data.
- Offline actions (especially stock counts) are queued client-side and synchronised to backend.
- AI assistant is read-only and references source records/documents.

## Authentication and trust boundaries

- **Self-managed accounts.** The backend owns a `users` table (Argon2id
  password hashes) and an `auth_sessions` table. There is no external identity
  provider, no JWT, and no public registration; accounts are created by an
  administrator, and the first owner is bootstrapped from the CLI
  (`python -m app.cli create-user`).
- **Sessions.** Login returns an opaque random token in an HttpOnly,
  `SameSite=Lax` cookie. Only the SHA-256 of the token is stored, so a database
  read never exposes a usable session. Expiry, logout, deactivation and role
  changes delete session rows, revoking access immediately.
- **CSRF posture.** `SameSite=Lax` blocks cross-site state-changing requests;
  the backend additionally rejects state-changing requests whose `Origin`
  header is not same-origin or in `ALLOWED_ORIGINS`. No CSRF tokens are issued.
  Production must serve over HTTPS with `SESSION_COOKIE_SECURE=true`.
- **Roles.** `owner` manages every account; `admin` manages `staff` accounts
  only; `staff` can sign in and change their own password. Invoice review,
  including every `/api/v1/invoices/*` route, is restricted to `owner` and
  `admin`; staff accounts never receive invoice data. No one can change their
  own role or deactivate themselves, and the last active owner cannot be
  removed or demoted.
- **Forced password change.** Administrator-created and reset accounts carry
  `must_change_password`; every normal route rejects them with `403` until the
  password is changed through the authenticated `/auth/password` endpoint.
- **Trust boundary with the invoice service.** The browser never talks to the
  invoice service directly. The backend facade authenticates the cookie and
  forwards the username as `X-Reviewer` alongside the internal service token.
  The invoice service trusts `X-Reviewer` **only** when the internal token is
  also valid, and records it as `reviewed_by`; a token-only call remains
  attributed to `backend`. The invoice service port (`:8081`) must stay
  internal because that token bypasses facade authentication.
