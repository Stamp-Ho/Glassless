# 2026-07-16 — Stats API 추가

변경 요약:

- 새 파일: `BE/src/app/routers/stats.py`
  - 엔드포인트: `GET /api/stats/regions`
  - 설명: 최근 7일간 각 권역(광주_전라권, 구미_경북권, 대전_충청권, 부산, 서울)에 대해 다음 통계를 반환함
    - `total_posts`: 권역 내 게시글 총수
    - `total_comments`: 권역 내 게시글에 대한 댓글 총수
    - `by_category`: 카테고리(잡담/후기/질문/구인)별 `{posts, comments}`
    - `top_locations`: 게시글 수 기준 상위 5개 명소 목록(`location_id`, `name`, `post_count`) — 게시글 수만 반환

- `BE/src/app/main.py`에 라우터 등록: `stats_router`를 `/api` 경로로 포함

테스트 및 결과:

- 로컬 서버(포트 8000)에서 `GET /api/stats/regions` 호출로 정상 동작 확인(HTTP 200).
- 현재 데이터베이스에 최근 7일내 게시글이 없으면 통계 값은 0, `top_locations`는 빈 배열로 반환됨.

추가 제안:

- 권역 목록을 하드코딩 대신 설정 파일로 이동
- 응답 페이징 또는 캐싱(빈번한 호출 방지)
- 관리자용 상세 필터(기간, 특정 권역 요청 등)

작성자: 자동화된 변경 (Git commit 포함)
