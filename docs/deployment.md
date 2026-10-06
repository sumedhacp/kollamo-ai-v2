# Deployment Guide — Kollamo.ai

## 1. Overview
Kollamo.ai is designed for reproducible containerized deployment across development, staging, and production environments using Docker and Docker Compose.

---

## 2. Infrastructure Services

1. **Frontend Service**:
   - Production build served via Nginx with reverse proxy caching and Brotli/Gzip compression.
2. **Backend API Service**:
   - FastAPI application served via Uvicorn with Gunicorn process management.
3. **Worker Service**:
   - Celery worker pool running concurrent task executors.
4. **Message Broker**:
   - Redis instance with persistent append-only file (AOF) storage.
5. **Database**:
   - PostgreSQL 15 with connection pooling (`pgbouncer` or internal SQLAlchemy async pool).

---

## 3. Environment Configuration

Ensure all variables in `.env` are populated according to [`.env.example`](../.env.example):

- `ENVIRONMENT=production`
- `DEBUG=False`
- `APP_SECRET_KEY=<strong-random-key>`
- `DATABASE_URL=postgresql+asyncpg://<user>:<password>@<db-host>:5432/<dbname>`
- `REDIS_URL=redis://<redis-host>:6379/0`
- `YOUTUBE_API_KEY=<google-cloud-api-key>`
- `ALLOWED_CORS_ORIGINS=https://app.kollamo.ai`

---

## 4. Migration & Startup Procedures

```bash
# 1. Run database migrations
cd backend
alembic upgrade head

# 2. Launch container stack
docker compose -f docker-compose.prod.yml up -d --build

# 3. Check health endpoint
curl https://api.kollamo.ai/api/health
```
