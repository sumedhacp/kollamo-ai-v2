# AGENTS.md — Permanent Engineering Contract

## Project Identity

**Kollamo.ai** is an academic MCA-level Malayalam-English sentiment analysis and audience-intelligence platform engineered for regional and code-mixed social media comments (Malayalam script, Manglish / Romanized Malayalam, English, and Malayalam-English code-mixing).

The platform ingests YouTube comment threads, classifies sentiment into five rigorous categories (Positive, Negative, Neutral, Mixed, Unsupported), provides English translations for readability, computes audience-level aggregation metrics, and offers an interactive analytics dashboard with PDF reporting.

---

## Authoritative Rule Precedence System

When determining engineering rules, development behavior, and product requirements for Kollamo.ai, the following strict 7-level precedence hierarchy governs:

```text
Level 1: System / Platform Constraints (Highest)
    ↓
Level 2: Current Explicit User Instruction
    ↓
Level 3: More-Specific Repository Rules (Scoped)
    ↓
Level 4: Root Repository Rules (AGENTS.md)
    ↓
Level 5: Project Specification
    ↓
Level 6: Approved Architecture Decisions (ADRs)
    ↓
Level 7: Recommended Engineering Practices (Advisory)
```

### Level 1 — System / Platform Constraints
**Highest priority.** These include host OS capabilities, fundamental execution constraints, security sandboxes, and immutable runtime boundaries. System and platform constraints cannot be overridden by project files, repository rules, or user project instructions.

### Level 2 — Current Explicit User Instruction
The user's latest explicit instruction takes precedence over older project preferences, prior decisions, and root documentation when there is an intentional or genuine conflict. Explicit instructions must never be silently ignored.

### Level 3 — More-Specific Repository Rules
A rule located closer to the affected code or module takes precedence over a broader rule.
For example:
```text
root AGENTS.md
    ↓
frontend/AGENTS.md
    ↓
frontend/components/AGENTS.md
```
A more-specific applicable rule overrides a broader repository rule within its designated scope.

### Level 4 — Root Repository Rules
`AGENTS.md` defines the general, permanent engineering contract for Kollamo.ai across all modules. It governs:
- System architecture & module boundaries
- Coding conventions & style standards
- Security requirements & credential management
- Git workflow, branch strategy, and commit conventions
- Testing expectations & test coverage tiers
- Prohibited implementation shortcuts (e.g. no heuristic/fake sentiment)
- Repository directory structures & file organization
- Mandatory technology choices (Google MuRIL, FastAPI, React/Vite, PostgreSQL, Redis, Celery)

*Distinction*: Root repository rules answer: **HOW** should Kollamo.ai be developed?

### Level 5 — Project Specification
The approved Kollamo.ai technical project specification defines the functional product scope. It determines:
- Required product features
- Supported input formats (YouTube URLs, Malayalam script, Manglish, English, code-mixed)
- Expected workflows (real-time sandbox, batch ingestion, progress polling, report generation)
- Required outputs (5 sentiment classes, approval metrics, script telemetry, PDF exports)
- Specified core technologies
- Stated constraints and boundaries

*Distinction*: The project specification answers: **WHAT** should Kollamo.ai do?
*Rule*: Do not interpret examples or targets as guaranteed implementation results.

### Level 6 — Approved Architecture Decisions
Approved Architectural Decision Records (`docs/adr/`) or equivalent documented decisions must be followed when the specification leaves an architectural decision open (e.g. database schema structure, service boundaries, Celery queue topologies, adapter contracts).
*Rule*: An ADR cannot silently redefine or contradict a higher-priority mandatory product requirement from the specification.

### Level 7 — Recommended Engineering Practices
Useful suggestions and engineering enhancements that represent industry best practices, but are **not mandatory requirements**.
Examples:
- Docker Compose containerization
- Playwright end-to-end automation
- Additional CI/CD stages
- Extensive debug logging
- Storybook component isolation
- Advanced Redis cache layers
- Extra developer documentation
- Additional developer tooling

*Rule*: Recommendations must **never** be treated as phase blockers unless explicitly promoted to **REQUIRED** by a higher-priority rule.

---

## Conflict Resolution Framework

