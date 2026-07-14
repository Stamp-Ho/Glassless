# 08. 게시글 카테고리 및 장소 연결

## 작업 개요

게시글에 `location_id`를 선택적으로 연결하고, 게시글 카테고리를 `잡담 / 후기 / 질문 / 구인` 4종으로 제한했습니다.

## 변경 내용

### Post 모델

- `category` 추가
- `location_id` 추가
- 기존 SQLite 환경을 위해 startup 시 컬럼 자동 보정

### Post API

- `GET /api/posts`
  - `region`, `category`, `location_id` 필터 지원
- `POST /api/posts`
  - `category` 필수
  - `location_id` 선택
  - `location_id`가 있으면 실제 장소 존재 여부 검증
- `PUT /api/posts/{post_id}`
  - `category`, `location_id` 수정 가능

### Pydantic 스키마

- 카테고리는 enum으로 고정
- 응답에도 `category`, `location_id` 노출

## 작업 결과

- 특정 장소에 연결된 게시글 작성 가능
- 게시글 목록에서 장소/카테고리 기준 필터링 가능
- 기존 DB가 있어도 startup에서 새 컬럼을 자동 추가

## 비고

- `location_id`는 선택 필드이므로 장소를 연결하지 않아도 게시글 작성 가능
- 카테고리는 4개 고정이며, 그 외 값은 API 입력 검증에서 거부