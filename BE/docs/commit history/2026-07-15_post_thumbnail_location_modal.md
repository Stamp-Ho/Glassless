# 2026-07-15 작업 요약: 게시글 썸네일 필드 및 명소 모달 연동

## 개요
게시글에 명소 썸네일 URL(`thumbnail_url`)을 저장/노출하는 기능을 추가하고, FE에서 명소 선택 모달을 통해 `location_id`와 썸네일 URL을 함께 처리하도록 개선했다.

## BE 변경

### 1) Post 모델/스키마 확장
- `posts` 테이블에 `thumbnail_url` 컬럼 추가
- PostCreate/PostUpdate/PostResponse/PostListItem 스키마에 `thumbnail_url` 필드 추가

### 2) DB 초기화 시 자동 컬럼 보정
- 기존 DB에 `thumbnail_url` 컬럼이 없으면 startup 시 `ALTER TABLE`로 추가

### 3) 게시글 생성/수정 로직 보강
- `location_id`가 지정된 경우, 연결된 Location의 `image_url(firstimage)`를 썸네일로 저장
- `location_id` 해제 시 `thumbnail_url`도 함께 비움
- 위치 변경 시 region을 명소 region으로 동기화

## FE 변경

### 1) PostListView
- 글 작성 시 명소 선택 모달에서 location 선택 시 `image_url`을 내부 상태에 저장
- 생성 payload에 `location_id`, `thumbnail_url` 포함
- 게시글 카드에서 `thumbnail_url`이 있으면 썸네일 배경 이미지 표시

### 2) DetailView
- 상세 화면에 썸네일 노출(`thumbnail_url` 존재 시)
- 수정 모드에서 명소 탐색 모달(권역 -> 카테고리 -> 키워드 검색) 추가
- 명소 재선택/연결 해제 가능
- 수정 payload에 `location_id`, `thumbnail_url` 반영

## 검증
- FE 빌드 성공 (`npm run build`)
- 변경 파일 정적 오류 없음

## 비고
- 썸네일 소스는 TourAPI `firstimage`를 적재한 `location.image_url`을 사용
- `firstimage`가 없는 명소는 `thumbnail_url`을 비워 저장
