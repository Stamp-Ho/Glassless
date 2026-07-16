from datetime import datetime, timedelta
import math

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.location import Location
from app.models.location_rating import LocationRating
from app.schemas.location import LocationRatingCreate, LocationRatingResponse, LocationResponse

router = APIRouter(prefix="/locations", tags=["locations"])


def _get_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    if request.client and request.client.host:
        return request.client.host

    return "unknown"


async def _attach_rating_stats(locations: list[Location], db: AsyncSession) -> list[Location]:
    if not locations:
        return locations

    location_ids = [location.id for location in locations]
    stats_stmt = (
        select(
            LocationRating.location_id.label("location_id"),
            func.count(LocationRating.id).label("rating_count"),
            func.round(func.avg(LocationRating.score), 1).label("rating_avg"),
        )
        .where(LocationRating.location_id.in_(location_ids))
        .group_by(LocationRating.location_id)
    )
    stats_result = await db.execute(stats_stmt)
    stats_map = {row.location_id: row for row in stats_result.all()}

    for location in locations:
        stats = stats_map.get(location.id)
        location.rating_count = int(stats.rating_count) if stats else 0
        location.rating_avg = float(stats.rating_avg) if stats and stats.rating_avg is not None else 0.0

    return locations


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
    locations = list(result.scalars().all())
    return await _attach_rating_stats(locations, db)


@router.get("/{location_id}", response_model=LocationResponse)
async def get_location(location_id: int, db: AsyncSession = Depends(get_db)) -> Location:
    stmt = select(Location).where(Location.id == location_id)
    result = await db.execute(stmt)
    location = result.scalar_one_or_none()
    if location is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")

    await _attach_rating_stats([location], db)
    return location


@router.post("/{location_id}/ratings", response_model=LocationRatingResponse, status_code=status.HTTP_201_CREATED)
async def create_location_rating(
    location_id: int,
    payload: LocationRatingCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> LocationRatingResponse:
    if payload.score < 1 or payload.score > 5:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Score must be between 1 and 5")

    location_stmt = select(Location.id).where(Location.id == location_id)
    location_result = await db.execute(location_stmt)
    if location_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")

    client_ip = _get_client_ip(request)
    user_agent = request.headers.get("user-agent", "unknown")
    cutoff = datetime.utcnow() - timedelta(hours=settings.rating_cooldown_hours)

    recent_stmt = (
        select(LocationRating)
        .where(
            LocationRating.location_id == location_id,
            LocationRating.created_at >= cutoff,
        )
        .order_by(desc(LocationRating.created_at))
    )
    recent_result = await db.execute(recent_stmt)
    recent_ratings = list(recent_result.scalars().all())

    for rating in recent_ratings:
        if rating.client_id == payload.client_id:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="You already rated this location recently")
        if rating.ip_address == client_ip and rating.user_agent == user_agent:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="This browser/network already rated this location recently")

    rating = LocationRating(
        location_id=location_id,
        score=payload.score,
        client_id=payload.client_id.strip(),
        ip_address=client_ip,
        user_agent=user_agent,
    )
    db.add(rating)
    await db.commit()
    await db.refresh(rating)

    stats_stmt = (
        select(
            func.count(LocationRating.id).label("rating_count"),
            func.round(func.avg(LocationRating.score), 1).label("rating_avg"),
        )
        .where(LocationRating.location_id == location_id)
    )
    stats_result = await db.execute(stats_stmt)
    stats = stats_result.one()

    return LocationRatingResponse(
        id=rating.id,
        location_id=rating.location_id,
        score=rating.score,
        client_id=rating.client_id,
        rating_count=int(stats.rating_count or 0),
        rating_avg=float(stats.rating_avg or 0.0),
    )
