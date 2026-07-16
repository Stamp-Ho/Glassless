from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy import func
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.location import Location
from app.models.post import Post
from app.schemas.post import PostCategory, PostCreate, PostDelete, PostListItem, PostResponse, PostUpdate

router = APIRouter(prefix="/posts", tags=["posts"])


@router.get("", response_model=list[PostListItem])
async def list_posts(
    response: Response,
    region: str | None = None,
    category: PostCategory | None = None,
    location_id: int | None = None,
    page: int = 1,
    per_page: int = 20,
    db: AsyncSession = Depends(get_db),
) -> list[PostListItem]:
    query = select(Post)
    if region:
        query = query.where(Post.region == region)
    if category:
        query = query.where(Post.category == category.value)
    if location_id is not None:
        query = query.where(Post.location_id == location_id)
    query = query.order_by(desc(Post.created_at))

    # sanitize paging
    if page < 1:
        page = 1
    if per_page < 1:
        per_page = 1
    per_page = min(per_page, 100)

    # total count for headers
    count_q = select(func.count()).select_from(Post)
    if region:
        count_q = count_q.where(Post.region == region)
    if category:
        count_q = count_q.where(Post.category == category.value)
    if location_id is not None:
        count_q = count_q.where(Post.location_id == location_id)
    total_res = await db.execute(count_q)
    total = int(total_res.scalar_one() or 0)

    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)

    result = await db.execute(query)
    posts = list(result.scalars().all())

    # expose total count for client-side pagination
    response.headers['X-Total-Count'] = str(total)
    return [
        PostListItem(
            id=post.id,
            title=post.title,
            content=post.content[:30],
            category=PostCategory(post.category),
            location_id=post.location_id,
            thumbnail_url=post.thumbnail_url,
            region=post.region,
            rating=post.rating_score,
            comments_count=post.comments_count,
            created_at=post.created_at,
            updated_at=post.updated_at,
        )
        for post in posts
    ]


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(post_id: int, db: AsyncSession = Depends(get_db)) -> Post:
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return post


async def _get_location(location_id: int | None, db: AsyncSession) -> Location | None:
    if location_id is None:
        return None

    result = await db.execute(select(Location).where(Location.id == location_id))
    location = result.scalar_one_or_none()
    if location is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")
    return location


@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(payload: PostCreate, db: AsyncSession = Depends(get_db)) -> Post:
    location = await _get_location(payload.location_id, db)

    # robustly derive category string whether PostCategory enum or raw string
    if isinstance(payload.category, PostCategory):
        category_str = payload.category.value
    else:
        category_str = str(payload.category) if payload.category is not None else None

    region_str = None
    if location:
        region_str = location.region
    elif payload.region:
        region_str = payload.region.strip() or None

    post = Post(
        title=payload.title.strip(),
        content=payload.content.strip(),
        password=payload.password,
        category=category_str,
        location_id=payload.location_id,
        thumbnail_url=location.image_url if location else None,
        region=region_str,
        rating_score=payload.rating if payload.rating is not None else None,
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)
    return post


@router.put("/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: int,
    payload: PostUpdate,
    db: AsyncSession = Depends(get_db),
) -> Post:
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    if post.password != payload.password:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid password")

    if payload.title is not None:
        post.title = payload.title.strip()
    if payload.content is not None:
        post.content = payload.content.strip()
    if payload.category is not None:
        post.category = payload.category.value if isinstance(payload.category, PostCategory) else str(payload.category)
    if "location_id" in payload.model_fields_set:
        if payload.location_id is None:
            post.location_id = None
            post.thumbnail_url = None
        else:
            location = await _get_location(payload.location_id, db)
            post.location_id = location.id
            post.thumbnail_url = location.image_url
            post.region = location.region

    await db.commit()
    await db.refresh(post)
    return post


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: int,
    payload: PostDelete,
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    if post.password != payload.password:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid password")

    await db.delete(post)
    await db.commit()