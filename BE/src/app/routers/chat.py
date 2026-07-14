import re

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.location import Location
from app.schemas.chat import ChatRequest, ChatResponse, LocationRef

router = APIRouter(prefix="/chat", tags=["chat"])


def _extract_keywords(query: str) -> list[str]:
    normalized = re.sub(r"\s+", " ", query).strip()
    tokens = [token for token in normalized.split(" ") if len(token) >= 2]
    return tokens[:8]


def _build_context(rows: list[Location]) -> str:
    lines: list[str] = []
    for idx, row in enumerate(rows, 1):
        line = (
            f"[{idx}] 이름={row.name} | 카테고리={row.category} | "
            f"주소={row.address or '-'} | 전화={row.tel or '-'}"
        )
        lines.append(line)
    return "\n".join(lines)


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

    tokens = _extract_keywords(query_text)
    stmt = select(Location)

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

    if like_filters:
        filters.append(or_(*like_filters))

    if filters:
        stmt = stmt.where(*filters)

    stmt = stmt.limit(settings.chat_max_references)
    result = await db.execute(stmt)
    rows = list(result.scalars().all())

    if not rows:
        return ChatResponse(answer="조건에 맞는 서울 지역 데이터를 찾지 못했습니다.", references=[])

    if not settings.openai_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OPENAI_API_KEY is not configured",
        )

    context_text = _build_context(rows)
    system_prompt = (
        "당신은 LocalHub 지역 정보 어시스턴트입니다. "
        "반드시 제공된 지역 데이터만 근거로 답변하세요. "
        "데이터에 없는 내용은 추측하지 말고 모른다고 답변하세요."
    )

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
        LocationRef(id=row.id, name=row.name, category=row.category, address=row.address)
        for row in rows
    ]
    return ChatResponse(answer=answer, references=refs)
