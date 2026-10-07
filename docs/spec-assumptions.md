# Kollamo.ai — Specification Fallback & Assumptions Record

This document records the specification access status, the authoritative fallback hierarchy, and the baseline assumptions for the Kollamo.ai platform in accordance with the project governance rules established in `AGENTS.md`.

---

## 1. Specification Access Status

- **Primary Specification Identity**: Kollamo.ai Technical Project Specification & Master Execution Prompt.
- **Physical Repository Availability**: The original project specification was provided as an external project prompt and is not checked in as a standalone static markdown document in the repository root.
- **Status**: **FALLBACK ACTIVE**. In the absence of a standalone physical specification file, the platform operates under the **Specification Access Fallback Procedure** codified in `AGENTS.md`.

---

## 2. Rule Precedence Framework & Specification Fallback

All engineering and product requirements operate under the 7-level precedence hierarchy codified in [AGENTS.md](../AGENTS.md):
```text
Level 1: System / Platform Constraints (Highest)
    ↓
Level 2: Current Explicit User Instruction
    ↓
Level 3: More-Specific Repository Rules (Scoped)
    ↓
Level 4: Root Repository Rules (AGENTS.md)
    ↓
Level 5: Project Specification
    ↓
Level 6: Approved Architecture Decisions (ADRs)
    ↓
Level 7: Recommended Engineering Practices (Advisory)
```

### Level 5 Specification Access Fallback Hierarchy:
When determining product requirements (WHAT Kollamo.ai is supposed to do) while the physical specification file is external:
```text
1. Existing repository implementation (decisions already made, established contracts, completed phase code)
   ↓
2. AGENTS.md / applicable repository rules (engineering standards, ML rules, API rules)
   ↓
3. Existing approved ADRs / architecture decisions (docs/adr/ADR-001-system-architecture.md, etc.)
   ↓
4. Explicit current user instructions (direct prompt instructions)
   ↓
5. Previously approved phase decisions (Phase 0 through Phase 10 completion records)
   ↓
6. General engineering judgment (conservative, documented assumptions only)
```

### Governing Fallback Rules:
1. Inferred requirements must **never** be claimed as having originated directly from the original specification.
2. If a requirement cannot be confirmed from the specification or approved project decisions, it must **never be invented or fabricated**.
3. Any assumption made using engineering judgment must be documented in this registry.

---

## 3. Specification Statement Classification Framework

Statements from prompts, documentation, and issues must be classified according to the following 4-tier taxonomy:

| Classification | Definition | Enforcement |
| :--- | :--- | :--- |
| **Required Product Behavior** | Features, workflows, constraints, or formats explicitly mandated by project requirements. | **Mandatory**: Must be fully implemented, tested, and verified before phase sign-off. |
| **Target / Goal** | Desired quantitative metrics, performance benchmarks, or aspirational objectives (e.g. accuracy targets). | **Empirical**: Must never be represented as achieved without experimental validation on held-out test splits. |
| **Example** | Concrete sample inputs, mock payloads, or illustrative scenarios provided for clarity. | **Illustrative**: Does not create additional unstated requirements or constrain general inputs. |
| **Implementation Recommendation** | Suggested engineering patterns, recommended libraries, or architectural suggestions. | **Advisory**: May be replaced if equivalent or better implementation satisfies requirement; does not block phase completion. |

---

## 4. Distinguishing REQUIRED from RECOMMENDED

- **REQUIRED**: Items that must be completely satisfied before a phase can be marked complete (mandated features, 5 sentiment classes, Google MuRIL inference, zero heuristic dictionaries, server-side secret management in `.env`, phase dependencies, mandatory tests).
- **RECOMMENDED**: Desirable enhancements that should be implemented when practical, but **must NOT block phase completion** unless explicitly promoted to REQUIRED (Docker Compose, Storybook, advanced CI/CD, extra telemetry, advanced caching, extra documentation).
- **Important: Do Not Over-Implement**: If a task is not explicitly required by higher-priority instructions, repository rules, specification, or approved ADRs, treat it as RECOMMENDED. Do not expend implementation effort on optional infrastructure when required features are pending.


---

## 5. Verification Against Requirement Fabrication

To guarantee project integrity, the codebase has been verified against requirement fabrication. The following potential additions were evaluated and confirmed **NOT** to have been fabricated:

