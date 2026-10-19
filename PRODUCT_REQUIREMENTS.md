# Legal Connect — Product Requirements

## 1. Product purpose

Legal Connect helps people in Chikodi and nearby areas find a suitable advocate, explain a legal concern, request a consultation, schedule it, communicate safely, and exchange relevant documents. It is a directory and case-intake platform; it is not a substitute for legal advice, a court filing system, or an outcome-guarantee service.

The first production release should support a small, trusted local network of advocates and a simple client experience on mobile devices.

## 2. Users and permissions

| User | Core capabilities |
| --- | --- |
| Visitor | Browse public advocate profiles and service categories; search by location and language; begin registration. |
| Client | Maintain a profile, submit a consultation request, choose/accept an appointment, message an advocate after a request is accepted, upload and manage documents, receive notifications. |
| Advocate | Apply and submit verification material, manage a professional profile, set availability, receive and accept/decline consultation requests, manage appointments, message assigned clients, access authorised documents. |
| Admin | Review verification applications, manage categories/localities, moderate profiles and abuse reports, audit sensitive actions, and resolve operational issues. |

Use role-based access control, plus object-level checks: an advocate must never see another advocate's client request or documents; an admin receives only the minimum access necessary for operational duties.

## 3. MVP scope

1. Client, advocate, and administrator accounts.
2. A searchable public directory of **verified and published** advocates.
3. Advocate verification application and manual administrator review.
4. Consultation requests with structured details, status tracking, and advocate accept/decline actions.
5. Advocate availability, temporary slot holds, and mutually confirmed appointments.
6. Authenticated, server-managed messaging for an accepted consultation request, with in-app and email notifications.
7. Private, authorised document upload and download.
8. Administrative dashboards for verification, disputes/abuse signals, content, and audit history.
9. Configurable local safety/help-resource information, abuse reporting, and an operational escalation workflow.

## 4. Explicitly out of scope for MVP

- Online court filing, case management for court proceedings, e-signature, or document drafting.
- Handling client money: fees, escrow, payment processing, refunds, and advocate payouts.
- Anonymous forums, social networking, and unmoderated user-generated content.
- Automated legal advice, legal conclusions, case-outcome predictions, or fully automatic advocate approval/rejection.
- Integrated video calling, call recording, live location tracking, or a native mobile application.
- Multi-tenant law-firm workspaces and organisation-level billing.
- Broad regional/national launch features before local operations are proven.
- AI features: legal-issue classification, advocate recommendation, natural-language search, and client-problem summarisation.
- Broadcasting a request, multi-advocate requests, shortlist invitations, payments, refunds, or payouts.
- WhatsApp, SMS, and push notifications.

## 5. Core user workflows

### Client

1. Browse or search verified and published advocates by legal area, language, locality, consultation mode, and availability.
2. Register and verify contact details; complete only the profile data needed for service delivery.
3. Select exactly one advocate for a consultation request.
4. Describe the issue, select a category if known, give preferred consultation mode/time, and optionally attach documents.
5. Submit a request and see its status. The client may withdraw it until the agreed policy cutoff.
6. When an advocate accepts, coordinate through the request message thread and confirm an offered appointment slot.
7. Attend the consultation outside the platform or by a later-approved integration; retain request history and authorised documents.

### Advocate

1. Register and submit an advocate verification application.
2. After approval, complete profile, practice areas, languages, service localities, consultation modes, and availability.
3. Receive a request notification; review only the minimum intake needed for a conflict/capacity check. Request documents remain unavailable until acceptance/conflict clearance under the approved workflow.
4. Accept, decline with a predefined neutral reason, or propose an appointment time within the response window.
5. Communicate with the client through the request thread, maintain availability, and mark appointment outcomes using non-sensitive operational statuses.
6. Pause publishing or availability at any time; update profile changes that require re-review.

### Admin

1. Review verification applications against an approved internal checklist and record the decision/reason.
2. Publish, suspend, or request updates to advocate profiles according to policy.
3. Manage legal categories and localities; handle abuse reports and account recovery/support cases.
4. Review audit logs and operational metrics without routinely opening user communications or documents.
5. Use a documented break-glass process for exceptional document/message access, with legitimate reason, required authorisation, audit trail, and periodic review. Admins are never ordinary conversation participants.

## 6. Advocate verification workflow

1. Advocate creates an account and confirms their contact channel(s).
2. They provide professional profile details and upload required evidence to a private verification application.
3. The system performs format/completeness checks only. Evidence requirements and checklist fields are configurable; the system does not claim that verification is legally conclusive.
4. An authorised reviewer records a review event and may request information, approve, or reject with a controlled reason.
5. On approval, the advocate receives a verification status and may publish their profile; public discovery requires both a completed platform verification workflow and `published` status.
6. Material profile/licence changes, complaints, expiry, periodic re-review, or an approved administrative decision may return the profile to review, suspension, or revocation. Private evidence is never public.

**Decision requiring confirmation:** the exact evidence, registry checks, validity interval, reviewer roles, handling of Bar Council enrolment details, and any obligation to verify the advocate's right to practise must be defined with qualified local legal/compliance advice. Until then, this workflow is a product process, not a statement of legal sufficiency.

## 7. Consultation request workflow

Request states: `draft → submitted → under_review → accepted | declined | withdrawn | expired → closed`.

Appointment states are independent: `proposed → confirmed | rescheduled | cancelled | completed | no_show`.

- A client can save a draft, then submit it to one selected advocate only.
- Submission freezes an immutable intake snapshot and creates an audit event; the client may later add a clearly versioned update.
- The advocate receives an alert and conducts a conflict/capacity check using only the minimum approved intake. They can accept, decline, or let the request expire. Never reveal a private decline reason beyond approved client-facing wording.
- Acceptance/conflict clearance unlocks the request conversation and its authorised request documents. An appointment becomes confirmed only after the defined mutual-confirmation rule.
- Expired, declined, and withdrawn requests remain with the client; the client may create a new request to another advocate. Phase 1 does not route or broadcast it automatically.