If two instructions, rules, or documents conflict:
1. **Apply the higher-priority level**: Strictly follow the 7-level precedence hierarchy above.
2. **Apply specificity**: Prefer the more-specific applicable repository rule over a broader rule (Level 3 over Level 4).
3. **Honor current user intent**: Prefer the latest explicit user instruction when it intentionally changes an earlier decision (Level 2).
4. **Never ignore silently**: Identify the contradiction, document it, and resolve it using this hierarchy.
5. **Document architectural decisions**: If an architectural ambiguity requires resolution, record the rationale in `docs/adr/` or `docs/spec-assumptions.md`.
6. **No personal preference**: Engineering decisions must never be based on arbitrary personal preference or informal assumptions.

---

## Distinguishing REQUIRED from RECOMMENDED

Every major project instruction, task, and feature must be classified into one of two categories:

### 1. REQUIRED
The implementation **must** satisfy this requirement before the relevant phase can be considered complete.
**Mandatory criteria include:**
- Explicitly specified project features and user workflows
- Required API behavior and standardized response envelopes
- Required security protections (input sanitization, rate limiting, SSRF guardrails)
- Explicitly mandated core technologies (Google MuRIL, FastAPI, React, PostgreSQL, Redis, Celery)
- Phase dependencies (must be satisfied before dependent phases can complete)
- Genuine ML inference (strict prohibition of fake/heuristic sentiment dictionaries or if/else rules)
- The 5 canonical sentiment classes (`positive`, `negative`, `neutral`, `mixed`, `unsupported`)
- Server-side secret and credential isolation (`.env` only, never leaked to client)
- Mandatory test suites passing (unit, integration, and type checks)
- Explicit current user instructions

### 2. RECOMMENDED
Useful improvements and engineering practices that should be implemented when practical, but **must NOT block phase completion** unless explicitly promoted to REQUIRED.
**Advisory items include:**
- Docker and multi-container deployment stacks
- Advanced CI/CD pipeline automation
- Storybook component explorer
- Additional performance micro-optimizations
- Extra APM telemetry or distributed tracing
- Advanced multi-tiered caching
- Additional developer guides and runbooks
- Optional UI animations or polish

### 3. Important: Do Not Over-Implement
- Do **NOT** turn every recommendation into a mandatory task.
- If a task is not explicitly required by:
  1. A higher-priority instruction (Level 1–2),
  2. A repository rule (Level 3–4),
  3. The project specification (Level 5), or
  4. An approved architecture decision (Level 6),
  it must be treated as **RECOMMENDED**.
- Do not spend significant implementation time on optional infrastructure when required project functionality is incomplete.

---

## Project Specification Interpretation Taxonomy

When reading the Kollamo.ai specification or project prompts, statements must be strictly classified into:

### 1. REQUIRED PRODUCT BEHAVIOR
The system **must** implement this feature or behavior. It is mandatory for phase completion.

### 2. TARGET / GOAL
Treat this as a quantitative objective that must be empirically measured rather than an automatic guarantee.
*Rule*: If the specification mentions a target accuracy (e.g. 85%+ or 90%+), do **NOT** claim that accuracy unless rigorous testing on a held-out test split empirically demonstrates it. Real baseline measurements take precedence over unverified targets.

### 3. EXAMPLE
Examples illustrate expected behavior, sample payloads, or representative edge cases.
*Rule*: Examples do **not** automatically create additional mandatory requirements or constrain general inputs.

### 4. IMPLEMENTATION RECOMMENDATION
A suggested implementation approach or library.
*Rule*: A suggested approach may be replaced if an equivalent or superior implementation satisfies the actual requirement, unless the specification explicitly mandates the specific technology choice.

---

## Specification Access Fallback Procedure

If the original Kollamo.ai specification is accessible:
**USE IT AS THE PRIMARY PRODUCT SOURCE (Level 5).** Do not replace it with general engineering knowledge.

If the specification is NOT accessible in the current repository/environment:
**DO NOT invent missing requirements.** Follow this strict fallback order:
```text
Existing repository implementation
        ↓
AGENTS.md / applicable repository rules
        ↓
Existing approved ADRs / architecture decisions
        ↓
Explicit current user instructions
        ↓
Previously approved phase decisions
        ↓
General engineering judgment
```

