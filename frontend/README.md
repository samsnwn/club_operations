# Blue Velvet Frontend

React + TypeScript + Vite PWA (pnpm) for the Club Operations Platform. It is
currently the **Phase 0.5 frontend**: internal sign-in, staff-account
management and the invoice review workspace. No platform modules (dashboard,
events, promoter form, mobile stock counts) exist yet.

## Run

The backend must be running for authentication and invoice data. Same-origin
`/api` requests are proxied by Vite (`vite.config.ts`):

```bash
pnpm install
pnpm run dev        # http://localhost:5173, proxies /api to BACKEND_URL
```

`BACKEND_URL` defaults to `http://localhost:8080`; Docker Compose sets it to
`http://backend:8080`. Keep the frontend and backend on the same origin (the
proxy) — there is no CORS middleware.

## Build and lint

```bash
pnpm run build      # type-check + production build (also emits the PWA service worker)
pnpm run lint
```

Repository-wide formatting is run from the repository root with
`pnpm format` / `pnpm format:check` (Prettier for web files).

## Structure

- `src/api.ts` — typed same-origin fetch wrapper and `ApiError`.
- `src/auth.ts` — typed auth/user calls.
- `src/App.tsx` — session shell: checking → login → forced password change →
  role-aware views (invoices / staff / password / staff home).
- `src/Login.tsx`, `src/ChangePassword.tsx` — sign-in and password flow.
- `src/StaffPanel.tsx` — account management (owner/admin).
- `src/InvoiceWorkspace.tsx` — import, review queue, corrections,
  confirm/reject, extracted text and original preview.

## Access behaviour

- `owner` and `admin` see the invoice workspace and staff panel.
- `staff` can sign in and change their own password only; they land on a
  no-modules home and never receive invoice data.
- Accounts flagged `must_change_password` are forced through
  `ChangePassword` before any normal view.
- Expired/invalid sessions return to the login screen.

Navigation is local React state, not URL routing, and there is no IndexedDB
offline queue yet — the PWA baseline only precaches the app shell.
