# Club Operations Platform — Project Plan

## 1. Project Overview

The goal is to build a self-hosted platform that centralises the day-to-day operations of a nightclub.

The platform will replace scattered tools, spreadsheets, documents and manual processes with one system where management and staff can organise events, 
promoters, shifts, inventory, orders, technical requirements and other operational information.

The system will also include a local AI assistant that can help staff find information and understand the club's data and documents.

The application will be built as a **Progressive Web App (PWA)**. This means users can access it through a browser on desktop, tablet or mobile, and 
install it on their devices like a normal application.

The platform will run on infrastructure controlled by the club. Its data, documents and AI processing will remain on the club's own infrastructure 
rather than relying on external AI services.

### Main objectives

- Centralise club operations in one platform.
- Make event planning and management easier.
- Simplify communication and information collection from promoters.
- Improve staff scheduling and operational coordination.
- Manage inventory, stock counts and supplier orders.
- Keep technical documents and event information organised.
- Make important information accessible from desktop and mobile.
- Support essential workflows when internet connectivity is temporarily unavailable.
- Introduce a local AI assistant to search and understand the club's information.

---

## 2. Application Structure

The platform will have three main user experiences within one application.

### A. Management dashboard

Designed primarily for desktop use, with a responsive layout for tablets and mobile devices.

Management will be able to:

- View upcoming events and the calendar.
- Review promoter submissions.
- Manage staff and shifts.
- Monitor stock levels and orders.
- Review urgent replenishment alerts.
- Manage suppliers and deliveries.
- Access documents and technical requirements.
- Track event budgets and expenses.
- Use the local AI assistant.

### B. Staff mobile interface

Designed primarily for phones and tablets.

The interface will focus on the tasks staff need to perform during and after events.

Examples:

- View assigned shifts and upcoming events.
- Check event information.
- Submit post-event stock counts.
- Flag products that need urgent replacement.
- View relevant technical and operational information.
- Receive important operational notifications.

The stock-counting interface should be particularly quick and easy to use, with minimal navigation and simple quantity inputs.

### C. Promoter submission form

Promoters will not need an account or access to the internal dashboard.

They will receive a private link that allows them to submit an event proposal.

The form will collect:

- Promoter name and contact details.
- Event name and description.
- Proposed date and times.
- Expected attendance.
- Budget.
- DJs and artists.
- Promotion plans and requirements.
- Ticketing information.
- Technical requirements and rider uploads.
- Additional requests or arrangements.

Management will review submissions internally and decide whether to approve, reject or request changes.

Submitting a proposal will not automatically reserve a date or approve a budget.

Private links should use secure, unguessable tokens, with the ability to revoke or expire them.

---

## 3. PWA Architecture and Device Support

The application will be developed as one responsive PWA rather than separate desktop and mobile applications.

### What this means

Users will be able to:

- Access the application through a browser.
- Install it on their phone or computer.
- Open it in an app-like full-screen experience.
- Use responsive interfaces adapted to their device.
- Access selected information while offline.
- Synchronise changes with the club's server when connectivity returns.

There will be no need to publish a separate application through the Apple App Store or Google Play Store.

### Recommended frontend stack

- React
- TypeScript
- Vite
- Tailwind CSS
- Component library for consistent UI
- Vite PWA Plugin
- Service Workers
- IndexedDB for offline data and queued actions

### Offline functionality

Offline functionality is particularly important for staff working during events.

The first version should support:

1. Caching the application shell so the interface can open without a connection.
2. Making selected event and inventory information available offline.
3. Allowing staff to enter post-event stock counts without an active connection.
4. Saving submitted information locally in IndexedDB.
5. Queuing changes until the server becomes reachable.
6. Synchronising queued information with the backend.
7. Showing whether information is pending, synchronised or has encountered an error.

The application must not silently lose information when a connection drops.

### Synchronisation and data consistency

The backend remains the source of truth for the club's data.

Mobile devices can temporarily store user actions locally, but they must not independently modify the club's global stock levels.

