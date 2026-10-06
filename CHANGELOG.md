# Changelog — Kollamo.ai

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Planned for Phase 5 (v0.6.0)
- Celery + Redis asynchronous background task queue.

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
