# Glassless BE

LocalHub 백엔드입니다. FE 담당자나 FE 개발용 AI가 이 문서만 읽어도 API 연결, 데이터 구조, 배포 형태를 이해할 수 있도록 정리했습니다.

## 한 줄 요약

- 익명 커뮤니티 + 지역 정보 조회 + 자연어 챗봇을 제공하는 FastAPI 백엔드
- SQLite + SQLAlchemy 2.0 async 기반
- 지역/장소 데이터는 `BE/data` JSON에서 적재되며, 서버 시작 시 비어 있으면 자동 복구
- 게시글은 `카테고리`와 `location_id`를 가질 수 있음

## 기술 스택

- Framework: FastAPI
- Language: Python 3.10+
- DB: SQLite
- ORM: SQLAlchemy 2.0
- DB Driver: `aiosqlite`
- Validation: Pydantic v2
- HTTP Client: `httpx`
- Deployment: Render
- CI/CD: GitLab CI + Render Deploy Hook

## 핵심 데이터 특징

### 1) 장소 데이터(Location)

장소 데이터는 한국관광공사 TourAPI 4.0 원천 JSON입니다.

- 지역: `서울`, `부산`, `광주_전라권`, `구미_경북권`, `대전_충청권`
- 카테고리: `관광지`, `레포츠`, `문화시설`, `쇼핑`, `숙박`, `여행코스`, `음식점`, `축제공연행사`
- 주요 필드:
	- `content_id`
	- `name`
	- `category`
	- `region`
	- `address`
	- `tel`
	- `image_url`
	- `mapx`, `mapy`

특징:

- FE는 이 데이터를 `/api/locations`로 직접 받을 수 있음
- 서버 시작 시 `locations` 테이블이 비어 있으면 `BE/data/<권역>/*.json`을 자동 적재
- Render Free 플랜에서는 SQLite가 `/tmp`를 쓰므로 재배포/재시작 시 DB가 날아갈 수 있음
- 대신 시작 시 자동 적재로 원천 데이터는 복구됨

### 2) 게시글 데이터(Post)

익명 커뮤니티용 게시글입니다.

- 필수: `title`, `content`, `password`, `category`
- 선택: `location_id`, `region`
- 카테고리 4종만 허용:
	- `잡담`
	- `후기`
	- `질문`
	- `구인`

`location_id`가 있으면 특정 장소와 연결된 글을 쓸 수 있습니다.

### 3) 챗봇 데이터(Chat)

- `/api/chat`은 `Location` 테이블에서 키워드/카테고리 기반으로 관련 데이터를 찾은 뒤 OpenAI에 전달하는 RAG 방식
- 응답에는 `answer`와 `references`가 함께 내려옴
- OpenAI 키가 없으면 503 응답

## 데이터 흐름

### Location 데이터 흐름

1. `BE/data/<권역>/*.json` 파일을 읽음
2. `migrate.py`가 JSON을 정규화해 `locations` 테이블로 적재
3. 서버 시작 시 `locations` 테이블이 비어 있으면 자동 시드
4. FE는 `/api/locations` 또는 `/api/locations/{location_id}`로 조회

### Post 데이터 흐름

1. FE가 `POST /api/posts`로 게시글 생성
2. `category`는 4종 enum
3. `location_id`가 있으면 실제 장소 존재 여부 검증
4. DB에 저장 후 목록/상세 조회에서 노출

### Chat 데이터 흐름

1. FE가 자연어 질문을 `POST /api/chat`으로 전송
2. 서버가 `Location`에서 키워드 검색 및 필터링
3. 관련 장소를 컨텍스트로 만들고 OpenAI 호출
4. 답변과 참고 장소 목록을 반환

## API 종류

### Health / Docs

- `GET /health`
- `GET /docs` (기본 Swagger UI)
- `GET /swagger-ui` (추가 Swagger UI)
- `GET /openapi.json`

### Posts

- `GET /api/posts`
- `GET /api/posts/{post_id}`
- `POST /api/posts`
- `PUT /api/posts/{post_id}`
- `DELETE /api/posts/{post_id}`

