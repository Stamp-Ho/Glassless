# 03. 데이터베이스 및 마이그레이션

## 1) DB 전략

- MVP는 SQLite 단일 파일 사용
- ORM은 SQLAlchemy 2.0 스타일 사용
- 비동기 세션(`AsyncSession`) 기본

## 2) 모델 정의 가이드

### Post

- `id: int (PK)`
- `title: str`
- `content: str`
- `password: str` (요구사항상 평문)
- `region: str | None`
- `created_at`, `updated_at`

### Location

- `id: int (PK)`
- `name: str`
- `category: str`
- `region: str`
- `description: str | None`
- `address: str | None`

## 3) 세션/엔진 예시 포인트

- 엔진: `create_async_engine(DATABASE_URL, future=True)`
- 세션팩토리: `async_sessionmaker(bind=engine, expire_on_commit=False)`
- 의존성: `get_db()` 제너레이터에서 `yield session`

## 4) JSON -> SQLite 마이그레이션 스크립트

`src/scripts/migrate.py`에서 다음 순서를 지킵니다.

1. `BE/data/<권역>/*.json` 파일 자동 탐색/로드
2. 카테고리/지역/설명 필드 정규화
3. `Location` 테이블로 bulk insert
4. 중복 레코드 방지(`content_id + name` 기준)

## 5) 실행 예시

```bash
cd BE/src
python -m scripts.migrate
```

## 6) 주의사항

- 하드코딩된 DB 경로 금지, 반드시 `DATABASE_URL` 환경변수 사용
- 대용량 JSON 처리 시 메모리 사용량 고려(파일 단위 처리)
- 현재 데이터 폴더 기준 `서울`, `부산` 권역은 `음식점` JSON이 없어 해당 카테고리 응답이 비어 있을 수 있음
