# Kollamo.ai — MCA Project Live Demonstration Script

This script provides a 14-step presentation walkthrough for conducting the live software demonstration of **Kollamo.ai** during MCA project evaluations and viva voce examinations.

---

## Pre-Demonstration Checklist

Before starting the presentation:
1. Ensure Docker or local services are running:
   ```bash
   # Terminal 1: Redis & PostgreSQL
   docker run -d --name kollamo-redis -p 6379:6379 redis:7-alpine
   
   # Terminal 2: FastAPI Backend
   uvicorn backend.app.main:app --reload --port 8000
   
   # Terminal 3: Celery Worker
   celery -A backend.app.workers.tasks.celery_app worker --loglevel=info --concurrency=2
   
   # Terminal 4: Frontend Development Server
   cd frontend && npm run dev
   ```
2. Open browser at `http://localhost:5173` (Frontend) and `http://localhost:8000/docs` (FastAPI Swagger Docs).
3. Have a valid Malayalam YouTube video URL ready (or use sample/mock analysis ID).

---

## Step-by-Step 14-Step Demonstration Workflow

### Step 1: Project Introduction & Problem Context (1 Minute)
- **Action**: Display the Kollamo.ai Landing Page (`http://localhost:5173`).
- **Talking Points**:
  - *"Welcome, respected examiners. Today I present Kollamo.ai, an audience intelligence and sentiment analysis platform designed specifically for regional Indian social media conversations."*
  - *"Standard tools fail on regional discussions because Malayalam social commentary uses three complex linguistic forms: pure Malayalam script, phonetic Manglish, and intra-sentential code-mixing."*
  - *"Kollamo.ai bridges this divide by extracting real YouTube discussions and running neural classification across a fine-grained 5-class taxonomy."*

### Step 2: Architecture Tour & Interactive Sandbox (1.5 Minutes)
- **Action**: Click on **"Sandbox"** in the navigation header.
- **Talking Points**:
  - *"Before running bulk video jobs, let us observe how Kollamo.ai evaluates individual comments in real time."*
  - Enter sample Manglish comment: `Padam adipoli aayirunnu, must watch movie!`
  - Click **"Analyze Sentiment"**.
  - Show the result: Winning class `Positive`, confidence score, and normalized probability bars across all 5 classes summing to 1.0.
  - Enter sample Code-Mixed comment: `First half entertaining aayirunnu pakshe climax bore aayi.`
  - Click **"Analyze Sentiment"**.
  - Show how the model captures dual valence and categorizes it into `Mixed`.

### Step 3: YouTube URL Submission (1 Minute)
- **Action**: Navigate to **"Analyze"** in the top navigation bar.
- **Talking Points**:
  - *"Now let us analyze an entire audience discussion thread directly from YouTube."*
  - Paste a YouTube video URL (e.g., `https://www.youtube.com/watch?v=ScMzIvxBSi4` or any valid video).
  - Select comment sample size: **100 Comments**.
  - Select comment sorting: **Most Liked** (or Newest).
  - Highlight: *"We use the official Google YouTube Data API v3—no web scraping or fragile DOM parsing is involved."*

### Step 4: Asynchronous Job Creation (30 Seconds)
- **Action**: Click **"Start Analysis"**.
- **Talking Points**:
  - *"Notice the instantaneous response. The FastAPI backend does not block or execute inference synchronously."*
  - Point to the Pipeline Execution Panel: *"FastAPI returned an HTTP 202 Accepted status with a unique UUID job ID, enqueuing the workload into Celery and Redis."*

### Step 5: Real Progress Telemetry (1 Minute)
- **Action**: Observe the live telemetry progress bar updating in real time.
- **Talking Points**:
  - *"The frontend automatically polls the backend every 2 seconds."*
  - Point out the active lifecycle stages as they transition:
    - `FETCHING_COMMENTS`: Extracting comment threads from YouTube API with pagination tokens.
    - `SENTIMENT_ANALYSIS`: Micro-batch tensor evaluation using Google MuRIL.
    - `FINALIZING`: Calculating sentiment distributions and engagement rollups.
  - Highlight: *"Zero fake progress is shown; every stage reflects actual worker state."*

### Step 6: Audience Intelligence Dashboard Overview (1 Minute)
- **Action**: The UI transitions automatically to the **Audience Intelligence Dashboard** (`/dashboard?job_id=...`).
- **Talking Points**:
  - Point to the **Video Overview Card**: Displays video thumbnail, title, channel name, total views, likes, and comment counts.
  - Point to the **Key Metric Cards**:
    - Total Comments Analyzed (e.g., 100).
    - Net Sentiment Approval Index (e.g., $+60\%$).
    - Dominant Sentiment Category Badge.