When operating under this fallback:
1. Clearly identify that the original specification is unavailable.
2. Do not claim that inferred requirements came from the specification.
3. Record important assumptions in `docs/spec-assumptions.md`.

---

## Prohibition on Fabricating Requirements

If a requirement cannot be confirmed from the specification or approved project decisions:
**DO NOT invent or fabricate it.**

Specifically, do **NOT** assume or introduce:
- Additional user roles (e.g. admin panels, RBAC, editor accounts)
- Additional sentiment categories (strictly the 5 canonical classes)
- Additional ML models or unauthorized architectures
- Additional unprompted APIs or external webhooks
- Additional dashboard features or chat widgets
- Additional authentication requirements (e.g. login walls for public analysis)
- Additional deployment infrastructure

Instead, classify the item as:
```text
Unknown / Assumption / Recommendation
```
and continue only if it is safe to do so. If a missing requirement blocks implementation, report it as a blocker instead of inventing a solution.


---

## Engineering Principles

1. **Modular Architecture**: Decouple frontend, API, asynchronous workers, ML inference, and data storage.
2. **Readable Code**: Maintain idiomatic, documented code across TypeScript, Python, and SQL. Preserve comments and docstrings.
3. **Typed Interfaces**: Enforce end-to-end typing using TypeScript interfaces on the frontend and Pydantic v2 schemas on the backend.
4. **Testable Services**: Write unit, integration, and mocked external API tests for every service layer.
5. **Minimal Duplication**: DRY principles across schemas, utility modules, and UI component primitives.
6. **Secure Configuration**: Strictly isolate secrets and credentials in environment variables (`.env`). Never commit credentials or expose them to client bundles.
7. **Reproducible ML**: Version datasets, preprocessing logic, model weights, hyperparameters, random seeds, and evaluation metrics.
8. **Observable Background Jobs**: Asynchronous pipelines must expose real-time status, deterministic state transitions, and granular logging.
9. **Accessible UI**: Strictly adhere to WCAG 2.1 AA accessibility guidelines, semantic HTML, ARIA attributes, keyboard navigation, and tap targets.
10. **Responsive UI**: Flawless layout and usability across mobile, tablet, and desktop viewports.
11. **No Fake Production Data**: Never fabricate mock progress, artificial accuracy, or synthetic production results.

---

## ML & NLP Rules

1. **No Heuristic / Fake Sentiment**:
   - Never use hard-coded sentiment dictionaries, keyword matching, static sentiment word lists, or if/else sentiment rules.
   - Sentiment inference must execute through Google MuRIL (Multilingual Representations for Indian Languages) fine-tuned with PyTorch and Hugging Face Transformers.
   - Do not train MuRIL from scratch; utilize the pre-trained MuRIL backbone with custom classification head.
2. **Evaluation Integrity**:
   - Never fabricate evaluation metrics.
   - Never claim 90–100% accuracy unless experimentally validated on a held-out test split.
   - Measure and document: Accuracy, Macro Precision, Macro Recall, Macro F1, Weighted F1, Per-Class F1, Confusion Matrix, and Validation Loss.
   - Establish baseline using TF-IDF + Logistic Regression before deep model comparison.
3. **Reproducibility**:
   - Log random seed, learning rate, batch size, gradient accumulation steps, max sequence length, preprocessing version, and Git commit SHA for every training run.
4. **Safe Preprocessing**:
   - Permitted: Unicode normalization (NFKC), whitespace normalization, URL removal, mention cleanup, repeated-character normalization, and safe transliteration normalization.
   - Forbidden: Stripping critical Malayalam characters, removing semantic negation markers, or destructive token truncation.
5. **Text Preservation**:
   - Always retain and store the original raw comment text alongside preprocessed tokens and English translations.
6. **Separation of Concerns**:
   - Strict separation between model training pipelines (`ml/training/`) and API runtime inference (`backend/app/ml/` and `ml/inference/`). Never train models inside web API request handlers.
7. **Probabilities Interpretation**:
   - Present classification probabilities as model confidence distributions over classes, not literal percentages of emotion contained in human text.

---

## API Rules

1. **Strict Input Validation**:
   - Validate all external requests using Pydantic schemas. Reject malformed JSON, empty strings, oversized payloads (>5000 chars for single comment), and invalid YouTube URLs.
