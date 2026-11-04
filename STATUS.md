# STATUS

Last updated: 2026-11-05

## Stage: Frontend scaffold (Vite PWA baseline) — Phase 0.5 discovery still blocking backend

## Snapshot

| Area | State |
| --- | --- |
| Product plan | Complete — full plan in `README.md`, including Phase 0.5 Invoice Ingestion Quick Win |
| Owner questions | Not yet answered — Phase 0 (discovery) and Phase 0.5 questions outstanding |
| Backend code | Placeholder only (`.gitkeep`) |
| Frontend code | React + TypeScript + Vite scaffold with PWA plugin configured (pnpm); placeholder UI, no real modules yet |
| Infra (Docker/HTTPS) | Placeholder only (`.gitkeep`) |
| Hosting hardware | Unknown — pending Phase 0 owner answers |

## Done

- Complete project plan written and committed (README.md): modules 4.1–4.10, technical architecture, security, access, 10-phase roadmap, first-usable-version scope, product principles.
- Phase 0.5 — Invoice Ingestion Quick Win defined and expanded (email + Google Drive ingestion, OCR decision, review queue with trust levels, Google Sheets API vs. local `.xlsx`, architecture notes, owner questions).
- Initial repository skeleton and planning docs committed (docs/architecture.md, docs/milestones.md, docs/next-steps.md).
- AGENTS.md, STATUS.md, CHANGE_LOG.md added.
- React + TypeScript + Vite scaffold created in `frontend/` (pnpm as package manager).
- PWA baseline configured: `vite-plugin-pwa` dependency added and `VitePWA` set up in `vite.config.ts` (autoUpdate registration, Web App manifest with icon set).

## In progress / uncommitted

- None — working tree clean; all scaffold and PWA work committed and pushed to `main`.

## Next steps (ordered)

1. Ask the owner the Phase 0.5 question set (8 questions, README §Phase 0.5) — highest priority, it unblocks the quick win.
2. Ask the owner the broader Phase 0 discovery questions (module workflows, hardware, hosting, access, users).
3. Replace PWA placeholder manifest icons/branding (favicon, apple-touch-icon, maskable icon) with real assets.
4. Based on owner answers, scaffold the Phase 0.5 invoice-ingestion service (independent Python service; mechanisms decided by the sheet-location + email-access answers).
5. Then proceed to Phase 1 foundation per `docs/next-steps.md`.

## Open questions blocking Phase 0.5

1. Is the accounting sheet on Google Drive, or must it remain a local `.xlsx`?
2. Email provider; OAuth/app-password feasibility; is a dedicated forwarding mailbox acceptable?
3. Proportion of clean PDF invoices vs. scans/photos (decides OCR approach; GDPR trade-off if cloud OCR).
4. Exact sheet columns, formula vs. value columns, tab structure.
5. Who opens the sheet, when, from where (incl. accountant)?
6. Monthly invoice volume and number of suppliers.
7. Credit-note/correction handling.
8. Notification preference for processed invoices / items needing attention.

## Risks

- **Email access friction:** personal Gmail OAuth verification or app-password setup can take days; a dedicated forwarding mailbox is the fallback.
- **OCR quality:** if most invoices are scans, local-only extraction may be too weak; cloud OCR raises local-first/GDPR questions the owner must decide.
- **Excel file locking/monolith drift:** mitigated by Google Sheets API path; and by keeping the sheet as output artifact with SQLite records as source of truth.
- **Plan-vs-reality drift:** the plan describes the full platform while no code exists; avoid ambiguity by keeping STATUS.md and docs/next-steps.md current.
