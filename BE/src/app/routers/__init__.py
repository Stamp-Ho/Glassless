from fastapi import APIRouter

from app.routers import posts, locations, chat, comments

router = APIRouter()

router.include_router(posts.router)
router.include_router(locations.router)
router.include_router(chat.router)
router.include_router(comments.router)

