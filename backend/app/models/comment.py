"""SQLAlchemy Model for Comments."""

import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base


class Comment(Base):
    """Represents an ingested YouTube comment with metadata and classification links."""

    __tablename__ = "comments"

    comment_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    job_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("analysis_jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    video_id: Mapped[Optional[str]] = mapped_column(
        String(32), ForeignKey("videos.video_id", ondelete="SET NULL"), nullable=True, index=True
    )
    original_text: Mapped[str] = mapped_column(Text, nullable=False)
    author_display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    like_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reply_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    detected_language: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    detected_script: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    translated_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    job: Mapped["AnalysisJob"] = relationship("AnalysisJob", back_populates="comments")
    video: Mapped[Optional["Video"]] = relationship("Video", back_populates="comments")
    prediction: Mapped[Optional["Prediction"]] = relationship(
        "Prediction", back_populates="comment", uselist=False, cascade="all, delete-orphan"
    )
