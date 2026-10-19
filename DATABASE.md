# Database Design

PostgreSQL is the authoritative transactional store. Use UUID primary keys for externally exposed records, UTC timestamps, `created_at`/`updated_at`, and explicit status fields. Do not store document blobs or message attachments in database rows.

## Core identity and profile entities

| Entity | Key fields | Relationships |
| --- | --- | --- |
| User | id, email/phone identifiers, primary service role (`CLIENT` or `ADVOCATE`), auth state, last_login | Has exactly one primary client or advocate profile. Staff/admin permissions are separate and do not create a public profile. |
| ClientProfile | user_id, display name, contact preferences, locality | Belongs to User; owns consultation requests and documents. |
| AdvocateProfile | user_id, display/public name, biography, publication status, verification status, locality, modes | Belongs to User; has practice areas, languages, service localities, availability, requests, appointments. |
| AdvocateVerificationApplication | advocate_id, status, submitted_at, expires_at, policy/checklist version, current decision | Belongs to AdvocateProfile; has private verification documents and immutable reviewer history. |
| VerificationDocument | application_id, storage reference, classification, scan state, retention status | Private evidence belonging only to a verification application; never discoverable through consultation/document routes. |
| VerificationReviewEvent | application_id, reviewer, action, controlled reason, notes reference, occurred_at | Immutable review/request-information/approval/rejection/suspension/revocation history. |
| RoleAssignment | user_id, role, granted_by, active | Supports tightly controlled administrator permissions rather than treating all staff alike. |
| ConsentRecord | user_id, purpose, version, granted/withdrawn timestamps | Records affirmative choices for non-essential processing/channels. |

## Directory and taxonomy entities

| Entity | Key fields | Relationships |
| --- | --- | --- |
| PracticeArea | id, name, slug, active, parent_id (optional) | Many-to-many with AdvocateProfile; optionally assigned to requests. |
| Language | code, name, active | Many-to-many with AdvocateProfile. |
| Locality | id, name, district/region, active | Many-to-many service areas for advocates; referenced by profiles and requests. |
| AdvocatePracticeArea | advocate_id, practice_area_id, verified/display flag | Join record, permits controlled publication. |
| AdvocateServiceArea | advocate_id, locality_id | Join record. |

## Consultation and scheduling entities

| Entity | Key fields | Relationships |
| --- | --- | --- |
| ConsultationRequest | id, client_id, advocate_id, minimum-intake snapshot, private detail snapshot, category, status, submitted/response/expiry timestamps | Belongs to one client and one selected advocate; has conflict-check outcome, messages, request documents, appointments, and events. |
| RequestStatusEvent | request_id, from_status, to_status, actor, reason code, occurred_at | Immutable request-state history. Valid states: draft, submitted, under_review, accepted, declined, withdrawn, expired, closed. |
| ConflictCheck | request_id, advocate_id, status, completed_at, controlled outcome reason | Captures the pre-acceptance conflict/capacity decision without exposing unnecessary request detail. |
| AvailabilityRule | advocate_id, weekday, start/end local time, timezone, mode, slot duration, buffer, active | Recurring availability; Phase 1 timezone is Asia/Kolkata and modes are in-person/phone. |
| AvailabilityException | advocate_id, start/end UTC, kind, mode | Blocks or adds one-off availability. |
| SlotHold | advocate_id, proposed starts/ends, request_id, expires_at, held_by | Short-lived transactional hold while a client confirms a proposed time; never treated as a confirmed appointment. |
| Appointment | request_id, advocate_id, client_id, starts_at, ends_at, booking_timezone, mode, private location/contact reference, status, confirmation timestamps | One request may have appointment history. States: proposed, confirmed, rescheduled, cancelled, completed, no_show. |
| AppointmentEvent | appointment_id, action, actor, reason code, occurred_at | Immutable scheduling-state history. |

Enforce at least: valid request and appointment transitions; exactly one selected advocate per request; a conflict check before acceptance; `ends_at > starts_at`; expiry for slot holds; unique no-overlap constraint for confirmed advocate appointments (PostgreSQL exclusion constraint or transactional conflict check); and indexes on request status/assignee, appointment start time, and public directory filters.

