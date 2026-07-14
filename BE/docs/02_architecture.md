# 02. 아키텍처 및 디렉토리 규칙

## 1) 설계 원칙

- 라우터/스키마/모델/코어 설정을 분리합니다.
- 엔드포인트는 `routers`에서만 선언하고, DB 접근은 세션 의존성(`Depends`)으로 주입합니다.
- Pydantic 스키마로 입출력을 엄격하게 검증합니다.

## 2) 계층 역할

- `app/core`
  - 설정(`config.py`), DB 엔진/세션(`database.py`), 공통 예외/유틸
- `app/models`
  - SQLAlchemy ORM 모델 (`Post`, `Location` 등)
- `app/schemas`
  - 요청/응답 모델 (`PostCreate`, `PostUpdate`, `ChatRequest`, `ChatResponse`)
- `app/routers`
  - `posts.py`, `chat.py`, `locations.py`
- `app/main.py`
  - FastAPI 앱 인스턴스, CORS, 라우터 등록

## 3) 권장 파일 초안

```text
src/app/core/config.py
src/app/core/database.py
src/app/models/post.py
src/app/models/location.py
src/app/schemas/post.py
src/app/schemas/chat.py
src/app/routers/posts.py
src/app/routers/chat.py
src/app/main.py
```

## 4) main.py 구성 체크리스트

- `FastAPI(title=...)`
- `CORSMiddleware` 등록 (`CORS_ORIGINS` 환경변수 반영)
- `include_router(posts_router, prefix="/api")`
- `include_router(chat_router, prefix="/api")`
- 헬스체크 엔드포인트 (`GET /health`)
