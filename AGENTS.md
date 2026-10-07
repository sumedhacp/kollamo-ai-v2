# AGENTS.md — Permanent Engineering Contract

## Project Identity

**Kollamo.ai** is an academic MCA-level Malayalam-English sentiment analysis and audience-intelligence platform engineered for regional and code-mixed social media comments (Malayalam script, Manglish / Romanized Malayalam, English, and Malayalam-English code-mixing).

The platform ingests YouTube comment threads, classifies sentiment into five rigorous categories (Positive, Negative, Neutral, Mixed, Unsupported), provides English translations for readability, computes audience-level aggregation metrics, and offers an interactive analytics dashboard with PDF reporting.

---

## Source Specification Hierarchy

When determining WHAT Kollamo.ai is supposed to do, use the following authoritative 6-tier order:

### SOURCE 1 — Provided Kollamo.ai Project Specification
The provided Kollamo.ai technical/project specification is the primary product-requirements source.
Use it for:
- Product scope
- Required functionality
- Supported input types
- Supported sentiment classes
- Expected workflows
- Specified technologies
- Stated constraints
- Stated project goals
- Specified outputs

Do not silently change requirements from the specification.

### SOURCE 2 — Existing Approved Repository Implementation
If the specification does not explicitly answer an implementation question, inspect the existing repository.
Existing implementation reveals decisions already made, established interfaces, existing architecture, data structures, completed phase outputs, and integration contracts.
*Rule*: Do not automatically treat existing code as a product requirement. Existing implementation is evidence of an implementation decision, not necessarily proof that the specification requires that behavior.

### SOURCE 3 — AGENTS.md and Applicable Repository Rules
Repository rules determine HOW the project should be developed (coding conventions, security rules, testing requirements, Git rules, directory conventions, implementation restrictions).
*Rule*: Repository rules do not automatically override product requirements.
- Product specification answers: **WHAT** should Kollamo.ai do?
- Repository rules answer: **HOW** should Kollamo.ai be developed?

### SOURCE 4 — Approved Architecture Decisions / ADRs
Use approved ADRs (`docs/adr/`) when the specification leaves an architectural decision open (database architecture, service boundaries, API structure, model-serving strategy, asynchronous processing strategy).
*Rule*: An ADR should not silently redefine a mandatory product requirement from the specification.

### SOURCE 5 — Explicit Current User Instruction
The user's current explicit instruction may intentionally change or clarify an earlier project decision.
If it conflicts with an older project decision, follow the rule-precedence system documented here. Do not silently ignore the user's explicit request.

### SOURCE 6 — Engineering Judgment
Use general engineering knowledge only when the above sources do not provide an answer.
*Rule*: When engineering judgment is used for a meaningful decision:
- Document the assumption in `docs/spec-assumptions.md`.
- Never present an engineering assumption as if it came from the original specification.

---

## Specification Access Fallback Procedure

If the original Kollamo.ai specification is accessible:
**USE IT AS THE PRIMARY PRODUCT SOURCE.** Do not replace it with general engineering knowledge.

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

## Specification Statement Classification

When interpreting project statements, distinguish strictly between:

1. **Required Product Behavior**:
   The specification explicitly requires the feature or behavior. This is **mandatory**.
2. **Target / Goal**:
   The specification states a target or objective (e.g. accuracy or throughput targets). Do **not** represent a target as an already-achieved result without empirical experimental evaluation.
3. **Example**:
   An example illustrates expected behavior or sample data. An example does **not** automatically create additional product requirements.
4. **Implementation Guidance**:
   A suggested implementation approach may be followed when appropriate, but must **not** be treated as a mandatory product requirement unless explicitly required.


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

## Phase Completion Gate & Recommended Work Principles

### 1. Phase Completion Gate
A phase may be marked **COMPLETE** only when all 7 criteria are satisfied:
1. Its required work is finished.
2. Its required tests and verification checks pass.
3. Its required outputs and artifacts exist.
4. Its documented dependency conditions are satisfied.
5. No known blocking issue remains.
6. The Git working state is reviewed and clean.
7. `docs/phase-status.md` reflects the actual verified state.

*Rule*: Do **NOT** mark a phase complete merely because its code exists.

### 2. Recommended Work Does Not Create Dependencies
A recommended feature must **NOT** become a phase dependency unless explicitly promoted to **REQUIRED**.
Optional enhancements (e.g. Storybook, advanced CI/CD stages, optional caching tiers, extra telemetry, additional documentation) must not block subsequent phases unless project rules explicitly classify them as required.