## 8. Appointments and availability

- Advocates define weekly recurring windows in the initial scheduling timezone, Asia/Kolkata, plus leave/blockout and one-off exceptions. Phase 1 supports only `in_person` and `phone` modes.
- The server calculates discrete slots using configured duration, buffer, minimum notice, booking horizon, and a temporary hold with a defined expiry. Store instants in UTC and retain the booking-time display timezone; later profile-timezone changes never silently alter existing appointments.
- A client requests a preferred time or accepts a proposed slot. A database-level concurrency rule must prevent overlapping confirmed appointments.
- Confirmation, cancellation, rescheduling, no-show, and completion are appointment events with timestamps, actors, reason codes where appropriate, and notifications to both parties.
- Do not expose an advocate's full private calendar. Show only bookable slots. Exact in-person location stays private until the defined confirmation stage and must never default to a private home address.

## 9. Messaging and notifications

- One conversation belongs to one accepted consultation request; only the client and assigned advocate may participate.
- Support authenticated server-managed messages, history, timestamps, unread state, controlled attachments, rate limits, abuse reporting, and retention-policy support. Use encryption in transit and appropriate encryption at rest; Phase 1 does not use end-to-end encryption.
- Notifications are events, not the source of truth: in-app notifications are canonical and email is the only external delivery channel in Phase 1.
- Do not include detailed legal matter content or document links in email or any future external notification channel. Send a generic alert that leads to authenticated in-app content.

## 10. Pages and navigation

### Public

- Home: purpose, search, how it works, safety/legal disclaimers.
- Find an advocate: filters and result list.
- Advocate profile: name, professional photo, completed platform-verification status, practice areas, experience, languages, service areas, consultation modes, availability summary, professional description, platform reviews/ratings where enabled, and request CTA. No personal phone number, private address, or verification evidence is public by default.
- Sign in/register, privacy policy, terms, support, and accessibility/help pages.

### Client portal

- Dashboard: active requests, upcoming appointments, unread messages, actions needed.
- Find advocates; recommendation results; advocate profile.
- New/edit request; request detail/timeline; messages; appointment detail; documents; notifications; profile and privacy settings.

### Advocate portal

- Dashboard; verification status/application; profile editor; availability; request inbox/detail; appointment calendar/list; messages; authorised documents; notifications; account/security settings.

### Admin portal

- Verification queue/detail; advocate management; user support; category/locality management; moderation/abuse reports; audit-log viewer; operational metrics; system configuration.

Keep the primary mobile navigation short: Dashboard, Find/Requests, Appointments, Messages, Profile. Use contextual links rather than duplicating every route in global navigation.

## 11. Safety and emergency boundary

Legal Connect is not an emergency-response service. Public and authenticated surfaces must show an appropriate emergency disclaimer, provide a reporting mechanism, support configurable local help resources, and route abuse/safety reports through a defined human escalation process. Phase 1 has no AI urgency classification.

## 12. Product success measures

- Percentage of submitted requests receiving a timely advocate response.
- Time from advocate application to review decision.
- Request-to-confirmed-appointment conversion.
- Appointment cancellation/no-show rate.
- Directory search success, request-to-appointment conversion, and client-reported match quality.
- Security/support indicators: unauthorised-access incidents, document scan failures, abuse report resolution time, and notification delivery health.

Metrics must use minimised, aggregated data and must not train AI or market to users without a documented lawful basis and consent decision.

## 13. Decisions required before implementation

1. Launch boundary: exact localities, languages, consultation modes, and support hours.
2. Verification policy, evidence list, source-of-truth checks, renewal cadence, review SLA, appeals, and compliance owner.
3. The precise request conflict-check fields, document-unlock point, request close policy, and decline/expiry wording.
4. Appointment hold duration, confirmation timeout, cancellation/rescheduling/no-show rules, and location-disclosure stage.
5. Data controller/processor roles, privacy notice, retention periods, deletion/export policy, and where data may be hosted.
6. Email consent/opt-out wording and notification templates; other channels are deferred.
7. Public advocate-profile policy, including whether platform reviews/ratings are enabled at launch and their moderation/dispute rules.
8. Emergency disclaimer, reporting, safety escalation workflow, and local help-resource owner.
9. Payments remain excluded from MVP; the future commercial model may be decided later.

## Phase 2 implementation status

Phase 2 delivers the advocate professional-profile and verification foundation. Advocates can complete a private/publicly separated profile, select administrator-managed practice areas, languages, localities, and in-person/phone modes, then submit configurable professional evidence for staff review. A profile is public only when it is complete, actually verified, and explicitly published. Consultation, appointment, messaging, payments, AI, and notification workflows remain out of scope.

## Phase 3 implementation status

Phase 3 delivers advocate discovery and a private consultation-request workflow. The directory exposes only complete, verified, and published advocate profiles and supports name/headline/description search plus practice-area, language, service-area, consultation-mode, sorting, and pagination filters. A client may submit a minimal request to one selected advocate, then view or withdraw it. The selected advocate alone can start review, accept, or decline with a required reason. Every state change records an audit event. Requests are not appointments, conversations, documents, payments, notifications, or representations.

## Client-profile implementation status

Every client account receives a private profile on registration. Clients can edit their own display name and optional preferred language and locality through an authenticated profile page. Language and locality choices are drawn from administrator-managed active taxonomy records. Client profile values are not public and are not automatically disclosed to advocates; information sharing remains governed by the consultation workflow.
