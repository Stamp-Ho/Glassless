from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.location import Location
from app.schemas.location import LocationResponse

router = APIRouter(prefix="/locations", tags=["locations"])


@router.get("", response_model=list[LocationResponse])
async def list_locations(
    region: str | None = Query(default=None, max_length=50),
    category: str | None = Query(default=None, max_length=100),
    keyword: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> list[Location]:
    stmt = select(Location)

    if region:
        stmt = stmt.where(Location.region == region.strip())
    if category:
        stmt = stmt.where(Location.category == category.strip())
    if keyword:
        like_pattern = f"%{keyword.strip()}%"
        stmt = stmt.where(
            Location.name.ilike(like_pattern)
            | Location.address.ilike(like_pattern)
            | Location.content_id.ilike(like_pattern)
        )

    stmt = stmt.order_by(Location.id.asc()).offset(offset).limit(limit)

    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/{location_id}", response_model=LocationResponse)
async def get_location(location_id: int, db: AsyncSession = Depends(get_db)) -> Location:
    stmt = select(Location).where(Location.id == location_id)
    result = await db.execute(stmt)
    location = result.scalar_one_or_none()
    if location is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")
    return location
