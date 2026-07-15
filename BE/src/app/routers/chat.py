import re

import httpx
import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.location import Location
from app.models.location_rating import LocationRating
from app.schemas.chat import ChatRequest, ChatResponse, LocationRef

router = APIRouter(prefix="/chat", tags=["chat"])

_REGION_ALIASES: dict[str, tuple[str, ...]] = {
    "서울": ("서울", "서울시", "서울특별시"),
    "부산": ("부산", "부산시", "부산광역시"),
    "대구": ("대구", "대구시", "대구광역시"),
    "인천": ("인천", "인천시", "인천광역시"),
    "광주": ("광주", "광주시", "광주광역시"),
    "대전": ("대전", "대전시", "대전광역시"),
    "울산": ("울산", "울산시", "울산광역시"),
    "세종": ("세종", "세종시", "세종특별자치시"),
    "경기": ("경기", "경기도"),
    "강원": ("강원", "강원도"),
    "충북": ("충북", "충청북도"),
    "충남": ("충남", "충청남도"),
    "전북": ("전북", "전라북도"),
    "전남": ("전남", "전라남도"),
    "경북": ("경북", "경상북도"),
    "경남": ("경남", "경상남도"),
    "제주": ("제주", "제주도", "제주특별자치도"),
}


# simple category aliases mapping: map many user words to canonical category
_CATEGORY_ALIASES: dict[str, tuple[str, ...]] = {
    "관광지": ("관광지", "관광", "명소", "볼거리"),
    "레포츠": ("레포츠", "스포츠", "액티비티", "레저"),
    "여행코스": ("여행코스", "코스", "코스추천"),
    "문화시설": ("문화시설", "박물관", "미술관", "전시"),
    "쇼핑": ("쇼핑", "몰", "시장"),
    "숙박": ("숙박", "호텔", "게스트하우스", "민박"),
    "음식점": ("음식점", "맛집", "식당", "카페"),
    "축제공연행사": ("축제", "공연", "행사", "페스티벌"),
}


def _infer_category(query: str) -> str | None:
    normalized = re.sub(r"\s+", " ", query).strip().lower()
    for canonical, aliases in _CATEGORY_ALIASES.items():
        for alias in aliases:
            if alias in normalized:
                return canonical
    return None


def _extract_keywords(query: str) -> list[str]:
    normalized = re.sub(r"\s+", " ", query).strip()
    tokens = [token for token in normalized.split(" ") if len(token) >= 2]
    return tokens[:8]


def _infer_region(query: str) -> str | None:
    normalized = re.sub(r"\s+", "", query)
    for region, aliases in _REGION_ALIASES.items():
        if any(alias in normalized for alias in aliases):
            return region
    return None


async def _fetch_candidates(payload: ChatRequest, db: AsyncSession) -> list[dict]:
    tokens = _extract_keywords(payload.query)
    inferred_region = payload.region.strip() if payload.region else _infer_region(payload.query)
    stmt = (
        select(
            Location,
            func.coalesce(func.round(func.avg(LocationRating.score), 1), 0.0).label("rating_avg"),
            func.coalesce(func.count(LocationRating.id), 0).label("rating_count"),
        )
        .outerjoin(LocationRating, LocationRating.location_id == Location.id)
    )

    like_filters = []
    for token in tokens:
        pattern = f"%{token}%"
        like_filters.append(Location.name.ilike(pattern))
        like_filters.append(Location.address.ilike(pattern))
        like_filters.append(Location.category.ilike(pattern))

    async def execute_with_filters(*, include_region: bool, include_category: bool, include_keywords: bool) -> list[dict]:
        scoped_stmt = stmt
        scoped_filters = []
        if include_region and inferred_region:
            scoped_filters.append(Location.region == inferred_region)
        if include_category and payload.category:
            scoped_filters.append(Location.category == payload.category.strip())
        if include_keywords and like_filters:
            scoped_filters.append(or_(*like_filters))

        if scoped_filters:
            scoped_stmt = scoped_stmt.where(*scoped_filters)

        scoped_stmt = scoped_stmt.group_by(Location.id).order_by(
            func.coalesce(func.avg(LocationRating.score), 0.0).desc(),
            func.count(LocationRating.id).desc(),
            Location.id.asc(),
        )
        scoped_stmt = scoped_stmt.limit(settings.chat_max_references)

        scoped_result = await db.execute(scoped_stmt)
        scoped_rows = []
        for location, rating_avg, rating_count in scoped_result.all():
            scoped_rows.append(
                {
                    "location": location,
                    "rating_avg": float(rating_avg or 0.0),
                    "rating_count": int(rating_count or 0),
                }
            )
        return scoped_rows

    if inferred_region:
        candidate_sets: list[list[dict]] = [
            await execute_with_filters(include_region=True, include_category=True, include_keywords=True),
            await execute_with_filters(include_region=True, include_category=True, include_keywords=False),
            await execute_with_filters(include_region=True, include_category=False, include_keywords=True),
            await execute_with_filters(include_region=True, include_category=False, include_keywords=False),
        ]
    else:
        candidate_sets = [
            await execute_with_filters(include_region=True, include_category=True, include_keywords=True),
            await execute_with_filters(include_region=True, include_category=True, include_keywords=False),
            await execute_with_filters(include_region=False, include_category=False, include_keywords=True),
            await execute_with_filters(include_region=True, include_category=False, include_keywords=False),
            await execute_with_filters(include_region=False, include_category=True, include_keywords=False),
            await execute_with_filters(include_region=False, include_category=False, include_keywords=False),
        ]

    for candidate_rows in candidate_sets:
        if candidate_rows:
            return candidate_rows

    return []


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


