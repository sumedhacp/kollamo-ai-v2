# Kollamo.ai — Project Handoff & Maintenance Guide

## 1. Project Purpose
**Kollamo.ai** is an academic Master of Computer Applications (MCA) capstone platform engineered for fine-grained sentiment analysis and audience intelligence on Malayalam, Manglish (Romanized Malayalam), English, and code-mixed YouTube comments.

Unlike generic sentiment analysis tools that only handle pure English and ternary (`Positive`/`Negative`/`Neutral`) classifications, Kollamo.ai:
- Solves vocabulary fragmentation in Malayalam script (`മലയാളം`) and out-of-vocabulary loss in Manglish.
- Adopts a verified **5-class sentiment taxonomy** (`Positive`, `Negative`, `Neutral`, `Mixed`, `Unsupported`).
- Ingests public YouTube comment threads using the official **Google YouTube Data API v3**.
- Executes asynchronous neural batch classification via **Celery and Redis**.
- Provides on-demand English translation as an advisory reading aid.
- Renders an executive audience intelligence dashboard and exports publication-ready PDF reports.
- Upholds a strict **Zero Fake AI** policy: if ML models are uninitialized or missing weights, it raises explicit HTTP 503 errors rather than fabricating heuristic sentiment.

---

## 2. Architecture Overview

```mermaid
flowchart TD
    subgraph Client ["Frontend (React 18 + Vite + TypeScript)"]
        UI_Home["Landing Page"]
        UI_Sandbox["Single Comment Sandbox"]
        UI_Analyze["YouTube Ingestion Trigger"]
        UI_Dashboard["Audience Dashboard & PDF Report"]
    end

    subgraph API ["API Layer (FastAPI + Pydantic v2)"]
        HealthRoute["GET /health & /api/health"]
        SentimentRoute["POST /api/v1/sentiment"]
        AnalyzeRoute["POST /api/v1/analysis/jobs"]
        JobRoute["GET /api/v1/analysis/jobs/{job_id}"]
        TranslateRoute["POST /api/v1/translate"]
    end

    subgraph Workers ["Worker Pool (Celery + Redis)"]
        YT_Ingest["YouTube Data API v3 Ingest"]
        Preprocessor["Unicode & Transliteration Cleaner"]
        InferenceEngine["MuRIL Neural Classifier Head"]
        TranslationSvc["Translation Service"]
        Aggregator["Audience Metric Aggregator"]
    end

    subgraph Storage ["Persistence Layer"]
        PG[(PostgreSQL / SQLite)]
        RedisCache[(Redis Broker & LRU Cache)]
    end

    UI_Sandbox -->|Direct text| SentimentRoute
    UI_Analyze -->|Video URL & sample limit| AnalyzeRoute
    SentimentRoute -->|Direct sync inference| InferenceEngine
    AnalyzeRoute -->|Enqueue job| RedisCache
    RedisCache --> Workers
    Workers --> PG
    UI_Dashboard -->|Poll job status| JobRoute
    JobRoute --> PG
    UI_Dashboard -->|Request translation| TranslateRoute
```

---

## 3. Repository Structure

