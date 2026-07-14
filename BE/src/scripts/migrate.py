import asyncio
import json
from pathlib import Path

from sqlalchemy import select

from app.core.database import SessionLocal, init_db
from app.models.location import Location

BASE_DIR = Path(__file__).resolve().parents[2]
SEOUL_DATA_DIR = BASE_DIR / "data" / "서울"


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


async def migrate_seoul() -> None:
    await init_db()

    files = sorted(SEOUL_DATA_DIR.glob("서울_*.json"))
    if not files:
        print("No Seoul JSON files found.")
        return

    inserted = 0
    skipped = 0

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

        await session.commit()

    print(f"Migration complete. inserted={inserted}, skipped={skipped}")


if __name__ == "__main__":
    asyncio.run(migrate_seoul())
