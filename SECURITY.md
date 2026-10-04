# Security and Privacy

## Security posture

Legal Connect will process highly sensitive personal and legal matter information. Security must be designed before feature expansion: least privilege, defence in depth, privacy by default, and auditable operations. A privacy/legal review is required to identify applicable Indian and local legal obligations; this document is an engineering baseline, not legal advice.

## Identity and access

- Use Django's mature authentication framework with verified email or phone and secure password hashing; support password reset without account enumeration. Enforce one primary public service role (`CLIENT` or `ADVOCATE`) per account; staff privileges are separate from public profiles.
- Require MFA for administrators before launch. Decide whether it is required or opt-in for advocates after testing local user access needs.
- Apply RBAC plus object-level authorisation in every view/API/query. Roles alone are insufficient for request, conversation, document, and appointment data.
- Use secure, HttpOnly, SameSite cookies for browser sessions; protect unsafe endpoints with CSRF controls. Rate-limit login, reset, registration, messaging, and document download operations.
- Record account-role changes, authentication security events, exports, private-document reads, and admin access in append-only audit logs.

## Data protection and privacy

- Collect only data needed for directory, intake, bookings, support, and approved verification. Separate public advocate data from private professional evidence and client matter data.
- Encrypt data in transit with modern TLS and at rest using managed database/object-storage encryption. Store secrets in a managed secret store, never source control or logs.
- Private documents use opaque storage keys, malware scanning before availability, server-side authorisation, short-lived signed download URLs, type/size limits, checksums, and download auditing. Phase 1 allows PDF, JPG/JPEG, and PNG only; files are quarantined until scan success and have no active-content preview.
- Establish and publish retention schedules per class: account/profile, request, message, appointment, verification evidence, audit, backup, and security logs. Apply legal holds and user deletion/export processes only after policy approval.
- Do not log message bodies, intake narratives, document names/URLs, access tokens, passwords, verification numbers, or raw AI prompts in normal application logs.
- Use clear notices and consent records for email notifications and any future optional AI processing. Consent must be withdrawable without blocking essential account/security notices. No AI processing occurs in Phase 1.

## Application and infrastructure controls

- Follow OWASP ASVS-informed controls: validated input, output encoding, parameterised ORM queries, secure file handling, CSP, security headers, clickjacking protection, dependency scanning, and secure error handling.
- Separate development, staging, and production accounts, databases, credentials, and notification providers. Production data must not be copied to developer devices or test environments.
- Apply automated backups, point-in-time recovery, restore drills, vulnerability patching, infrastructure access MFA, least-privilege cloud IAM, and network/private database controls.
- Set alerting for authentication anomalies, permission denials, bulk downloads, failed malware scans, unusual admin actions, and provider/webhook failures.
- Create a written incident response process: triage, containment, evidence preservation, impact review, required notification, remediation, and post-incident review.

## Admin and exceptional access

Admin access to content is not routine support access. Admins are never normal conversation participants. Use role tiers (verification reviewer, support, security, super-admin), mask sensitive fields by default, and require legitimate reason, required authorisation, and a time-limited documented break-glass grant for exceptional document or message access. Every grant and access must be searchable in the audit trail and reviewed periodically.

## Decisions before launch

1. Obtain privacy/compliance advice on applicable data-protection, advocate-confidentiality, and hosting/cross-border transfer requirements.
2. Approve a data classification scheme and retention/deletion schedule.
3. Select hosting region, storage provider, backup retention, encryption key ownership/rotation, and incident contacts.
4. Define verification-evidence access, reviewer training, and whether identity/professional data needs field-level encryption.
5. Approve terms, privacy notice, user consent text, grievance/contact process, and an abuse/safety escalation procedure.
6. Approve the precise point at which request documents become visible to the selected advocate after the conflict/capacity process.

## Phase 2 verification controls

Verification evidence is stored outside public URL routes and uses generated storage paths rather than user-controlled file paths. The application accepts only PDF, JPG/JPEG, and PNG evidence within the configured size limit. Every upload begins in a quarantined `PENDING` scan state; the local implementation intentionally has no scanner and never marks an upload clean automatically.

Only the owning advocate or staff may request an authorised verification-document download, and neither may download it until its scan status is explicitly `CLEAN`. Clients and other advocates receive a forbidden response. Staff verification decisions use the controlled review workflow, record actor/status/comment history, and require a comment for more-information, rejection, suspension, and revocation decisions. Direct status fields are read-only in the Django admin interface.
