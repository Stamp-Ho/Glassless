from datetime import datetime, timedelta
from typing import Dict, Any

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.post import Post
from app.models.comment import Comment
from app.models.location import Location

router = APIRouter(prefix="/stats", tags=["stats"])

# canonical regions used in app
CANONICAL_REGIONS = ["광주_전라권", "구미_경북권", "대전_충청권", "부산", "서울"]


@router.get("/regions")
async def regions_stats(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """Return stats per canonical region for the past 7 days.

    For each region return:
      - total_posts: int
      - total_comments: int
      - by_category: {category: {posts:int, comments:int}}
      - top_locations: list of {location_id: int, name: str, post_count: int} (top 5 by post_count)
    """
    now = datetime.utcnow()
    since = now - timedelta(days=7)

    results: Dict[str, Any] = {}

    for region in CANONICAL_REGIONS:
        # total posts
        stmt_posts = select(func.count(Post.id)).where(Post.created_at >= since, Post.region == region)
        total_posts = (await db.execute(stmt_posts)).scalar() or 0

        # total comments (comments on posts in region)
        stmt_comments = (
            select(func.count(Comment.id))
            .join(Post, Comment.post_id == Post.id)
            .where(Comment.created_at >= since, Post.region == region)
        )
        total_comments = (await db.execute(stmt_comments)).scalar() or 0

        # categories breakdown for posts
        categories = ["잡담", "후기", "질문", "구인"]
        by_category = {}
        for cat in categories:
            stmt_cat_posts = select(func.count(Post.id)).where(Post.created_at >= since, Post.region == region, Post.category == cat)
            pcount = (await db.execute(stmt_cat_posts)).scalar() or 0
            stmt_cat_comments = (
                select(func.count(Comment.id))
                .join(Post, Comment.post_id == Post.id)
                .where(Comment.created_at >= since, Post.region == region, Post.category == cat)
            )
            ccount = (await db.execute(stmt_cat_comments)).scalar() or 0
            by_category[cat] = {"posts": int(pcount), "comments": int(ccount)}

        # top 5 connected locations by post count (only posts count)
        stmt_top_locations = (
            select(Location.id, Location.name, func.count(Post.id).label("post_count"))
            .join(Post, Post.location_id == Location.id)
            .where(Post.created_at >= since, Location.region == region)
            .group_by(Location.id)
            .order_by(func.count(Post.id).desc())
            .limit(5)
        )
        top_locs_rows = (await db.execute(stmt_top_locations)).all()
        top_locations = [
            {"location_id": int(r.id), "name": r.name, "post_count": int(r.post_count)} for r in top_locs_rows
        ]

        results[region] = {
            "total_posts": int(total_posts),
            "total_comments": int(total_comments),
            "by_category": by_category,
            "top_locations": top_locations,
        }

    return {"since": since.isoformat(), "until": now.isoformat(), "regions": results}
