from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.location import Location
from app.models.post import Post
from app.schemas.post import PostCategory, PostCreate, PostDelete, PostListItem, PostResponse, PostUpdate

router = APIRouter(prefix="/posts", tags=["posts"])


@router.get("", response_model=list[PostListItem])
async def list_posts(
    region: str | None = None,
    category: PostCategory | None = None,
    location_id: int | None = None,
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

    result = await db.execute(query)
    posts = list(result.scalars().all())
    return [
        PostListItem(
            id=post.id,
            title=post.title,
            content=post.content[:30],
            category=PostCategory(post.category),
            location_id=post.location_id,
            region=post.region,
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

    post = Post(
        title=payload.title.strip(),
        content=payload.content.strip(),
        password=payload.password,
        category=payload.category.value,
        location_id=payload.location_id,
        thumbnail_url=location.image_url if location else None,
        region=location.region if location else (payload.region.strip() if payload.region else None),
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
        post.category = payload.category.value
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
