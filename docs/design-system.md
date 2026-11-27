# Blue Velvet Design System

The visual language for every Blue Velvet surface — management dashboard,
staff mobile interface and promoter form. It is derived from the club's street
sign, so the app feels like the club rather than generic admin software.

- **Tokens (source of truth):** [`frontend/src/styles/tokens.css`](../frontend/src/styles/tokens.css)
- **Primitives:** [`frontend/src/styles/components.css`](../frontend/src/styles/components.css)
- **Brand components:** [`frontend/src/ui/`](../frontend/src/ui/) (`Sign`, `Wordmark`, `Crest`, `ThemeToggle`)

If this document and the token file disagree, the token file wins; fix the doc.

## 1. Reference: the sign

The sign at the entrance is the brand. What we take from it:

| Sign element | Becomes | Token family |
| --- | --- | --- |
| Deep blue panel | Brand colour, header panel, Day-theme primary button | `velvet` |
| Gold script lettering "Blue Velvet" | Wordmark, primary actions at night | `gold` |
| White/cream frame and pillars | Panel border, headings at night, Day-theme page | `cream` |
| Gold stripe under the name | Stripe at the bottom of every `Sign` panel | `gold` |
| Round emblem on the left | `Crest` (BV monogram) | `cream` + `gold` |
| Copper beech hedge under the street light | Attention / "needs a human" state | `copper` |
| Blue neon glow behind the hedge | Links, info, selected state, background glow | `neon` |
| The night itself | Dark, blue-tinted neutrals | `night` |

Personality: **warm, nocturnal, a little retro, never kitsch.** The script
face and gold glow appear only at brand moments; working screens are calm,
legible and dense enough for real operations.

## 2. Themes

| Theme | When | Feel |
| --- | --- | --- |
| **Night** (default) | Dark OS setting, or pinned by the user | Velvet-night page, gold actions — the sign at night |
| **Day** | Light OS setting, or pinned by the user | Cream page, navy ink, navy buttons with gold text — the sign by day |

Night is the primary design target: staff use the app in dim rooms during
service. Every screen must be checked in both themes. The user's choice is
stored per device (`localStorage` key `bv-theme`) and applied before first
paint by the inline script in `index.html`. The `Sign` panel looks the same
in both themes — it is the physical object.

## 3. Colour

### 3.1 Palette (raw)

Available as Tailwind utilities (`bg-velvet-800`, `text-gold-300`, …).

| Family | Key steps | Use |
| --- | --- | --- |
| `velvet` 50–950 | 600 `#2c3f94`, 700 `#243377`, **800 `#1d2960`**, 900 `#161f4a`, 950 `#0c1130` | Brand panel, Day primary/accent |
| `gold` 50–900 | **300 `#efcd55`**, **400 `#e9bf3a`**, 500 `#cf9f1a` | Wordmark, Night primary, stripe |
| `cream` 50–500 | 100 `#f7f4ec`, **200 `#f6f1e3`**, 300 `#e3dccb` | Frame, Night headings, Day page |
| `copper` 300–700 | 400 `#f39461`, 600 `#a84a17` | Warning / needs attention |
| `neon` 300–600 | 400 `#8b98ff`, 500 `#5c6dff` | Night accent, glows |
| `night` 50–950 | 50 `#e9ecf7` … 800 `#0f1430`, 900 `#080b18` | Night surfaces and text |
| `success` / `danger` | 400 (Night), 700 (Day) | Status only |

### 3.2 Semantic roles — use these in product code

Product screens use semantic names so they work in both themes. Each exists
as a CSS variable (`var(--bv-surface)`) and a Tailwind utility
(`bg-surface`, `text-fg-muted`, `border-line`).