For example:

- A member of staff completes a stock count offline.
- The PWA saves the count locally.
- When connectivity returns, the PWA submits the count to the backend.
- The backend validates and processes the count.
- The backend updates the stock records and recalculates upcoming requirements.
- Any resulting shortage alerts are generated centrally.

The system must handle duplicate submissions, retries and conflicting updates.

Each offline action should have a unique identifier so that retrying a submission does not accidentally create duplicate records.

The interface should clearly communicate synchronisation status.

### Notifications

The application should support operational notifications, such as:

- Urgent stock shortages before an upcoming event.
- Changes to staff shifts.
- New promoter submissions.
- Important event updates.

Push notifications can be introduced where supported by the user's browser and operating system. In-app notifications should also be available.

### Important technical considerations

- Service Workers and many PWA features require a secure HTTPS context.
- Local hosting must therefore include a suitable local HTTPS setup.
- Remote access must use a secure connection.
- Offline functionality must be designed into the relevant workflows from the beginning.
- Sensitive documents and credentials should not be stored unnecessarily in browser storage.
- Offline data should be limited to what each user needs.

---

## 4. Main Functional Modules

### 4.1 Dashboard

The central overview of the club's operations.

It should display:

- Upcoming events.
- Pending promoter submissions.
- Upcoming staff shifts.
- Stock shortages.
- Urgent replenishment alerts.
- Orders awaiting approval.
- Expected deliveries.
- Recent activity.
- Missing or incomplete information.

The dashboard should prioritise information that requires attention.

### 4.2 Events and Calendar

Events are the central entity connecting the different modules.

The calendar should support daily, weekly and monthly views.

Each event should have a central record containing:

- Event name and description.
- Date and times.
- Promoter information.
- Expected attendance.
- DJs and artists.
- Staff assignments.
- Technical requirements.
- Inventory requirements.
- Orders and deliveries.
- Marketing information.
- Budget information.
- Related documents.
- Activity history.

Information from other modules should be connected to the relevant event rather than stored in isolation.

### 4.3 Promoter Submissions

A public-facing form accessed through a private link.

Management should be able to:

- View incoming proposals.
- Review submitted information.
- Open uploaded documents.
- Request additional information or changes.
- Approve or reject proposals.
- Convert approved proposals into actual events.

Suggested submission statuses:

- Submitted.
- Under review.
- Changes requested.
- Approved.
- Rejected.

### 4.4 Staff and Shifts

Manage the people working at the club.

Features:

- Staff profiles.
- Roles and responsibilities.
- Availability.
- Shift schedules.
- Event-specific assignments.
- Changes and replacements.

Staff should be able to access relevant shift and event information through the mobile PWA.

### 4.5 Technical Requirements and Equipment

Centralise technical information for events.

Features:

- Upload technical riders.
- Record sound, lighting and stage requirements.
- Manage equipment inventory.
- Associate equipment with events.
- Identify equipment availability and conflicts.
- Keep technical documents linked to their respective events.

### 4.6 Inventory, Stock Counts and Ordering

This is one of the most important operational modules.

The ordering process must consider the needs of individual events and entire weekends, rather than relying only on generic minimum-stock alerts.

#### Product catalogue

Each inventory item should have:

- Product name.
- Category.
- Supplier.
- Unit or packaging size.
- Price, where available.
- Current stock.
- Minimum stock level.
- Preferred supplier.
- Typical delivery time.

Categories could include:

- Beer.
- Soft drinks.
- Mixers.
- Spirits.
- Bottled products.
- Bar supplies.
- Cleaning products.
- Consumables.
- Other.

The system must support different units such as bottles, cans, crates, boxes and individual items.

#### Post-event stock counts

After each event, bar staff should be able to record the remaining stock through the mobile interface.

Workflow:

1. Select the event that has just finished.
2. Open the relevant product list.
3. Enter the remaining quantity for each item.
4. Flag products that need immediate replacement.
5. Add optional notes.
6. Submit the count.

