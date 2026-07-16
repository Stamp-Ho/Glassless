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

# Allowed canonical regions (user requested): map aliases to these
_ALLOWED_REGION_MAP: dict[str, tuple[str, ...]] = {
    "광주_전라권": ("광주", "광주시", "광주광역시", "전라권"),
    "구미_경북권": ("구미", "경북", "경상북도", "구미_경북권"),
    "대전_충청권": ("대전", "대전시", "대전광역시", "충청권"),
    "부산": ("부산", "부산시", "부산광역시"),
    "서울": ("서울", "서울시", "서울특별시"),
}


def _map_to_allowed_region(region_str: str | None) -> str | None:
    if not region_str:
        return None
    norm = re.sub(r"\s+", "", region_str).lower()
    for canonical, aliases in _ALLOWED_REGION_MAP.items():
        # accept if the extracted region already matches a canonical key
        if canonical.lower() in norm:
            return canonical
        for a in aliases:
            if a.lower() in norm:
                return canonical
    return None


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


def _detect_excluded_categories(query: str) -> list[str]:
    """Detect categories explicitly excluded by user phrases.

    Strategy:
    - Find negation keyword positions (e.g., '말고', '싫어') and look backward a short window
      to find any category aliases mentioned before the negation. This captures forms like
      '관광이나 액티비티는 싫어' and '액티비티는 말고'.
    - Also check for aliases directly adjacent to negation words.
    """
    text = query.strip().lower()
    excluded: set[str] = set()
    negation_keywords = [
        "말고",
        "빼고",
        "제외",
        "않고",
        "아니고",
        "싫어",
        "안 좋아",
        "원치",
        "싫습니다",
        "안좋아",
        "질렸",
        "질려",
        "지겹",
        "지겨",# --- [추천 추가 1] 직접적인 거부 및 비선호 (Dislike & Reject) ---
        "싫어해", "싫어함", "꺼려", "안할래", "안 할래", "안먹", "안 먹", "안갈", "안 갈", "안볼", "안 볼",
        "피하고", "피해", "거부", "사양", "사절", "패스", "스킵", "Pass", "Skip",

        # --- [추천 추가 2] '않다/아니다'의 다양한 활용형 (Variations of Negation) ---
        "않은", "않는", "아닌", "아니라", "아닙니다", "못하", "못 하", "없고", "없는", "없어",

        # --- [추천 추가 3] 질림 / 지루함 / 과다 (Boredom & Overuse) ---
        "물렸", "물려", "뻔한", "뻔해", "흔한", "흔해", "지루", "심심",

        # --- [추천 추가 4] 강한 부정 및 배제 조사 (Exclusive Particles) ---
        "말아", "말고는", "외에는", "말아줘", "말아주", "금지", "제한"
    ]

    # find negation positions
    neg_pattern = re.compile("|".join(re.escape(k) for k in negation_keywords))
    neg_positions = [m.start() for m in neg_pattern.finditer(text)]

    # window size to look back for aliases (covers lists like 'A이나 B는 싫어')
    window_back = 40

    for pos in neg_positions:
        window_start = max(0, pos - window_back)
        window = text[window_start: pos + 10]
        for canonical, aliases in _CATEGORY_ALIASES.items():
            for alias in aliases:
                if alias in window:
                    excluded.add(canonical)
                    break

    # also check adjacency: alias immediately followed/preceded by negation within short distance
    for canonical, aliases in _CATEGORY_ALIASES.items():
        for alias in aliases:
            # if alias appears and a negation word appears within 10 chars after it
            for m in re.finditer(re.escape(alias), text):
                snippet = text[m.start(): m.start() + 20]
                if neg_pattern.search(snippet):
                    excluded.add(canonical)
                    break

    return list(excluded)


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