2. **Predictable Errors**:
   - Return RFC 7807 problem details or consistent `{ "error": { "code": string, "message": string, "details": any } }` response envelopes.
3. **Security & Secrets**:
   - Never leak API keys, database credentials, or secret tokens.
   - Never expose internal tracebacks or raw database errors to clients in production mode.
4. **CORS & Environment**:
   - Configure CORS origins explicitly through environment variables.
5. **Health Checks**:
   - Provide `GET /api/health` with connectivity checks for database, Redis, and ML model readiness.

---

## Background Jobs & Ingestion Rules

1. **State Persistence**:
   - Background jobs must transition through deterministic states:
     - `queued`
     - `running`
     - `completed`
     - `failed`
     - `cancelled`
   - Real progress (`processed_comments` / `total_comments`) must be tracked; never simulate fake progress bars.
2. **Idempotency & Batching**:
   - Tasks must be idempotent where practical.
   - Process comments in micro-batches to optimize GPU/CPU memory and database writes.
   - Load ML models once per worker process; never reload weights per comment.
3. **YouTube Data API v3 Compliance**:
   - Use the official YouTube Data API v3 exclusively; never scrape YouTube HTML.
   - Handle pagination tokens, quota exhaustion, comment disabled/deleted errors, duplicate comments, and network retries gracefully.
   - Never expose YouTube API keys to frontend clients.

---

## UI / UX Rules

1. **Design System & Tokens**:
   - Modern, professional, clean SaaS aesthetic.
   - Use Tailwind CSS with consistent spacing, typography, and elevation tokens.
   - Accessible component library (Radix UI / shadcn style primitives).
2. **Sentiment Color Palette**:
   - Positive: Emerald / Green (`#10B981` / semantic token)
   - Negative: Rose / Red (`#EF4444` / semantic token)
   - Neutral: Slate / Gray (`#64748B` / semantic token)
   - Mixed: Amber / Orange (`#F59E0B` / semantic token)
   - Unsupported: Zinc / Muted (`#71717A` / semantic token)
   - *Never rely on color alone*: Always accompany color with explicit text labels and semantic icons.
3. **State Completeness**:
   - Every view and interactive widget must implement four states:
     1. Loading (skeletons / accessible spinners)
     2. Empty (clear calls-to-action or guidance)
     3. Success (rich, structured presentation)
     4. Error (actionable recovery message)
4. **Cognitive Load**:
   - Avoid excessive gradients, neon glows, intrusive glassmorphism, or gratuitous animations.
   - Keep the homepage clear and non-technical; reserve deep metrics for the audience dashboard.

---

## Database Rules

1. **Migration-First**:
   - All schema modifications must occur via Alembic migrations. Never alter database tables manually or silently in code.
2. **Relational Integrity**:
   - Enforce foreign key constraints, explicit indexing on queried columns (e.g. `job_id`, `video_id`, `sentiment`), and UUID primary keys.
3. **Core Entities**:
   - `analysis_jobs`
   - `videos`
   - `comments`
   - `predictions`
   - `summary_metrics`
   - `model_versions`

---

## Git Workflow & Version Control

1. **Branch Strategy**:
   - `main`: Production-ready, stable branch.
   - Phase branches:
     - `phase/01-foundation`
     - `phase/02-ml`
     - `phase/03-backend`
     - `phase/04-ingestion`
     - `phase/05-async`
     - `phase/06-integration`
     - `phase/07-dashboard`
     - `phase/08-reporting`
     - `phase/09-hardening`
     - `phase/10-release`
   - Feature branches: `feat/<short-description>`
   - Bugfix branches: `fix/<short-description>`
   - Documentation: `docs/<short-description>`
2. **Conventional Commits**:
   - Format: `<type>(<scope>): <short description>`
   - Types: `feat`, `fix`, `test`, `docs`, `chore`, `refactor`, `perf`
3. **Pre-Commit Checklist**:
   1. `git status`
   2. `git diff`
   3. `git diff --check`
   4. Execute relevant test suites
   5. Secrets audit (no `.env`, no credentials, no private keys)
   6. Clean untracked files
   7. Successful local build
4. **Strict Rules**:
   - Never force-push (`git push --force`).
   - Never rewrite shared history.
   - Never push unless explicitly instructed by the user.