### Comments

- `POST /api/comments/posts/{post_id}` — create a comment for a post. The `post_id` is provided as a URL path parameter; the request body should include only `nickname`, `password`, and `content`.
- `PUT /api/comments/{comment_id}` — update a comment (password required)
- `DELETE /api/comments/{comment_id}` — delete a comment (password required)

Notes:
- Comments carry `nickname`, `password`, and `content`. The parent `post_id` is specified in the POST endpoint's path, not the request body.
- When a comment is created or deleted, the parent post's `comments_count` is updated atomically.
- Comment edits/deletes require the comment password similar to post password flow.

지원 필터:

- `region`
- `category`
- `location_id`

### Locations

- `GET /api/locations`
- `GET /api/locations/{location_id}`

지원 필터:

- `region`
- `category`
- `keyword`
- `limit`
- `offset`

### Chat

- `POST /api/chat`

## FE 연동 포인트

### 1) 장소 목록 페이지

- 권역별/카테고리별 필터를 걸어 `/api/locations`를 호출
- 카드 목록은 `name`, `category`, `address`, `image_url`, `mapx`, `mapy` 중심으로 렌더링

### 2) 장소 상세 페이지

- `/api/locations/{location_id}`로 상세 정보 조회
- 지도 컴포넌트가 있으면 `mapx`, `mapy`를 활용

### 3) 게시글 목록 페이지

- `/api/posts?region=...&category=...&location_id=...`로 필터링 가능
- 목록은 `title`, `category`, `location_id`, `region`, `created_at`을 사용

### 4) 게시글 작성 페이지

- `category`는 드롭다운 고정값으로 제공
- `location_id`는 선택값
- `location_id`를 선택하면 장소 검색 UI와 연결 가능

### 5) 챗봇 페이지

- `/api/chat`에 사용자의 질의를 전송
- 응답의 `references`를 별도 카드나 사이드바로 노출 가능

## 요청/응답 예시

### POST /api/posts

```json
{
	"title": "서울 공원 후기",
	"content": "양화한강공원 다녀왔어요",
	"password": "1234",
	"category": "후기",
	"location_id": 1,
	"region": "서울"
}
```

### GET /api/locations?region=서울&category=관광지&limit=1

```json
[
	{
		"id": 1,
		"region": "서울",
		"category": "관광지",
		"content_type_id": 12,
		"content_id": "1059877",
		"name": "양화한강공원",
		"description": null,
		"address": "서울특별시 영등포구 노들로 221 (당산동)",
		"tel": null,
		"image_url": "https://...",
		"mapx": 126.902365881,
		"mapy": 37.5382819489,
		"raw_cat1": null,
		"raw_cat2": null,
		"raw_cat3": null
	}
]
```

## 실행 방법

### 로컬 실행

```bash
cd BE
C:/Users/SSAFY/AppData/Local/Python/pythoncore-3.14-64/python.exe -m pip install -r src/requirements.txt
cd src
C:/Users/SSAFY/AppData/Local/Python/pythoncore-3.14-64/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 데이터 적재

```bash
cd BE/src
C:/Users/SSAFY/AppData/Local/Python/pythoncore-3.14-64/python.exe -m scripts.migrate
```

## 환경 변수

- `DATABASE_URL`
- `CORS_ORIGINS`
- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `OPENAI_MAX_TOKENS`
- `OPENAI_TIMEOUT_SECONDS`
- `CHAT_MAX_QUERY_LENGTH`
- `CHAT_MAX_REFERENCES`

## 배포 메모

- Render Free 플랜에서는 disk를 쓰지 않음
- SQLite는 `/tmp/localhub.db` 사용
- 재배포/재시작 시 `posts` 데이터는 유실될 수 있음
- `locations` 데이터는 시작 시 JSON 자동 시드로 복구됨

## 문서

- Swagger UI: `/docs`
- 추가 Swagger UI: `/swagger-ui`
- 상세 가이드: [BE/docs](docs/README.md)
