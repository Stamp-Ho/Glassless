from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html

from app.core.config import settings
from app.core.database import init_db
from app.routers.chat import router as chat_router
from app.routers.locations import router as locations_router
from app.routers.posts import router as posts_router
from app.routers.comments import router as comments_router
from app.routers.stats import router as stats_router
from scripts.migrate import seed_locations_if_empty


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await seed_locations_if_empty()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

cors_allow_origins = settings.cors_origins_list
cors_allow_credentials = True
if settings.app_env and settings.app_env.lower() == 'dev':
    # In dev, allow all origins for convenience (no credentials)
    cors_allow_origins = ["*"]
    cors_allow_credentials = False

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_allow_origins,
    allow_credentials=cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count", "X-Total-Pages", "X-Has-Next"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/swagger-ui", include_in_schema=False)
async def swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{settings.app_name} - Swagger UI",
    )


app.include_router(posts_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(locations_router, prefix="/api")
app.include_router(comments_router, prefix="/api")
app.include_router(stats_router, prefix="/api")
