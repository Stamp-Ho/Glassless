from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(settings.database_url, echo=False, future=True)
SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session


async def init_db() -> None:
    from app.models import location, location_rating, post  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        column_rows = await conn.exec_driver_sql("PRAGMA table_info(posts)")
        column_names = {row[1] for row in column_rows.fetchall()}

        if "category" not in column_names:
            await conn.exec_driver_sql(
                "ALTER TABLE posts ADD COLUMN category VARCHAR(20) NOT NULL DEFAULT '잡담'"
            )
        if "location_id" not in column_names:
            await conn.exec_driver_sql("ALTER TABLE posts ADD COLUMN location_id INTEGER")
        if "thumbnail_url" not in column_names:
            await conn.exec_driver_sql("ALTER TABLE posts ADD COLUMN thumbnail_url VARCHAR(1000)")
