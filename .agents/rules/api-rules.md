# API & Backend Services Rules — Kollamo.ai

## FastAPI & Async Architecture
- All web endpoints must be non-blocking. Compute-heavy operations (sentiment batching, YouTube pagination) must be queued into Celery background tasks.
- Keep FastAPI handlers thin: request validation -> service invocation -> response serialization.

## YouTube Data API Compliance
- Must use Google's official YouTube Data API v3 (`google-api-python-client` or asynchronous `httpx` client).
- Scraping YouTube web pages is strictly forbidden.
- Support sample sizes: 50, 100, 250, 500, ALL.
- Support sorting: Most Liked, Newest, Oldest.
- Robust pagination with `nextPageToken`.
- Handle edge cases: disabled comments, private videos, deleted comments, rate limit 403 quota errors, exponential backoff with jitter.
- YouTube API credentials must never be passed to frontend clients or checked into git.

## Job Lifecycle Management
- Every analysis task is assigned a UUID `job_id`.
- States:
  - `queued`: Enqueued into Redis.
  - `running`: Worker has claimed task and is processing chunks.
  - `completed`: All comments processed, metrics aggregated, results stored.
  - `failed`: Job terminated due to unrecoverable error (with structured error context).
  - `cancelled`: Explicitly cancelled.
- Progress updates must reflect verified counts: `processed_comments` / `total_comments`. Never simulate progress increments.

## Database & Persistence
- PostgreSQL database access managed through SQLAlchemy with Alembic migrations.
- Index lookup columns: `job_id`, `video_id`, `created_at`, `sentiment`.
- Prevent N+1 queries by eager-loading relations or using batch aggregation queries.
