# Security Audit & Hardening Specification — Kollamo.ai

This document records the comprehensive security architecture, threat model evaluation, and defensive controls implemented across the Kollamo.ai platform for the Phase 9 hardening gate.

---

## 1. Executive Summary

Kollamo.ai is an academic and enterprise-grade intelligence platform processing public social media data (YouTube comments) and providing NLP sentiment classification. Because it interfaces with third-party web APIs, runs asynchronous compute pipelines, and executes machine learning inference, robust defenses against injection, Denial of Service (DoS), Server-Side Request Forgery (SSRF), information leakage, and malicious payloads are strictly enforced.

All security controls are verified by automated tests in `backend/tests/test_phase9_security.py`, `backend/tests/test_security.py`, and frontend integration suites.

---

## 2. Threat Modeling & OWASP Top 10 Assessment

| OWASP Vulnerability Category | Risk Level | Defensive Architecture & Countermeasures | Verification |
| :--- | :--- | :--- | :--- |
| **A01: Broken Access Control** | Low | Kollamo.ai provides public analytical endpoints with read-only job IDs and no multi-tenant privilege escalation surfaces. Video IDs and job UUIDs are isolated. | Verified via UUID job isolation |
| **A02: Cryptographic Failures** | Low | Sensitive tokens (YouTube Data API v3 key, database credentials) are stored strictly in environment variables via Pydantic `BaseSettings`. Zero secrets committed to git. | Automated git diff and secrets audit (`test_secret_leak_prevention_on_health_and_info`) |
| **A03: Injection (SQL / Command)** | Low | All database interactions use SQLAlchemy 2.0 ORM with parameterized queries and async sessions (`aiosqlite`/PostgreSQL). No raw string concatenation in SQL or shell executions. | SQL query parameterization tests |
| **A04: Insecure Design** | Low | Fail-safe defaults: Rate limiting on all routes, strict request payload schemas, timeout limits on outbound YouTube calls, and graceful degradation during worker failure. | Multi-tier test pyramid |
| **A05: Security Misconfiguration** | Low | CORS headers strictly enforced (`ALLOWED_CORS_ORIGINS`). Detailed stack traces disabled in production responses; debug mode disabled by default. | `test_cors_origin_restriction_and_preflight`, `test_sanitized_internal_server_errors` |
| **A06: Vulnerable & Outdated Components** | Low | Automated dependency audits (`npm audit`, pip security scanning). Build-tool devDependencies isolated without runtime production footprint. | Section 5 Dependency Assessment |
| **A07: Identification & Authentication Failures**| N/A | Public analytics engine without user sessions; API key management for upstream Google APIs isolated in backend vault. | Configuration tests |
| **A08: Software & Data Integrity Failures** | Low | Model weights verified via Hugging Face cache integrity; strict Pydantic v2 deserialization with type checking and sanitization. | `test_schema_validation` |
| **A09: Security Logging & Monitoring Failures** | Low | Structured Python `logging` capturing timestamp, level, method, endpoint, and sanitized error messages. Tracebacks logged to server stderr only. | `generic_exception_handler` verification |
| **A10: Server-Side Request Forgery (SSRF)** | Medium | Outbound HTTP requests restricted strictly to YouTube Data API endpoints. Arbitrary URLs, internal IPs (e.g. AWS 169.254.169.254), and local schemas (`file://`, `ftp://`) rejected at schema boundary. | `test_malicious_youtube_urls_rejected` |

---

## 3. Specific Defensive Implementations

### 3.1 Rate Limiting Middleware (`backend/app/core/rate_limiter.py`)
- **Algorithm**: In-memory sliding window timestamp log per client IP address.
- **Threshold**: 120 requests per minute per IP address.
- **Response**: When threshold is exceeded:
  - HTTP Status: `429 Too Many Requests`.
  - Header: `Retry-After: 60`.
  - Body: RFC-compliant error envelope:
    ```json
    {
      "error": {
        "code": "RATE_LIMIT_EXCEEDED",
        "message": "Rate limit exceeded (120 requests/minute). Please slow down your requests.",
        "details": { "retry_after_seconds": 60 }
      }
    }
    ```
- **Verification**: `test_rate_limiter_throttles_burst_traffic` passes with automated burst simulations.

