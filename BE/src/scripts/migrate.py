import asyncio
import json
from pathlib import Path

from sqlalchemy import func, select

from app.core.database import SessionLocal, init_db
from app.models.location import Location
from app.models.post import Post, PostCategory
from app.models.comment import Comment

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"


def _to_float(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _combine_address(addr1: str | None, addr2: str | None) -> str | None:
    left = (addr1 or "").strip()
    right = (addr2 or "").strip()
    if left and right:
        return f"{left} {right}"
    if left:
        return left
    if right:
        return right
    return None


def _discover_region_json_files() -> list[Path]:
    files: list[Path] = []
    for region_dir in sorted(DATA_DIR.iterdir()):
        if not region_dir.is_dir():
            continue
        files.extend(sorted(region_dir.glob("*.json")))
    return files


async def migrate_locations() -> None:
    await init_db()

    files = _discover_region_json_files()
    if not files:
        print("No JSON files found under data directory.")
        return

    inserted = 0
    skipped = 0
    inserted_content_ids: list[str] = []

    async with SessionLocal() as session:
        for file_path in files:
            with file_path.open("r", encoding="utf-8") as f:
                payload = json.load(f)

            region = payload.get("region", "서울")
            category = payload.get("contentType", "기타")
            content_type_id = int(payload.get("contentTypeId", 0))

            for item in payload.get("items", []):
                content_id = str(item.get("contentid", "")).strip()
                name = str(item.get("title", "")).strip()
                if not content_id or not name:
                    skipped += 1
                    continue

                stmt = select(Location.id).where(
                    Location.content_id == content_id,
                    Location.name == name,
                )
                exists = (await session.execute(stmt)).first()
                if exists:
                    skipped += 1
                    continue

                session.add(
                    Location(
                        region=region,
                        category=category,
                        content_type_id=content_type_id,
                        content_id=content_id,
                        name=name,
                        description=None,
                        address=_combine_address(item.get("addr1"), item.get("addr2")),
                        tel=(item.get("tel") or "").strip() or None,
                        image_url=(item.get("firstimage") or "").strip() or None,
                        mapx=_to_float(item.get("mapx")),
                        mapy=_to_float(item.get("mapy")),
                        raw_cat1=(item.get("cat1") or "").strip() or None,
                        raw_cat2=(item.get("cat2") or "").strip() or None,
                        raw_cat3=(item.get("cat3") or "").strip() or None,
                    )
                )
                inserted += 1
                inserted_content_ids.append(content_id)

        await session.commit()

        # After committing new locations, create seed posts/comments for them (idempotent)
        if inserted_content_ids:
            for cid in inserted_content_ids:
                stmt = select(Location).where(Location.content_id == cid)
                res = await session.execute(stmt)
                loc = res.scalar_one_or_none()
                if not loc:
                    continue

                # Check whether a post already exists for this location
                post_stmt = select(Post.id).where(Post.location_id == loc.id)
                existing_post = (await session.execute(post_stmt)).first()
                if existing_post:
                    continue

                # create a simple seed post and one comment
                seed_post = Post(
                    title=f"{loc.name} 후기",
                    content=f"이 글은 자동 생성된 샘플 후기입니다. {loc.name}에 대한 간단한 설명입니다.",
                    password="init",
                    category=PostCategory.review.value if hasattr(Post, 'category') else "후기",
                    location_id=loc.id,
                    thumbnail_url=loc.image_url,
                    region=loc.region,
                    rating_score=None,
                )
                session.add(seed_post)
                await session.flush()

                seed_comment = Comment(
                    post_id=seed_post.id,
                    nickname="관리자",
                    password="init",
                    content="샘플 댓글입니다.",
                )
                session.add(seed_comment)

            await session.commit()

    print(f"Migration complete. files={len(files)}, inserted={inserted}, skipped={skipped}")


async def seed_locations_if_empty() -> None:
    await init_db()

    async with SessionLocal() as session:
        result = await session.execute(select(func.count(Location.id)))
        count = result.scalar_one() or 0

    if count > 0:
        print(f"Location table already seeded. count={count}")
        return

    await migrate_locations()


if __name__ == "__main__":
    asyncio.run(migrate_locations())
