# 04. API 구현 가이드 (Anonymous CRUD + RAG Chat)

## 1) Posts API

### GET `/api/posts`

- 지역(`region`) 필터 지원
- 최신순 정렬
- 응답은 목록 스키마 사용

### GET `/api/posts/{post_id}`

- 단건 상세 반환
- 없으면 404

### POST `/api/posts`

- 요청: `title`, `content`, `password`, `region?`
- 검증: 빈 문자열 금지, 최대 길이 제한

### PUT `/api/posts/{post_id}`

- 본문에 `password` 포함
- 검증 규칙: `post.password == request.password`
- 일치 시 수정, 불일치 시 403

### DELETE `/api/posts/{post_id}`

- 본문에 `password` 포함
- 일치 시 삭제, 불일치 시 403

## 2) Chat API (`POST /api/chat`)

### 입력 검증

- `query` 길이 제한 (`CHAT_MAX_QUERY_LENGTH`)
- 공백-only 입력 거부

### RAG 흐름

1. 자연어 질의 수신
2. SQLite `Location`에서 키워드 LIKE 검색 또는 카테고리 필터
3. 상위 N건 컨텍스트 문자열로 직렬화
4. OpenAI에 시스템 프롬프트 + 컨텍스트 + 사용자 질문 전달
5. 응답 + 참고 데이터 목록 반환

### OpenAI 호출 제약

- `max_tokens` 명시 (기본 500)
- `httpx.Timeout` 필수
- 모델은 환경변수로 주입

## 3) 스키마 권장안

### ChatRequest

- `query: str`
- `region: str | None = None`
- `category: str | None = None`

### ChatResponse

- `answer: str`
- `references: list[LocationRef]`

### LocationRef

- `name: str`
- `category: str`
- `address: str | None`

## 4) 라우터 분리

- `routers/posts.py`
- `routers/chat.py`
- `routers/locations.py`
- `APIRouter(prefix="/posts", tags=["posts"])`
- `APIRouter(prefix="/chat", tags=["chat"])`

## 5) Locations API (원천 데이터 조회)

이 API는 서버 시작 시 `BE/data/<권역>/*.json`에서 적재된 `Location` 테이블을 조회합니다.

### GET `/api/locations`

- 권역/카테고리/키워드 기반 조회
- 페이지네이션 지원: `limit`, `offset`

쿼리 파라미터:

- `region`: 예) `서울`, `부산`, `광주_전라권`, `구미_경북권`, `대전_충청권`
- `category`: 예) `관광지`, `레포츠`, `문화시설`, `쇼핑`, `숙박`, `여행코스`, `음식점`, `축제공연행사`
- `keyword`: 이름/주소/content_id 부분 검색
- `limit`: 기본 20, 최대 100
- `offset`: 기본 0

### GET `/api/locations/{location_id}`

- 단건 상세 조회
- 없으면 404
