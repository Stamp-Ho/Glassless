# 2026-07-14 다권역 Location API 연결

## 작업 개요

요청한 5개 권역(서울, 부산, 광주_전라권, 구미_경북권, 대전_충청권)과 카테고리 데이터가 API에서 조회되도록 locations 조회 API와 마이그레이션 로직을 확장했습니다.

## 변경 파일

- `BE/src/app/routers/locations.py`
- `BE/src/app/schemas/location.py`
- `BE/src/app/main.py`
- `BE/src/scripts/migrate.py`
- `BE/docs/03_database_and_migration.md`
- `BE/docs/04_api_implementation.md`

## 상세 변경

1. Locations 라우터 추가
- `GET /api/locations`
  - 필터: `region`, `category`, `keyword`
  - 페이지네이션: `limit`, `offset`
- `GET /api/locations/{location_id}`
  - 단건 상세 조회

2. 앱 라우터 등록
- `main.py`에 `locations_router` 등록 (`/api` prefix)

3. 마이그레이션 확장
- 기존 서울 전용 적재 -> `BE/data/<권역>/*.json` 전체 자동 순회
- 중복 방지 기준: `content_id + name`

4. 문서 갱신
- API 구현 문서에 Locations API 섹션 추가
- DB/마이그레이션 문서에 다권역 구조와 실행법 업데이트
- 서울/부산 음식점 JSON 부재 가능성 주의사항 반영

## 검증 결과

- 마이그레이션 실행 결과:
  - `files=38, inserted=6184, skipped=6518`

- API 스팟 체크:
  - `서울/관광지` -> `200`, 데이터 존재
  - `부산/레포츠` -> `200`, 데이터 존재
  - `광주_전라권/음식점` -> `200`, 데이터 존재
  - `구미_경북권/축제공연행사` -> `200`, 데이터 존재
  - `대전_충청권/문화시설` -> `200`, 데이터 존재

## 비고

- 현재 데이터셋 기준 `서울`, `부산`은 `음식점` JSON 파일이 없어 해당 카테고리 조회가 비어 있을 수 있습니다.
