# Changelog — Kollamo.ai

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.9.0] - 2026-10-07

### Added
- Multi-tier translation service abstraction (`backend/app/services/translation_service.py`) supporting Malayalam script, Romanized Malayalam (Manglish), English, and Malayalam-English code-mixed comments.
- Direct colloquial Manglish lexicon for idiomatic movie review expressions (e.g. *padam thooki*, *pwoli*, *kidilan padam*, *valare bore*, *paisa nashtam*) ensuring guaranteed accuracy and sub-millisecond execution.
- Orthographic normalization for phonetic variations in Romanized Malayalam spelling.
- Dedicated translation endpoint `POST /api/translate` with input validation, confidence scoring, and source/script metadata.
- Comprehensive audience intelligence report generation schemas and service (`backend/app/schemas/report.py`, `backend/app/services/report_service.py`).
- Structured report endpoint `GET /api/analyze/{job_id}/report` and downloadable PDF document streaming endpoint `GET /api/analyze/{job_id}/report/pdf` built with ReportLab.
- Background/batch comment translation endpoint `POST /api/analyze/{job_id}/translate-comments`.
- Client-side multi-page PDF report generation utility (`frontend/src/utils/pdfGenerator.ts`) powered by jsPDF featuring Kollamo.ai branding, video metadata, Net Sentiment Approval Index, 5-class distribution table and bars, script breakdown, exemplary comments, technical methodology, and academic disclaimer.
- Full PDF export and batch comment translation integration in `frontend/src/pages/Dashboard.tsx` with loading spinners, feedback alerts, and server fallback.
- Added 7 new frontend Vitest tests in `frontend/src/test/reporting.test.tsx` (31/31 Vitest tests passing) and 13 new backend pytest tests in `backend/tests/test_translation.py` and `backend/tests/test_report.py` (65/65 pytest tests passing).

---

## [0.8.0] - 2026-10-07

### Added
- Complete Audience Intelligence Dashboard in `frontend/src/pages/Dashboard.tsx` with rich analytics, script breakdowns, and drill-down controls.
- Net Sentiment Approval Index computing spread between positive and negative reactions with categorical consensus badges (`Overwhelmingly Positive`, `Predominantly Favorable`, `Mixed / Divided`, `Critical`).
- Multi-view chart analytics with tab switcher toggling between 5-class distribution and linguistic script breakdown (Malayalam, Latin, Code-Mixed).
- Discussion theme chips extracting high-frequency discussion topics (BGM/Music, Direction, Acting, Pacing, Theatres) enabling 1-click filtering.
- Comments Intelligence Explorer with multi-attribute filtering (sentiment, script, free text), sort order selection (Likes, Confidence, Recent), author avatars, and client-side pagination (10 per page).
- Instant client-side JSON and CSV data exports with formatted filename metadata.
- Pre-loaded academic demonstration dataset (`frontend/src/data/sampleJob.ts`) allowing full offline exploration of video intelligence without external API dependency.
- Dedicated backend endpoint `GET /api/analyze/{job_id}/comments` with query filtering (sentiment, script, search, pagination).
- Eager-loading and mapping of comments and predictions in `JobService.format_job_status_response`.
- 7 new Vitest dashboard unit & integration tests (`frontend/src/test/dashboard.test.tsx`, 24 total frontend tests passing) and 2 new pytest endpoint tests (37 backend tests, 52 total pytest tests passing).

---

## [0.7.0] - 2026-10-07

### Added
- Frontend API client service layer (`frontend/src/services/api.ts`) with typed endpoints for health, sentiment inference, job creation, and telemetry polling.
- Standardized `ApiError` class with RFC error envelope parsing, status codes, and connection failure handling.
- Real-time job polling hook (`frontend/src/hooks/useJobPolling.ts`) with configurable intervals, status transition callbacks, and error recovery.
- Live backend connection status indicator (`frontend/src/components/ui/api-status.tsx`) integrated into navigation bar.
- Connected Comment Sentiment Sandbox (`frontend/src/pages/Sandbox.tsx`) to live `POST /api/sentiment` inference endpoint with 5-class distribution bars and English translation display.
- Connected YouTube Analysis page (`frontend/src/pages/Analyze.tsx`) to live `POST /api/analyze` and real-time polling pipeline with 5-stage progress lifecycle indicators, video metadata preview, and navigation CTAs.
- Integrated Audience Intelligence Dashboard (`frontend/src/pages/Dashboard.tsx`) with dynamic `job_id` query parameter loading, summary metric cards, interactive distribution charts, and comment intelligence table.
- Vite development server proxy configuration (`frontend/vite.config.ts`) routing `/api` requests to backend at `http://localhost:8000`.
- Comprehensive frontend integration test suite (`frontend/src/test/integration.test.tsx`) covering API layer, Sandbox live inference, Analyze real-time polling, and Dashboard telemetry (17/17 Vitest tests passing).

