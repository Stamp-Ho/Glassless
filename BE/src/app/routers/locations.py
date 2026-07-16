from datetime import datetime, timedelta
import math

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import desc, func, select
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
    mapx: float | None = Query(default=None),
    mapy: float | None = Query(default=None),
    radius_km: float = Query(default=10.0, gt=0, le=100),
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

    if (mapx is None) != (mapy is None):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="mapx and mapy must be provided together")

    if mapx is not None and mapy is not None:
        lat_km_per_deg = 111.32
        lng_km_per_deg = max(111.32 * math.cos(math.radians(mapy)), 1e-6)
        lat_delta = radius_km / lat_km_per_deg
        lng_delta = radius_km / lng_km_per_deg

        stmt = stmt.where(Location.mapx.isnot(None), Location.mapy.isnot(None))
        stmt = stmt.where(
            Location.mapy >= mapy - lat_delta,
            Location.mapy <= mapy + lat_delta,
            Location.mapx >= mapx - lng_delta,
            Location.mapx <= mapx + lng_delta,
        )

        lat_diff_km = (Location.mapy - mapy) * lat_km_per_deg
        lng_diff_km = (Location.mapx - mapx) * lng_km_per_deg
        distance_sq_expr = lat_diff_km * lat_diff_km + lng_diff_km * lng_diff_km
        stmt = stmt.order_by(distance_sq_expr.asc(), Location.id.asc())
    else:
        stmt = stmt.order_by(Location.id.asc())

    stmt = stmt.offset(offset).limit(limit)

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
