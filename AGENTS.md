# AGENTS.md — Permanent Engineering Contract

## Project Identity

**Kollamo.ai** is an academic MCA-level Malayalam-English sentiment analysis and audience-intelligence platform engineered for regional and code-mixed social media comments (Malayalam script, Manglish / Romanized Malayalam, English, and Malayalam-English code-mixing).

The platform ingests YouTube comment threads, classifies sentiment into five rigorous categories (Positive, Negative, Neutral, Mixed, Unsupported), provides English translations for readability, computes audience-level aggregation metrics, and offers an interactive analytics dashboard with PDF reporting.

---

## Source of Truth

The **Kollamo.ai Technical Project Specification** and Master Prompt represent the primary product specification and single source of truth.

- In case of ambiguity, make the smallest reasonable engineering decision and document it in an Architectural Decision Record (`docs/adr/`).
- Do not invent requirements silently.
- Do not overwrite working code unnecessarily.
- Understand existing implementations before modifying them.

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