```text
kollamo-ai-v2/
├── .agents/                    # Antigravity agent configuration and workflows
├── .github/                    # GitHub Actions CI/CD workflows and issue templates
├── backend/                    # FastAPI backend and Celery worker implementation
│   ├── alembic/                # Database migrations (PostgreSQL / SQLite)
│   ├── app/
│   │   ├── api/                # API routers (/health, /sentiment, /analyze, /translate)
│   │   ├── core/               # App configuration, security, CORS, rate limiting
│   │   ├── db/                 # Database engine, base model, async sessions
│   │   ├── models/             # SQLAlchemy ORM models (Video, Comment, AnalysisJob)
│   │   ├── schemas/            # Pydantic v2 validation contracts
│   │   ├── services/           # Ingestion, sentiment, translation & PDF reporting
│   │   └── workers/            # Celery task definitions (tasks.py)
│   ├── tests/                  # Backend unit, security, regression & benchmark tests
│   ├── requirements.txt        # Backend production Python dependencies
│   └── requirements-dev.txt    # Testing, linting, and development dependencies
├── docker/                     # Production Dockerfiles (backend & Celery worker)
├── docs/                       # Comprehensive documentation, ADRs & viva guides
│   ├── adr/                    # Architecture Decision Records
│   ├── api.md                  # REST API contract specification
│   ├── architecture.md         # Technical architecture details
│   ├── evaluation.md           # Model evaluation and benchmarks
│   ├── ml-pipeline.md          # MuRIL fine-tuning and inference pipeline
│   ├── performance.md          # Multi-scale latency and load benchmarks
│   ├── security-audit.md       # Security review, CORS, XSS, and hardening
│   ├── testing.md              # Quality pyramid test plan and results
│   ├── VIVA_PREPARATION.md     # MCA Viva Voce questions & technically accurate answers
│   └── PROJECT_HANDOFF.md      # This document
├── frontend/                   # React 18 + Vite + TypeScript frontend
│   ├── e2e/                    # Playwright end-to-end integration journeys
│   ├── src/
│   │   ├── components/         # Reusable UI components (SentimentBadge, Navbar, etc.)
│   │   ├── pages/              # View pages (Home, Sandbox, Dashboard)
│   │   ├── services/           # Frontend API client and PDF generator
│   │   ├── types/              # TypeScript interfaces matching backend schemas
│   │   └── tests/              # Vitest component & integration test suites
│   ├── Dockerfile              # Multi-stage production Nginx container
│   ├── nginx.conf              # SPA routing reverse proxy configuration
│   └── package.json            # Frontend Node dependencies and scripts
├── ml/                         # ML scripts, datasets, model card & offline benchmarks
│   ├── models/                 # Model architectures, tokenizers, and weights path
│   ├── tests/                  # ML pipeline pytest test suite
│   └── requirements.txt        # PyTorch & HuggingFace dependencies
├── docker-compose.yml          # Multi-container orchestration (5 services)
├── docker-compose.prod.yml     # Production stack with resource limits
├── .env.example                # Canonical environment variable template
├── AGENTS.md                   # Permanent engineering contract & governance
├── CHANGELOG.md                # Version changelog
└── README.md                   # Main project overview and getting started guide
```

---

## 4. Environment Variables Reference

| Variable Name | Required? | Default / Example | Purpose / Security Notes |
| :--- | :--- | :--- | :--- |
| `ENVIRONMENT` | Yes | `development` | Set to `production` in live deployments to disable debug error traces. |
| `DEBUG` | No | `False` | Toggles verbose error handling. Must be `False` in production. |
| `APP_SECRET_KEY` | Yes | *Generate random hex* | Cryptographic salt for token signing and internal session state. |
| `BACKEND_HOST` | No | `0.0.0.0` | Host IP address for Uvicorn server binding. |
| `BACKEND_PORT` | No | `8000` | Port for FastAPI server. |
| `FRONTEND_URL` | No | `http://localhost:5173` | Allowed origin for frontend SPA. |
| `ALLOWED_CORS_ORIGINS`| Yes | `http://localhost:5173,http://localhost:3000` | Comma-separated list of trusted origins. Never use `*` with credentials. |
| `DATABASE_URL` | Yes | `postgresql+asyncpg://postgres:postgres@localhost:5432/kollamo_db` | Async SQLAlchemy DB URI. Supports `sqlite+aiosqlite:///./kollamo.db` for local dev. |
| `DB_POOL_SIZE` | No | `10` | SQLAlchemy connection pool size. |
| `DB_MAX_OVERFLOW` | No | `20` | Max overflow connections beyond pool size. |
| `REDIS_URL` | Yes | `redis://localhost:6379/0` | Redis broker and in-memory cache URI. |
| `CELERY_BROKER_URL` | Yes | `redis://localhost:6379/0` | Celery broker connection string. |
| `CELERY_RESULT_BACKEND`| Yes | `redis://localhost:6379/0` | Celery task result backend. |
| `YOUTUBE_API_KEY` | Optional | `AIzaSy...` | Official Google YouTube Data API v3 key. Required for live ingestion. |
| `TRANSLATION_SERVICE` | No | `marianmt` | Backend translation engine: `marianmt`, `nllb`, or `api_fallback`. |
| `TRANSLATION_API_KEY` | No | `optional_key` | API key if an external translation provider is configured. |
| `ML_DEVICE` | No | `auto` | Execution device: `cpu`, `cuda`, `mps`, or `auto`. |
| `MURIL_MODEL_PATH` | No | `google/muril-base-cased` | HuggingFace base model identifier or local directory. |
| `FINETUNED_WEIGHTS_PATH`| No | `ml/models/saved_weights/muril_sentiment_v1` | Local path to fine-tuned classification weights checkpoint. |
| `BATCH_SIZE` | No | `32` | Maximum batch size for neural classifier inference. |
| `LOG_LEVEL` | No | `INFO` | Logging granularity: `DEBUG`, `INFO`, `WARNING`, `ERROR`. |

