import re

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.location import Location
from app.models.location_rating import LocationRating
from app.schemas.chat import ChatRequest, ChatResponse, LocationRef

router = APIRouter(prefix="/chat", tags=["chat"])


def _extract_keywords(query: str) -> list[str]:
    normalized = re.sub(r"\s+", " ", query).strip()
    tokens = [token for token in normalized.split(" ") if len(token) >= 2]
    return tokens[:8]


async def _fetch_candidates(payload: ChatRequest, db: AsyncSession) -> list[dict]:
    tokens = _extract_keywords(payload.query)
    stmt = (
        select(
            Location,
            func.coalesce(func.round(func.avg(LocationRating.score), 1), 0.0).label("rating_avg"),
            func.coalesce(func.count(LocationRating.id), 0).label("rating_count"),
        )
        .outerjoin(LocationRating, LocationRating.location_id == Location.id)
    )

    filters = []
    if payload.region:
        filters.append(Location.region == payload.region.strip())
    if payload.category:
        filters.append(Location.category == payload.category.strip())

    like_filters = []
    for token in tokens:
        pattern = f"%{token}%"
        like_filters.append(Location.name.ilike(pattern))
        like_filters.append(Location.address.ilike(pattern))
        like_filters.append(Location.category.ilike(pattern))

    if like_filters:
        filters.append(or_(*like_filters))

    if filters:
        stmt = stmt.where(*filters)

    stmt = stmt.group_by(Location.id).order_by(func.coalesce(func.avg(LocationRating.score), 0.0).desc(), Location.id.asc())
    stmt = stmt.limit(settings.chat_max_references)

    result = await db.execute(stmt)
    rows = []
    for location, rating_avg, rating_count in result.all():
        rows.append(
            {
                "location": location,
                "rating_avg": float(rating_avg or 0.0),
                "rating_count": int(rating_count or 0),
            }
        )
    return rows


def _build_context(rows: list[dict]) -> str:
    lines: list[str] = []
    for idx, row in enumerate(rows, 1):
        location: Location = row["location"]
        lines.append(
            f"[{idx}] 이름={location.name} | 권역={location.region} | 카테고리={location.category} | "
            f"주소={location.address or '-'} | 전화={location.tel or '-'} | "
            f"별점={row['rating_avg']:.1f}({row['rating_count']}개)"
        )
    return "\n".join(lines)


def _build_system_prompt() -> str:
    return (
        "당신은 LocalHub의 지역 정보 챗봇이다. "
        "반드시 아래 [참고 데이터]에 포함된 로컬 데이터만 사용해서 답변한다. "
        "외부 지식, 추측, 일반 상식, 인터넷 정보는 사용하지 않는다. "
        "질문이 참고 데이터로 답할 수 없으면 '제공된 로컬 데이터만으로는 답할 수 없습니다.'라고 말한다. "
        "답변은 한국어로 짧고 명확하게 작성한다. "
        "사용자가 장소 추천을 요청하면 참고 데이터에서 가장 적절한 항목을 우선적으로 제시한다. "
        "정확한 수치나 사실은 참고 데이터에 있는 값만 사용한다."
    )


@router.post("", response_model=ChatResponse)
async def chat(payload: ChatRequest, db: AsyncSession = Depends(get_db)) -> ChatResponse:
    query_text = payload.query.strip()
    if not query_text:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Query is empty")
    if len(query_text) > settings.chat_max_query_length:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Query too long. Max length is {settings.chat_max_query_length}",
        )

    if not settings.openai_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OPENAI_API_KEY is not configured",
        )

    rows = await _fetch_candidates(payload, db)
    if not rows:
        return ChatResponse(answer="제공된 로컬 데이터만으로는 답할 수 없습니다.", references=[])

    context_text = _build_context(rows)
    system_prompt = _build_system_prompt()

    body = {
        "model": settings.openai_model,
        "max_tokens": settings.openai_max_tokens,
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"[참고 데이터]\n{context_text}\n\n[질문]\n{query_text}",
            },
        ],
    }

    timeout = httpx.Timeout(settings.openai_timeout_seconds)
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=body,
            )
            response.raise_for_status()
            data = response.json()
    except httpx.TimeoutException as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="OpenAI timeout") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="OpenAI request failed") from exc

    answer = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    refs = [
        LocationRef(
            id=row["location"].id,
            name=row["location"].name,
            category=row["location"].category,
            address=row["location"].address,
        )
        for row in rows
    ]
    return ChatResponse(answer=answer, references=refs)
