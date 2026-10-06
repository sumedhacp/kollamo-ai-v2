# API Specification — Kollamo.ai

## Overview
The Kollamo.ai REST API provides endpoints for health checks, synchronous single-comment sentiment classification, and asynchronous bulk YouTube comment analysis.

Base URL: `http://localhost:8000/api`

---

## 1. System Health

### `GET /api/health`
Checks server, database, Redis broker, and ML inference readiness.

#### Response: `200 OK`
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "services": {
    "database": "connected",
    "redis": "connected",
    "ml_engine": "loaded"
  },
  "timestamp": "2026-10-06T13:30:00Z"
}
```

---

## 2. Single-Comment Sentiment Analysis

### `POST /api/sentiment`
Synchronously classifies the sentiment of a single comment.

#### Request Body
```json
{
  "text": "Ee padam kidilan aayirunnu, must watch!",
  "translate": true
}
```

#### Response: `200 OK`
```json
{
  "original_text": "Ee padam kidilan aayirunnu, must watch!",
  "detected_language": "ml-en",
  "detected_script": "Latin",
  "sentiment": "positive",
  "confidence": 0.942,
  "class_probabilities": {
    "positive": 0.942,
    "negative": 0.015,
    "neutral": 0.021,
    "mixed": 0.018,
    "unsupported": 0.004
  },
  "translation_status": "translated",
  "translated_text": "This movie was awesome, must watch!"
}
```

#### Error Response: `422 Unprocessable Entity`
Returned if `text` is empty or exceeds character limits.

---

## 3. Bulk YouTube Ingestion & Analysis

### `POST /api/analyze`
Dispatches an asynchronous job to retrieve and analyze YouTube video comments.

#### Request Body
```json
{
  "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "sample_size": 250,
  "sort_mode": "top"
}
```
*`sample_size` options:* `50`, `100`, `250`, `500`, `all`
*`sort_mode` options:* `top` (Most Liked), `newest`, `oldest`

#### Response: `202 Accepted`
```json
{
  "job_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "status": "queued",
  "message": "Analysis job queued successfully",
  "created_at": "2026-10-06T13:35:00Z"
}
```

---

## 4. Job Telemetry & Audience Intelligence

### `GET /api/analyze/{job_id}`
Retrieves progress, status, and audience intelligence summary metrics for a job.

#### Response: `200 OK` (Completed State)
```json
{
  "job_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "status": "completed",
  "progress": 1.0,
  "processed_comments": 250,
  "total_comments": 250,
  "video": {
    "video_id": "dQw4w9WgXcQ",
    "title": "Sample Malayalam Movie Review",
    "channel_title": "Cinema Reviews",
    "view_count": 1250000
  },
  "summary": {
    "sentiment_counts": {
      "positive": 140,
      "negative": 35,
      "neutral": 50,
      "mixed": 20,
      "unsupported": 5
    },
    "sentiment_percentages": {
      "positive": 56.0,
      "negative": 14.0,
      "neutral": 20.0,
      "mixed": 8.0,
      "unsupported": 2.0
    },
    "engagement_metrics": {
      "total_likes": 8450,
      "average_likes_per_sentiment": {
        "positive": 42.1,
        "negative": 12.4,
        "neutral": 8.0,
        "mixed": 19.5,
        "unsupported": 1.2
      }
    }
  },
  "created_at": "2026-10-06T13:35:00Z",
  "completed_at": "2026-10-06T13:36:12Z",
  "error": null
}
```
