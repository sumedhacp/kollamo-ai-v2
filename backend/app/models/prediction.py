"""SQLAlchemy Model for Sentiment Predictions."""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy import String, Float, DateTime, ForeignKey, Uuid, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base


class Prediction(Base):
    """Represents a fine-grained sentiment classification prediction for a comment."""

    __tablename__ = "predictions"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    comment_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("comments.comment_id", ondelete="CASCADE"), nullable=False, index=True
    )
    model_version_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("model_versions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    sentiment: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    class_probabilities: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    comment: Mapped["Comment"] = relationship("Comment", back_populates="prediction")
    model_version: Mapped[Optional["ModelVersion"]] = relationship(
        "ModelVersion", back_populates="predictions"
    )
