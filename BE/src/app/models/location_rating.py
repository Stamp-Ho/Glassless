from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class LocationRating(Base):
    __tablename__ = "location_ratings"
    __table_args__ = (
        Index("ix_location_ratings_location_created_at", "location_id", "created_at"),
        Index("ix_location_ratings_location_client_id", "location_id", "client_id"),
        Index("ix_location_ratings_location_ip_user_agent", "location_id", "ip_address", "user_agent"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"), nullable=False, index=True)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    client_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    ip_address: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    user_agent: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
