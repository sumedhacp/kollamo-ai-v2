# Kollamo.ai — Release Notes (v1.0.0)

## Overview
**Kollamo.ai v1.0.0** is the first stable, release-ready distribution of the Malayalam-English Sentiment & Audience Intelligence platform. Kollamo.ai enables content creators, researchers, and media analysts to analyze Malayalam script (`മലയാളം`), Manglish (Romanized Malayalam), English, and code-mixed comments from YouTube video threads with high throughput and academic rigor.

---

## 🌟 Key Capabilities & Architectural Highlights

### 1. Fine-Grained Five-Class Sentiment Analysis
- **Standardized Taxonomy**: Preserves an immutable 5-class contract across the entire stack:
  - `Positive` — Admiration, approval, praise, satisfaction.
  - `Negative` — Criticism, disappointment, dissatisfaction, anger.
  - `Neutral` — Factual, informational, neutral commentary.
  - `Mixed` — Co-occurring positive and negative sentiments within a single review.
  - `Unsupported` — Unintelligible text, noise, or unsupported languages.
- **Zero Fake Predictions**: Strictly rejects mock fallbacks or heuristic random guesses when ML engines are uninitialized or offline. Returns explicit RFC error envelopes (HTTP 503 `MODEL_NOT_READY` / `MODEL_UNAVAILABLE`).
- **Probability Invariants**: All five class probabilities are guaranteed to be normalized floats in `[0.0, 1.0]` summing to 1.0 (within `1e-3` tolerance), labeled strictly as probabilities rather than emotional intensity.

### 2. Official YouTube Data API v3 Ingestion
- **Official API Integration**: Direct integration with Google's official YouTube Data API v3 endpoints; strictly zero HTML scraping.
- **URL Normalization**: Canonical 11-character video ID extraction supporting standard (`youtube.com/watch?v=...`), short (`youtu.be/...`), embed (`/embed/...`), and YouTube Shorts (`/shorts/...`) URLs.
- **Configurable Ingestion**: Flexible comment thresholds (50, 100, 250, 500, ALL) with sort order options (`Most Liked`, `Newest`, `Oldest`).
- **Verbatim Text Preservation**: Preserves original comment text without destructive stripping of emojis, punctuation, or Malayalam glyphs.
- **Quota & Error Handling**: Graceful degradation with typed exceptions for private videos, disabled comments, missing auth keys, and API quota exhaustion.

### 3. Asynchronous Task Processing (Celery + Redis)
- **Non-Blocking Architecture**: Long-running ingestion and batch sentiment inference jobs are dispatched to Celery background workers over Redis.
- **Real-Time Polling & Telemetry**: FastAPI immediately returns HTTP 202 Accepted with a unique `job_id`. Clients poll status through structured stages:
  - `QUEUED` → `FETCHING_VIDEO` → `FETCHING_COMMENTS` → `SENTIMENT_ANALYSIS` → `FINALIZING` → `COMPLETED` / `FAILED`.
- **Fault Recovery**: Task retries with exponential backoff and jitter, late acknowledgments (`acks_late=True`), prefetch limits (`prefetch_multiplier=1`), and 30-minute hard task limits.

### 4. Audience Intelligence Dashboard
- **Executive Analytics**: Key metric cards including Total Analyzed Comments, Sentiment Breakdown, Net Sentiment Approval Index, and Script Distribution (Malayalam vs. Manglish vs. English).
- **Interactive Visualizations**: Recharts-powered responsive sentiment distribution (donut/bar views), linguistic breakdown, and sentiment vs. engagement impact correlation.
- **Comment Intelligence Explorer**: Real-time substring search, sentiment category filter chips with live counts, script filtering, and paginated comment inspection with detailed breakdown modals.
- **Data Portability**: Instant client-side CSV and JSON exports for offline research.

