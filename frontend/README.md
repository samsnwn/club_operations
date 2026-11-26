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

## PWA icons

```bash
pnpm run generate-pwa-assets
```

Regenerates the install icons from `public/favicon.svg` with
`@vite-pwa/assets-generator` (`pwa-assets.config.ts`, `minimal-2023` preset on
the Night background): `public/pwa-192x192.png`, `public/pwa-512x512.png`,
`public/maskable-icon-512x512.png` and `public/apple-touch-icon-180x180.png`.
The PNGs are committed; rerun the command after changing the SVG. The
rasteriser has no Lobster font, so the "Bv" glyphs fall back to a cursive
system font.

## Structure

- `src/api.ts` — typed same-origin fetch wrapper and `ApiError`.
- `src/connectivity.ts` — online/offline state fed by `request()` and the
  browser's `online`/`offline` events, read with `useOnline()`.
- `src/auth.ts` — typed auth/user calls.
- `src/App.tsx` — session shell: checking → login → forced password change →
  role-aware views (invoices / staff / password / staff home).
- `src/Login.tsx`, `src/ChangePassword.tsx` — sign-in and password flow.
- `src/StaffPanel.tsx` — account management (owner/admin).
- `src/InvoiceWorkspace.tsx` — import, review queue, corrections,
  confirm/reject, extracted text and original preview.
- `src/styles/tokens.css` — design tokens (palette, semantic roles, Night/Day
  themes) exposed as Tailwind v4 utilities.
- `src/styles/components.css` — base styles and UI primitives (`.btn`,
  `.card`, `.field`/`.input`, `.badge`, `.alert`, `.nav-tab`, `.meter`).
- `src/ui/` — brand components (`Sign`, `Wordmark`, `Crest`), `ThemeToggle`
  and the offline bar and screen (`Offline.tsx`).
- `src/App.css` — screen layouts only.

## Styling

Follow [`../docs/design-system.md`](../docs/design-system.md). Compose screens
from the primitives plus Tailwind layout utilities, use semantic colours
(`bg-surface`, `text-fg-muted`, `border-line`) rather than hex values, keep one
`btn-primary` per view, and check both Night and Day themes at phone and
desktop widths. Fonts are bundled via Fontsource; do not add a font CDN.

## Access behaviour

- `owner` and `admin` see the invoice workspace and staff panel.
- `staff` can sign in and change their own password only; they land on a
  no-modules home and never receive invoice data.
- Accounts flagged `must_change_password` are forced through
  `ChangePassword` before any normal view.
- Expired/invalid sessions return to the login screen.

## Offline behaviour

- While the server can't be reached (a failed request, a 502/503/504, or the
  browser's `offline` event), the signed-in shell shows a persistent
  "Offline – changes can't be saved…" bar above the header. It goes away after
  the next successful request or the browser's `online` event.
- If the startup session check can't reach the server, a "You're offline"
  screen with Retry replaces the sign-in page.

Navigation is still local React state, not URL routing. There is no offline
data: nothing is cached from the API and there is no IndexedDB queue. The
service worker precaches the app shell and icons only (navigations to `/api/`
are never answered with the shell), and the offline indicator only reports
connectivity.
