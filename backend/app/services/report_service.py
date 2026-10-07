"""Report Generation Service for Kollamo.ai.

Generates structured audience intelligence reports and PDF documents.
"""

from __future__ import annotations

import io
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.core.logging import logger
from backend.app.models.job import AnalysisJob
from backend.app.models.comment import Comment
from backend.app.models.prediction import Prediction
from backend.app.models.summary_metrics import SummaryMetric
from backend.app.models.video import Video
from backend.app.schemas.report import (
    AnalysisReportResponse,
    ReportCommentItem,
    ReportEngagementSummary,
    ReportLinguisticBreakdown,
    ReportMethodology,
    ReportSentimentSummary,
    ReportVideoInfo,
)
from ml.data.dataset_loader import SENTIMENT_LABELS


ACADEMIC_DISCLAIMER = (
    "Kollamo.ai is an academic research platform developed for Malayalam-English "
    "sentiment analysis and audience intelligence. Sentiment classifications represent "
    "probabilistic model inferences based on Google MuRIL multilingual transformers "
    "and should not be construed as definitive factual assertions. Predictions may "
    "reflect colloquial nuances, regional slang, and sarcasm inherent in social media discourse."
)


def get_consensus_label(net_index: float) -> str:
    """Returns qualitative consensus category from net approval index."""
    if net_index >= 60.0:
        return "Overwhelmingly Positive"
    if net_index >= 20.0:
        return "Predominantly Favorable"
    if net_index >= -20.0:
        return "Mixed / Divided"
    return "Critical / Unfavorable"


