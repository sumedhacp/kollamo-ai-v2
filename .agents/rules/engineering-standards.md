# Engineering Standards — Kollamo.ai

## Architecture & Code Organization
- **Separation of Concerns**: Keep business logic, database persistence, API routing, and ML pipelines decoupled into dedicated modules.
- **Frontend Layer**: `frontend/src/` with component hierarchy: `components/ui/` (primitives), `components/features/` (domain widgets), `pages/` (routes), `services/` (API clients), `hooks/` (reusable state), `types/` (TypeScript interfaces).
- **Backend Layer**: `backend/app/` structured as `api/` (routers), `core/` (config, security, telemetry), `models/` (SQLAlchemy models), `schemas/` (Pydantic v2 schemas), `services/` (business logic), `repositories/` (database queries), `ml/` (inference runner), `workers/` (Celery background tasks).
- **ML Layer**: `ml/` structured into `data/` (splits and manifest), `preprocessing/` (cleaners, normalizers), `models/` (architectures), `training/` (trainer loop), `evaluation/` (metrics, confusion matrix), `inference/` (predictor), `configs/` (YAML configs).

## TypeScript / Frontend Standards
- Strict type checking enabled (`strict: true` in `tsconfig.json`).
- Avoid `any`. Use strict union types, branded types, and schema inference.
- Reusable UI elements must implement semantic HTML and keyboard accessibility (focus rings, ARIA roles, screen-reader text).
- Responsive layouts default to mobile-first (`sm:`, `md:`, `lg:`, `xl:` breakpoints in Tailwind).

## Python / Backend Standards
- Python 3.10+ standard with strict type hints (`typing` / `Annotated`).
- FastAPI routers depend on Dependency Injection (`Depends()`) for database sessions and configuration.
- Pydantic v2 schemas used for all API request validation and response serialization.
- SQLAlchemy 2.0 async engine and declarative models with explicit column types and foreign keys.
- Comprehensive test coverage using `pytest`, `pytest-asyncio`, and `httpx`.

## Git & Versioning Standards
- Commit messages strictly adhere to Conventional Commits:
  - `feat(scope): message`
  - `fix(scope): message`
  - `test(scope): message`
  - `docs(scope): message`
  - `chore(scope): message`
- Every phase operates on its designated branch before PR/merge consideration.
