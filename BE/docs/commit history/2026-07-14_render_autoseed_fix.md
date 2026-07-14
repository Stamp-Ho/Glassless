# 2026-07-14 Render 자동 시드 연결 수정

## 작업 개요

Render Free 플랜에서 서비스 시작 시 `locations` 테이블이 비어 있으면 `BE/data/<권역>/*.json`을 자동 적재하도록 연결했습니다.

## 변경 파일

- `BE/src/app/main.py`
- `BE/src/scripts/migrate.py`
- `BE/docs/03_database_and_migration.md`
- `BE/docs/04_api_implementation.md`
- `BE/docs/07_render_cicd.md`

## 상세 변경

1. 앱 시작 시 자동 시드
- `lifespan`에서 `seed_locations_if_empty()` 호출
- `locations` 테이블이 비어 있으면 JSON 적재
- Render 재배포/재시작 시 `/tmp` DB가 비어도 데이터가 다시 채워짐

2. 마이그레이션 스크립트 보강
- 전체 권역 디렉토리 자동 탐색
- 비어 있을 때만 시드하는 함수 추가
- 기존 데이터가 있으면 중복 적재하지 않음

3. 문서 갱신
- 데이터베이스/마이그레이션 문서에 startup auto-seed 반영
- API 문서에 Locations API가 JSON 기반 데이터 조회임을 명시
- Render CI/CD 문서에 자동 시드 동작과 Free 플랜 주의사항 반영

## 검증 결과

- 서버 시작 로그에서 `Location table already seeded. count=12702` 확인
- API 응답 확인:
  - `서울/관광지` -> `200`
  - `부산/레포츠` -> `200`
  - `광주_전라권/음식점` -> `200`

## 비고

- Render Free 플랜은 디스크를 지원하지 않으므로, `/tmp` DB는 재시작 시 유지되지 않습니다.
- 대신 시작 시 JSON 자동 적재로 데이터 연결을 복구합니다.
