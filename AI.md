# Future AI Architecture (Deferred from Phase 1)

## Principle

Phase 1 contains **no AI features, AI provider, AI jobs, model calls, vector search, or AI-derived user data**. The core directory, routing, request, appointment, messaging, document, and verification flows must work without AI.

When separately approved for a later phase, AI should reduce intake friction and improve discovery; it must not provide legal advice, determine rights, predict outcomes, decide advocate verification, or make irreversible decisions. The user remains in control, advocates make professional decisions, and administrators make verification/moderation decisions.

Every later AI feature requires a consent, privacy, vendor, and evaluation decision. Each has a non-AI equivalent.

## Future architecture

```text
Client text / public query
       │
       ▼
Consent + input minimisation + redaction policy
       │
       ▼
Internal AI gateway ──► approved model provider
       │                     (no training/use retention unless approved)
       ▼
Schema validation + safety rules + confidence/quality checks
       │
       ├── user-reviewable suggestion
       ├── structured, versioned future AI output (AIJob)
       └── evaluation/audit telemetry with minimised content
```

If introduced, the gateway should be a Django domain module and asynchronous worker task, not a separate service initially. It centrally enforces provider configuration, request size limits, redaction, approved prompts, model/output versioning, timeout/retry policies, feature flags, and no-log rules.

## Deferred features

### 1. Legal issue classification

Input: a client's voluntarily supplied intake description. Output: one or more suggested practice areas, urgency/safety flag only when confidently detected, and a request for missing operational details. The client reviews/edits before submission.

Use a constrained taxonomy and structured JSON output. Never label an issue as legally valid/invalid. High-risk signals must show crisis/emergency/help guidance written and approved by humans, not an AI diagnosis; define the local escalation policy before enabling it.

### 2. Advocate recommendation

Start with explainable deterministic ranking: verified/published status, declared practice area, service locality, language, chosen consultation mode, availability, capacity/opt-in, and fair rotation/diversity rules. This is safer and more auditable than an LLM recommender.

AI may later interpret a client's wording into taxonomy/filter suggestions. It must not use protected/sensitive inferred traits, private message contents, unapproved performance scores, or opaque outcome predictions. Display why a candidate was recommended and let the client browse all matching advocates.

### 3. Natural-language search

Translate a public search query into controlled filters and semantic retrieval over **public advocate profile content only**. Hybrid retrieval is recommended: PostgreSQL full-text/filter search first, plus optional vector search only when it materially improves relevance and has a tested evaluation set.

Do not index consultation narratives, messages, documents, verification evidence, or hidden admin data for search. Search output must never promise that an advocate will take the matter.

### 4. Client problem summarisation

Generate a concise, factual, editable summary from a client's own intake text after explicit request/consent. Show it to the client before sharing with an advocate; store the final client-approved text as the operational summary and mark any machine-generated draft/version separately.

Prompts must ask for neutral facts, dates, parties as provided, requested help, and missing information—not legal advice, arguments, recommendations, or inventions. If the service cannot safely process sensitive content with the approved provider, this feature remains off.

## Controls and evaluation

- Feature flag every AI capability and default it off until approved.
- Obtain explicit product/legal review of provider terms, geography, retention, training use, subcontractors, and data-processing agreement.
- Minimise payloads, redact direct identifiers where feasible, avoid file/document ingestion in MVP, and prohibit secondary use/training without a lawful approved basis.
- Validate response schema; apply content/safety screening; give a safe fallback to ordinary category selection/search.
- Maintain a de-identified, approved test set covering local language(s), English, Kannada, mixed-language spelling, short/ambiguous queries, and unsafe prompts. Measure classification accuracy, search relevance, summary faithfulness, latency, cost, disparate impact, and harmful outputs.
- Log model/prompt/output schema versions, timing, quality signals, and user edits; do not retain raw content unnecessarily. Provide a way to report a bad result and disable a feature quickly.

## Possible later rollout order

1. Continue structured categories and deterministic advocate matching as the baseline.
2. Consider public natural-language query-to-filter suggestions only after assessment.
3. Consider client-editable classification and summary drafts after assessment and consent approval.
4. Evaluate semantic/vector search only after measuring shortcomings of public full-text search.

## Decisions requiring approval

- Approved provider/model and its data-processing/retention terms.
- Whether any sensitive legal narrative may leave the primary hosting environment.
- User disclosure, consent, opt-out, and human escalation language.
- Supported languages and quality thresholds for each language.
- Human owners for evaluation, incident response, and periodic bias/quality review.
