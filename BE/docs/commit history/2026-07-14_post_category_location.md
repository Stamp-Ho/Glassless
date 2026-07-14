# 2026-07-14 게시글 카테고리 및 장소 연결

## 작업 개요

게시글에 선택적으로 `location_id`를 연결할 수 있도록 하고, 게시글 카테고리를 `잡담 / 후기 / 질문 / 구인` 4종으로 제한했습니다.

## 변경 파일

- `BE/src/app/models/post.py`
- `BE/src/app/schemas/post.py`
- `BE/src/app/routers/posts.py`
- `BE/src/app/core/database.py`
- `BE/docs/03_database_and_migration.md`
- `BE/docs/04_api_implementation.md`
- `BE/docs/08_post_category_location.md`
- `BE/docs/README.md`

## 상세 변경

1. Post 모델 확장
- `category` 컬럼 추가
- `location_id` 컬럼 추가
- 기존 SQLite DB가 있어도 startup 시 컬럼 자동 보정

2. Post API 확장
- `GET /api/posts`
  - `region`, `category`, `location_id` 필터 지원
- `POST /api/posts`
  - `category` 필수
  - `location_id` 선택
  - `location_id`가 있으면 실제 장소 존재 여부 검증
- `PUT /api/posts/{post_id}`
  - `category`, `location_id` 수정 가능

3. Pydantic 스키마
- `category`를 4종 enum으로 고정
- 응답에도 `category`, `location_id` 노출

4. 데이터베이스 보정
- startup 시 `posts` 테이블에 `category`/`location_id` 컬럼이 없으면 `ALTER TABLE`로 자동 추가

## 검증 결과

- `python -m compileall app scripts` 성공
- 서버 기동 후 `POST /api/posts` 201 Created 확인
- 생성된 게시글 조회 결과:
  - `category=후기`
  - `location_id=1`
  - `region=서울`
- 필터 조회 결과:
  - `GET /api/posts?category=후기&location_id=1` -> `200`
  - 반환 목록에 생성한 게시글 포함

## 비고

- `location_id`는 선택 필드이므로 장소 연결 없이도 게시글 작성 가능
- 카테고리 외 값은 API 입력 검증에서 거부