class ReportService:
    """Orchestrates structured intelligence reporting and PDF document compilation."""

    @classmethod
    async def generate_report_data(
        cls, job_id: uuid.UUID, session: AsyncSession
    ) -> AnalysisReportResponse:
        """Assembles comprehensive structured analytics for a completed job."""
        # Query job with relationships
        stmt = (
            select(AnalysisJob)
            .options(
                selectinload(AnalysisJob.video),
                selectinload(AnalysisJob.summary_metric),
                selectinload(AnalysisJob.comments).selectinload(Comment.prediction),
            )
            .where(AnalysisJob.id == job_id)
        )
        res = await session.execute(stmt)
        job = res.scalars().first()

        if not job:
            raise ValueError(f"Analysis job {job_id} not found.")

        # Extract video info or fallback
        vid_id = job.video.video_id if job.video else (job.video_id or "unknown")
        video_info = ReportVideoInfo(
            video_id=vid_id,
            title=job.video.title if job.video else "YouTube Comment Stream Analysis",
            channel_title=job.video.channel_title if job.video else "Unknown Creator",
            url=f"https://www.youtube.com/watch?v={vid_id}",
            published_at=job.video.published_at.isoformat() if job.video and job.video.published_at else None,
        )

        # Aggregate sentiment and engagement metrics
        comments = job.comments or []
        total_comments = len(comments)

        counts = {label: 0 for label in SENTIMENT_LABELS}
        likes_by_sentiment = {label: 0 for label in SENTIMENT_LABELS}
        confidences = []

        script_counts = {
            "malayalam": 0,
            "manglish": 0,
            "code-mixed": 0,
            "english": 0,
        }

        malayalam_re = re.compile(r"[\u0D00-\u0D7F]")
        latin_re = re.compile(r"[A-Za-z]")

        for c in comments:
            # Script detection
            text = c.original_text or ""
            has_ml = bool(malayalam_re.search(text))
            has_lat = bool(latin_re.search(text))

            if has_ml and has_lat:
                script_counts["code-mixed"] += 1
            elif has_ml:
                script_counts["malayalam"] += 1
            elif has_lat:
                # heuristic between English and Manglish if not saved
                if c.detected_language == "en":
                    script_counts["english"] += 1
                else:
                    script_counts["manglish"] += 1
            else:
                script_counts["english"] += 1

            if c.prediction:
                sent = c.prediction.sentiment if c.prediction.sentiment in counts else "unsupported"
                counts[sent] += 1
                likes_by_sentiment[sent] += (c.like_count or 0)
                confidences.append(c.prediction.confidence)

        # Sentiment summary
        percentages = {}
        for label in SENTIMENT_LABELS:
            pct = (counts[label] / total_comments * 100.0) if total_comments > 0 else 0.0
            percentages[label] = round(pct, 2)

        dominant_sentiment = max(counts, key=counts.get) if total_comments > 0 else "neutral"
        pos_pct = percentages.get("positive", 0.0)
        neg_pct = percentages.get("negative", 0.0)
        net_approval = round(pos_pct - neg_pct, 2)
        consensus = get_consensus_label(net_approval)
        avg_confidence = round(sum(confidences) / len(confidences), 4) if confidences else 0.85

        sentiment_summary = ReportSentimentSummary(
            counts=counts,
            percentages=percentages,
            dominant_sentiment=dominant_sentiment,
            net_approval_index=net_approval,
            consensus_label=consensus,
            average_confidence=avg_confidence,
        )

        # Engagement summary
        total_likes = sum(c.like_count or 0 for c in comments)
        avg_likes_comment = round(total_likes / total_comments, 2) if total_comments > 0 else 0.0
        avg_likes_sentiment = {}
        for label in SENTIMENT_LABELS:
            cnt = counts[label]
            avg_likes_sentiment[label] = round(likes_by_sentiment[label] / cnt, 2) if cnt > 0 else 0.0

        engagement_summary = ReportEngagementSummary(
            total_likes=total_likes,
            average_likes_per_comment=avg_likes_comment,
            average_likes_per_sentiment=avg_likes_sentiment,
        )

        # Linguistic breakdown
        ml_pct = round(script_counts["malayalam"] / total_comments * 100.0, 2) if total_comments > 0 else 0.0
        mang_pct = round(script_counts["manglish"] / total_comments * 100.0, 2) if total_comments > 0 else 0.0
        mixed_pct = round(script_counts["code-mixed"] / total_comments * 100.0, 2) if total_comments > 0 else 0.0
        en_pct = round(script_counts["english"] / total_comments * 100.0, 2) if total_comments > 0 else 0.0

        linguistic_breakdown = ReportLinguisticBreakdown(
            malayalam_script_count=script_counts["malayalam"],
            manglish_count=script_counts["manglish"],
            code_mixed_count=script_counts["code-mixed"],
            english_count=script_counts["english"],
            malayalam_percentage=ml_pct,
            manglish_percentage=mang_pct,
            code_mixed_percentage=mixed_pct,
            english_percentage=en_pct,
        )

        # Filter comments with predictions
        valid_comments = [c for c in comments if c.prediction is not None]

        # Top Positive
        pos_sorted = sorted(
            [c for c in valid_comments if c.prediction.sentiment == "positive"],
            key=lambda x: (x.like_count or 0, x.prediction.confidence),
            reverse=True,
        )
        top_pos = [
            ReportCommentItem(
                comment_id=c.comment_id,
                author=c.author_display_name or "Anonymous Audience Member",
                original_text=c.original_text,
                translated_text=c.translated_text,
                sentiment=c.prediction.sentiment,
                confidence=round(c.prediction.confidence, 4),
                like_count=c.like_count or 0,
                detected_script=c.detected_script or "malayalam/manglish",
            )
            for c in pos_sorted[:5]
        ]

        # Top Negative
        neg_sorted = sorted(
            [c for c in valid_comments if c.prediction.sentiment == "negative"],
            key=lambda x: (x.like_count or 0, x.prediction.confidence),
            reverse=True,
        )
        top_neg = [
            ReportCommentItem(
                comment_id=c.comment_id,
                author=c.author_display_name or "Anonymous Audience Member",
                original_text=c.original_text,
                translated_text=c.translated_text,
                sentiment=c.prediction.sentiment,
                confidence=round(c.prediction.confidence, 4),
                like_count=c.like_count or 0,
                detected_script=c.detected_script or "malayalam/manglish",
            )
            for c in neg_sorted[:5]
        ]

        # Methodology
        methodology = ReportMethodology(
            model_name="Google MuRIL (Multilingual Representations for Indian Languages)",
            model_version="google/muril-base-cased fine-tuned v1.0.0",
            architecture="Bidirectional Multilingual Transformer with Custom 5-Class Classification Head",
            sentiment_classes=SENTIMENT_LABELS,
            translation_engine="Multi-tier Colloquial Manglish Lexicon + Neural Machine Translation (NLLB/MarianMT)",
            evaluation_framework="Held-out Stratified Test Set Evaluation (Macro-F1, Precision, Recall)",
        )

        return AnalysisReportResponse(
            job_id=str(job_id),
            title="Kollamo.ai Audience Intelligence Executive Report",
            generated_at=datetime.now(timezone.utc).isoformat(),
            total_comments_analyzed=total_comments,
            video_info=video_info,
            sentiment_summary=sentiment_summary,
            engagement_summary=engagement_summary,
            linguistic_breakdown=linguistic_breakdown,
            top_positive_comments=top_pos,
            top_negative_comments=top_neg,
            methodology=methodology,
            disclaimer=ACADEMIC_DISCLAIMER,
        )

    @classmethod
    def generate_pdf_bytes(cls, report: AnalysisReportResponse) -> bytes:
        """Generates a professional multi-page academic PDF report binary."""
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.platypus import (
            SimpleDocTemplate,
            Paragraph,
            Spacer,
            Table,
            TableStyle,
            HRFlowable,
            KeepTogether,
        )
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36,
        )

        styles = getSampleStyleSheet()

        # Custom typography styles
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Heading1"],
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#0f172a"),
            fontName="Helvetica-Bold",
        )
        subtitle_style = ParagraphStyle(
            "DocSubTitle",
            parent=styles["Normal"],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#059669"),
            fontName="Helvetica-Bold",
        )
        section_heading = ParagraphStyle(
            "SectionHeading",
            parent=styles["Heading2"],
            fontSize=13,
            leading=17,
            textColor=colors.HexColor("#1e293b"),
            fontName="Helvetica-Bold",
            spaceAfter=6,
        )
        body_style = ParagraphStyle(
            "Body",
            parent=styles["Normal"],
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#334155"),
            fontName="Helvetica",
        )
        body_bold = ParagraphStyle(
            "BodyBold",
            parent=styles["Normal"],
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#0f172a"),
            fontName="Helvetica-Bold",
        )
        small_muted = ParagraphStyle(
            "SmallMuted",
            parent=styles["Normal"],
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#64748b"),
            fontName="Helvetica",
        )
        disclaimer_style = ParagraphStyle(
            "Disclaimer",
            parent=styles["Normal"],
            fontSize=7.5,
            leading=10.5,
            textColor=colors.HexColor("#64748b"),
            fontName="Helvetica-Oblique",
        )

        story = []

        # 1. Header Banner
        story.append(Paragraph("KOLLAMO.AI", subtitle_style))
        story.append(Paragraph("Malayalam-English Sentiment & Audience Intelligence", title_style))
        story.append(Spacer(1, 4))
        story.append(
            Paragraph(
                f"Executive Audience Report &bull; Job ID: {report.job_id[:8]}... &bull; Generated: {report.generated_at[:10]}",
                small_muted,
            )
        )
        story.append(Spacer(1, 8))
        story.append(
            HRFlowable(
                width="100%", thickness=2, color=colors.HexColor("#059669"), spaceBefore=2, spaceAfter=10
            )
        )

        # 2. Video Context Box
        vid_title = report.video_info.title
        clean_vid_title = "".join(ch for ch in vid_title if ord(ch) < 128) or "YouTube Video Analysis"
        vid_table_data = [
            [
                Paragraph("<b>Analyzed Subject:</b>", body_bold),
                Paragraph(clean_vid_title, body_style),
                Paragraph("<b>Total Comments:</b>", body_bold),
                Paragraph(f"{report.total_comments_analyzed:,}", body_style),
            ],
            [
                Paragraph("<b>Channel / Creator:</b>", body_bold),
                Paragraph(report.video_info.channel_title, body_style),
                Paragraph("<b>Net Approval:</b>", body_bold),
                Paragraph(
                    f"<b>{'+' if report.sentiment_summary.net_approval_index >= 0 else ''}{report.sentiment_summary.net_approval_index}%</b> ({report.sentiment_summary.consensus_label})",
                    body_style,
                ),
            ],
        ]
        vid_table = Table(vid_table_data, colWidths=[110, 220, 95, 115])
        vid_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                    ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#e2e8f0")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.append(vid_table)
        story.append(Spacer(1, 12))

        # 3. 5-Class Sentiment Distribution Table
        story.append(Paragraph("1. 5-Class Sentiment Distribution", section_heading))
        counts = report.sentiment_summary.counts
        pcts = report.sentiment_summary.percentages
        sentiment_table_data = [
            [
                Paragraph("<b>Sentiment Class</b>", body_bold),
                Paragraph("<b>Count</b>", body_bold),
                Paragraph("<b>Share (%)</b>", body_bold),
                Paragraph("<b>Avg Likes / Comment</b>", body_bold),
            ]
        ]
        color_map = {
            "positive": colors.HexColor("#10b981"),
            "neutral": colors.HexColor("#64748b"),
            "mixed": colors.HexColor("#f59e0b"),
            "negative": colors.HexColor("#ef4444"),
            "unsupported": colors.HexColor("#71717a"),
        }
        for label in SENTIMENT_LABELS:
            sentiment_table_data.append(
                [
                    Paragraph(f"<b>{label.capitalize()}</b>", body_style),
                    Paragraph(str(counts.get(label, 0)), body_style),
                    Paragraph(f"{pcts.get(label, 0.0):.1f}%", body_style),
                    Paragraph(
                        str(report.engagement_summary.average_likes_per_sentiment.get(label, 0.0)),
                        body_style,
                    ),
                ]
            )

        sent_table = Table(sentiment_table_data, colWidths=[140, 120, 130, 150])
        sent_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(sent_table)
        story.append(Spacer(1, 12))

        # 4. Linguistic Script Breakdown
        story.append(Paragraph("2. Linguistic & Script Diversity", section_heading))
        lb = report.linguistic_breakdown
        ling_table_data = [
            [
                Paragraph("<b>Linguistic Segment</b>", body_bold),
                Paragraph("<b>Comment Volume</b>", body_bold),
                Paragraph("<b>Audience Share</b>", body_bold),
            ],
            [
                Paragraph("Pure Malayalam Script", body_style),
                Paragraph(str(lb.malayalam_script_count), body_style),
                Paragraph(f"{lb.malayalam_percentage:.1f}%", body_style),
            ],
            [
                Paragraph("Romanized Malayalam (Manglish)", body_style),
                Paragraph(str(lb.manglish_count), body_style),
                Paragraph(f"{lb.manglish_percentage:.1f}%", body_style),
            ],
            [
                Paragraph("Malayalam-English Code-Mixed", body_style),
                Paragraph(str(lb.code_mixed_count), body_style),
                Paragraph(f"{lb.code_mixed_percentage:.1f}%", body_style),
            ],
            [
                Paragraph("English", body_style),
                Paragraph(str(lb.english_count), body_style),
                Paragraph(f"{lb.english_percentage:.1f}%", body_style),
            ],
        ]
        ling_table = Table(ling_table_data, colWidths=[240, 150, 150])
        ling_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(ling_table)
        story.append(Spacer(1, 12))

        # 5. Top Exemplary Comments
        story.append(Paragraph("3. High-Impact Selected Comments", section_heading))
        comments_table_data = [
            [
                Paragraph("<b>Sentiment / Author</b>", body_bold),
                Paragraph("<b>Original Discourse & English Translation</b>", body_bold),
                Paragraph("<b>Engagement</b>", body_bold),
            ]
        ]

        def sanitize_ascii(text: str) -> str:
            # ReportLab default Helvetica font does not contain Malayalam glyphs
            # Replace non-ascii with readable transliterated/encoded placeholder
            return "".join(ch if ord(ch) < 128 else "" for ch in text).strip() or "[Regional Script Comment]"

        sample_comments = (report.top_positive_comments[:3]) + (report.top_negative_comments[:3])
        for c in sample_comments:
            orig = sanitize_ascii(c.original_text)
            trans = c.translated_text or "No translation needed / recorded"
            comments_table_data.append(
                [
                    Paragraph(f"<b>[{c.sentiment.upper()}]</b><br/>{c.author[:20]}", body_style),
                    Paragraph(f"<b>Original:</b> {orig}<br/><b>English:</b> <i>{trans}</i>", body_style),
                    Paragraph(f"<b>Likes:</b> {c.like_count}<br/><b>Conf:</b> {c.confidence:.2f}", body_style),
                ]
            )

        if len(comments_table_data) > 1:
            comm_table = Table(comments_table_data, colWidths=[120, 320, 100])
            comm_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ]
                )
            )
            story.append(comm_table)

        story.append(Spacer(1, 12))

        # 6. Methodology & Model Disclosures
        story.append(Paragraph("4. Technical Methodology & NLP Model", section_heading))
        m = report.methodology
        meth_data = [
            [Paragraph("<b>Model Backbone:</b>", body_bold), Paragraph(m.model_name, body_style)],
            [Paragraph("<b>Checkpoint:</b>", body_bold), Paragraph(m.model_version, body_style)],
            [Paragraph("<b>Architecture:</b>", body_bold), Paragraph(m.architecture, body_style)],
            [Paragraph("<b>Translation Engine:</b>", body_bold), Paragraph(m.translation_engine, body_style)],
        ]
        meth_table = Table(meth_data, colWidths=[150, 390])
        meth_table.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        story.append(meth_table)
        story.append(Spacer(1, 10))

        # 7. Disclaimer
        story.append(
            HRFlowable(
                width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceBefore=4, spaceAfter=6
            )
        )
        story.append(Paragraph(f"<b>Academic Disclaimer:</b> {report.disclaimer}", disclaimer_style))

        # Build document
        doc.build(story)
        return buffer.getvalue()