The system should record:

- Event.
- Product.
- Remaining quantity.
- Staff member.
- Timestamp.
- Notes.

Stock counts should update the recorded inventory and provide the basis for future ordering.

Key products should have required counts, and management should be able to see which counts are incomplete.

#### Event-based stock planning

The system should calculate suggested orders based on:

- Current stock.
- Expected requirements for upcoming events.
- Stock already reserved for events.
- Confirmed incoming deliveries.
- Minimum stock levels.
- Safety buffers.

For example, if the club has an event on Friday and another on Saturday, the system should calculate the combined requirements for both events.

It should identify which products need ordering before the weekend.

Initially, expected requirements can be entered manually. Historical event data can later help improve estimates.

#### Urgent replenishment between events

The system must identify shortages between events.

Example:

- Friday's event finishes.
- Staff submit the remaining stock count.
- The system recalculates available stock.
- Saturday's event has additional requirements.
- One or more products are insufficient.
- The system creates an urgent replenishment alert.

The alert should display:

- Product.
- Remaining quantity.
- Required quantity.
- Shortage.
- Next event.
- Event start time.
- Whether a replacement has been arranged.

Alert statuses:

- Open.
- Acknowledged.
- Replacement arranged.
- Resolved.

Simply viewing an alert must not clear it.

#### Supplier orders and deliveries

Management should be able to:

- Manage suppliers.
- Review suggested order quantities.
- Create purchase orders.
- Approve orders.
- Record when orders are sent.
- Track expected delivery dates.
- Record partial deliveries.
- Confirm received quantities.
- Track order costs and invoices.

Suggested order statuses:

- Draft.
- Awaiting approval.
- Approved.
- Sent to supplier.
- Partially delivered.
- Delivered.
- Cancelled.

Products should only be added to available stock once physically received.

#### Stock movement history

Maintain a record of stock changes, including:

- Deliveries.
- Post-event counts.
- Manual adjustments.
- Transfers.
- Consumption.

This provides a reliable history of how inventory changes over time.

### 4.7 Marketing and Promotions

Organise the promotional work associated with each event.

Features:

- Marketing plans.
- Campaign deadlines.
- Social media content.
- Promotional assets.
- Promoter responsibilities.
- Links between marketing activities and events.

Automatic social media publishing is not required for the initial version.

### 4.8 Finance and Budgets

Track the financial side of events.

Features:

- Planned and actual budgets.
- Event income.
- Expenses.
- Supplier costs.
- Ticketing information.
- Event-related purchase orders.
- Financial history.

Inventory orders should be linkable to the relevant event or weekend so their costs can be tracked.

### 4.9 Documents and Technical Information

A central repository for club documents.

Examples:

- Contracts.
- Technical riders.
- Event documents.
- Supplier information.
- Invoices.
- Staff documentation.
- Operational procedures.

Documents should be linked to the relevant event, promoter, supplier or other record.

Support common formats such as PDF, Word, Excel and text files.

The system should maintain useful metadata, version information and searchable content.

### 4.10 Local AI Assistant

A local AI assistant that helps staff find and understand information.

Examples:

- What events are coming up this weekend?
- What technical requirements does an upcoming event have?
- Which products need to be ordered?
- What stock was left after the previous event?
- Where can I find a particular contract?
- What information is missing from an event proposal?
- Summarise the technical rider for an event.

The AI assistant will initially be read-only.

It must not autonomously approve events, place orders, modify stock or make financial decisions.

Answers should include references to the original records or documents.

---

## 5. Technical Architecture

The application will use a modular monolith architecture.

This keeps development and deployment manageable while allowing individual modules to evolve independently.

### Frontend

- React.
- TypeScript.
- Vite.
- Tailwind CSS.
- Component library.
- Vite PWA Plugin.
- Service Workers.
- IndexedDB.

### Backend

- Python.
- FastAPI.
- Pydantic.
- SQLAlchemy.
- Alembic.