---

## 5. Required Services

For full system execution, the following services must run:
1. **PostgreSQL Database** (`port 5432`): Persists videos, analyzed comments, and job records (or local SQLite fallback).
2. **Redis In-Memory Broker** (`port 6379`): Acts as message queue for Celery tasks and LRU cache for translations.
3. **FastAPI Backend Server** (`port 8000`): Serves REST endpoints, validates schemas, and queries jobs.
4. **Celery Worker Pool**: Consumes async analysis jobs from Redis, fetches YouTube comments, and runs ML inference.
5. **Frontend Client Application** (`port 5173` in Vite dev, `port 80` in production Nginx): React SPA interface.

---

## 6. Startup Commands

### Option A: Complete Multi-Container Stack (Docker Compose)

```bash
# 1. Clone repository
git clone https://github.com/sumedhacp/kollamo-ai-v2.git
cd kollamo-ai-v2

# 2. Setup environment variables
cp .env.example .env
# Edit .env and set your YOUTUBE_API_KEY (optional for mock datasets)

# 3. Launch all 5 containers
docker compose up -d --build

# 4. Verify running services
docker compose ps

# Web Application: http://localhost:80
# API Documentation: http://localhost:8000/docs
# API Health Check: http://localhost:8000/api/health
```

### Option B: Local Development (Separate Processes)

```bash
# Terminal 1: Start Redis & PostgreSQL (using Docker or local native services)
docker run -d --name kollamo-redis -p 6379:6379 redis:7-alpine
docker run -d --name kollamo-postgres -p 5432:5432 -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=kollamo_db postgres:16-alpine

# Terminal 2: Start FastAPI Backend
python -m venv .venv
# Windows: .venv\Scripts\activate | Linux/macOS: source .venv/bin/activate
pip install -r backend/requirements.txt -r backend/requirements-dev.txt
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 3: Start Celery Worker
# (Inside activated virtualenv)
celery -A backend.app.workers.tasks.celery_app worker --loglevel=info --concurrency=2

# Terminal 4: Start Frontend Development Server
cd frontend
npm install
npm run dev
# Frontend accessible at http://localhost:5173
```

---

## 7. Testing Commands & Verification

Kollamo.ai enforces a rigorous testing pyramid with **295 automated tests passing (100% pass rate)**:

```bash
# 1. Backend Pytest Suite (177 tests - unit, security, api, integration)
python -m pytest backend/tests

# 2. ML Pipeline Pytest Suite (49 tests - tokenizer, inference, evaluation, schemas)
python -m pytest ml/tests

# 3. Dedicated Hardening & Performance Suites
python -m pytest backend/tests/test_phase9_regression.py backend/tests/test_phase9_security.py backend/tests/test_phase9_performance.py -v

# 4. Frontend Vitest Suite (69 tests - components, pages, services, pdf export)
cd frontend
npm test -- --run

# 5. Strict TypeScript Typecheck
cd frontend
npm run type-check

# 6. Production Asset Build
cd frontend
npm run build
```

---

## 8. ML Model Information

- **Foundation Model**: `google/muril-base-cased` (Multilingual Representations for Indian Languages).
- **Classification Head**: Sequence classification head fine-tuned over 5 classes.
- **Sentiment Classes**:
  1. `Positive` (Index 0)
  2. `Negative` (Index 1)
  3. `Neutral` (Index 2)
  4. `Mixed` (Index 3)
  5. `Unsupported` (Index 4)