---


## [0.6.0] - 2026-10-06

### Added
- Celery asynchronous application configuration (`backend/app/workers/celery_app.py`) with Redis message broker and result backend.
- Background task pipeline `process_youtube_analysis_job` and `run_analysis_pipeline` with micro-batching (`batch_size=32`).
- Asynchronous inference engine loading ML weights once per worker process with zero in-request training.
- Live progress tracking updating `processed_comments` and `total_comments` atomically in PostgreSQL.
- Audience intelligence metric rollup engine computing 5-class distribution percentages and engagement like metrics per sentiment.
- Job completion and error handling transitions (`queued` -> `running` -> `completed` / `failed`).
- Worker fallback endpoint `POST /api/analyze/{job_id}/process` for direct pipeline execution.
- High-throughput micro-batching benchmark fixture verifying 3,500+ comments processed with verified percentages and metrics.
- 6 new tests in `test_celery_tasks.py`, `test_async_benchmark.py`, and `test_analyze.py` (50 total passing tests).

---


## [0.5.0] - 2026-10-06

### Added
- Official YouTube Data API v3 asynchronous client (`backend/app/services/youtube_client.py`).
- Robust pagination loop with `nextPageToken` and requested sample size cutoff (50, 100, 250, 500, all).
- Sort mode mapping (`top` -> `relevance`, `newest` -> `time`, `oldest` -> chronological ordering).
- Granular domain exceptions: `YouTubeVideoNotFoundError`, `YouTubeCommentsDisabledError`, `YouTubeQuotaExceededError`, `YouTubeAuthError`, and `YouTubeNetworkError`.
- Exponential backoff with jitter and retry mechanism for transient 5xx HTTP server errors.
- Ingestion orchestrator (`backend/app/services/ingestion_service.py`) extracting video metadata and comment threads into PostgreSQL.
- Raw text preservation and automatic Malayalam/Latin script detection on ingestion.
- Trigger endpoint `POST /api/analyze/{job_id}/ingest` with mapped RFC error responses (401, 403, 404, 429).
- 15 comprehensive unit and mocked integration tests across YouTube API client, ingestion pipeline, and API endpoints.

---

## [0.4.0] - 2026-10-06

### Added
- Complete FastAPI backend application in `backend/app/` with non-blocking async architecture.
- Centralized configuration system in `backend/app/core/config.py` using Pydantic Settings loading from `.env`.
- Structured logging configuration in `backend/app/core/logging.py` with automatic credential and token sanitization filter.
- Async SQLAlchemy 2.0 database engine, session factory, and `get_db` dependency in `backend/app/db/session.py`.
- 6 relational database entity models in `backend/app/models/` (`Video`, `AnalysisJob`, `Comment`, `Prediction`, `SummaryMetric`, `ModelVersion`).
- Alembic database migration environment and template (`backend/alembic.ini`, `backend/alembic/env.py`).
- Pydantic v2 validation schemas in `backend/app/schemas/` for health telemetry, sentiment requests/responses, analysis jobs, and RFC error envelopes.
- ML Sentiment inference service (`backend/app/services/sentiment_service.py`) loading ML checkpoints once at application startup with zero in-request training.
- Job persistence service (`backend/app/services/job_service.py`) for YouTube video metadata tracking and job dispatch.
- Health check endpoint `GET /api/health` monitoring PostgreSQL, Redis, and ML engine readiness.
- Single-comment sentiment analysis endpoint `POST /api/sentiment` with strict character limits (5000 chars), non-empty validation, and 5-class distribution output.
- Batch analysis ingestion endpoints `POST /api/analyze` (202 Accepted) and `GET /api/analyze/{job_id}`.
- Standardized error exception handlers preventing internal tracebacks or secrets from leaking to clients.
- 14 automated backend pytest tests passing across health, sentiment, and analysis job endpoints.

---

## [0.3.0] - 2026-10-06