### Step 7: Sentiment Distribution Visualization (1 Minute)
- **Action**: Hover over the Recharts visual components in the **Sentiment Distribution** card.
- **Talking Points**:
  - *"Here we have interactive charts representing the 5 discrete sentiment classes."*
  - Toggle between **Donut View** and **Bar Chart View**.
  - Highlight the 5-class breakdown: `Positive`, `Negative`, `Neutral`, `Mixed`, and `Unsupported`.
  - Explain: *"Notice that the sum of the five counts strictly equals the total number of analyzed comments—no data is lost or altered."*

### Step 8: Comment Exploration & Faceted Filtering (1 Minute)
- **Action**: Scroll down to the **Comments Table**.
- **Talking Points**:
  - Click on the **"Positive"** filter pill: the table updates immediately to display only positive comments.
  - Click on the **"Mixed"** filter pill: display comments containing co-occurring praise and criticism.
  - Use the search bar to search for a specific term (e.g., `padam` or `bgm`).
  - Demonstrate table pagination controls.

### Step 9: Inspection Modal & Probability Calibration (1 Minute)
- **Action**: Click on the **"Inspect Details"** button on any comment row.
- **Talking Points**:
  - *"Kollamo.ai enforces transparent AI inference."*
  - The modal opens displaying:
    - Original comment text.
    - Author name, published timestamp, and YouTube like count.
    - Winning class and calibrated confidence.
    - Full 5-class softmax probability distribution vector summing to 1.0.
  - Highlight: *"Probabilities represent categorical model uncertainty, never emotional intensity."*

### Step 10: On-Demand English Translation (1 Minute)
- **Action**: In the comment table or modal, click the **"Translate to English"** button on a Malayalam/Manglish comment.
- **Talking Points**:
  - *"To aid non-Malayalam speaking decision-makers, Kollamo.ai provides on-demand translation."*
  - Show the English translated text appearing below the comment.
  - Highlight:
    - *"The original comment is permanently preserved as immutable ground truth."*
    - *"The backend uses an in-memory LRU cache, providing sub-millisecond retrieval on repeated queries."*

### Step 11: High-DPI PDF Report Export (1 Minute)
- **Action**: Click the **"Export PDF Report"** button at the top right of the dashboard.
- **Talking Points**:
  - The browser downloads `kollamo-ai-analysis-<video-id>.pdf`.
  - Open the downloaded PDF in the browser or PDF viewer.
  - Show:
    - Executive title and branding.
    - Video metadata summary and Net Approval Index.
    - 5-class distribution table.
    - Sample comments table.
  - Highlight: *"Notice how the Malayalam characters are rendered cleanly without broken ligatures or squashed boxes. We use high-DPI HTML5 canvas font rendering with Noto Sans Malayalam to ensure publishing-quality output."*

### Step 12: Technical Architecture & API Documentation (1 Minute)
- **Action**: Switch to the browser tab showing FastAPI Swagger documentation (`http://localhost:8000/docs`).
- **Talking Points**:
  - Point to the documented REST endpoints:
    - `GET /health` (lightweight liveness probe).
    - `POST /api/v1/sentiment` (synchronous single comment).
    - `POST /api/v1/analysis/jobs` (asynchronous bulk creation).
    - `GET /api/v1/analysis/jobs/{job_id}` (polling endpoint).
    - `POST /api/v1/translate` (on-demand translation).
  - Highlight strict Pydantic v2 schemas and RFC 7807 error responses.

### Step 13: Error Handling Demonstration (1 Minute)
- **Action**: Return to the **Analyze** page and submit an invalid URL (e.g., `https://invalid-domain.com/video`).
- **Talking Points**:
  - The UI immediately displays a friendly validation error: *"Please enter a valid YouTube URL."*
  - Explain: *"Kollamo.ai never shows raw stack traces or internal server error dumps to users. All errors are categorized gracefully."*

### Step 14: Conclusion, Quality Assurance & Summary (1 Minute)
- **Action**: Show terminal test suite execution summary (or show `docs/FINAL_VERIFICATION_REPORT.md`).
- **Talking Points**:
  - *"The entire platform is backed by 295 automated tests with a 100% pass rate across backend, ML pipeline, and frontend."*
  - *"We adhere to an absolute Zero Fake AI policy: real models, real APIs, and honest probabilistic classifications."*
  - *"Thank you, and I am now ready for questions and technical defense."*