## Communication and files

| Entity | Key fields | Relationships |
| --- | --- | --- |
| Conversation | request_id, status | Exactly one per accepted request; participants are derived from client and assigned advocate, not admin roles. |
| Message | conversation_id, sender_id, body, sent_at, read_at/recipient read state, report/moderation state, retention status | Server-managed message protected in transit and at rest; attachments use MessageAttachment. |
| Notification | user_id, type, payload reference, read_at, channel delivery states | In-app source of truth; references but does not duplicate sensitive content. |
| RequestDocument | request_id, owner_id, storage key, original filename, media type, byte size, checksum, scan/quarantine state, retention status | Consultation/request file. Access is derived from request workflow; it is not a public URL. |
| MessageAttachment | message_id, storage key, original filename, media type, byte size, checksum, scan/quarantine state, retention status | Attachment access is derived from the message's conversation. |
| ExceptionalContentAccess | target type/id, requesting staff member, authoriser, legitimate reason, granted/revoked/expiry timestamps | Narrow break-glass grant for private messages/documents, always audited and periodically reviewed. |

Phase 1 permits only PDF, JPG/JPEG, and PNG files under an approved size limit. Every file is validated and quarantined until malware scanning succeeds; unsafe files are rejected and never previewed as active content. Request-document access is derived from client ownership plus the accepted/conflict-cleared request workflow. Verification evidence and message attachments remain separate classes.

## Governance and operations

| Entity | Key fields | Relationships |
| --- | --- | --- |
| AuditEvent | actor, action, target type/id, request ID, IP/device metadata minimised, timestamp, reason | Append-only record of sensitive state changes, document access, exports, and break-glass access. |
| AbuseReport | reporter, subject, category, status, assigned admin, resolution | Moderation/support workflow. |
| DataDeletionRequest | user, requested_at, decision/status, exceptions, completed_at | Tracks deletion/export lifecycle and legal-retention exceptions. |

## Relationship summary

```text
User ──1:1── ClientProfile ──1:N── ConsultationRequest ──1:N── Appointment
  │                                  │        │
  │                                  │        ├──1:1── Conversation ──1:N── Message
  │                                  │        ├──1:N── RequestDocument
  │                                  │        └──1:1── ConflictCheck
  └──1:1── AdvocateProfile ──1:N── AvailabilityRule / AvailabilityException
                         │     └──N:M── PracticeArea, Language, Locality
                         └──1:N── AdvocateVerificationApplication ──N── VerificationDocument
```

## Data-handling constraints

- Encrypt sensitive application fields where risk assessment calls for it; passwords are never reversibly stored.
- Keep minimum conflict-check intake, private request detail, advocate-facing information, and later AI-derived data distinguishable.
- Soft deletion is not a privacy policy: use lifecycle states, legal holds, and scheduled irreversible deletion after an approved retention policy.
- Confirm local legal retention obligations before finalising fields, encryption, backup retention, or deletion timing.

## Phase 2 implementation status

Implemented profile taxonomy records are `PracticeArea`, `Language`, and `Locality`; they are administrator-managed and advocates select from active records. `AdvocateProfile` stores separate publication and verification statuses, public professional fields, a private office-address field, and profile-completion inputs.

The verification domain implements `VerificationEvidenceType`, `VerificationApplication`, `VerificationDocument`, `VerificationReviewEvent`, and `VerificationDocumentAccessEvent`. Verification documents have generated private storage paths, an original-filename record, byte-size record, replacement state, and scan status. They are not public URL resources. A document is only downloadable through an authorised application route after its status is explicitly `CLEAN`.

## Phase 3 implementation status

`ConsultationRequest` is implemented with an opaque `public_id`, one `ClientProfile`, one selected `AdvocateProfile`, minimal subject/description/practice-area/mode/locality intake, timestamps, and the states `DRAFT`, `SUBMITTED`, `UNDER_REVIEW`, `ACCEPTED`, `DECLINED`, `WITHDRAWN`, `EXPIRED`, and `CLOSED`. `RequestStatusEvent` records the actor, transition, reason, and timestamp for each application-controlled transition. This Phase 3 model has no appointment, message, document, conflict-check, payment, or notification relation.