The backend will expose a versioned REST API, initially under `/api/v1/`.

The API should remain independent of the frontend so other applications and services can integrate with it later.

### Database

Start with SQLite.

Use a structured relational database for:

- Events.
- Promoters.
- Staff.
- Shifts.
- Inventory.
- Stock counts.
- Orders.
- Suppliers.
- Budgets.
- Permissions.
- Activity records.

Use SQLite FTS5 for keyword-based document and record searching.

Vector search can be added for semantic document retrieval when the AI module is implemented.

### AI and Local Inference

Use Ollama for local model inference, depending on the available hardware.

The AI system should distinguish between:

- Structured information, which should be retrieved through database queries and business logic.
- Unstructured documents, which can be processed and searched through document retrieval and embeddings.

Use a hybrid search approach combining keyword and vector search.

Exact names, dates, prices, product models and technical specifications should not depend solely on semantic search.

### File Storage

Store uploaded documents and files on the club's own infrastructure.

The database should hold document metadata and references to the stored files.

### Deployment

Use Docker Compose to manage the application services.

Initial deployment should include:

- Backend.
- Database.
- Frontend delivery.
- File storage.
- Local AI inference service, when introduced.

The application should run on a server or suitable computer located at the club.

### Integration with Local AI Control Plane

The backend should be designed as an independent service with a documented API.

This will allow the user's separate local-ai-control-plane project to integrate with it in the future.

The two projects should remain separate.

The Club Operations Platform owns club-specific data and business logic. The control plane can eventually manage infrastructure, AI agents and deployments.

---

## 6. Security and Data Management

Security must be considered from the beginning.

Requirements:

- Authentication for internal users.
- Role-based access control.
- Secure promoter submission links.
- Permission-aware access to documents and AI search.
- Secure file upload validation.
- Activity logs for important operations.
- Protected API endpoints.
- HTTPS for local and remote access.
- Regular backups.
- Tested restore procedures.
- Appropriate data retention and access controls.

Uploaded documents must be treated as untrusted content. Their contents must never be allowed to override system instructions or trigger unauthorised actions by the AI assistant.

The application should also be designed with relevant German and EU data protection requirements in mind.

---

## 7. Access and Hosting

The platform will be self-hosted, but access requirements must be established with the club before implementation.

Possible access arrangements:

- Only inside the club, using its Wi-Fi.
- Inside the club and remotely.
- From anywhere with an internet connection.
- Different access rules depending on the user's role.

If remote access is required, it must be implemented securely.

Possible approaches include a VPN or a carefully configured secure reverse proxy.

The application should not expose the club's server or internal services directly to the public internet without appropriate protection.

The PWA will need a secure HTTPS connection, including when accessing the locally hosted application.

---

## 8. Development Roadmap

Development should happen in stages, with a usable result delivered as early as possible.

### Phase 0 — Requirements and Discovery

- Review the owner's questionnaire answers.
- Understand existing operational processes.
- Collect examples of spreadsheets, documents and forms.
- Understand event planning and promoter workflows.
- Understand stock counting and ordering.
- Identify supplier processes and delivery times.
- Establish access requirements.
- Identify the hardware available for hosting.
- Define the first version's scope.

### Phase 0.5 — Invoice Ingestion Quick Win

The club owner has requested an immediate, focused tool: a service that reads an email account and/or a Google Drive folder, scans incoming invoices, and puts their data into the Excel sheet he already uses for accounting, which already has its columns defined.

This is deliberately built before the main platform foundation. It needs no PWA and no offline functionality, and it delivers visible value to the owner early. Internal authentication was added once reviewer attribution became necessary; it is self-managed by the backend and shared with the main platform. The components built here — document ingestion, invoice storage, field extraction and spreadsheet export — will later flow directly into the Documents (4.9), Inventory and Finance (4.8) modules rather than being throwaway work.

The service is essentially a small independent Python pipeline:

