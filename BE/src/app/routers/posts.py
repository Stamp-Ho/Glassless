from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.post import Post
from app.schemas.post import PostCreate, PostDelete, PostListItem, PostResponse, PostUpdate

router = APIRouter(prefix="/posts", tags=["posts"])


@router.get("", response_model=list[PostListItem])
async def list_posts(
    region: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[Post]:
    query = select(Post)
    if region:
        query = query.where(Post.region == region)
    query = query.order_by(desc(Post.created_at))

    result = await db.execute(query)
    return list(result.scalars().all())


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(post_id: int, db: AsyncSession = Depends(get_db)) -> Post:
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return post


@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(payload: PostCreate, db: AsyncSession = Depends(get_db)) -> Post:
    post = Post(
        title=payload.title.strip(),
        content=payload.content.strip(),
        password=payload.password,
        region=payload.region.strip() if payload.region else None,
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