| Category | Potential Fabricated Item | Authoritative Baseline Decision | Status |
| :--- | :--- | :--- | :--- |
| **User Roles** | Multi-tier RBAC, Admin/Editor/Viewer accounts, User profiles | Single public / anonymous user access for analysis and sandbox workflows. | Verified (No extra roles assumed) |
| **Sentiment Classes** | 3-class (pos/neg/neu) or 7-class emotion expansion (anger, joy, etc.) | Strictly 5 canonical classes: `positive`, `negative`, `neutral`, `mixed`, `unsupported`. | Verified (5 classes only) |
| **ML Architectures** | Alternative transformers (mBERT, XLM-R, LLM prompt classifiers) | Google MuRIL (`google/muril-base-cased`) with PyTorch/HF head + TF-IDF baseline. | Verified (MuRIL backbone exclusively) |
| **API Endpoints** | Custom external webhook integrations, third-party auth callbacks | 11 documented REST endpoints for health, sentiment, ingestion, async jobs, and reports. | Verified (No unprompted endpoints) |
| **Dashboard Features** | Real-time live streaming charts, user notification center, chat bots | 6 metric cards, Net Approval Index, multi-view chart tabs, topic chips, comments explorer. | Verified (Specified features only) |
| **Authentication** | Mandatory OAuth2, JWT login wall for public analysis, API key subscriptions | Public API access with IP sliding-window rate limiting; YouTube API key isolated in backend `.env`. | Verified (No fabricated auth wall) |
| **Infrastructure** | Multi-cluster Kubernetes, Apache Kafka, Distributed Ceph storage | Docker Compose with PostgreSQL 16, Redis 7, Celery, FastAPI, and Nginx. | Verified (Standardized stack) |

---

## 6. Phase Dependency Model & Contradiction Resolution

### The Approved Phase Sequence:
```text
Phase 0 (Foundation / Repository Setup)
  ↓
Phase 1 (Frontend / UI Foundation)
  ↓
Phase 2 (ML / NLP Foundation)
  ↓
Phase 3 (Backend / FastAPI Foundation)
  ↓
Phase 4 (YouTube Ingestion)
  ↓
Phase 5 (Celery + Redis Async)
  ↓
Phase 6 (Frontend ↔ Backend Integration)
  ↓
Phase 7 (Audience Intelligence Dashboard)
  ↓
Phase 8 (Translation + PDF Reporting)
  ↓
Phase 9 (Testing + Security + Performance)
  ↓
Phase 10 (Final Release & Docker Deployment)
```

### Contradiction Resolution (Phase 2 vs. Phase 3):
- **Conflict Identified**: Prior prompt instructions contained conflicting phrasing stating on one hand that *"Phase 2 and Phase 3 are independent"* while simultaneously stating that *"Phase 3 requires Phase 2"*.
- **Authoritative Resolution**: The dependency is strictly **`Phase 2 → Phase 3`**.
  - **Phase 2** establishes the ML/NLP foundation (preprocessing pipelines, PyTorch/Transformers Google MuRIL predictor contract, TF-IDF baseline, model evaluation protocols).
  - **Phase 3** consumes and integrates with this established ML/NLP interface inside FastAPI service layers (`backend/app/ml/adapter.py`).
  - Phase 3 does **not** duplicate, mock, or recreate Phase 2 ML logic.
  - This eliminates all claims of parallel independence and enforces clean, contract-driven phase boundaries.

---

## 7. Treatment of Recommended Work

- Recommended features (e.g. Storybook, advanced multi-cluster orchestration, external APM agents, optional cache tiers) **do not create phase dependencies** unless explicitly promoted to **REQUIRED** by project rules.
- Non-blocking recommended work that has been deferred:
  - Integration of live Hugging Face Hub automated model uploads (local checkpoint loading is active).
  - Advanced Kubernetes Helm charts (Docker Compose production multi-container setup is complete).
  - Additional language pair machine translation models beyond Malayalam-English.

---

## 8. Current Project State & Blockers

- **Completed Phases**: Phases 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 (All phases COMPLETE).
- **Active Blockers**: **NONE** (0 blockers).
- **Next Permitted Action**: Documentation and clarification sign-off only; no new feature implementation permitted without explicit user instruction.
