# Testing Strategy

## Objective

Testing must demonstrate that the platform is trustworthy with sensitive matters: correct permissions and workflow state, reliable scheduling/notifications, secure documents, useful accessible interfaces, and safe AI assistance. Tests should be part of every delivery stage, not postponed until launch.

## Test pyramid

| Level | Focus | Examples |
| --- | --- | --- |
| Unit | Fast domain logic | request transition rules, availability calculation, ranking, consent, serializers, input validation. |
| Integration | App + PostgreSQL/queue/storage adapters | permissions on object queries, overlap constraints, signed URL lifecycle, worker idempotency, notification/webhook handling. |
| API/contract | Stable endpoint behaviour | authentication, pagination, error formats, role/object access, provider adapters. |
| End-to-end | Critical browser journeys | register, verified directory search, submit one request to one advocate, conflict check/acceptance, book/reschedule appointment, message, authorised upload/download, admin verification decision. |
| Manual/UAT | Real local usability and policy validation | mobile network/low-bandwidth behaviour, Kannada/English content, accessibility, support/admin process, legal wording. |
| Security/performance/resilience | Production risks | SAST/dependency scans, DAST with approval, rate limits, access-control testing, file-upload abuse, load, backup restore, provider failure/retry. |

## Critical acceptance scenarios

1. An unverified or unpublished advocate never appears in public search.
2. A client cannot read another client's requests, messages, appointments, or documents by changing a URL/API ID.
3. An advocate accesses only requests assigned/accepted under policy, and never verification documents belonging to another advocate.
4. A staff role cannot perform actions outside its explicit operational permissions; break-glass actions create an audit event.
5. A temporary slot hold expires correctly and conflicting appointments cannot both become confirmed under concurrent booking attempts.
6. Request and appointment state changes obey their separate approved state machines and notify the right parties without exposing matter details.
7. A malicious/unsupported document is rejected or quarantined; an authorised file is retrievable only through a valid short-lived access path.
8. Account recovery and login do not reveal whether an email/phone is registered.
9. Notification retries do not create duplicate user-facing messages or duplicate booking state changes.
10. Phase 1 makes no AI call and no AI-derived output is present in user workflows; future AI must be separately evaluated before enablement.

## Security and privacy verification

- Write permission tests for every endpoint/domain action before adding feature UI.
- Run static analysis, dependency/CVE checking, secret scanning, and lint/type checks in CI.
- Test CSRF, session/cookie settings, security headers, rate limiting, enumeration, insecure direct object references, injection, XSS, upload validation, signed URL expiry, logging redaction, audit completeness, and deletion/retention jobs.
- Commission an independent penetration test and resolve high/critical findings before production handles real client documents. Scope and timing require budget approval.
- Conduct a privacy review of data flows, vendors, AI, consent text, administrative access, backups, and retention before go-live.

## Quality gates

- Every change has peer review and appropriate automated tests; no test suite may rely on real personal/legal data.
- Main branch must pass unit/integration/API checks, migration checks, security scans, and accessibility linting where available.
- Staging release must pass smoke tests and the affected end-to-end critical path.
- Production release requires a rollback plan, monitoring readiness, and no unresolved high-severity security/privacy issue.
- Track coverage as a signal, not a substitute: prioritise meaningful coverage of risk-heavy policies, state transitions, and data access.

## AI evaluation

Before enabling each AI feature, test against an approved de-identified evaluation set. Measure taxonomy accuracy, recommendation relevance/fairness, summary faithfulness, unsafe output rate, language quality, latency, and fallback behaviour. Re-run evaluations whenever prompt, provider, model, taxonomy, or safety policy changes. Human reviewers must approve launch thresholds.

## Decisions required

- Testing budget/tools, target browsers/devices, accessibility target (recommended: WCAG 2.2 AA), performance targets, and local language UAT participants.
- Penetration-test provider/scope and remediation deadline.
- Release approval roles, acceptable severity thresholds, and change-freeze/incident procedures.

## Phase 2 automated coverage

The implemented suite covers professional profile editing, selection of active practice-area/language/locality records, profile completion and publication gates, public visibility rules, verification submission, required-evidence validation, staff approval, rejection-reason validation, suspension/revocation, review history, private document access, and staff-only verification management. Existing Phase 1 account, authentication, dashboard-role, public-page, and health tests remain part of the suite.

## Phase 3 automated coverage

The suite covers directory visibility/search/filtering, public profile eligibility, consultation submission, status-event creation, client and advocate object ownership boundaries, withdrawal, start-review and acceptance transitions, decline-reason validation, and practice-area restrictions. Tests use only isolated test-database records and no real client or advocate data.
