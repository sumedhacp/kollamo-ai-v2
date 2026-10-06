# Performance Benchmarks & Engineering Targets — Kollamo.ai

## 1. Performance Objectives

| Metric | Target | Verification Method |
| :--- | :--- | :--- |
| Single Comment Sentiment Latency | < 150 ms (CPU/GPU) | `POST /api/sentiment` benchmark |
| Batch Inference Throughput | > 100 comments/sec (GPU) | PyTorch DataLoader evaluation |
| YouTube Ingestion Rate | ~100 comments / 1.5s | YouTube Data API v3 pagination |
| Dashboard First Contentful Paint | < 1.2 s | Lighthouse / DevTools audit |
| End-to-End Processing (500 comments) | < 30 seconds | Asynchronous Celery pipeline trace |

---

## 2. Optimization Principles

1. **Model Weight Caching**:
   - Model weights must be loaded into memory once during worker or server initialization; never instantiate transformers on a per-request basis.
2. **Micro-Batch Inference**:
   - Comments enqueued in background workers are processed in batches (size 32 or 64) to maximize vectorization and GPU utilization.
3. **Database Bulk Operations**:
   - Raw comments, translations, and model predictions are inserted using SQLAlchemy bulk insert statements (`bulk_save_objects` or `insert().values([...])`) rather than individual row transactions.
4. **Redis Status Caching**:
   - Progress telemetry is cached in Redis keys with TTLs to minimize relational database reads during client polling intervals.
