# Kollamo.ai — Malayalam-English Sentiment & Audience Intelligence

[![CI](https://github.com/sumedhacp/kollamo-ai-v2/actions/workflows/ci.yml/badge.svg)](https://github.com/sumedhacp/kollamo-ai-v2/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Node: 18+](https://img.shields.io/badge/Node-18%2B-green.svg)](https://nodejs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-blue.svg)](https://www.typescriptlang.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0%2B-EE4C2C.svg)](https://pytorch.org/)
[![HuggingFace](https://img.shields.io/badge/MuRIL-google%2Fmuril--base--cased-yellow.svg)](https://huggingface.co/google/muril-base-cased)

**Kollamo.ai** is an academic Master of Computer Applications (MCA) platform designed for fine-grained sentiment analysis and audience intelligence across regional Indian social web conversations. Specifically tailored for **Malayalam script**, **Manglish** (Romanized Malayalam), **English**, and **Malayalam-English code-mixed comments**, Kollamo.ai provides high-throughput ingestion of YouTube video comment threads, asynchronous neural classification, English translations for readability, and an executive audience intelligence dashboard.

---

## 🏛️ System Architecture

```mermaid
flowchart TD
    subgraph Client ["Frontend (React + Vite + TypeScript)"]
        UI_Home["Landing Page"]
        UI_Sandbox["Single Comment Sandbox"]
        UI_Analyze["YouTube Ingestion Trigger"]
        UI_Dashboard["Audience Dashboard & PDF Report"]
    end

    subgraph API ["API Layer (FastAPI)"]
        HealthRoute["GET /api/health"]
        SentimentRoute["POST /api/sentiment"]
        AnalyzeRoute["POST /api/analyze"]
        JobRoute["GET /api/analyze/:jobId"]
    end

    subgraph Workers ["Distributed Worker Pool (Celery + Redis)"]
        YT_Ingest["YouTube Data API v3 Ingestion"]
        Preprocessor["Unicode & Transliteration Cleaner"]
        InferenceEngine["MuRIL Neural Classifier Head"]
        TranslationSvc["Translation Service (NLLB / MarianMT)"]
        Aggregator["Audience Metric Aggregator"]
    end

    subgraph Storage ["Persistence Layer"]
        PG[(PostgreSQL Database)]
        RedisCache[(Redis Broker & Cache)]
    end

    UI_Sandbox -->|Single Text| SentimentRoute
    UI_Analyze -->|Video URL & Sample Size| AnalyzeRoute
    SentimentRoute -->|Direct Inference| InferenceEngine
    AnalyzeRoute -->|Enqueue Job| RedisCache
    RedisCache --> Workers
    Workers --> PG
    UI_Dashboard -->|Poll / Stream Status| JobRoute
    JobRoute --> PG
```

---

## 🌟 Core Features

- **Multilingual & Code-Mixed NLP**: Robust sentiment analysis across pure Malayalam (`മലയാളം`), Manglish (`adipoli movie aayirunnu`), standard English, and complex code-mixed expressions.
- **Five-Class Sentiment Taxonomy**:
  - `Positive` — Admiration, praise, satisfaction.
  - `Negative` — Criticism, dissatisfaction, anger.
  - `Neutral` — Factual, informational, or objective queries.
  - `Mixed` — Co-occurring positive and negative sentiments.
  - `Unsupported` — Unintelligible text, pure noise, or unsupported languages.
- **Google MuRIL Foundation**: Powered by `google/muril-base-cased` fine-tuned for regional Dravidian code-mixed nuances with reproducible training checkpoints. No heuristic dictionaries or keyword rules.
- **Official YouTube Data API v3 Ingestion**: Configurable comment extraction (50, 100, 250, 500, or ALL comments) supporting Most Liked, Newest, and Oldest sort modes with pagination and quota resilience.
- **Asynchronous Scalability**: Celery + Redis architecture ensuring zero UI freeze or FastAPI blocking during multi-thousand comment processing.
- **Audience Intelligence Dashboard**: Real-time distribution charts, sentiment vs. engagement analysis, top positive/negative comment highlights, and multifaceted filtering.
- **Translation & Reporting**: Original comment preservation with English translations and client-side PDF executive report export using `jsPDF` and `html2canvas`.

---

## 📂 Repository Structure

```text
kollamo-ai-v2/
├── .agents/                    # Antigravity agent configuration
│   ├── rules/                  # Directory & architectural rules
│   └── skills/                 # Multi-step workflow skills
├── .github/                    # CI/CD workflows and issue templates
├── backend/                    # FastAPI application & Celery workers
│   ├── app/
│   │   ├── api/                # API routes and endpoints
│   │   ├── core/               # App configuration & security
│   │   ├── db/                 # Database engine & migrations
│   │   ├── ml/                 # Inference runtime services
│   │   ├── models/             # SQLAlchemy ORM models
│   │   ├── repositories/       # Data access layer
│   │   ├── schemas/            # Pydantic v2 validation models
│   │   ├── services/           # Business logic & YouTube ingestion
│   │   ├── utils/              # Helper utilities
│   │   └── workers/            # Celery task definitions
│   └── tests/                  # Backend unit & integration tests
├── docs/                       # System documentation and ADRs
│   ├── adr/                    # Architecture Decision Records
│   ├── architecture.md         # Full system architecture
│   ├── api.md                  # API reference
│   ├── database.md             # Database schema & migrations
│   ├── ml-pipeline.md          # ML training & preprocessing specs
│   ├── evaluation.md           # Metrics and baseline results
│   ├── ui.md                   # UI/UX design tokens and guides
│   ├── testing.md              # Testing guidelines
│   ├── performance.md          # Benchmark results & optimization
│   └── deployment.md           # Production deployment guide
├── frontend/                   # React + Vite + TypeScript frontend
│   ├── public/                 # Static assets
│   └── src/                    # UI components, pages, hooks, services
├── ml/                         # ML training, data, and offline evaluation
│   ├── configs/                # Hyperparameter & training YAMLs
│   ├── data/                   # Dataset splits and registries
│   ├── evaluation/             # Metrics calculators and confusion matrices
│   ├── inference/              # Offline prediction wrappers
│   ├── models/                 # Model architectures & head definitions
│   ├── preprocessing/          # Malayalam & Manglish text sanitizers
│   ├── scripts/                # Training and evaluation runner scripts
│   └── tests/                  # ML test suite
├── .env.example                # Environment variable configuration template
├── .gitignore                  # Git ignore rules
├── AGENTS.md                   # Permanent engineering contract
├── CHANGELOG.md                # Version changelog
├── GEMINI.md                   # Antigravity root rules
└── SECURITY.md                 # Security policies and reporting
```

---

## 🚀 Getting Started

### Prerequisites

- **Python**: 3.10 or higher
- **Node.js**: 18.x or higher (LTS recommended)
- **PostgreSQL**: 14+
- **Redis**: 6+
- **Git**

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd kollamo-ai-v2
   ```

2. **Configure Environment:**
   ```bash
   cp .env.example .env
   # Update .env with your PostgreSQL credentials, Redis URL, and YouTube API key
   ```

3. **Backend Setup:**
   ```bash
   cd backend
   python -m venv .venv
   # Windows: .venv\Scripts\activate
   # Linux/macOS: source .venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Frontend Setup:**
   ```bash
   cd ../frontend
   npm install
   ```

---

## 🧪 Testing & Verification

- **Backend Tests:**
  ```bash
  cd backend && pytest
  ```
- **Frontend Tests:**
  ```bash
  cd frontend && npm run test
  ```
- **ML Pipeline Tests:**
  ```bash
  cd ml && pytest
  ```

---

## 📜 Development & Git Workflow

This project adheres strictly to **Conventional Commits** and phase branches:

- `main`: Stable, release-ready branch.
- `phase/01-foundation`: UI & foundation scaffolding.
- `phase/02-ml`: Multilingual MuRIL pipeline & baseline.
- `phase/03-backend`: FastAPI backend and database layer.
- `phase/04-ingestion`: YouTube Data API v3 ingestion service.
- `phase/05-async`: Celery + Redis distributed execution.
- `phase/06-integration`: Frontend-backend integration.
- `phase/07-dashboard`: Audience intelligence analytics.
- `phase/08-reporting`: Translation service and PDF generator.
- `phase/09-hardening`: End-to-end testing, security, and performance.
- `phase/10-release`: Deployment readiness and demonstration.

---

## ⚖️ Academic License & Ethics

This project is submitted in partial fulfillment of the Master of Computer Applications (MCA) degree. All YouTube data ingestion strictly adheres to YouTube API Terms of Service. Sentiment predictions are probabilistic model estimates and should not be construed as absolute emotional judgments.