async def _extract_region_category_via_openai(query_text: str) -> tuple[str | None, list[str] | None, list[str] | None]:
    """Send `query_text` to OpenAI and request a JSON reply with `region`, `categories`, and `excluded`.

    Returns (region, categories, excluded) where:
      - region: str or None
      - categories: list[str] or None
      - excluded: list[str] or None
    """
    system = (
        "당신은 텍스트에서 한국의 '권역', '카테고리 목록', 그리고 '제외할 카테고리 목록'을 추출하는 도우미입니다.\n"
        "권역은 예: 광주_전라권, 구미_경북권, 대전_충청권, 부산, 서울 중 하나입니다.\n"
        "카테고리는 예: 관광지, 레포츠, 여행코스, 문화시설, 쇼핑, 숙박, 음식점, 축제공연행사 중 하나입니다.\n"
        "사용자 질문에서 가능한 경우 위에 적힌 '권역' 키(예: 광주_전라권)를 그대로 반환하세요.\n"
        "응답은 반드시 JSON 하나의 객체로만 하세요. 형식 예시: {\"region\": \"광주_전라권\", \"categories\": [\"레포츠\", \"관광지\"], \"excluded\": [\"레포츠\"]}\n"
        "필드 설명: 'region'은 문자열(위 다섯 중 하나) 또는 null, 'categories'는 문자열 배열 또는 null, 'excluded'는 문자열 배열 또는 null.\n"
        "값을 알 수 없으면 해당 필드를 null로 하세요. 다른 텍스트나 설명을 덧붙이지 마세요."
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
        return None, None, None
    except httpx.HTTPError:
        return None, None, None

    # Extract JSON object from the response text
    try:
        jstart = text.find("{")
        jend = text.rfind("}")
        if jstart != -1 and jend != -1 and jend > jstart:
            payload = json.loads(text[jstart : jend + 1])
        else:
            payload = json.loads(text)
    except Exception:
        return None, None, None

    if not isinstance(payload, dict):
        return None, None, None

    region = payload.get("region")
    categories = payload.get("categories")
    excluded = payload.get("excluded")

    # normalize types
    if isinstance(region, str):
        region = region.strip() or None
    else:
        region = None

    if isinstance(categories, list):
        categories = [c.strip() for c in categories if isinstance(c, str) and c.strip()]
        if not categories:
            categories = None
    elif isinstance(categories, str):
        categories = [categories.strip()] if categories.strip() else None
    else:
        categories = None

    if isinstance(excluded, list):
        excluded = [c.strip() for c in excluded if isinstance(c, str) and c.strip()]
        if not excluded:
            excluded = None
    elif isinstance(excluded, str):
        excluded = [excluded.strip()] if excluded.strip() else None
    else:
        excluded = None

    return region, categories, excluded


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

    # If user explicitly mentions a category (e.g. '레포츠'), prefer that and skip OpenAI extraction
    explicit_cat = _infer_category(query_text)
    if explicit_cat:
        # Map region from text or default
        inferred = _infer_region(query_text)
        mapped_region = _map_to_allowed_region(inferred) if inferred else None
        region = mapped_region if mapped_region else "서울"
        categories = [explicit_cat]
        excluded_categories = _detect_excluded_categories(query_text)
        extraction_source = "heuristic"
    else:
        # 1) Ask OpenAI to extract region and category from the user's text
        orig_region, orig_categories, orig_excluded = await _extract_region_category_via_openai(query_text)

        # Map extracted region to allowed canonical regions; default to 서울 if unmapped
        mapped_region = _map_to_allowed_region(orig_region) if orig_region else None
        if not mapped_region:
            # try to infer from text as a fallback
            inferred = _infer_region(query_text)
            mapped_region = _map_to_allowed_region(inferred) if inferred else None
        region = mapped_region if mapped_region else "서울"
        categories = orig_categories if orig_categories else ["관광지"]
        excluded_categories = orig_excluded if orig_excluded else []
        extraction_source = "openai"

    # detect excluded categories from user phrasing (e.g., '액티비티는 말고')
    # We allow OpenAI to supply excluded list; if absent, we can optionally detect heuristically.
    if not excluded_categories:
        # keep heuristic detection optional; if it finds something, add it
        heur = _detect_excluded_categories(query_text)
        if heur:
            excluded_categories = list(set(excluded_categories) | set(heur))

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
    # If OpenAI returned categories, use them (multiple allowed). Exclude any excluded_categories.
    # Build a single stmt that filters region + categories (IN) first, then fallbacks.
    if categories:
        stmt = base_stmt.where(Location.region == region, Location.category.in_(categories))
        if excluded_categories:
            stmt = stmt.where(~Location.category.in_(excluded_categories))
        candidate_stmts.append(stmt)
    # fallback: region only
    stmt_region = base_stmt.where(Location.region == region)
    if excluded_categories:
        stmt_region = stmt_region.where(~Location.category.in_(excluded_categories))
    candidate_stmts.append(stmt_region)
    # fallback: categories only
    if categories:
        stmt_cat = base_stmt.where(Location.category.in_(categories))
        if excluded_categories:
            stmt_cat = stmt_cat.where(~Location.category.in_(excluded_categories))
        candidate_stmts.append(stmt_cat)
    # final fallback: any location excluding excluded categories
    stmt_any = base_stmt
    if excluded_categories:
        stmt_any = stmt_any.where(~Location.category.in_(excluded_categories))
    candidate_stmts.append(stmt_any)
    # fallback: any location
    candidate_stmts.append(base_stmt)

    chosen_row = None
    # apply exclusion to fallback stmt(s)
    candidate_stmts_with_exclusions = []
    # Execute candidate statements. If categories contained multiple values, we want multiple references
    rows = []
    for stmt in candidate_stmts:
        stmt = stmt.group_by(Location.id).order_by(
            func.coalesce(func.avg(LocationRating.score), 0.0).desc(),
            func.count(LocationRating.id).desc(),
            Location.id.asc(),
        )
        # request up to chat_max_references rows
        stmt = stmt.limit(settings.chat_max_references)
        result = await db.execute(stmt)
        fetched = result.all()
        if fetched:
            rows = fetched
            break

    if not rows:
        return ChatResponse(
            answer="제공된 로컬 데이터만으로는 답할 수 없습니다.",
            references=[],
            extracted_region=region,
            extracted_category=categories,
            extracted_excluded=excluded_categories,
            extraction_source=extraction_source,
        )

    refs = []
    for idx, (location_obj, rating_avg, rating_count) in enumerate(rows, 1):
        refs.append(
            LocationRef(id=location_obj.id, name=location_obj.name, category=location_obj.category, address=location_obj.address)
        )

    # Simplified user-facing answer: short confirmation sentence
    _display_region_map = {
        "광주_전라권": "광주/전라권",
        "구미_경북권": "구미/경북권",
        "대전_충청권": "대전/충청권",
        "부산": "부산",
        "서울": "서울",
    }
    display_region = _display_region_map.get(region, (region or "지역").replace("_", "/"))
    cat_display = categories[0] if categories else "정보"
    answer = f"네, {display_region}의 {cat_display} 정보를 알려드릴게요."
    return ChatResponse(
        answer=answer,
        references=refs,
        extracted_region=region,
        extracted_category=categories,
        extracted_excluded=excluded_categories,
        extraction_source=extraction_source,
    )