| Role | Night | Day | Use |
| --- | --- | --- | --- |
| `bg` | night-900 | cream-100 | Page |
| `surface` | night-800 | white | Cards, panels |
| `surface-raised` | night-700 | cream-50 | Secondary buttons, popovers |
| `surface-sunken` | night-950 | cream-100 | Inputs, code/source text |
| `line` / `line-strong` | night-600 / night-400 | cream-300 / cream-500 | Dividers / input borders (≥3:1) |
| `fg` | night-50 | `#141a3a` | Body text |
| `fg-muted` | night-200 | `#4f5679` | Secondary text, descriptions |
| `fg-subtle` | night-300 | `#6b7294` | Metadata, placeholders only |
| `heading` | cream-200 | velvet-900 | Headings, key values |
| `primary` / `on-primary` | gold-400 / velvet-950 | velvet-800 / gold-300 | The one main action |
| `accent` / `accent-soft` | neon-400 | velvet-600 | Links, eyebrow, selection, info |
| `focus` | gold-300 | velvet-500 | Focus ring |
| `success`, `warning`, `danger` (+`-soft`) | 400 steps | 600/700 steps | Status text and tinted backgrounds |

### 3.3 Rules

1. **Gold is for action and brand, not decoration.** One gold (primary) button
   per view. Never gold body text on a light background.
2. **Status colour always carries a label.** Badges have text and a dot;
   never rely on hue alone (colour-blind staff, glare at the bar).
3. **Copper means "a human should look".** Low extraction confidence,
   `needs_attention`, pending password change. It is not an error.
4. **Red is for destructive actions and failures only.** Reject, delete,
   failed import.
5. **Don't introduce hex values in components.** Add a token, or use an
   existing role. Raw palette utilities are for brand elements only.
6. **Contrast:** body text ≥ 4.5:1, UI borders and icons ≥ 3:1, in both
   themes. Current values (checked): Night `fg`/`surface` 15.3:1, `fg-muted`
   7.1:1, `fg-subtle` 4.7:1, `on-primary`/`primary` 10.5:1; Day `fg-muted`
   7.1:1, gold-on-velvet 8.8:1, status colours ≥ 5.7:1.

## 4. Typography

Fonts are self-hosted via Fontsource (bundled, no Google Fonts CDN — keeps the
app fully self-hosted and avoids third-party requests under GDPR).

| Role | Face | Where |
| --- | --- | --- |
| UI | **Inter Variable** | Everything |
| Wordmark | **Lobster** | `Wordmark` component only — never for headings, buttons or body |
| Mono | system mono | Extracted source text, IDs if needed |

| Style | Size / weight | Notes |
| --- | --- | --- |
| H1 page title | `clamp(1.75rem → 2.5rem)` / 650 | One per screen, `heading` colour |
| H2 section | `clamp(1.25rem → 1.5rem)` / 650 | |
| H3 | 1.0625rem / 650 | |
| Body | 1rem / 400, line-height 1.5 | 16px minimum on inputs (prevents iOS zoom) |
| Label | 0.875rem / 600 | `.field` |
| Eyebrow | 0.75rem / 600, uppercase, 0.12em tracking, `accent` | Context above titles: "Invoice #12 · drop-folder" |
| Small / meta | 0.8125rem / 400, `fg-muted` | |

- Use the `.numeric` class (tabular figures) for money, quantities and
  counts so columns align.
- Sentence case for headings, buttons and labels ("Confirm invoice", not
  "Confirm Invoice"). British spelling per AGENTS.md.

## 5. Shape, space and depth

- **Radius:** `sm` 6px (inputs), `md` 10px (buttons, sign), `lg` 14px
  (cards), `xl` 20px (sheets). Pills (999px) for badges only.
- **Spacing:** 4px grid. Use Tailwind spacing (`gap-4` = 16px). Common steps:
  8, 12, 16, 20, 24, 32. Page gutter 16px on mobile; content width ≤ 1180px.
- **Depth:** cards use `shadow-card`; the primary button gets `shadow-glow` on
  hover (the gold lettering glow). No other glows.
- **Motion:** 160ms with `--ease-velvet` for hover/focus; nothing bounces.
  `prefers-reduced-motion` disables transitions globally.

## 6. Components

All primitives are plain CSS classes, so they compose with Tailwind utilities.

### Brand

| Component | Use |
| --- | --- |
| `<Sign>` (`.bv-sign`) | Velvet panel with cream frame and gold stripe. App header, sign-in, splash. Max one per screen. |
| `<Wordmark>` (`.bv-wordmark`) | "Blue Velvet" in Lobster, gold with glow. Only inside a `Sign`. |
| `<Crest>` (`.bv-crest`) | BV emblem. Next to the wordmark; also the favicon/app icon. |

