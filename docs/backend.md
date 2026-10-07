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
│   │   ├── health.py        # Service readiness health checks
│   │   ├── sentiment.py     # Single-comment sentiment endpoints (/sentiment, /v1/sentiment)
│   │   └── routes/          # Module route compatibility layer
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
│   │   ├── common.py        # Standardized ErrorResponse, ErrorDetail, HealthStatus
│   │   ├── error.py         # Error schema aliases
│   │   ├── health.py        # Health responses
│   │   └── sentiment.py     # SentimentRequest, SentimentResponse, ClassProbabilities
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
    "status": "healthy",
    "project": "Kollamo.ai",
    "version": "0.4.0",
    "environment": "development"
  }
  ```

#### Readiness Health: `GET /api/health` and `GET /api/v1/health`
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

#### `POST /api/v1/sentiment` & `POST /api/sentiment`
Synchronously classifies a single Malayalam, Manglish, English, or code-mixed social media comment.

#### Request Contract (`SentimentRequest`)
```json
{
  "text": "ഈ സിനിമ വളരെ മികച്ചതാണ്, അഭിനയം ഗംഭീരം!",
  "translate": false
}
```
- `text` (string, required): 1 to 5000 characters. Rejects empty strings and whitespace-only payloads with `422 Unprocessable Entity`.
- `translate` (boolean, optional, default: `true`): Flag requesting English translation for regional/code-mixed comments.

#### Response Contract (`SentimentResponse`)
```json
{
  "original_text": "ഈ സിനിമ വളരെ മികച്ചതാണ്, അഭിനയം ഗംഭീരം!",
  "detected_language": "ml",
  "detected_script": "Malayalam",
  "sentiment": "positive",
  "confidence": 0.942,
  "class_probabilities": {
    "positive": 0.942,
    "negative": 0.015,
    "neutral": 0.021,
    "mixed": 0.018,
    "unsupported": 0.004
  },
  "probabilities": {
    "positive": 0.942,
    "negative": 0.015,
    "neutral": 0.021,
    "mixed": 0.018,
    "unsupported": 0.004
  },
  "translation_status": "not_requested",
  "translated_text": null,
  "model_metadata": {
    "architecture": "BaselineClassifier",
    "device": "cpu"
  },
  "processing_metadata": {
    "raw_length": 42,
    "cleaned_length": 42,
    "inference_time_ms": 1.25
  }
}
```

The five discrete sentiment classes are strictly:
1. `positive` / `Positive`
2. `negative` / `Negative`
3. `neutral` / `Neutral`
4. `mixed` / `Mixed`
5. `unsupported` / `Unsupported`

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
       "message": "Trained sentiment model checkpoint is not available for inference.",
       "details": {
         "status": "MODEL_NOT_TRAINED"
       }
     }
   }
   ```

---

## 5. Security & Error Handling

- **Credential Masking**: `SensitiveDataFilter` in `backend/app/core/logging.py` intercepts logs and redacts tokens, API keys, passwords, and authorization headers (`***REDACTED***`).
- **Internal Stack Trace Protection**: Unhandled exceptions are caught by `generic_exception_handler` and logged internally; clients receive a sanitized RFC-compliant error envelope with code `INTERNAL_SERVER_ERROR`.
- **CORS Protection**: CORS origins are restricted to configured hosts (`settings.ALLOWED_CORS_ORIGINS`). Broad wildcard (`*`) origins in production are strictly avoided.
- **Input Sanitization**: Pydantic v2 validates size (1-5000 chars), types, and non-empty string integrity.

---

## 6. Testing

Run backend tests using pytest:
```bash
pytest backend/tests/test_health.py backend/tests/test_sentiment.py backend/tests/test_app.py backend/tests/test_sentiment_api.py -v
```

All 24 test cases execute synchronously in memory without requiring external dependencies (YouTube, Redis, Celery, or external database servers).
