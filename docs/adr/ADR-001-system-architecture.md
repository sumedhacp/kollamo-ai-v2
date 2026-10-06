# ADR-001: System Architecture and Technology Selection

## Status
Accepted

## Context
Kollamo.ai requires a resilient, reproducible system capable of performing NLP sentiment analysis on regional Malayalam and Malayalam-English code-mixed social media comments. The system must support real-time single-comment queries as well as asynchronous ingestion of thousands of YouTube comments without freezing the web UI or timing out HTTP connections.

## Decision

1. **ML Architecture**:
   - Utilize **Google MuRIL** (`google/muril-base-cased`) fine-tuned with PyTorch and Hugging Face Transformers.
   - *Rationale*: MuRIL is specifically pre-trained on 17 Indian languages and English with transliterated scripts, making it far superior to general mBERT or XLM-RoBERTa for Manglish and Malayalam-English code-mixing.
   - Prohibit heuristic/keyword dictionaries to ensure genuine scientific evaluation.

2. **Backend Framework**:
   - Utilize **FastAPI** with Python 3.10+, **Pydantic v2**, and **SQLAlchemy 2.0**.
   - *Rationale*: High-performance asynchronous HTTP processing, automatic OpenAPI schema generation, and robust schema validation.

3. **Asynchronous Processing**:
   - Utilize **Celery** with **Redis** as message broker and results backend.
   - *Rationale*: Isolates YouTube API latency, network pagination, and PyTorch tensor batching from the FastAPI event loop, ensuring horizontal scalability.

4. **Frontend Architecture**:
   - Utilize **React**, **Vite**, **TypeScript**, and **Tailwind CSS**.
   - *Rationale*: Fast developer feedback, strict type safety, modular component composition, and responsive utility-first styling.

5. **Relational Database**:
   - Utilize **PostgreSQL** with Alembic migrations.
   - *Rationale*: ACID compliance, JSONB indexing for model output storage, and compatibility with cloud providers (Supabase / AWS RDS).

## Consequences
- **Positive**: Clear separation of concerns, horizontally scalable background worker tier, reproducible academic experimentation, and high UI responsiveness.
- **Trade-offs**: Requires running multi-container setup (API, Celery worker, Redis, PostgreSQL) for full end-to-end integration during local development.