def _build_chat_completion_payload(*, query_text: str, context_text: str) -> dict:
    body = {
        "model": settings.openai_model,
        "messages": [
            {"role": "system", "content": _build_system_prompt()},
            {
                "role": "user",
                "content": f"[참고 데이터]\n{context_text}\n\n[질문]\n{query_text}",
            },
        ],
    }

    if settings.openai_model.startswith("gpt-5"):
        body["max_completion_tokens"] = settings.openai_max_tokens
        body["reasoning_effort"] = "minimal"
    else:
        body["max_tokens"] = settings.openai_max_tokens

    return body


async def _extract_region_category_via_openai(query_text: str) -> tuple[str | None, str | None]:
    """Send `query_text` to OpenAI and request a JSON reply with `region` and `category`.

    Returns (region, category) where each may be None.
    """
    system = (
        "당신은 텍스트에서 한국의 '권역'과 '카테고리'를 추출하는 도우미입니다.\n"
        "권역은 예: 서울, 부산, 대구, 인천, 광주, 대전, 울산, 세종, 경기, 강원, 충북, 충남, 전북, 전남, 경북, 경남, 제주 중 하나입니다.\n"
        "카테고리는 예: 관광지, 레포츠, 여행코스, 문화시설, 쇼핑, 숙박, 음식점, 축제공연행사 중 하나입니다.\n"
        "사용자 질문에서 가능하면 정확히 해당하는 값(한국어)만을 추출하세요.\n"
        "응답은 반드시 JSON 하나의 객체로만 하세요. 예: {\"region\": \"서울\", \"category\": \"관광지\"}\n"
        "만약 해당 항목을 찾을 수 없으면 null로 설정하세요. 다른 텍스트나 설명을 덧붙이지 마세요."
    )

    body = {
        "model": settings.openai_model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": query_text},
        ],
    }
    if settings.openai_model.startswith("gpt-5"):
        body["max_completion_tokens"] = settings.openai_max_tokens
        body["reasoning_effort"] = "minimal"
    else:
        body["max_tokens"] = settings.openai_max_tokens

    timeout = httpx.Timeout(settings.openai_timeout_seconds)
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=body)
            resp.raise_for_status()
            text = resp.text
    except httpx.TimeoutException:
        return None, None
    except httpx.HTTPError:
        return None, None

    # Extract JSON object from the response text
    try:
        # Try to find the first JSON object in the text
        jstart = text.find("{")
        jend = text.rfind("}")
        if jstart != -1 and jend != -1 and jend > jstart:
            payload = json.loads(text[jstart : jend + 1])
        else:
            payload = json.loads(text)
    except Exception:
        return None, None

    region = payload.get("region") if isinstance(payload, dict) else None
    category = payload.get("category") if isinstance(payload, dict) else None
    if region is not None:
        region = region.strip() or None
    if category is not None:
        category = category.strip() or None
    return region, category


@router.post("", response_model=ChatResponse)
async def chat(payload: ChatRequest, db: AsyncSession = Depends(get_db)) -> ChatResponse:
    # We ignore any provided payload.region / payload.category and use OpenAI to extract them from text
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

    # 1) Ask OpenAI to extract region and category from the user's text
    orig_region, orig_category = await _extract_region_category_via_openai(query_text)

    # 2-step extraction: if OpenAI couldn't extract, fall back to local heuristics
    region = orig_region
    category = orig_category
    extraction_source = "openai" if (orig_region or orig_category) else None

    if not region:
        region = _infer_region(query_text)
        if region:
            extraction_source = (extraction_source + "+heuristic") if extraction_source else "heuristic"
    if not category:
        category = _infer_category(query_text)
        if category:
            extraction_source = (extraction_source + "+heuristic") if extraction_source else "heuristic"

    # 2) Query DB for top-rated location using extracted region/category (try combinations)
    base_stmt = (
        select(
            Location,
            func.coalesce(func.round(func.avg(LocationRating.score), 1), 0.0).label("rating_avg"),
            func.coalesce(func.count(LocationRating.id), 0).label("rating_count"),
        )
        .outerjoin(LocationRating, LocationRating.location_id == Location.id)
    )

    candidate_stmts = []
    if region and category:
        candidate_stmts.append(base_stmt.where(Location.region == region, Location.category == category))
    if region:
        candidate_stmts.append(base_stmt.where(Location.region == region))
    if category:
        candidate_stmts.append(base_stmt.where(Location.category == category))
    # fallback: any location
    candidate_stmts.append(base_stmt)

    chosen_row = None
    for stmt in candidate_stmts:
        stmt = stmt.group_by(Location.id).order_by(
            func.coalesce(func.avg(LocationRating.score), 0.0).desc(),
            func.count(LocationRating.id).desc(),
            Location.id.asc(),
        )
        stmt = stmt.limit(1)
        result = await db.execute(stmt)
        row = result.first()
        if row:
            chosen_row = row
            break

    if not chosen_row:
        return ChatResponse(
            answer="제공된 로컬 데이터만으로는 답할 수 없습니다.",
            references=[],
            extracted_region=region,
            extracted_category=category,
            extraction_source="openai",
        )

    location_obj, rating_avg, rating_count = chosen_row
    answer = f"추천: {location_obj.name} — {location_obj.category} | 주소: {location_obj.address or '-'} | 별점: {float(rating_avg):.1f} ({int(rating_count)}개)"
    refs = [
        LocationRef(
            id=location_obj.id,
            name=location_obj.name,
            category=location_obj.category,
            address=location_obj.address,
        )
    ]
    return ChatResponse(
        answer=answer,
        references=refs,
        extracted_region=region,
        extracted_category=category,
        extraction_source="openai",
    )
