---
name: kollamo-pipeline
description: >-
  Use this skill when managing, running, testing, or debugging the Kollamo.ai
  end-to-end pipeline across frontend, FastAPI backend, Celery workers, and ML services.
---

# Kollamo.ai Pipeline Skill

This skill defines the procedures for operating, developing, and testing the Kollamo.ai multi-service system.

## System Topology
- **Frontend**: React + Vite + TypeScript on port 5173.
- **Backend API**: FastAPI + Uvicorn on port 8000.
- **Background Worker**: Celery worker consuming from Redis.
- **Message Broker & Cache**: Redis on port 6379.
- **Database**: PostgreSQL on port 5432.
- **ML Engine**: PyTorch + Hugging Face Transformers (Google MuRIL).

## Development Workflows

### 1. Frontend Development
- Directory: `frontend/`
- Install dependencies: `npm install`
- Start dev server: `npm run dev`
- Build production bundle: `npm run build`
- Type checking: `npm run type-check`
- Unit tests: `npm run test`

### 2. Backend & Worker Development
- Directory: `backend/`
- Environment setup: `python -m venv .venv && source .venv/bin/activate` (or Windows equivalent)
- Install requirements: `pip install -r requirements.txt`
- Start FastAPI server: `uvicorn app.main:app --reload --port 8000`
- Start Celery worker: `celery -A app.workers.celery_app worker --loglevel=info`
- Run test suite: `pytest`

### 3. ML Pipeline
- Directory: `ml/`
- Baseline training: `python scripts/train_baseline.py`
- MuRIL fine-tuning: `python scripts/train_muril.py --config configs/muril_config.yaml`
- Evaluation: `python scripts/evaluate.py --model_path models/muril_sentiment`

## Verification Checklist
- Always verify all 4 status states (Loading, Empty, Success, Error) on the UI.
- Never mock progress updates in Celery tasks.
- Ensure all API endpoints adhere to schemas defined in `backend/app/schemas/`.