**Ingest (email + Drive) → Classify (is it an invoice? which supplier?) → Extract (fields) → Review queue → Write to sheet**

#### Ingestion channels

There are two ingestion channels, with different roles:

1. **Google Drive folder (primary).** The owner drops invoice files into a defined Drive folder; the service picks up new files by polling the Drive API. This is the most reliable channel: no email filtering, and the owner controls exactly what enters by dragging files in.
2. **Email account (secondary, automated).** Emails are read through the Gmail API (or IMAP, depending on the provider). Invoice attachments are extracted from recognized supplier senders.

For a personal Gmail account, OAuth verification or an app password is required; this setup friction should be budgeted. A cleaner alternative is a **dedicated Google account** for the system, with a Gmail forwarding rule on the owner's own mailbox (e.g. "messages from supplier X with attachments → forward"). The service then only touches that dedicated account, permissions stay simple, and the owner's daily mailbox is untouched. Once processed, source emails should be labelled (e.g. "ingested"), not deleted.

#### Invoice classification and field extraction

- Text-based PDFs: extract text and apply **supplier-specific parsing templates** where invoice layouts are consistent.
- Scans and photos: these require OCR. Local options (Tesseract plus a local vision model via Ollama) work but demand setup effort and have mediocre accuracy on real invoices; cloud OCR is more accurate but conflicts with the plan's local-first and data-protection stance. The proportion of scanned invoices is a key deciding question — if most invoices are clean PDFs, local OCR tooling is sufficient; if most are scans, the owner should explicitly decide whether accounting data may pass through a third-party service (GDPR relevance).
- Output of extraction is always a **suggestion**, never a written fact.

#### Review queue and trust levels

Every extracted invoice lands in a review list before anything reaches the accountant's sheet:

- **Rollout stage 1 (first weeks):** every invoice requires the owner's confirmation; only confirmed values are written.
- **Rollout stage 2 (after accuracy is proven):** auto-write for trusted, consistently-parsed suppliers; review remains required for new suppliers, corrected/reversed invoices and low-confidence extractions.

The service must never fully automate the accounting step without this review point. A human confirms extracted values once, and the structured data becomes reliable from day one.

Unmatched or low-confidence invoices go to a "needs attention" list rather than being skipped silently, and the owner is notified (email digest, or a message via his preferred channel).

#### Spreadsheet output — one decisive detail

If the accounting sheet already lives on Google Drive (or can be moved there), the service should write through the **Google Sheets API** rather than writing to an `.xlsx` file:

- No file locking, no risk of corrupting a file that is open in Excel.
- No file shuffling between the server and Drive.
- Free, and works from any server.

If the sheet must remain a local `.xlsx` (formulas, macros, or local workflow), the service appends rows with openpyxl while preserving formatting and formulas, and handles the "file currently open and locked" case gracefully (retry, never silent loss).

Which of the two applies is one of the first questions to settle with the owner. In either case, the sheet is an **output artifact**: the invoice records (SQLite, with the original file attached and classified) are the source of truth, so the data flows into the main platform later.

#### Architecture notes

- Small independent Python service (FastAPI + scheduled worker), later deployed via Docker Compose — the same backend technology as the main platform, already isolated.
- Minimal documented API so the service can be integrated into the main backend from Phase 1 onward rather than replaced.
- Storage: invoice files on disk, metadata and extracted values in SQLite, following the same pattern as the future documents repository (4.9).

#### Phase 0 questions specific to this phase

1. Where does the Excel sheet live today — on Google Drive, or must it remain a local `.xlsx`? (Determines Sheets API vs. file locking.)
2. Which email provider is in use, and can OAuth/app-password access be arranged? Is a dedicated forwarding mailbox acceptable?
3. What proportion of invoices are clean PDFs versus scans or photos? (Determines the OCR approach and the local-first trade-off.)
4. What are the exact columns of the existing sheet, which columns are formulas versus plain values, and is there one tab or several (per month/supplier/year)?
5. Who opens the sheet, from where, and how often — including the accountant, if one is involved?
6. Roughly how many invoices arrive per month, and from how many distinct suppliers?
7. Are there credit notes or corrections that reverse earlier invoices, and how are those represented in the sheet today?
8. How should the owner be alerted about new processed invoices and about items needing attention?

