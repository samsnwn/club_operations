# Blue Velvet — Club Operations Platform

Blue Velvet is a self-hosted Progressive Web App (PWA) for centralising nightclub operations in one platform.

It replaces fragmented spreadsheets, documents, and manual coordination with a single system for:

- Event and calendar management
- Promoter proposal intake and review
- Staff and shift coordination
- Inventory, stock counts, ordering, and deliveries
- Technical requirements and document management
- Operational notifications and alerts
- A local, read-only AI assistant for data and document retrieval

## Core Product Principles

- **One application**: one responsive PWA for desktop, tablet, and mobile
- **Local-first infrastructure**: data and AI processing remain on club-controlled systems
- **Event-centred model**: events connect operations across modules
- **Offline-aware workflows**: critical staff flows (especially stock counts) continue during temporary connectivity loss
- **Backend as source of truth**: server validates and applies operational changes
- **API-first backend**: versioned REST API under `/api/v1/` for future integrations
- **AI as assistant only**: read-only support with source references, no autonomous operational decisions

## Main User Experiences

### 1) Management dashboard

Responsive dashboard prioritising actions that need attention:

- Upcoming events and key calendar views
- Pending promoter submissions
- Shift and staffing issues
- Stock shortages and urgent replenishment alerts
- Supplier orders and deliveries
- Missing or incomplete operational data

### 2) Staff mobile interface

Mobile-first workflows for event operations:

- Assigned shifts and relevant event details
- Post-event stock counting with fast quantity input
- Urgent replacement flags
- Relevant technical and operational information
- Synchronisation status visibility (pending/synced/error)

### 3) Promoter submission form (public by private link)

Promoters submit proposals through revocable/expirable, unguessable token links.

Submission lifecycle:

- Submitted
- Under review
- Changes requested
- Approved
- Rejected

Approval does not auto-reserve date or auto-approve budget.

## Technical Stack

### Frontend

- React + TypeScript + Vite
- Tailwind CSS + shared component library
- Vite PWA Plugin + Service Worker
- IndexedDB for offline data and queued actions

### Backend

- Python + FastAPI
- Pydantic + SQLAlchemy
- Alembic migrations
- Versioned REST API (`/api/v1/`)

### Data and AI

- SQLite (initial), including FTS5 for keyword search
- Local file storage for uploaded documents
- Ollama for local inference (when AI module is introduced)
- Hybrid retrieval model:
  - Structured queries for exact operational data
  - Document retrieval (keyword + vector) for unstructured content

### Deployment

- Docker Compose-managed services
- Initial stack: backend, database, frontend delivery, file storage
- Local HTTPS required for Service Worker/PWA features

## Offline and Sync Design (Required)

For stock-count workflows, the first usable version must:

- Cache application shell for offline launch
- Expose selected event and inventory data offline
- Save stock-count actions to IndexedDB when offline
- Queue submissions with unique action IDs (idempotency)
- Retry/synchronise on reconnect
- Show explicit action state (`pending`, `synced`, `error`)
- Prevent silent data loss

The backend remains authoritative and must handle duplicates, retries, and conflicts safely.

## Core Functional Modules

1. Dashboard
2. Events and Calendar
3. Promoter Submissions
4. Staff and Shifts
5. Technical Requirements and Equipment
6. Inventory, Stock Counts, and Ordering
7. Marketing and Promotions
8. Finance and Budgets
9. Documents and Technical Information
10. Local AI Assistant (read-only)

## Security Requirements

- Internal authentication + role-based access control
- Secure promoter links (unguessable, revocable, expirable)
- Endpoint protection and activity logging
- Secure file upload validation
- Permission-aware document and AI access
- HTTPS for local and remote access
- Regular backups and restore validation
- Treat uploaded files as untrusted content
- Avoid unnecessary storage of sensitive data in browser storage

## MVP (First Usable Version)

The first usable release focuses on immediate operational value:

- Secure internal login
- Responsive management dashboard
- Event calendar and event management
- Private promoter submission and internal review workflow
- Document uploads
- Inventory catalogue
- Mobile post-event stock counts
- Offline stock-count queueing and synchronisation
- Suggested orders based on upcoming events
- Urgent between-event shortage alerts
- Supplier order + delivery tracking
- Basic document search

## Delivery Roadmap

- **Phase 0**: discovery and requirements validation
- **Phase 1**: project foundation (auth, permissions, API structure, storage, PWA base, HTTPS)
- **Phase 2**: events and calendar
- **Phase 3**: internal dashboard
- **Phase 4**: promoter submission workflow
- **Phase 5**: inventory and ordering with offline stock-count sync
- **Phase 6**: documents and technical requirements
- **Phase 7**: staff + additional operations
- **Phase 8**: local AI assistant
- **Phase 9**: end-to-end testing and production deployment

---

This repository currently defines the platform scope, architecture, and implementation requirements for staged delivery.