### Added
- Complete multilingual ML/NLP pipeline in `ml/` for Malayalam, Manglish, Code-mixed, and English comments.
- Preprocessing module (`ml/preprocessing/cleaner.py`) with Unicode NFKC normalization, URL/mention sanitization, repeated character collapse, and zero-width joiner preservation.
- Language and script detector (`ml/preprocessing/detector.py`) identifying Malayalam, Latin, Mixed, and Unknown scripts.
- Curated multi-script research corpus (`ml/data/corpus.json`) covering 5 classes and 8 linguistic phenomena.
- Dataset loader with stratification, inverse frequency class weights, and strict zero-data-leakage verification.
- Classical TF-IDF + Logistic Regression baseline benchmark (`ml/models/baseline_model.py`) establishing 33.3% accuracy / 0.3371 Macro F1 baseline.
- Google MuRIL transformer neural classifier architecture (`ml/models/muril_classifier.py`) with 768-dim pooled representations, LayerNorm, Dropout, and 5-class linear head.
- Training loop (`ml/training/trainer.py`) with AdamW, linear warmup scheduler, and model checkpointing.
- Evaluation metrics engine (`ml/evaluation/metrics.py`) and 8-phenomenon linguistic error analyzer (`ml/evaluation/error_analyzer.py`).
- Inference predictor engine (`ml/inference/predictor.py`) enforcing the probability interpretation contract (not percentages of emotion).
- Comprehensive pytest test suite (15 unit tests passing).
- Detailed documentation: `docs/ml-pipeline.md`, `docs/evaluation.md`, and `docs/model-card.md`.

### Planned for Phase 4 (v0.5.0)
- YouTube Data API v3 integration with pagination and quota management.

### Planned for Phase 5 (v0.6.0)
- Celery + Redis asynchronous background task queue.

### Planned for Phase 6 (v0.7.0)
- Frontend-backend integration with real-time job progress polling.

### Planned for Phase 7 (v0.8.0)
- Audience intelligence dashboard with interactive charts, metrics, and filtering.

### Planned for Phase 8 (v0.9.0)
- Replaceable translation service abstraction and PDF report export.

### Planned for Phase 9 (v1.0.0-rc1)
- Comprehensive end-to-end testing, security hardening, and performance benchmarking.

### Planned for Phase 10 (v1.0.0)
- Production containerization and release readiness.

---

## [0.2.0] - 2026-10-06

### Added
- Complete React + Vite + TypeScript frontend shell in `frontend/`.
- Tailwind CSS configuration with semantic sentiment color palette (Positive, Negative, Neutral, Mixed, Unsupported).
- Routing structure via React Router:
  - `/` (Home landing page with hero, problem section, supported languages, 3-step workflow, and CTA).
  - `/sandbox` (Single comment testing tool with live script detection, character counter, and multi-state result panel).
  - `/analyze` (YouTube comment ingestion configuration with sample sizes 50-ALL, sorting modes, URL validation, and execution panel).
  - `/dashboard` (Audience Intelligence Dashboard skeleton with 6 summary cards, charts, and filterable comments table).
  - `*` (Accessible 404 handler).
- 12 accessible UI primitives: `Button`, `Input`, `Textarea`, `Card`, `Badge` (with `SentimentBadge`), `Alert`, `Modal`, `Table`, `Tabs`, `Skeleton`, `Progress`, `EmptyState`.
- Zero fake AI predictions guarantee in sandbox and dashboard skeletons per `AGENTS.md`.
- Comprehensive Vitest unit and integration test suite (8 tests passing).
- Production build verified (`dist/` bundle created cleanly).

---

## [0.1.0] - 2026-10-06

### Added
- Initial project scaffolding and directory architecture.
- Permanent engineering contract in `AGENTS.md`.
- Workspace directives in `GEMINI.md`.
- Antigravity project rules in `.agents/rules/` (`engineering-standards.md`, `ml-rules.md`, `api-rules.md`).
- Antigravity workflow skills in `.agents/skills/` (`kollamo-pipeline`, `muril-sentiment`).
- Global environment configuration template in `.env.example`.
- Comprehensive `.gitignore` configuration for Python, Node, Vite, and PyTorch artifacts.
- Architecture documentation in `docs/architecture.md` and documentation outlines.
- Initial Architectural Decision Record `docs/adr/ADR-001-system-architecture.md`.
- Phase dependency and lifecycle tracking document in `docs/phase-status.md`.
- GitHub issue templates (`bug_report.md`, `feature_request.md`).
- GitHub pull request template (`pull_request_template.md`).
- GitHub Actions CI workflow skeleton (`.github/workflows/ci.yml`).
