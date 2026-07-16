from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class LocationRating(Base):
    __tablename__ = "location_ratings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"), nullable=False, index=True)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
