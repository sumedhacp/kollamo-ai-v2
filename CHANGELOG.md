# Changelog — Kollamo.ai

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Planned for Phase 1 (v0.2.0)
- React + Vite + TypeScript frontend scaffolding.
- Route implementation: Home, Sandbox, YouTube Analyze, Dashboard skeleton.
- Accessible UI primitives and semantic sentiment badges.

### Planned for Phase 2 (v0.3.0)
- Multilingual preprocessing pipeline for Malayalam, Manglish, English, and code-mixed text.
- TF-IDF + Logistic Regression baseline establishment.
- Google MuRIL 5-class fine-tuning pipeline with reproducible experiment tracking.

### Planned for Phase 3 (v0.4.0)
- FastAPI core application with health check and sentiment endpoints.
- PostgreSQL / Supabase async database integration with Alembic migrations.

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
