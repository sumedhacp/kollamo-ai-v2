# Kollamo.ai — Malayalam-English Sentiment & Audience Intelligence

[![Release: v1.0.0](https://img.shields.io/badge/Release-v1.0.0-blue.svg)](CHANGELOG.md)
[![CI](https://github.com/sumedhacp/kollamo-ai-v2/actions/workflows/ci.yml/badge.svg)](https://github.com/sumedhacp/kollamo-ai-v2/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Node: 20+](https://img.shields.io/badge/Node-20%2B-green.svg)](https://nodejs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-blue.svg)](https://www.typescriptlang.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](docker-compose.yml)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.2-EE4C2C.svg)](https://pytorch.org/)
[![HuggingFace](https://img.shields.io/badge/MuRIL-google%2Fmuril--base--cased-yellow.svg)](https://huggingface.co/google/muril-base-cased)

**Kollamo.ai** is an academic Master of Computer Applications (MCA) platform designed for fine-grained sentiment analysis and audience intelligence across regional Indian social web conversations. Specifically tailored for **Malayalam script**, **Manglish** (Romanized Malayalam), **English**, and **Malayalam-English code-mixed comments**, Kollamo.ai provides high-throughput ingestion of YouTube video comment threads, asynchronous neural classification, English translations for readability, and an executive audience intelligence dashboard.

> **Development Status**: **Release Ready (v1.0.0)**. All development phases (Phases 0 through 10) are complete, fully hardened, and verified with 295 automated tests, comprehensive security defenses, and empirical multi-scale benchmarks.

---


## 🏛️ System Architecture

```mermaid
flowchart TD
    subgraph Client ["Frontend (React + Vite + TypeScript)"]
        UI_Home["Landing Page"]
        UI_Sandbox["Single Comment Sandbox"]
        UI_Analyze["YouTube Ingestion Trigger"]
        UI_Dashboard["Audience Dashboard & PDF Report"]
    end

    subgraph API ["API Layer (FastAPI)"]
        HealthRoute["GET /api/health"]
        SentimentRoute["POST /api/sentiment"]
        AnalyzeRoute["POST /api/analyze"]
        JobRoute["GET /api/analyze/:jobId"]
    end

    subgraph Workers ["Distributed Worker Pool (Celery + Redis)"]
        YT_Ingest["YouTube Data API v3 Ingestion"]
        Preprocessor["Unicode & Transliteration Cleaner"]
        InferenceEngine["MuRIL Neural Classifier Head"]
        TranslationSvc["Translation Service (MarianMT / Lexicon)"]
        Aggregator["Audience Metric Aggregator"]
    end

    subgraph Storage ["Persistence Layer"]
        PG[(PostgreSQL Database)]
        RedisCache[(Redis Broker & Cache)]
    end

    UI_Sandbox -->|Single Text| SentimentRoute
    UI_Analyze -->|Video URL & Sample Size| AnalyzeRoute
    SentimentRoute -->|Direct Inference| InferenceEngine
    AnalyzeRoute -->|Enqueue Job| RedisCache
    RedisCache --> Workers
    Workers --> PG
    UI_Dashboard -->|Poll / Stream Status| JobRoute
    JobRoute --> PG
```

---

## 🌟 Core Features

- **Multilingual & Code-Mixed NLP**: Robust sentiment analysis across pure Malayalam (`മലയാളം`), Manglish (`adipoli movie aayirunnu`), standard English, and complex code-mixed expressions.
- **Five-Class Sentiment Taxonomy**:
  - `Positive` — Admiration, praise, satisfaction.
  - `Negative` — Criticism, dissatisfaction, anger.
  - `Neutral` — Factual, informational, or objective queries.
  - `Mixed` — Co-occurring positive and negative sentiments.
  - `Unsupported` — Unintelligible text, pure noise, or unsupported languages.
- **Google MuRIL Foundation**: Powered by `google/muril-base-cased` fine-tuned for regional Dravidian code-mixed nuances with reproducible training checkpoints. No heuristic dictionaries or fake fallback predictions.
- **Official YouTube Data API v3 Ingestion**: Configurable comment extraction (50, 100, 250, 500, or ALL comments) supporting Most Liked, Newest, and Oldest sort modes with pagination and quota resilience.
- **Asynchronous Scalability**: Celery + Redis architecture ensuring zero UI freeze or FastAPI blocking during multi-thousand comment processing.
- **Audience Intelligence Dashboard**: Real-time distribution charts, sentiment vs. engagement analysis, Net Sentiment Approval Index (+60%), and multifaceted filtering.
- **Translation & Reporting**: Original comment preservation with English translations and publication-quality PDF report generation using `jsPDF` and ReportLab.

---

## 📂 Repository Structure

```text
kollamo-ai-v2/
├── .agents/                    # Antigravity agent configuration
├── .github/                    # CI/CD workflows and issue templates
├── backend/                    # FastAPI application & Celery workers
│   ├── alembic/                # Database migrations
│   ├── app/
│   │   ├── api/                # API routes and endpoints
│   │   ├── core/               # Configuration, security & rate limiting
│   │   ├── db/                 # Database engine & session management
│   │   ├── models/             # SQLAlchemy ORM models
│   │   ├── schemas/            # Pydantic v2 validation models
│   │   ├── services/           # Ingestion, sentiment, translation & reports
│   │   └── workers/            # Celery task definitions
│   ├── tests/                  # Backend unit & security & benchmark tests
│   └── requirements.txt        # Production Python dependencies
├── docker/                     # Production Dockerfiles (backend & worker)
├── docs/                       # Comprehensive documentation & ADRs
├── frontend/                   # React + Vite + TypeScript frontend
│   ├── e2e/                    # Playwright E2E journey specifications
│   ├── src/                    # UI components, pages, hooks, services, tests
│   ├── Dockerfile              # Multi-stage Nginx production container
│   ├── nginx.conf              # SPA reverse proxy configuration
│   └── package.json            # Node.js dependencies
├── ml/                         # ML training, data, models, and tests
├── docker-compose.yml          # Five-tier container orchestration
├── docker-compose.prod.yml     # Production stack with resource limits
├── .env.example                # Environment variable configuration template
├── AGENTS.md                   # Permanent engineering contract
├── CHANGELOG.md                # Version changelog
└── README.md                   # Project overview & documentation
```

---

## 🚀 Getting Started

### Option A: Quickstart via Docker Compose (Recommended)

Run the entire 5-tier production stack (PostgreSQL, Redis, FastAPI backend, Celery worker, and Nginx frontend) with a single command:

```bash
# 1. Clone repository & configure environment
git clone https://github.com/sumedhacp/kollamo-ai-v2.git
cd kollamo-ai-v2
cp .env.example .env

# 2. Build and run multi-container stack
docker compose up -d --build

# 3. Access the platform
# Web Application: http://localhost
# API Documentation: http://localhost:8000/docs
# Health Check: http://localhost:8000/api/health
```

---

### Option B: Local Development Setup

#### Prerequisites
- **Python**: 3.12 (or 3.10+)
- **Node.js**: 20+ (or 18+ LTS)
- **PostgreSQL**: 16+ (or local SQLite fallback)
- **Redis**: 7+

#### 1. Backend & ML Setup
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate | Linux/macOS: source .venv/bin/activate
pip install -r backend/requirements.txt
pip install -r backend/requirements-dev.txt

# Start FastAPI server
uvicorn backend.app.main:app --reload --port 8000
```

#### 2. Redis & Celery Worker Setup
```bash
# Start Redis (via Docker or local daemon)
docker run -d --name kollamo-redis -p 6379:6379 redis:7-alpine

# Start Celery worker pool
celery -A backend.app.workers.tasks.celery_app worker --loglevel=info --concurrency=2
```

#### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
# Frontend accessible at http://localhost:5173
```

#### 4. API Keys & Optional Configuration
- **YouTube Data API v3**: Set `YOUTUBE_API_KEY` in `.env` to enable live video comment ingestion. If not provided, single-comment sandbox and mock bulk data analysis remain fully operational.
- **Translation Engine**: Configurable via `TRANSLATION_SERVICE=marianmt` or `nllb` with in-memory caching.
- **PDF Reporting**: Client-side high-fidelity PDF export powered by `jsPDF` and `html2canvas` directly from the dashboard.

---

## 🧪 Testing & Verification

Kollamo.ai enforces a multi-tier testing pyramid with **295 automated tests passing (100%)**:

```bash
# 1. Run Backend Pytest Suite (177 tests)
python -m pytest backend/tests

# 2. Run ML Pipeline Pytest Suite (49 tests)
python -m pytest ml/tests

# 3. Run Dedicated Regression, Security & Performance Suites
python -m pytest backend/tests/test_phase9_regression.py backend/tests/test_phase9_security.py backend/tests/test_phase9_performance.py -v

# 4. Run Frontend Vitest & Integration Journey Tests (69 tests)
cd frontend && npm test -- --run

# 5. Strict TypeScript Typecheck & Production Build
npm run type-check
npm run build
```

---

## 📚 Academic Documentation & Handoff

Detailed guides for viva voce defense, architectural decisions, and repository handoff:

- **[Viva Voce Preparation & Technical Defense Guide](docs/VIVA_PREPARATION.md)**: Direct, verified answers for 10 evaluation domains.
- **[Project Handoff & Maintenance Runbook](docs/PROJECT_HANDOFF.md)**: Complete operational handoff, architecture, and maintenance guide.
- **[REST API Contract Specification](docs/api.md)**: FastAPI endpoints, Pydantic schemas, and error contracts.
- **[Machine Learning Pipeline & Model Card](docs/ml-pipeline.md)**: MuRIL architecture, tokenizer details, and evaluation metrics.
- **[Testing Strategy & Quality Pyramid](docs/testing.md)**: Unit, integration, security, and performance test suites.
- **[Security Audit & Defense Analysis](docs/security-audit.md)**: CORS, input sanitization, API secret protection, and dependency audit.
- **[Empirical Performance Benchmarks](docs/performance.md)**: Latency, throughput, and memory measurements across 50 to 3,500+ comments.

---

## ⚠️ Known Limitations (Honest Disclosures)

- **Environment Scope**: Tested and hardened locally and within Docker multi-container environments; not deployed to public multi-region cloud infrastructure.
- **User Authentication**: Single-tenant academic architecture without user logins (JWT/OAuth2) or multi-tenant workspace isolation.
- **YouTube API Quotas**: Ingestion is constrained by Google's default 10,000 units/day quota.
- **Translation Purpose**: Translation is designed as an advisory English reading aid; original Malayalam/Manglish text remains the immutable ground truth.
- **Batch Processing Limits**: Empirically validated locally up to 3,500 comments; larger datasets require horizontal Celery worker scaling.

---

## 📜 Development & Git Workflow

This project adheres strictly to **Conventional Commits** and organized phase branches:

- `main`: Final stable release (`v1.0.1`).
- `developer`: Main integration and active staging branch.
- `feature/phase-0-foundation` through `feature/phase-10-release-readiness`: Dedicated feature branches tracking each developmental milestone.

---

## ⚖️ Academic License & Ethics

This project is submitted in partial fulfillment of the Master of Computer Applications (MCA) degree. All YouTube data ingestion strictly adheres to YouTube API Terms of Service. Sentiment predictions are probabilistic model estimates and should not be construed as absolute emotional judgments.
