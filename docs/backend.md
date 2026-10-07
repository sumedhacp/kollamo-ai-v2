# Backend Foundation Architecture & Run Guide — Kollamo.ai (Phase 3)

## Architectural Role and Boundaries
Phase 3 establishes the **backend foundation and ML-service integration contract** for Kollamo.ai.

> **Explicit Phase Boundary:**
> Phase 3 provides the backend foundation. YouTube ingestion, asynchronous processing, persistence, and frontend integration are implemented in later phases.

---

## 1. How to Run the FastAPI Application

### Prerequisites
- Python 3.12+ virtual environment
- Installed project dependencies (`pip install -r requirements.txt`)

### Running the Development Server
```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive OpenAPI documentation will be accessible at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI Schema**: `http://localhost:8000/openapi.json`

---

## 2. Backend Directory & Responsibility Boundaries

```text
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app creation, middleware, exception handlers, lifespans
│   │
│   ├── api/                 # Endpoint controllers and routing
│   │   ├── __init__.py
│   │   ├── router.py        # Centralized router aggregation
│   │   ├── health.py        # Subsystem readiness health checks (/api/health)
│   │   ├── sentiment.py     # Legacy sentiment endpoint (/api/sentiment)
│   │   └── routes/          # Route module layout
│   │       ├── __init__.py
│   │       ├── health.py
│   │       └── sentiment.py
│   │
│   ├── core/                # Infrastructure, configuration, logging
│   │   ├── __init__.py
│   │   ├── config.py        # Centralized Pydantic BaseSettings
│   │   ├── logging.py       # Structured logging with SensitiveDataFilter credential masking
│   │   └── rate_limiter.py  # In-memory sliding-window rate limiting
│   │
│   ├── schemas/             # Pydantic v2 request/response contracts
│   │   ├── __init__.py
│   │   ├── common.py        # ErrorDetail, ErrorResponse, HealthResponse {"status": "ok"}
│   │   ├── error.py         # Error schema aliases
│   │   ├── health.py        # Subsystem health responses
│   │   └── sentiment.py     # SentimentAnalyzeRequest, SentimentAnalyzeResponse
│   │
│   └── services/            # Application service orchestration
│       ├── __init__.py
│       └── sentiment_service.py # Bridges FastAPI to Phase 2 ModelLoader/SentimentPredictor
│
└── tests/                   # Backend test suites
    ├── test_app.py          # App startup, root, minimal health, CORS, OpenAPI
    ├── test_health.py       # API health endpoint tests
    ├── test_sentiment.py    # Sentiment baseline and validation tests
    └── test_sentiment_api.py # Full Phase 3 API contract and MODEL_NOT_TRAINED tests
```

---

## 3. Endpoints & API Contract

### Health Endpoints

#### Minimal Health: `GET /health`
A lightweight, non-blocking liveness probe indicating that the FastAPI process is running.
- **Dependencies**: None. Does not depend on database, Redis, or ML inference.
- **Response**: `200 OK`
  ```json
  {
    "status": "ok"
  }
  ```

#### Readiness Health: `GET /api/health`
Inspects subsystem connectivity (PostgreSQL, Redis broker, ML engine).
- **Response**: `200 OK`
  ```json
  {
    "status": "healthy",
    "version": "0.4.0",
    "services": {
      "database": "connected",
      "redis": "connected",
      "ml_engine": "loaded"
    },
    "timestamp": "2026-10-08T00:00:00Z"
  }
  ```

---

### Sentiment Analysis Endpoints

#### Primary Versioned Endpoint: `POST /api/v1/sentiment`
Synchronously classifies a single Malayalam, Manglish, English, or code-mixed social media comment.

#### Request Contract (`SentimentAnalyzeRequest`)
```json
{
  "text": "ഇത് വളരെ നല്ല സിനിമയാണ്"
}
```
- `text` (string, required): Cannot be null, missing, empty, or whitespace-only. Maximum 5000 characters.

#### Response Contract (`SentimentAnalyzeResponse`)
```json
{
  "original_text": "ഇത് വളരെ നല്ല സിനിമയാണ്",
  "sentiment": "Positive",
  "confidence": 0.96,
  "probabilities": {
    "Positive": 0.96,
    "Negative": 0.01,
    "Neutral": 0.01,
    "Mixed": 0.01,
    "Unsupported": 0.01
  },
  "model": {
    "name": "kollamo-muril-5class",
    "version": "v1"
  },
  "processing": {
    "processing_time_ms": 42.0
  }
}
```

The five discrete sentiment classes and probability keys are strictly:
1. `Positive`
2. `Negative`
3. `Neutral`
4. `Mixed`
5. `Unsupported`

---

## 4. Model Availability & `MODEL_NOT_TRAINED` State Handling

Kollamo.ai enforces a strict **Zero Fabricated Sentiment** policy:
1. **Reuse of Phase 2 ModelLoader**: The FastAPI backend accesses the ML layer strictly through `ModelLoader` in `ml/models/loader.py` and `SentimentPredictor` in `ml/inference/predictor.py`.
2. **Missing Fine-Tuned Weights**: If a fine-tuned model checkpoint is not provided or unavailable for production inference, the backend raises `ModelNotTrainedError`.
3. **Structured 503 Error Response**:
   Instead of returning HTTP 200 with fake predictions or heuristics, the API returns `503 Service Unavailable`:
   ```json
   {
     "error": {
       "code": "MODEL_NOT_TRAINED",
       "message": "The Kollamo sentiment model is not available for inference.",
       "details": null
     }
   }
   ```