---

## Verification Contract

Before declaring any feature or phase complete:
1. Automated unit and integration tests must pass.
2. Static typing and lint checks must pass.
3. Production build (`npm run build` / Python packaging) must succeed.
4. Review git diff for unintended changes.
5. For UI changes, verify desktop and mobile layouts in browser, checking console logs, loading states, empty states, and error handling.

---

## Authoritative Phase Dependency Model

The single authoritative development sequence across all project phases is:

```text
PHASE 0: Foundation / Repository Setup
    ↓
PHASE 1: Frontend / UI Foundation
    ↓
PHASE 2: ML / NLP Foundation
    ↓
PHASE 3: Backend / FastAPI Foundation
    ↓
PHASE 4: YouTube Ingestion
    ↓
PHASE 5: Async Processing
    ↓
PHASE 6: Frontend ↔ Backend Integration
    ↓
PHASE 7: Audience Intelligence Dashboard
    ↓
PHASE 8: Translation + PDF Reporting
    ↓
PHASE 9: Testing + Security + Performance
    ↓
PHASE 10: Final Release
```

---

## Phase Dependency Correction: Phase 2 → Phase 3

Conflicting statements regarding Phase 2 and Phase 3 independence are permanently eliminated. There must never be a contradiction claiming that *"Phase 2 and Phase 3 are independent"* while simultaneously stating that *"Phase 3 requires Phase 2"*.

For Kollamo.ai:
```text
Phase 2 → Phase 3
```
is the sole authoritative dependency relationship.
- **Phase 2** establishes the ML/NLP foundation required by the backend (preprocessing pipelines, Google MuRIL predictor contract, baseline benchmarks, and evaluation schemas).
- **Phase 3** integrates with and consumes that established ML/NLP foundation via backend adapters (`backend/app/ml/adapter.py`).
- **Phase 3 must NOT attempt to recreate Phase 2.**

---

## Definition of Phase Dependency

A phase dependency does **not** mean that every file from the previous phase must remain immutable. It means:
> **The required output/contract of the previous phase must exist and be usable before the dependent phase is considered complete.**

For example:
- Phase 2 establishes a usable ML/NLP interface (`ml.inference.predictor.SentimentPredictor`).
- Phase 3 consumes that interface via `backend/app/ml/adapter.py` rather than duplicating or mocking ML logic.
This maintains clean, unpolluted phase boundaries.

---

## Phase Completion Gate: REQUIRED vs. RECOMMENDED Criteria

### 1. Phase Dependencies Are REQUIRED
Phase dependencies are **mandatory**. They must **never** be treated as optional recommendations:
- A later phase **cannot** be marked COMPLETE if its required dependency phase is incomplete.
- The approved linear sequence (`Phase 0 → Phase 1 → ... → Phase 10`) and contract integration (`Phase 2 → Phase 3`) are strictly enforced.

### 2. Phase Completion Gate Rule
For every development phase, requirements are strictly separated:
- **REQUIRED**: Items that must be completely implemented, tested, and verified before the phase can be signed off. A phase is COMPLETE when all REQUIRED items are satisfied.
- **RECOMMENDED**: Desirable improvements that may remain open or deferred without blocking the start or completion of subsequent phases. Deferred recommendations must be recorded in `docs/phase-status.md` rather than silently forgotten.

A phase may be marked **COMPLETE** only when all 7 gate criteria are verified:
1. All REQUIRED work and features are finished.
2. All REQUIRED tests, verification suites, and type-checks pass cleanly.
3. All REQUIRED build outputs and documentation artifacts exist.
4. All documented prerequisite dependency conditions are fully satisfied.
5. No known blocking issues remain.
6. The Git working state is reviewed and verified clean (`git diff --check`).
7. `docs/phase-status.md` accurately reflects the verified state and records any deferred recommendations.

*Rule*: Do **NOT** mark a phase complete merely because its code exists.

### 3. Recommended Work Does Not Create Blocking Dependencies
A recommended feature must **NOT** become a phase dependency unless explicitly promoted to **REQUIRED** by a higher-priority rule.
Optional enhancements (e.g. Storybook, advanced CI/CD stages, optional caching tiers, extra telemetry, additional documentation) must not block subsequent phases unless project rules explicitly classify them as required.
