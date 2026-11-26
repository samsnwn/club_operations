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
- `src/App.tsx` — session check (checking → offline screen or router) and the
  session state (user, sign-out) shared with the routes through
  `src/session.ts`.
- `src/router.tsx` — the route tree and every access guard, defined in code
  with TanStack Router (no file-based routing, no generated tree).
- `src/redirect.ts` — `safeRedirect`, the dependency-free validator for the
  `?redirect=` value after sign-in.
- `src/AppShell.tsx` — signed-in layout: forced password change, or the header,
  nav tabs and page header around the current screen.
- `src/screens.tsx` — the route screens (login, invoices, staff, account,
  password, not found).
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

## Routes

| Path                | Who                 | Screen                                                         |
| ------------------- | ------------------- | -------------------------------------------------------------- |
| `/login`            | Signed out          | Sign in                                                        |
| `/`                 | Signed in           | Redirects owner/admin to `/invoices`, staff to `/account`      |
| `/invoices`         | Owner, admin        | Invoice review                                                 |
| `/staff`            | Owner, admin        | Internal accounts                                              |
| `/account`          | Signed in           | Your account (empty state)                                     |
| `/account/password` | Signed in           | Change password; a successful change returns to `/`            |
| any other path      | Anyone              | Not-found page with a link to `/`                              |

Redirect rules (all in `src/router.tsx`, `beforeLoad`, with `replace` so the
back gesture never lands on a redirecting entry):

- Signed out on any signed-in route → `/login?redirect=<path and query>`.
- Staff on `/invoices` or `/staff` → `/account`; those screens never render.
- Signed in on `/login` → the `redirect` value when `safeRedirect` accepts it,
  otherwise `/`. Only paths starting with a single `/` (no `\`, control
  characters or whitespace, same origin, and not resolving to a `//…` path
  such as `/..//host`) are accepted, so `?redirect=` can't send anyone to
  another site.
- Sign out → `/login` with no `redirect`.

Check the validator with Node (no test runner; run from `frontend/`):

```bash
node --input-type=module -e "import { safeRedirect as s } from './src/redirect.ts'; const cases = [['/invoices','/invoices'],['/account/password','/account/password'],['/staff?x=1','/staff?x=1'],[undefined,'/'],['','/'],['https://example.com','/'],['//example.com','/'],['/\\\\example.com','/'],['\\\\\\\\example.com','/'],['\\\\/example.com','/'],['javascript:alert(1)','/'],['invoices','/'],[' /invoices','/'],['/%0a','/%0a'],[42,'/']]; for (const [i,o] of cases) { if (s(i)!==o) { console.error('FAIL', JSON.stringify(i), s(i)); process.exit(1); } } console.log('ok');"
```

It prints `ok`.

## Styling

Follow [`../docs/design-system.md`](../docs/design-system.md). Compose screens
from the primitives plus Tailwind layout utilities, use semantic colours
(`bg-surface`, `text-fg-muted`, `border-line`) rather than hex values, keep one
`btn-primary` per view, and check both Night and Day themes at phone and
desktop widths. Fonts are bundled via Fontsource; do not add a font CDN.

## Access behaviour

- Access is enforced by URL guards in `src/router.tsx` (see Routes), which
  re-run whenever the signed-in user changes.
- `owner` and `admin` see the invoice workspace and staff panel.
- `staff` can sign in and change their own password only; they land on
  `/account` and are redirected there from `/invoices` and `/staff`, so they
  never receive invoice data.
- Accounts flagged `must_change_password` are forced through
  `ChangePassword` at any URL; after the change the URL renders normally.
- Expired/invalid sessions return to `/login?redirect=<current page>`.

## Offline behaviour

- While the server can't be reached (a failed request, a 502/503/504, or the
  browser's `offline` event), the signed-in shell shows a persistent
  "Offline – changes can't be saved…" bar above the header. It goes away after
  the next successful request or the browser's `online` event.
- If the startup session check can't reach the server, a "You're offline"
  screen with Retry replaces the sign-in page.

Deep links open offline too: the service worker answers navigations with the
app shell (navigations to `/api/` excluded) and the router renders the URL.
There is no offline
data: nothing is cached from the API and there is no IndexedDB queue. The
service worker precaches the app shell and icons only, and the offline
indicator only reports connectivity.