---

## 5. Standardized Error Handling & Status Codes

| Condition | Code | HTTP Status | Description |
| :--- | :--- | :--- | :--- |
| Valid Request & Inference | - | `200 OK` | Successful sentiment classification |
| Invalid Syntax / Semantics | `INVALID_REQUEST` | `400 Bad Request` | Request violates application rules |
| Validation Failure | `VALIDATION_ERROR` | `422 Unprocessable Entity` | Pydantic validation failed |
| Untrained Checkpoint | `MODEL_NOT_TRAINED` | `503 Service Unavailable` | Model requires fine-tuning |
| Model Initialization Failure | `MODEL_UNAVAILABLE` | `503 Service Unavailable` | Checkpoint cannot be loaded |
| Inference Failure | `INFERENCE_ERROR` | `500 Internal Server Error` | Model forward pass failed |
| Unhandled Server Failure | `INTERNAL_ERROR` | `500 Internal Server Error` | Unexpected server-side failure |

---

## 6. Security & Error Handling

- **Credential Masking**: `SensitiveDataFilter` in `backend/app/core/logging.py` intercepts logs and redacts tokens, API keys, passwords, and authorization headers (`***REDACTED***`).
- **Internal Stack Trace Protection**: Unhandled exceptions are caught by `generic_exception_handler` and logged internally; clients receive a sanitized RFC-compliant error envelope with code `INTERNAL_ERROR`.
- **CORS Protection**: CORS origins are restricted to configured hosts (`settings.ALLOWED_CORS_ORIGINS`). Broad wildcard (`*`) origins in production are strictly avoided.
- **Input Sanitization**: Pydantic v2 validates size (1-5000 chars), types, and non-empty string integrity.

---

## 7. Testing

Run backend tests using pytest:
```bash
pytest backend/tests/test_health.py backend/tests/test_sentiment.py backend/tests/test_app.py backend/tests/test_sentiment_api.py -v
```

All 26 test cases execute synchronously in memory without requiring external dependencies (YouTube, Redis, Celery, or external database servers).

---

## 8. Phase 5 — Asynchronous Processing with Celery & Redis

### Architecture & Workflows
Phase 5 decouples long-running operations (YouTube comment collection and ML sentiment inference) from the FastAPI HTTP request cycle:
1. **Client** issues `POST /api/v1/analysis/jobs` with `video_url`, `comment_limit` (50, 100, 250, 500, ALL), and `sort_by` (most_liked, newest, oldest).
2. **FastAPI** generates a collision-resistant UUID `job_id`, records initial `QUEUED` state in `JobStateService`, enqueues `process_analysis_job` via Celery, and returns `202 Accepted` immediately.
3. **Celery Worker** claims the job:
   - Sets status to `PROCESSING` with progress stage `FETCHING_VIDEO`.
   - Checks Phase 2 model readiness; if `MODEL_NOT_READY`, marks job `FAILED` without fake predictions.
   - Executes Phase 4 `YouTubeIngestionService` for metadata and comments (stage `FETCHING_COMMENTS`).
   - Runs Phase 2 `SentimentInferenceService` for each comment, updating mathematical progress stage `SENTIMENT_ANALYSIS` (`completed / total * 100%`).
   - Marks job `COMPLETED` (stage `COMPLETED`, 100%) and records normalized results.
4. **Client** polls `GET /api/v1/analysis/jobs/{job_id}` to retrieve current stage progress or final analysis results.

### Local Development Services
To run the full asynchronous stack locally:
```bash
# Terminal 1: Redis Broker (default: localhost:6379)
docker run -d -p 6379:6379 redis:7-alpine
# or native: redis-server

# Terminal 2: Celery Worker (from backend/)
celery -A app.workers.celery_app.celery_app worker --loglevel=INFO

# Terminal 3: FastAPI Web Server (from backend/)
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Job Status Lifecycle
- `QUEUED`: Job received and waiting in Celery queue; no comments processed yet.
- `PROCESSING`: Worker actively collecting comments or running sentiment inference.
- `COMPLETED`: Ingestion and inference finished; results available; error is null.
- `FAILED`: Non-recoverable error occurred (e.g. `MODEL_NOT_READY`, `YOUTUBE_INVALID_VIDEO`, `YOUTUBE_COMMENTS_DISABLED`); error details provided.

### Real vs Artificial Progress
Progress indicators represent actual completed operations (`completed`, `total`, `percentage`):
- `FETCHING_COMMENTS`: `completed=0, total=null, percentage=null` (total comment count unknown until pagination finishes).
- `SENTIMENT_ANALYSIS`: `completed=N, total=Total, percentage=int(N / Total * 100)` strictly representing verified inference calls.
- `COMPLETED`: `completed=Total, total=Total, percentage=100`.

### Error Handling & Bounded Retries
- Retries are strictly bounded (`max_retries=3`) with exponential backoff.
- Transient network or broker drops are retried.
- Non-retryable conditions (`MODEL_NOT_READY`, `YOUTUBE_INVALID_VIDEO`, `YOUTUBE_VIDEO_NOT_FOUND`, `YOUTUBE_COMMENTS_DISABLED`, `YOUTUBE_QUOTA_EXCEEDED`) immediately transition the job to `FAILED` without retrying.