### 5. Translation & English Readability
- **Advisory English Translations**: On-demand per-comment and batch translation to assist non-Malayalam speaking researchers and stakeholders.
- **Immutable Source of Truth**: Original comment text remains the authoritative record; translations are treated strictly as an auxiliary readability layer.
- **Lifecycle State Machine**: Transparent state tracking (`NOT_REQUESTED`, `PENDING`, `COMPLETED`, `FAILED`, `NOT_NEEDED`). Plain English comments automatically bypass translation (`NOT_NEEDED`).
- **In-Memory Caching**: High-performance LRU cache yielding >30x speedup (<0.1ms) for repeated comment strings.

### 6. Publication-Grade PDF Reporting
- **Automated Report Generation**: High-fidelity client-side PDF document generation using `jsPDF` and ReportLab.
- **Comprehensive Structure**: Header overview, video metadata summary, Net Sentiment Approval Index badge, full 5-class distribution table, and sample comments organized by sentiment.
- **Unicode Support & Layout**: Preserves Malayalam font rendering and cleanly wraps long text across multi-page layouts with sanitized filename exports (`kollamo-ai-analysis-<video-id>.pdf`).

---

## 🔒 Security Hardening

- **SSRF Protection**: Strict regex validation (`^[a-zA-Z0-9_-]{11}$`) rejects internal loopback IPs (`127.0.0.1`), metadata IPs (`169.254.169.254`), and dangerous URI schemes (`file://`, `ftp://`).
- **XSS Neutralization**: Comment text is rendered strictly as plain text via React JSX default escaping; zero instances of `dangerouslySetInnerHTML`.
- **Credential Protection**: Public health probes (`/api/health`) and metadata endpoints (`/`) guarantee zero disclosure of server credentials, database connection strings, or API keys.
- **Sliding-Window Rate Limiting**: In-memory rate limiting middleware restricts traffic to 120 requests/minute per client IP, returning RFC-compliant HTTP 429 envelopes with `Retry-After: 60`.
- **Stack Trace Sanitization**: Global exception handlers intercept unhandled server exceptions, logging full tracebacks to internal server stderr and returning sanitized HTTP 500 responses without exposing code paths or database queries.

---

## ⚡ Empirical Performance Benchmarks

All performance metrics were verified using automated micro-benchmarks and heap profiling (`tracemalloc`):

- **Single-Comment Sentiment Latency**: Average < 15 ms, P95 < 45 ms.
- **Batch Inference Throughput**: > 750 comments/second (micro-batches of 64).
- **Large Dataset Processing (3,500+ comments)**: Completed in < 5 seconds.
- **Peak Memory Allocation (3,500 comments)**: < 30 MB heap memory.
- **Translation LRU Cache Speedup**: > 30x speedup (~3.5 ms cold vs < 0.1 ms cached).
- **Summary Metrics Rollup**: 3,500 classified comments aggregated in < 15 ms.
- **Frontend Production Bundle**: ~336 KB gzipped JavaScript.

---

## 🧪 Quality Gates & Verification

- **Backend Pytest Suite**: 177 tests passing (100%).
- **ML Pipeline Pytest Suite**: 49 tests passing (100%).
- **Frontend Vitest Suite**: 69 tests passing (100%).
- **TypeScript Strict Mode**: 0 errors (`tsc --noEmit`).
- **Total Automated Tests**: **295 tests passing (100%)** with 0 regressions.

---

## ⚠️ Known Limitations & Deployment Notes

1. **Google YouTube API Quota**: Production high-volume comment ingestion requires an active Google Cloud YouTube Data API v3 key with sufficient daily quota units.
2. **GPU Acceleration**: Benchmarks were measured on CPU vectorization. Production deployments handling millions of daily comments can leverage CUDA acceleration by setting `ML_DEVICE=cuda`.
3. **Translation Scope**: Translation support is optimized for Malayalam/Manglish-to-English readability; other Indian language families are outside current scope.
4. **Third-Party Build Tooling Advisories**: `npm audit` flagged low-risk development advisories in `tailwindcss` and `vite` that require breaking major upgrades (`tailwindcss@4`, `vite@8`). These are isolated to build tooling and do not impact runtime production assets.
