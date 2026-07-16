# API 명세서 — Glassless

Base URL: `http(s)://<HOST>/api`

Authentication: 없음(퍼블릭). 일부 기능에서 서버 환경변수(OpenAI 키 등)가 필요.

Headers:
- 요청: `Content-Type: application/json` (POST/PUT)
- 응답: 페이징 메타: `X-Total-Count`, `X-Total-Pages`, `X-Has-Next`

---

## Posts

### GET /posts
- 설명: 게시글 목록 조회 (페이징 / 필터)
- 쿼리 파라미터:
  - `region` (string, optional)
  - `category` ("잡담"|"후기"|"질문"|"구인", optional)
  - `location_id` (int, optional)
  - `page` (int, default=1)
  - `per_page` (int, default=20, max=100)
- 응답 헤더:
  - `X-Total-Count`: 총 항목 수
  - `X-Total-Pages`: 총 페이지 수
  - `X-Has-Next`: 다음 페이지 유무 ("1" 또는 "0")
- 응답 예시 (200):
```json
[
  {
    "id": 5,
    "title": "test post",
    "content": "미리보기 텍스트...",
    "category": "잡담",
    "location_id": null,
    "thumbnail_url": null,
    "region": "서울",
    "rating": null,
    "comments_count": 1,
    "created_at": "2026-07-16T02:20:11",
    "updated_at": "2026-07-16T02:20:11"
  }
]
```

---

### GET /posts/{post_id}
- 설명: 게시글 상세 조회
- 응답 예시 (200):
```json
{
  "id": 5,
  "title": "test post",
  "content": "상세 본문...",
  "category": "잡담",
  "location_id": null,
  "thumbnail_url": null,
  "region": "서울",
  "rating": null,
  "comments_count": 1,
  "created_at": "2026-07-16T02:20:11",
  "updated_at": "2026-07-16T02:20:11"
}
```

---

### POST /posts
- 설명: 게시글 생성
- 요청 바디 예시:
```json
{
  "title": "제목",
  "content": "본문",
  "password": "pw",
  "category": "후기",
  "region": "서울",
  "location_id": 123,
  "thumbnail_url": null,
  "rating": 4
}
```
- 응답: 생성된 `PostResponse` (201)

---

### PUT /posts/{post_id}
- 설명: 게시글 수정(비밀번호 검증 필요)
- 요청 바디(예):
```json
{
  "password": "pw",
  "title": "수정된 제목",
  "content": "수정된 본문"
}
```
- 응답: 수정된 PostResponse

---

### DELETE /posts/{post_id}
- 설명: 게시글 삭제(비밀번호 필요)
- 요청 바디:
```json
{ "password": "pw" }
```
- 응답: 204 No Content

---

## Comments

### POST /comments/posts/{post_id}
- 설명: 댓글 작성
- 요청 예시:
```json
{ "nickname": "작성자", "password": "pw", "content": "댓글 내용" }
```

### GET /comments/posts/{post_id}
- 설명: 게시글 댓글 목록

### PUT /comments/{comment_id}
- 설명: 댓글 수정 (비밀번호 필요)

### DELETE /comments/{comment_id}
- 설명: 댓글 삭제 (비밀번호 필요)

---

## Locations

### GET /locations
- 설명: 명소 목록 조회/검색
- 파라미터 예시:
  - `region`, `category`, `keyword`, `limit`, `offset`, `mapx`, `mapy`, `radius_km`
- 예: `GET /api/locations?region=서울&category=관광지&limit=50&offset=0`

### GET /locations/{id}
- 설명: 명소 상세

### POST /locations/{id}/ratings
- 설명: 명소 별점 등록
- 요청 바디 예시:
```json
{ "score": 4, "client_id": "<client-uuid>" }
```
- 중복 방지: 서버에서 `client_id` 기반 또는 IP/UA 기반 제한

---

## Chat

### POST /chat
- 설명: 사용자 질의에 대해 로컬 명소 데이터(참고자료)를 기반으로 OpenAI를 호출해 요약/추천 답변을 생성
- 요청 예: `{ "query": "이번 주말 부산에서 놀만한 곳 추천해줘" }`
- 특이사항: OpenAI 모델/키는 서버 환경변수(`OPENAI_API_KEY`, `OPENAI_MODEL`)로 관리

---

## 기타
- GET `/health` : 헬스체크
- Swagger UI: `/swagger-ui` (FastAPI에서 제공)


---

파일: `BE/docs/api_spec.md` (이 파일)

---

## Quick Endpoint Index (from Swagger)

- GET [`/health`](http://localhost:8000/docs#/default/health_health_get) — Health

### posts
- GET [`/api/posts`](http://localhost:8000/docs#/posts/list_posts_api_posts_get) — List Posts
- POST [`/api/posts`](http://localhost:8000/docs#/posts/create_post_api_posts_post) — Create Post
- GET [`/api/posts/{post_id}`](http://localhost:8000/docs#/posts/get_post_api_posts__post_id__get) — Get Post
- PUT [`/api/posts/{post_id}`](http://localhost:8000/docs#/posts/update_post_api_posts__post_id__put) — Update Post
- DELETE [`/api/posts/{post_id}`](http://localhost:8000/docs#/posts/delete_post_api_posts__post_id__delete) — Delete Post

### chat
- POST [`/api/chat`](http://localhost:8000/docs#/chat/chat_api_chat_post) — Chat

### locations
- GET [`/api/locations`](http://localhost:8000/docs#/locations/list_locations_api_locations_get) — List Locations
- GET [`/api/locations/{location_id}`](http://localhost:8000/docs#/locations/get_location_api_locations__location_id__get) — Get Location

### comments
- POST [`/api/comments/posts/{post_id}`](http://localhost:8000/docs#/comments/create_comment_api_comments_posts__post_id__post) — Create Comment
- GET [`/api/comments/posts/{post_id}`](http://localhost:8000/docs#/comments/get_comments_api_comments_posts__post_id__get) — Get Comments
- PUT [`/api/comments/{comment_id}`](http://localhost:8000/docs#/comments/update_comment_api_comments__comment_id__put) — Update Comment
- DELETE [`/api/comments/{comment_id}`](http://localhost:8000/docs#/comments/delete_comment_api_comments__comment_id__delete) — Delete Comment

### stats
- GET [`/api/stats/regions`](http://localhost:8000/docs#/stats/regions_stats_api_stats_regions_get) — Regions Stats