#### Owner answers (working assumptions, recorded 2026-11-05)

The owner answered the questionnaire with these working assumptions; the plan
below is written against them and will be adjusted where reality differs.

1. **Sheet location:** Google Drive → the service writes through the **Google
   Sheets API** (append-only; existing rows and formula columns are never
   touched — output artifact, hard rule 3).
2. **Email:** Gmail, with a **dedicated forwarding mailbox** created for the
   service (owner's daily mailbox untouched, exactly the "cleaner alternative"
   described above). Gmail API via OAuth for that mailbox only.
3. **Format mix:** ~50% photos/scans, ~50% clean PDFs → local OCR is
   mandatory; **Tesseract only, no cloud OCR**. Lower photo-quality accuracy is
   absorbed by the review queue (stage 1: everything is confirmed by a human
   anyway).
4. **Columns:** the assumed v1 set is the common club-invoice columns:
   supplier, invoice number, invoice date, due date, net, VAT, gross,
   category, description, payment method. The mapping is **confirmed against
   the real sheet before the first write is switched on** (export stays
   feature-flagged off until then).
5. **Access:** the owner and one admin staff member, each with their own
   account. Accounts are created by an administrator — there is no
   self-registration. Roles are `owner` (manages every account), `admin`
   (manages staff accounts) and `staff` (sign-in only). No broader RBAC in
   this service.
6. **Volume:** ~20 invoices/month from a small number of suppliers → a
   nightly batch (and catch-up polling) is entirely sufficient; tables are
   sized accordingly.
7. **Credit notes/corrections:** not yet answered — **open**. Until answered,
   corrections follow the review-queue path only (fix values before confirm);
   reverse-document handling stays out of scope.
8. **Notifications:** the owner receives an **email digest with instructions**
   on what needs attention (link to the review queue plus step-by-step
   guidance).

Interim hosting: the dedicated club-hardware setup does not exist yet, so the
service initially runs **on demand on the owner's workstation** (catch-up
polling with per-source sync watermarks; offline periods simply mean the next
run ingests the backlog — the forwarding mailbox and Drive folder buffer
everything). Collapsed digest notifications: a quiet period produces one
"everything since last review" summary. This upgrades to a dedicated always-on
box with no rework the moment the hardware exists.

#### Internal authentication (implemented 2026-11-06)

- Accounts are self-managed by the backend: a `users` table with Argon2id
  password hashes and database-backed sessions. There is no external identity
  provider and **no public registration**.
- The first owner is bootstrapped with
  `uv run python -m app.cli create-user --username owner --role owner`.
  Everyone else is created by an owner or admin from the **Staff** screen; new
  accounts receive a temporary password and must choose their own at first
  sign-in.
- Roles: `owner` manages every account, `admin` manages staff accounts, and
  `staff` can sign in and change their own password. **Invoice review is
  limited to owners and administrators**; staff accounts have no access to
  invoice data or the staff panel.
- The browser holds an opaque session token in an HttpOnly, `SameSite=Lax`
  cookie. `POST /api/v1/auth/login`, `/logout`, `/me` and `/password` are the
  only auth endpoints; state-changing requests from unknown origins are
  rejected.
- The backend facade authenticates the browser and forwards the username to
  the invoice service as `X-Reviewer`, together with the internal service
  token. The invoice service trusts that header **only** alongside the token
  and records it in `reviewed_by`; a token-only call stays attributed to
  `backend`.
- Production requirements: serve over HTTPS and set
  `SESSION_COOKIE_SECURE=true`; set `ALLOWED_ORIGINS` to the real frontend
  origin; and keep the invoice service (`:8081`) internal-only, because its
  internal token bypasses the facade's authentication.

