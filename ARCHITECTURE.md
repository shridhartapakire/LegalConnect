# Architecture

## Recommendation

Build a modular monolith: one Django application deployment, one PostgreSQL database, private object storage, and optional background processing when a real asynchronous requirement exists. This is intentionally not a microservice architecture. The domains are separated in code and permissions so individual services can be extracted later only when evidence justifies it.

## Logical architecture

```text
Browser (responsive web/PWA-ready UI)
        │ HTTPS
        ▼
Django web application ── Django REST Framework API
  ├─ Identity & access       ├─ Directory & verification
  ├─ Consultation/booking    ├─ Messaging/notifications
  ├─ Documents               └─ Admin & audit
        │                 │                    │
        ▼                 ▼                    ▼
 PostgreSQL       Optional worker/queue   Private object storage
                    (email/scans/expiry)     (encrypted documents)
        │                 │
        └────── observability / error reporting
```

The public pages should be server-rendered initially, with progressively enhanced interactive components. Authenticated portal interactions may use DRF endpoints. This avoids prematurely operating a separate frontend deployment and gives strong accessibility, SEO, and low-bandwidth performance for directory discovery.

## Major components

| Component | Responsibility |
| --- | --- |
| Django domain apps | Own models, services, policies, routes, and tests for accounts, advocates, consultations, scheduling, messaging, documents, notifications, AI, and audit. |
| DRF API | Versioned, authenticated endpoints for dynamic portal actions and future native applications. API permissions invoke the same domain policies as HTML views. |
| PostgreSQL | Transactional source of truth, constraints, JSON fields only for flexible metadata, and full-text/search support where appropriate. |
| Background worker + queue | Introduce only when needed for email delivery, malware scanning, document processing, expiry jobs, and reminders. Jobs must be idempotent and retry-safe. AI jobs are deferred. |
| Private object storage | Original document blobs; application database holds metadata, authorisation, checksum, and retention status. |
| Notification providers | In-app notifications plus email in Phase 1; use a small provider interface so SMS, WhatsApp, and push can be considered later. Delivery status is recorded but sensitive body content is kept minimal. |
| Future AI boundary | No AI module or provider in Phase 1. Keep AI-derived data distinct from core facts and add a gateway only after a separately approved future-phase design. |

## Boundaries and design rules

- Put business transitions in service-layer functions, not only views or serializers.
- Enforce object access in one policy layer, using database queries constrained to the active principal; never rely on hidden UI controls.
- Use transactional operations and row-level locking for accepting a slot or changing request state.
- Publish internal domain events after committed state changes. A worker consumes them for reminders, provider notifications, scans, and AI; these side effects must not make the primary transaction fail.
- Store an immutable audit event for sensitive states and reads/exports. Keep audit data separate from editable business records.
- Start with Django templates/forms. Keep DRF available for focused asynchronous interactions and future integrations; do not create an API duplicate for every HTML page. Add WebSockets only if real-time messaging needs demonstrably exceed safe polling/refresh; a short-poll endpoint is adequate for MVP.

## Frontend decision

Use Django templates and Django forms as the primary interface, with small JavaScript/TypeScript enhancements only when they materially improve a workflow (for example, slot selection, upload progress, or message refresh). Do **not** start with React or a separate SPA. A React/Next.js frontend becomes worthwhile only if the product later needs a highly interactive portal, dedicated mobile API clients, and an independently staffed frontend team.

## Availability, operations, and scale

- Place the web app behind a managed HTTPS load balancer/reverse proxy; serve static assets through a CDN/object store.
- Run stateless web instances and separately scale workers.
- Use managed PostgreSQL with automated point-in-time recovery, encrypted backups, and tested restore procedures.
- Design for a regional launch: caching public directory reads, indexes for filters, pagination, and asynchronous slow work are sufficient initially.
- Define health checks, structured logs, request IDs, metrics, alerting, staged deployments, and rollbacks before inviting real users.
