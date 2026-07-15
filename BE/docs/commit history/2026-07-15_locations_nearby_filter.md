# 2026-07-15 작업 요약: locations API 좌표 근접 조회 추가

## 개요
`GET /api/locations`에서 `mapx`, `mapy` 좌표를 받으면 해당 좌표 인근 명소만 반환하도록 필터를 추가했다.

## 변경 파일
- `BE/src/app/routers/locations.py`

## 주요 변경
- 쿼리 파라미터 추가
  - `mapx: float | None`
  - `mapy: float | None`
  - `radius_km: float = 10.0` (최소 0 초과, 최대 100)
- 입력 검증 추가
  - `mapx`와 `mapy`는 반드시 함께 전달해야 하며, 하나만 전달하면 422 반환
- 근접 범위 필터 추가
  - 위도/경도 1도당 km 환산값을 사용해 bounding box를 계산
  - `mapx/mapy`가 null인 레코드는 제외
- 거리순 정렬 추가
  - 단순 거리 제곱식(위도/경도 차이 km 환산)으로 가까운 순 정렬
  - 동률 시 `id` 오름차순 정렬
- 기존 동작 유지
  - 좌표 파라미터가 없으면 기존과 동일하게 `id` 오름차순 정렬
  - `offset/limit` 페이지네이션은 동일하게 적용

## 사용 예시
- `GET /api/locations?mapx=126.9780&mapy=37.5665&radius_km=5&limit=20`

## 기대 효과
- 지도 중심 기반의 근접 명소 조회 가능
- 불필요한 전체 목록 조회 감소
