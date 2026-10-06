"""SQLAlchemy Model for Analysis Jobs."""

import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base


class AnalysisJob(Base):
    """Represents an asynchronous or queued sentiment analysis job."""

    __tablename__ = "analysis_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    video_id: Mapped[Optional[str]] = mapped_column(
        String(32), ForeignKey("videos.video_id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(
        String(32), default="queued", nullable=False, index=True
    )
    sample_size_requested: Mapped[int] = mapped_column(Integer, default=250, nullable=False)
    sort_mode: Mapped[str] = mapped_column(String(32), default="top", nullable=False)
    total_comments: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    processed_comments: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    video: Mapped[Optional["Video"]] = relationship("Video", back_populates="jobs")
    comments: Mapped[List["Comment"]] = relationship(
        "Comment", back_populates="job", cascade="all, delete-orphan"
    )
    summary_metric: Mapped[Optional["SummaryMetric"]] = relationship(
        "SummaryMetric", back_populates="job", uselist=False, cascade="all, delete-orphan"
    )
