# 2026-07-14 명소 별점 기능

## 작업 개요

명소(Location)에 사용자가 별점을 남길 수 있는 기능을 추가했습니다.
별점은 IP + User-Agent + localStorage 기반 `client_id` 조합으로 24시간 제한을 적용합니다.

## 변경 파일

- `BE/src/app/models/location_rating.py`
- `BE/src/app/models/__init__.py`
- `BE/src/app/core/config.py`
- `BE/src/app/core/database.py`
- `BE/src/app/schemas/location.py`
- `BE/src/app/routers/locations.py`
- `BE/README.md`
- `BE/docs/03_database_and_migration.md`
- `BE/docs/04_api_implementation.md`
- `BE/docs/09_location_ratings.md`
- `BE/docs/README.md`

## 상세 변경

1. 별점 저장 테이블 추가
- `location_ratings` 테이블 생성
- 저장 필드:
  - `location_id`
  - `score` (1~5)
  - `client_id`
  - `ip_address`
  - `user_agent`
  - `created_at`

2. 별점 API 추가
- `POST /api/locations/{location_id}/ratings`
- 중복 제한:
  - 동일 `client_id`
  - 동일 IP + User-Agent
  - 24시간 이내 재등록 차단

3. 장소 조회 응답 확장
- `GET /api/locations`
- `GET /api/locations/{location_id}`
- 각 응답에 다음 통계 포함:
  - `rating_avg`
  - `rating_count`

4. FE 연동 가이드
- localStorage에 `client_id`(UUID) 저장
- 별점 제출 시 `client_id`를 함께 전송
- 응답의 평균/개수를 즉시 UI 반영

5. 문서 정리
- README에 별점 기능 요약 및 FE 연동 포인트 추가
- 별점 전용 문서(`09_location_ratings.md`) 추가
- 데이터베이스/API 문서에 테이블/엔드포인트/제한 규칙 반영

## 검증 결과

- `python -m compileall app scripts` 성공
- 서버 기동 후 별점 등록 성공
- 동일 `client_id` 즉시 재등록 시 429 응답 확인
- 장소 목록 응답에 `rating_avg`, `rating_count` 반영 확인

## 비고

- FE는 `client_id`를 localStorage에 저장해서 재방문 UX를 개선하는 것이 좋음
- 별점 평균은 소수 첫째 자리 기준으로 표시 가능
