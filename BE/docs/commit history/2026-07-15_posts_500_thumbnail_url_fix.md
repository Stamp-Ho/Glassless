# 2026-07-15 작업 요약: posts 500 에러 수정

## 이슈
- `GET /api/posts` 호출 시 500 Internal Server Error 발생
- 에러 원인: `PostListItem` 생성 시 `thumbnail_url` 필드 누락으로 Pydantic 검증 실패

## 원인 분석
- `posts` 라우터의 `list_posts`에서 응답 객체를 수동 생성하면서
  - `id`, `title`, `content`, `category`, `location_id`, `region`, `created_at`, `updated_at`만 채움
  - `thumbnail_url` 누락

## 수정 내용
- `BE/src/app/routers/posts.py`
  - `PostListItem(...)` 생성부에 `thumbnail_url=post.thumbnail_url` 추가

## 검증
- 서버 로그 기준 기존 ValidationError 재현 지점 제거
- `curl http://127.0.0.1:8000/api/posts` 응답 코드 `200` 확인

## 영향 범위
- 게시글 목록 API 응답 안정화
- FE 게시글 목록 조회 시 500 에러 해소