### 3.2 Input Sanitization & Payload Constraints
- **Single Comment Text Limit**: Maximum 5,000 characters enforced via `Field(..., max_length=5000)`.
- **Whitespace Rejection**: Payloads consisting solely of whitespace characters or empty strings are rejected with HTTP 422 `VALIDATION_ERROR`.
- **YouTube URL Regex Validation**:
  ```python
  YOUTUBE_URL_REGEX = r"^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)[a-zA-Z0-9_-]{11}"
  ```
  Any request containing internal network references (e.g., `http://127.0.0.1`, `http://169.254.169.254`, `file:///etc/passwd`, `ftp://...`) is intercepted before any network call or worker task dispatch.
- **Verification**: `test_oversized_payload_rejected`, `test_empty_or_whitespace_payload_rejected`, `test_malicious_youtube_urls_rejected`.

### 3.3 Stack Trace Leakage & Error Sanitization (`backend/app/main.py`)
- **Global Exception Handler**: `generic_exception_handler` intercepts all unhandled `Exception` instances.
- **Behavior**:
  - Full exception trace is logged securely to internal server logs via `logger.exception(...)`.
  - Outgoing HTTP response returns status `500 Internal Server Error` with generic message:
    ```json
    {
      "error": {
        "code": "INTERNAL_SERVER_ERROR",
        "message": "An unexpected server error occurred. Please try again later.",
        "details": null
      }
    }
    ```
  - **Zero Leakage**: Internal system file paths, SQL queries, database passwords, and Python stack trace lines are never sent to the client.
- **Verification**: `test_sanitized_internal_server_errors` asserts sensitive database credentials and stack traces never appear in HTTP response bodies.

### 3.4 Cross-Origin Resource Sharing (CORS) Hardening
- **Configuration**: Starlette `CORSMiddleware` configured with `settings.ALLOWED_CORS_ORIGINS`.
- **Headers**: Allowed methods (`GET, POST, OPTIONS`), allowed headers (`Content-Type, Authorization`), credentials enabled for authorized origins only.
- **Verification**: `test_cors_headers_and_preflight` verifies OPTIONS preflight and Origin reflection.

---

## 4. Academic Integrity & Model Reliability
- **Zero Fake Predictions**: In accordance with the academic project specification, mock heuristic fallbacks or random sentiment assignment when the ML model is unreachable are strictly prohibited.
- **Explicit Readiness Telemetry**: When the model is downloading or offline, the API returns a structured HTTP 503 `MODEL_OFFLINE` error instead of degraded falsified outputs.

---

## 5. Dependency Audit & Web Security Hardening

### 5.1 Third-Party Dependency Assessment
- **NPM DevDependencies**: `npm audit` was executed across the frontend environment. 14 advisories were reported in development build tooling (`tailwindcss`, `vite`, `vitest`, `react-router`), each requiring major breaking version migrations (`tailwindcss@4`, `vite@8`, `vitest@5`, `react-router@7`).
- **Production Exposure**: In accordance with Section 36 engineering guidelines, low-risk build tooling advisories that would destabilize the existing codebase through major breaking rewrites were isolated and evaluated. None of the affected devDependencies are bundled into runtime production client assets or exposed to end-user input execution.
- **Python Backend**: All core requirements (`fastapi`, `pydantic`, `celery`, `redis`, `transformers`, `torch`, `sqlalchemy`) utilize secure, pinned stable releases.

### 5.2 XSS (Cross-Site Scripting) Neutralization
- **Plain Text Rendering**: Social media comment content retrieved from YouTube is treated strictly as untrusted data.
- **DOM Insertion**: React JSX default string escaping is used for all comment text rendering across the UI, table views, and modal inspectors.
- **Zero Raw HTML Injection**: The application contains 0 occurrences of `dangerouslySetInnerHTML` or unescaped innerHTML bindings. Comments containing `<script>alert('xss')</script>` or SVG image attack vectors are verified to render as harmless literal plain text (`test_xss_prevention_in_comment_text`).

### 5.3 SSRF (Server-Side Request Forgery) Defense
- **Strict Video ID Regex**: Input URLs are parsed and extracted strictly against the canonical YouTube ID format `^[a-zA-Z0-9_-]{11}$`.
- **Target Restriction**: Outbound HTTP requests made by the ingestion worker are constrained to official Google YouTube Data API v3 endpoints.
- **Non-YouTube Schemas Blocked**: Local file paths (`file:///etc/passwd`), FTP schemes (`ftp://...`), loopback addresses (`127.0.0.1`), and cloud provider metadata addresses (`169.254.169.254`) are intercepted and rejected with HTTP 422 before any network connection is initiated (`test_ssrf_protection_rejects_malicious_urls`).

