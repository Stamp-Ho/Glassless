# 09. 명소 별점 기능

## 작업 개요

명소(Location)에 사용자가 별점을 남길 수 있도록 별도 테이블과 API를 추가했습니다.

## 저장 구조

- 테이블: `location_ratings`
- 저장 필드:
  - `location_id`
  - `score` (1~5)
  - `client_id` (localStorage 기반 UUID)
  - `ip_address`
  - `user_agent`
  - `created_at`

## 제한 규칙

- 동일 `location_id`에 대해 24시간 내 재평가 제한
- 제한 판단 기준:
  - `client_id`
  - IP + User-Agent
- FE는 localStorage에 `client_id`를 저장하고 매 요청에 함께 전송

## API

### POST `/api/locations/{location_id}/ratings`

- 사용자가 명소에 별점을 남김
- 1~5점만 허용
- 중복 제한에 걸리면 429 반환

### GET `/api/locations`

- 각 명소에 대해 다음 값을 함께 반환
  - `rating_avg`
  - `rating_count`

### GET `/api/locations/{location_id}`

- 상세 페이지에서도 동일한 별점 요약 값을 함께 반환

## FE 연동 가이드

1. 최초 진입 시 localStorage에 `client_id`가 없으면 UUID 생성
2. 별점 UI 제출 시 `client_id`와 점수를 함께 전송
3. 응답의 `rating_avg`와 `rating_count`를 즉시 반영
4. 이미 평가한 경우 localStorage에 마지막 평점 정보를 저장해 UX를 개선

## UI 권장

- 별점은 5점 고정
- 평균 점수는 소수 첫째 자리까지 표시
- 별점 개수는 별 아이콘/텍스트와 함께 노출
