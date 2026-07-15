# 2026-07-15 작업 요약: MapView API 조회 시점 최적화

## 개요
MapView의 장소 데이터 조회를 과도하게 반복하지 않도록, BE locations API 호출 시점을 카테고리/권역 필터 변경 시점으로 제한했다.

## 변경 내용
- `FE/src/views/MapView.vue`
- 장소 조회 함수 `loadPlacesByFilters`로 정리
- API 호출 파라미터를 필터 상태와 연동
  - `region=서울` 고정
  - 카테고리 선택 시 `category` 전달
  - 권역 선택 시 `keyword` 전달
- `watch([selectedCategory, selectedDistrict])`에서만 재조회 실행
- 지도 이동/줌(`idle`) 시에는 마커 렌더만 수행하고 API 재호출하지 않음
- 빠른 필터 변경 시 오래된 응답이 최신 상태를 덮어쓰지 않도록 요청 토큰(`fetchRequestToken`) 가드 추가

## 기대 효과
- 불필요한 네트워크 호출 감소
- 필터 중심 조회 UX 일관성 개선
- 빠른 연속 변경 시 데이터 표시 안정성 향상

## 검증
- FE 빌드 성공: `npm run build`
- Vite production build 통과 확인