### Controls

| Class | Use |
| --- | --- |
| `.btn .btn-primary` | The single forward action of a view (Sign in, Confirm invoice, Import). |
| `.btn .btn-secondary` | Other actions (Activate, Reset password). |
| `.btn .btn-ghost` | Low-emphasis navigation (Back to queue, Sign out on a form). |
| `.btn .btn-danger` | Destructive actions (Reject). Outline only — never a filled red button next to a gold one. |
| `.btn-sm` | Dense rows. Default buttons are 44px tall (touch target); `btn-sm` is 36px and only for desktop-dense lists. |
| `.nav-tabs` + `.nav-tab` | Section switcher inside the `Sign`. Active tab: `aria-current="page"` (gold). |
| `.field` + `.input` | Label wrapping a control. Works for `input`, `select.input`, `textarea.input`. `aria-invalid="true"` for errors; `.field-hint` for help text. |

### Display

| Class | Use |
| --- | --- |
| `.card` (+ `.card-interactive`) | Any grouped content. Interactive for clickable rows. |
| `.badge` + `badge-info / -success / -warning / -danger` | Status. Plain `.badge` = neutral (inactive). |
| `.alert` + `alert-danger / -success / -info` | Inline messages; use `role="alert"` for errors, `role="status"` for notices. |
| `.meter[data-level=low|medium|high]` | Progress. Low = copper, high = green. |
| `.empty-state` | Dashed box with a short heading and one sentence. |
| `.eyebrow` | Context label above a title. |

### Status mapping (invoices)

| Status | Badge |
| --- | --- |
| `pending_review` | `badge-info` |
| `needs_attention` | `badge-warning` |
| `confirmed` | `badge-success` |
| `rejected` | `badge-danger` |

Queue cards name the required fields extraction did not suggest ("Missing:
Invoice date") rather than a confidence score. Extraction output is always a
*suggestion* — a card with nothing missing still needs a human confirm
(AGENTS.md hard rule 1); the UI must never imply otherwise.

## 7. Layout patterns

- **App shell:** `Sign` header (crest + wordmark, nav tabs, account, theme
  toggle, sign out) → page header (eyebrow, H1, muted description) → content.
- **Lists:** a stack of `.card` rows. On mobile, row content stacks vertically
  and actions go full-width.
- **Review/detail:** one card; two-column field grid on desktop, one column
  below 760px. On mobile the action bar sticks to the bottom (thumb reach).
- **Sign-in:** centred column — `Sign` with large wordmark, then the form card.
- **Documents** (invoice previews, riders) render on a white background in both
  themes: they are paper.

## 8. Platform and accessibility

- **Mobile first for staff screens** (PLAN.md §2), desktop first for the
  management dashboard; both use the same tokens.
- Touch targets ≥ 44px. Inputs use 16px text. Respect safe-area insets.
- Visible focus ring on every interactive element (`:focus-visible`).
- Use real elements (`button`, `label`, `nav`) and ARIA state
  (`aria-current`, `aria-busy`, `aria-invalid`) rather than visual-only classes.
- PWA `theme_color` and `<meta name="theme-color">` follow the themes
  (`#080b18` Night, `#f7f4ec` Day).

## 9. Building new screens

1. Start from the app shell; add a page header with eyebrow + H1 + description.
2. Compose with primitives (`.card`, `.btn`, `.field`, `.badge`) and Tailwind
   layout utilities (`grid`, `gap-4`, `md:grid-cols-2`).
3. Use semantic colours only (`bg-surface`, `text-fg-muted`, `border-line`).
4. Exactly one `btn-primary` per view.
5. Check Night and Day, at 375px and desktop width, with keyboard only.
6. If a pattern repeats on a second screen, promote it to `components.css`
   (or a component in `src/ui/`) and add it to §6 of this document.

## 10. Do / don't

| Do | Don't |
| --- | --- |
| Gold for the one action that moves work forward | Gold borders, gold text blocks, several gold buttons |
| Script face only in the wordmark | Lobster headings, Lobster buttons |
| Copper for "needs a look" | Red for things that are merely uncertain |
| Semantic tokens in screens | Hex values in JSX or new CSS |
| Calm working screens, brand at the edges | Neon glows on cards and tables |
