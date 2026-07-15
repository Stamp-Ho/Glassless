from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.comment import Comment
from app.models.post import Post
from app.schemas.comment import CommentCreate, CommentResponse, CommentUpdate

router = APIRouter(prefix="/comments", tags=["comments"])


@router.post("/posts/{post_id}", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(post_id: int, payload: CommentCreate, db: AsyncSession = Depends(get_db)) -> Comment:
    # validate post
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    comment = Comment(post_id=post_id, nickname=payload.nickname.strip(), password=payload.password, content=payload.content.strip())
    db.add(comment)
    # increment post.comments_count
    await db.flush()
    await db.execute(update(Post).where(Post.id == post_id).values(comments_count=Post.comments_count + 1))
    await db.commit()
    await db.refresh(comment)
    return comment

@router.get("/posts/{post_id}", response_model=list[CommentResponse])
async def get_comments(post_id: int, db: AsyncSession = Depends(get_db)) -> list[Comment]:
    result = await db.execute(select(Comment).where(Comment.post_id == post_id).order_by(Comment.created_at.desc()))
    comments = result.scalars().all()
    return comments

@router.put("/{comment_id}", response_model=CommentResponse)
async def update_comment(comment_id: int, payload: CommentUpdate, db: AsyncSession = Depends(get_db)) -> Comment:
    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    if comment.password != payload.password:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid password")

    comment.content = payload.content.strip()
    await db.commit()
    await db.refresh(comment)
    return comment


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(comment_id: int, payload: CommentUpdate, db: AsyncSession = Depends(get_db)) -> None:
    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    if comment.password != payload.password:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid password")

    post_id = comment.post_id
    await db.delete(comment)
    await db.execute(update(Post).where(Post.id == post_id).values(comments_count=Post.comments_count - 1))
    await db.commit()
    return None
