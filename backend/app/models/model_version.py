"""SQLAlchemy Model for ML Model Versions and Registries."""

import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import String, DateTime, Uuid, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base


class ModelVersion(Base):
    """Represents a registered ML checkpoint version and evaluation benchmark."""

    __tablename__ = "model_versions"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    version_tag: Mapped[str] = mapped_column(String(64), nullable=False)
    checkpoint_hash: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    evaluation_metrics: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    predictions: Mapped[List["Prediction"]] = relationship(
        "Prediction", back_populates="model_version"
    )
