# Production Deployment

## Target topology

Deploy one containerised Django application in a managed cloud environment with managed PostgreSQL, private encrypted object storage, and a transactional email provider. Introduce a managed queue/worker only when asynchronous email delivery, malware scanning, document processing, expiry jobs, or reminders requires it. Put managed HTTPS protection/load balancing in front of the web application; add CDN/WAF capabilities according to selected hosting and risk assessment.

```text
Internet → CDN/WAF + HTTPS load balancer → stateless Django web instances
                                              ├─ Managed PostgreSQL (private network)
                                              ├─ Optional Redis/queue (private network)
                                              ├─ Optional worker instances
                                              └─ Private object storage + malware scanner
```

Select hosting geography only after the privacy/compliance decision. Prefer managed services with IAM, encryption, audit logging, backups, and documented recovery options over self-managed servers.

## Environments

- **Local development:** synthetic data only; developer secrets are local and excluded from source control.
- **Staging:** production-like controls where feasible, isolated database/storage/provider credentials, synthetic or formally anonymised test data only.
- **Production:** isolated cloud account/project, restricted IAM, managed secrets, protected branches, and no interactive database access except approved break-glass procedures.

## Delivery pipeline

1. Pull request: formatting/linting, unit tests, dependency/security scans, and secret scanning.
2. Build an immutable, versioned container/image with a software bill of materials if supported.
3. Deploy automatically to staging; run integration/end-to-end smoke checks.
4. Approve a production release, run compatible schema migration separately, deploy a small canary/rolling release, and monitor errors/latency/jobs.
5. Roll back application image if needed. Database migrations must follow expand/contract practice and have documented rollback or forward-fix plans.

Do not deploy source directly from a developer machine. Production secrets, document storage, audit logs, and databases must never be committed to Git.

## Reliability and recovery

- Define availability and recovery objectives before launch (MVP proposal: service RTO and RPO values to be approved).
- Enable automated encrypted backups and point-in-time database recovery; lifecycle-version documents; back up configuration/IaC and audit records according to policy.
- Test restoration into an isolated environment at least before launch and periodically thereafter. A backup is not accepted until a restore test succeeds.
- Health checks cover web, database connectivity, queue backlog, worker health, malware scan pipeline, storage, and notification delivery.
- Alert on error rates, latency, failed deployments, backup failures, queue age, scan failures, suspicious access, database capacity, and expiring certificates/secrets.

## Operational requirements before real users

1. Infrastructure-as-code, least-privilege IAM, environment inventory, and documented ownership.
2. Domain/DNS, TLS, secure headers, WAF/rate-limit rules, email domain authentication, and provider webhook validation.
3. Runbooks for incident response, account recovery, document scan failure, stuck request/appointment, notification outage, database restore, and privacy requests.
4. Central structured logging/error monitoring with sensitive-field redaction, metrics dashboards, uptime monitoring, and on-call/escalation contacts.
5. Capacity and cost baseline from a staging load test; use pagination, caching, and worker limits before adding infrastructure complexity.

## Decisions required

- Cloud provider/account ownership, hosting region, budget, support/on-call arrangement, and service-level targets.
- Email provider, sender identity, template approval, and email-consent policy. SMS/WhatsApp/push are deferred.
- Malware scanning service, object-storage lifecycle/versioning policy, backup duration, and disaster-recovery test cadence.
- CI/CD provider, production approval owners, change-management expectations, and whether an external security review is required before launch.
