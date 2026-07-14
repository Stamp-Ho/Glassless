from sqlalchemy import Float, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Location(Base):
    __tablename__ = "locations"
    __table_args__ = (
        UniqueConstraint("content_id", "name", name="uq_location_content_id_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    region: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    content_type_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    content_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    tel: Mapped[str | None] = mapped_column(String(100), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    mapx: Mapped[float | None] = mapped_column(Float, nullable=True)
    mapy: Mapped[float | None] = mapped_column(Float, nullable=True)

    raw_cat1: Mapped[str | None] = mapped_column(String(50), nullable=True)
    raw_cat2: Mapped[str | None] = mapped_column(String(50), nullable=True)
    raw_cat3: Mapped[str | None] = mapped_column(String(50), nullable=True)
