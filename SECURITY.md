# Security Policy — Kollamo.ai

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

---

## Reporting a Vulnerability

If you discover a security vulnerability within Kollamo.ai, please do **NOT** disclose it publicly via GitHub issues or discussions.

Instead, please report the vulnerability privately:
1. Send an email describing the vulnerability, proof of concept, and steps to reproduce to `security@kollamo.ai` (or the project academic supervisor).
2. Include the affected commit SHA or version tag.
3. Allow up to 48 hours for an initial response before public coordination.

---

## Core Security Directives

### 1. API Keys & Secrets
- Never commit API keys, database credentials, or secret keys to source control.
- All secrets must be loaded through `.env` and environment variables.
- The YouTube Data API v3 key must only be accessible by the backend ingestion service and never transmitted to frontend clients.

### 2. Input Sanitization & Validation
- All single-comment and bulk-analysis requests are validated strictly against Pydantic schemas.
- Payload size limits are enforced on the backend to mitigate Denial of Service (DoS) attacks.
- YouTube video URLs are verified and parsed securely using strict regular expressions to prevent SSRF and injection.

### 3. Error Handling & Data Leakage
- In production mode (`ENVIRONMENT=production`), detailed stack traces, internal database schema definitions, and raw library errors are suppressed from API responses.
- Errors are logged server-side with sensitive parameters redacted.

### 4. Cross-Origin Resource Sharing (CORS)
- CORS origin whitelisting is enforced through the `ALLOWED_CORS_ORIGINS` configuration.
- Wildcard `*` origins are strictly forbidden in production configurations.