### Phase 1 — Project Foundation

- Set up repository and project structure.
- Configure frontend and backend.
- Establish database and migrations.
- Implement authentication. — done early (2026-11-06) for the Phase 0.5 quick win; see §Phase 0.5, "Internal authentication".
- Implement permissions.
- Create the initial API structure.
- Configure Docker Compose.
- Set up file storage.
- Establish the PWA foundation.
- Configure HTTPS for the development and deployment environments.

### Phase 2 — Events and Calendar

- Implement event data models.
- Create event management.
- Build calendar views.
- Add event details.
- Connect related operational information.

### Phase 3 — Internal Dashboard

- Build the main dashboard.
- Add upcoming events.
- Show pending submissions.
- Display important operational alerts.
- Create role-specific navigation.
- Make the interface responsive.

### Phase 4 — Promoter Submission

- Build the private promoter form.
- Implement secure submission links.
- Support document uploads.
- Create the internal review workflow.
- Implement approval and rejection.
- Convert approved proposals into events.

### Phase 5 — Inventory and Ordering

- Create product catalogue.
- Implement suppliers.
- Implement stock movements.
- Build the mobile stock-count interface.
- Support offline stock counts.
- Implement local queuing and synchronisation.
- Handle retries and duplicate submissions.
- Calculate event and weekend stock requirements.
- Implement suggested purchase orders.
- Implement urgent replenishment alerts.
- Track deliveries and received quantities.

### Phase 6 — Documents and Technical Requirements

- Implement document storage.
- Add document metadata.
- Link documents to events and other records.
- Support technical riders.
- Implement document search.

### Phase 7 — Staff and Other Operations

- Implement staff profiles.
- Manage availability and shifts.
- Assign staff to events.
- Add marketing organisation.
- Add financial and budget tracking.

### Phase 8 — Local AI Assistant

- Configure local inference.
- Implement document processing.
- Add keyword and vector search.
- Connect the assistant to structured database queries.
- Add source references to answers.
- Implement permission-aware retrieval.
- Test accuracy and handling of insufficient information.

### Phase 9 — Testing and Deployment

- Test all main workflows.
- Test desktop, tablet and mobile interfaces.
- Test PWA installation.
- Test offline behaviour.
- Test synchronisation and conflict handling.
- Test remote access.
- Test permissions and security.
- Configure backups.
- Test restoration.
- Deploy to the club's infrastructure.
- Provide basic user documentation.

---

## 9. First Usable Version — Scope

The first usable version should focus on the features that solve the club's most immediate operational problems.

It should include:

1. Secure internal login.
2. Responsive management dashboard.
3. Event calendar and event management.
4. Private promoter submission form.
5. Submission review and approval workflow.
6. Document uploads.
7. Inventory catalogue.
8. Post-event stock counts through the mobile PWA.
9. Offline stock-count submission and synchronisation.
10. Suggested orders based on upcoming events.
11. Urgent stock shortage alerts between events.
12. Supplier orders and delivery tracking.
13. Basic document search.

The local AI assistant, advanced financial tracking and more complex automation can follow once the underlying operational data is reliable.

---

## 10. Main Product Principles

The following principles should guide all implementation decisions:

1. **One application:** Build one responsive PWA instead of separate desktop and mobile applications.
2. **Local-first infrastructure:** Keep club data and AI processing under the club's control.
3. **Event-centred design:** Events connect the different operational modules.
4. **Simple user experience:** The application must be usable by people who are not technically experienced.
5. **Offline-aware workflows:** Essential staff tasks, especially stock counts, must tolerate temporary connectivity loss.
6. **Backend as source of truth:** The server validates and processes all important operational changes.
7. **API-first architecture:** Keep the backend independent and ready for future integrations.
8. **Structured data first:** Build reliable operational records before introducing AI.
9. **AI as an assistant:** AI helps retrieve and understand information but does not make operational decisions.
10. **Modular development:** Build and deliver features in manageable stages rather than trying to implement everything at once.