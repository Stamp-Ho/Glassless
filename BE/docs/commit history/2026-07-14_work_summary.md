# 2026-07-14 작업 요약 (BE)

## 개요

이번 작업에서는 LocalHub 백엔드 MVP를 문서 기준으로 실제 실행 가능한 형태까지 초기 구축했습니다.
핵심은 FastAPI 비동기 구조, SQLite 기반 데이터 적재, 익명 게시판 CRUD, RAG 챗봇 기본 흐름 구성입니다.

## 주요 커밋 히스토리

1. `a74029b` `docs(be): add LocalHub backend development guides`
2. `8a569e4` `feat(be): scaffold FastAPI backend and Seoul data migration`

참고: 중간에 기존 저장소 이력으로 `cc2497b`(데이터 구조 변경/부산 추가) 등이 존재합니다.

## 생성/수정된 주요 문서

### 개발 가이드 문서

- `BE/docs/README.md`
- `BE/docs/01_project_setup.md`
- `BE/docs/02_architecture.md`
- `BE/docs/03_database_and_migration.md`
- `BE/docs/04_api_implementation.md`
- `BE/docs/05_security_and_constraints.md`
- `BE/docs/06_workflow_and_deploy.md`

### 백엔드 스캐폴드 코드

- `BE/src/app/main.py`
- `BE/src/app/core/config.py`
- `BE/src/app/core/database.py`
- `BE/src/app/models/post.py`
- `BE/src/app/models/location.py`
- `BE/src/app/schemas/post.py`
- `BE/src/app/schemas/chat.py`
- `BE/src/app/routers/posts.py`
- `BE/src/app/routers/chat.py`
- `BE/src/scripts/migrate.py`
- `BE/src/requirements.txt`
- `BE/src/.env.example`
- `BE/src/.gitignore`

## 구현 내용 상세

## 1) FastAPI 앱 구성

- 앱 엔트리포인트: `app/main.py`
- CORS 설정 및 `/health` 엔드포인트 추가
- `posts`, `chat` 라우터를 `/api` prefix로 등록
- 앱 시작 시 `init_db()`를 호출해 테이블 자동 생성

## 2) DB/ORM 계층

- SQLAlchemy 2.0 + AsyncSession 기반 구성
- SQLite 비동기 드라이버(`aiosqlite`) 사용
- 모델:
  - `Post`: 익명 게시글 CRUD용(title, content, password, region, timestamps)
  - `Location`: 서울 관광 데이터 저장용(content_id, category, address, 좌표 등)

## 3) Posts API (익명 CRUD)

- `GET /api/posts`
- `GET /api/posts/{post_id}`
- `POST /api/posts`
- `PUT /api/posts/{post_id}`
- `DELETE /api/posts/{post_id}`

비밀번호 검증 규칙(요구사항):
- 수정/삭제 시 요청 본문의 평문 비밀번호와 DB 평문 비밀번호를 직접 비교

## 4) Chat API

- `POST /api/chat`
- 질의 길이 제한 적용 (`CHAT_MAX_QUERY_LENGTH`)
- 지역/카테고리/키워드 기반 Location 조회
- 조회 결과를 컨텍스트로 구성해 OpenAI Chat Completions 호출
- 비용/안정성 제약 반영:
  - `max_tokens` 고정
  - `httpx.Timeout` 적용
  - API Key 미설정 시 503 반환

## 5) 서울 데이터 마이그레이션

- 스크립트: `src/scripts/migrate.py`
- 입력: `BE/data/서울/서울_*.json`
- 처리:
  - 주소 결합(`addr1 + addr2`)
  - 좌표 문자열 float 변환
  - content_id/name 기준 중복 방지
- 실행 결과:
  - `inserted=6518`
  - `skipped=0`

## 실행 검증 결과

### 설치

- `pip install -r src/requirements.txt` 성공

### 서버

- `uvicorn app.main:app` 기동 성공

### API 스모크 테스트

- `GET /health` -> `200`, `{"status":"ok"}`
- `GET /api/posts` -> `200`, `[]`
- `POST /api/chat` (API key 없음) -> `503`, `{"detail":"OPENAI_API_KEY is not configured"}`

## 현재 상태

- 브랜치: `BE`
- 최신 커밋: `8a569e4`
- 워킹 트리: clean (문서 생성 전 기준)

## 후속 권장 작업

1. `.env` 구성 후 OpenAI 실연동 테스트
2. posts/chat API 테스트 코드 추가
3. 데이터 출처/라이선스 표기 문구를 API 응답 또는 서비스 안내에 반영
4. Render 배포 설정 및 환경변수 세팅
