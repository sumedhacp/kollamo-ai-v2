"""Unit and Integration Tests for Report Generation and PDF Export Services."""

import uuid
import pytest
from httpx import AsyncClient

from backend.app.schemas.report import (
    AnalysisReportResponse,
    ReportCommentItem,
    ReportEngagementSummary,
    ReportLinguisticBreakdown,
    ReportMethodology,
    ReportSentimentSummary,
    ReportVideoInfo,
)
from backend.app.services.report_service import ReportService, get_consensus_label


def test_consensus_label():
    """Verifies consensus label calculation across Net Sentiment thresholds."""
    assert get_consensus_label(75.0) == "Overwhelmingly Positive"
    assert get_consensus_label(35.0) == "Predominantly Favorable"
    assert get_consensus_label(0.0) == "Mixed / Divided"
    assert get_consensus_label(-30.0) == "Critical / Unfavorable"


def test_pdf_generation_bytes():
    """Verifies that ReportService.generate_pdf_bytes compiles a valid PDF binary."""
    sample_report = AnalysisReportResponse(
        job_id=str(uuid.uuid4()),
        generated_at="2026-10-07T00:00:00Z",
        total_comments_analyzed=100,
        video_info=ReportVideoInfo(
            video_id="dQw4w9WgXcQ",
            title="Aavesham Official Trailer Review & Public Response",
            channel_title="Mollywood Trends",
            url="https://youtube.com/watch?v=dQw4w9WgXcQ",
            published_at="2026-04-10T10:00:00Z",
        ),
        sentiment_summary=ReportSentimentSummary(
            counts={"positive": 65, "neutral": 15, "mixed": 10, "negative": 8, "unsupported": 2},
            percentages={"positive": 65.0, "neutral": 15.0, "mixed": 10.0, "negative": 8.0, "unsupported": 2.0},
            dominant_sentiment="positive",
            net_approval_index=57.0,
            consensus_label="Predominantly Favorable",
            average_confidence=0.9125,
        ),
        engagement_summary=ReportEngagementSummary(
            total_likes=1450,
            average_likes_per_comment=14.5,
            average_likes_per_sentiment={
                "positive": 18.2,
                "neutral": 5.1,
                "mixed": 8.4,
                "negative": 12.0,
                "unsupported": 1.0,
            },
        ),
        linguistic_breakdown=ReportLinguisticBreakdown(
            malayalam_script_count=45,
            manglish_count=35,
            code_mixed_count=15,
            english_count=5,
            malayalam_percentage=45.0,
            manglish_percentage=35.0,
            code_mixed_percentage=15.0,
            english_percentage=5.0,
        ),
        top_positive_comments=[
            ReportCommentItem(
                comment_id="c1",
                author="Rahul Menon",
                original_text="Fahadh Faasil acting vere level, Sushin Shyam bgm romancham!",
                translated_text="Fahadh Faasil's acting is another level, Sushin Shyam BGM gave goosebumps!",
                sentiment="positive",
                confidence=0.965,
                like_count=320,
                detected_script="manglish",
            )
        ],
        top_negative_comments=[
            ReportCommentItem(
                comment_id="c2",
                author="Vineeth K",
                original_text="Second half valare bore aayirunnu, full lag waste of money.",
                translated_text="Second half was very boring, full of lag and waste of money.",
                sentiment="negative",
                confidence=0.945,
                like_count=45,
                detected_script="manglish",
            )
        ],
        methodology=ReportMethodology(
            model_name="Google MuRIL (Multilingual Representations for Indian Languages)",
            model_version="google/muril-base-cased fine-tuned v1.0.0",
            architecture="Bidirectional Multilingual Transformer",
            sentiment_classes=["positive", "negative", "neutral", "mixed", "unsupported"],
            translation_engine="Multi-tier Colloquial Manglish Lexicon + Neural Machine Translation",
            evaluation_framework="Held-out Stratified Test Set Evaluation",
        ),
        disclaimer="Kollamo.ai is an academic research platform developed for Malayalam-English sentiment analysis.",
    )

    pdf_bytes = ReportService.generate_pdf_bytes(sample_report)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    # PDF magic byte header check
    assert pdf_bytes.startswith(b"%PDF")


@pytest.mark.asyncio
async def test_get_job_report_endpoint(async_client: AsyncClient):
    """Verifies GET /api/analyze/{job_id}/report returns structured report data."""
    # Create an initial job
    create_resp = await async_client.post(
        "/api/analyze",
        json={"youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "sample_size": 50},
    )
    job_id = create_resp.json()["job_id"]

    report_resp = await async_client.get(f"/api/analyze/{job_id}/report")
    assert report_resp.status_code == 200
    data = report_resp.json()
    assert data["job_id"] == job_id
    assert "video_info" in data
    assert "sentiment_summary" in data
    assert "engagement_summary" in data
    assert "linguistic_breakdown" in data
    assert "methodology" in data
    assert "disclaimer" in data


@pytest.mark.asyncio
async def test_get_job_report_pdf_endpoint(async_client: AsyncClient):
    """Verifies GET /api/analyze/{job_id}/report/pdf streams downloadable PDF."""
    create_resp = await async_client.post(
        "/api/analyze",
        json={"youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "sample_size": 50},
    )
    job_id = create_resp.json()["job_id"]

    pdf_resp = await async_client.get(f"/api/analyze/{job_id}/report/pdf")
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"
    assert "attachment" in pdf_resp.headers["content-disposition"]
    assert pdf_resp.content.startswith(b"%PDF")


@pytest.mark.asyncio
async def test_report_endpoints_not_found(async_client: AsyncClient):
    """Verifies 404 response for non-existent job report requests."""
    random_uuid = str(uuid.uuid4())
    resp1 = await async_client.get(f"/api/analyze/{random_uuid}/report")
    assert resp1.status_code == 404

    resp2 = await async_client.get(f"/api/analyze/{random_uuid}/report/pdf")
    assert resp2.status_code == 404


@pytest.mark.asyncio
async def test_translate_job_comments_endpoint(async_client: AsyncClient):
    """Verifies POST /api/analyze/{job_id}/translate-comments executes."""
    create_resp = await async_client.post(
        "/api/analyze",
        json={"youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "sample_size": 50},
    )
    job_id = create_resp.json()["job_id"]

    trans_resp = await async_client.post(f"/api/analyze/{job_id}/translate-comments?limit=10")
    assert trans_resp.status_code == 200
    data = trans_resp.json()
    assert "translated_count" in data
    assert data["job_id"] == job_id
