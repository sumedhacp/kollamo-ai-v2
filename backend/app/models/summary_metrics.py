"""SQLAlchemy Model for Job Aggregate Summary Metrics."""

import uuid
from datetime import datetime
from typing import Dict, Any
from sqlalchemy import DateTime, ForeignKey, Uuid, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base


class SummaryMetric(Base):
    """Represents audience intelligence aggregated summary metrics for a job."""

    __tablename__ = "summary_metrics"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("analysis_jobs.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    sentiment_counts: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    sentiment_percentages: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    engagement_metrics: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    job: Mapped["AnalysisJob"] = relationship("AnalysisJob", back_populates="summary_metric")
