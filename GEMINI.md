# Kollamo.ai — Workspace Agent Guidelines

These guidelines apply across the entire Kollamo.ai repository. All agents, developers, and tools must follow these rules.

## Core Directives

1. **Academic MCA Standard & Code Quality**:
   - Write clean, modular, production-grade code.
   - Maintain comprehensive docstrings and TypeScript types.
   - Never compromise code quality or introduce mock shortcuts for core logic.

2. **Source of Truth**:
   - Refer to [AGENTS.md](./AGENTS.md) for the permanent engineering contract.
   - Refer to [docs/architecture.md](./docs/architecture.md) for architectural blueprints.

3. **ML & Sentiment Integrity**:
   - Google MuRIL is the designated encoder for multilingual Malayalam, Manglish, and code-mixed sentiment classification.
   - Never implement heuristic sentiment analysis (keyword matching, positive/negative word dictionaries, or if/else sentiment rules).
   - Never fabricate evaluation metrics or accuracy scores. Real validation metrics on held-out splits are mandatory.

4. **Security & Secrets**:
   - No hardcoded API keys, tokens, or credentials anywhere in the repository.
   - All external keys (YouTube API, database URLs, Redis URLs) must reside in `.env`.
   - Never log secrets or include sensitive data in error messages or client responses.

5. **Asynchronous Processing**:
   - All YouTube ingestion and large-scale sentiment analysis jobs must execute asynchronously through Celery and Redis.
   - Track deterministic job states: `queued`, `running`, `completed`, `failed`, `cancelled`.
   - Never simulate or fake job progress bars.

6. **UI/UX Standards**:
   - Modern, high-trust SaaS aesthetic using React, Vite, TypeScript, and Tailwind CSS.
   - Accessible WCAG 2.1 AA standards; never communicate sentiment solely via color.
   - Complete states: Loading skeleton, Empty state, Success state, Error state with recovery action.

7. **Git & Commit Hygiene**:
   - Use Conventional Commits (`feat`, `fix`, `test`, `docs`, `chore`, `refactor`).
   - Work within phase branches (`phase/01-foundation`, `phase/02-ml`, etc.).
   - Never force-push. Never push without explicit user consent.