- **Output Contract**:
  - `sentiment`: String name of top winning class (`max(P)`).
  - `confidence`: Calibrated float in `[0.0, 1.0]`.
  - `probabilities`: Normalized float dictionary for all 5 classes summing to `1.0`.
- **Zero Fake Policy**:
  - If model weights cannot be loaded, `SentimentService` raises `ModelNotTrainedError` or `ModelLoadingError`.
  - FastAPI maps these exceptions to HTTP 503 (`MODEL_NOT_TRAINED`), never returning random or rule-based fake labels.

---

## 9. API Overview

| Method | Endpoint | Description | Status Code |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | Minimal liveness probe for load balancers. | `200 OK` |
| `GET` | `/api/health` | Deep health probe verifying DB, Redis, and ML readiness. | `200 OK` |
| `POST`| `/api/v1/sentiment` | Synchronous sentiment classification for a single comment. | `200 OK`, `422`, `503` |
| `POST`| `/api/v1/analysis/jobs` | Enqueues asynchronous YouTube video comment analysis. | `202 Accepted`, `400`, `422` |
| `GET` | `/api/v1/analysis/jobs/{job_id}` | Polls progress (`QUEUED`, `PROCESSING`, `COMPLETED`, `FAILED`). | `200 OK`, `404 Not Found` |
| `POST`| `/api/v1/translate` | Translates Malayalam/Manglish comment text to English on demand. | `200 OK`, `422` |

Interactive Swagger documentation is available at `http://localhost:8000/docs` and Redoc at `http://localhost:8000/redoc`.

---

## 10. Known Limitations (Honest Disclosures)

1. **Environment Scope**: Tested and hardened locally and in Docker container environments. Has not undergone live multi-region public cloud deployment (e.g., AWS ECS or GCP GKE).
2. **Authentication & Multi-tenancy**: No user authentication (JWT/OAuth2) or multi-tenant workspace isolation is implemented in v1.0. Analysis jobs are public to the local instance.
3. **YouTube Quota Limits**: The YouTube Data API v3 enforces a default daily quota of 10,000 units. Bulk extraction of thousands of comments consumes API quota and requires a valid user-supplied API key.
4. **Translation Scope**: Translation is designed as an advisory English readability feature with in-memory caching. Offline translation quality depends on local model availability and may fall back to verbatim presentation if models are not present.
5. **Batch Scale**: Validated locally up to 3,500 comments. Production ingestion of 50,000+ comments would require persistent horizontal Celery worker scaling and sharded PostgreSQL partitions.

---

## 11. Maintenance Runbook

### Routine Tasks
1. **Rotating YouTube API Key**: Update `YOUTUBE_API_KEY` in `.env` and restart the Celery worker and FastAPI backend.
2. **Database Migrations**:
   ```bash
   alembic revision --autogenerate -m "description_of_change"
   alembic upgrade head
   ```
3. **Flushing Redis Cache**: If translation or task cache needs clearing:
   ```bash
   redis-cli flushdb
   ```
4. **Updating Model Weights**:
   Place fine-tuned checkpoints in `ml/models/saved_weights/muril_sentiment_v1/`, update `FINETUNED_WEIGHTS_PATH` in `.env`, and restart FastAPI and Celery.

---

## 12. Deployment Notes

- **Reverse Proxy**: In production, Nginx or Traefik should sit in front of FastAPI and the Vite build, terminating SSL/TLS and enforcing rate limiting.
- **Resource Recommendations**:
  - Celery Worker (Inference): Minimum 4 GB RAM, 2 vCPUs (or NVIDIA GPU with CUDA for faster batch inference).
  - FastAPI API Server: Minimum 1 GB RAM, 1 vCPU.
  - Redis + PostgreSQL: Minimum 1 GB RAM.
- **CORS Configuration**: Ensure `ALLOWED_CORS_ORIGINS` strictly contains the exact production domain(s) to protect against unauthorized cross-origin requests.
