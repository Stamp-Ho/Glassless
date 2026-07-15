# 2026-07-14 포럼 페이지 API 전환 및 UX 개선

## 개요
더미/localStorage 기반 게시판 화면을 백엔드 API 기반으로 전환하고, 상세 페이지에서 수정/삭제 UX를 개선했다.

## 변경 파일
- `FE/src/views/PostListView.vue`
- `FE/src/views/DetailView.vue`

## PostListView 변경
1. 더미/localStorage 제거
- 게시글 목록을 `GET /api/posts`로 조회
- 필터(`region`, `category`, `location_id`)를 쿼리로 전달

2. 등록 기능 API 연동
- `POST /api/posts` 사용
- 필수 입력: 카테고리, 제목, 지역, 본문, 비밀번호
- 등록 중 중복 클릭 방지(`isSubmitting`)

3. 지역 입력 제한
- 자유 입력 제거
- FE에서 5개 권역 고정 선택
  - `서울`, `부산`, `광주_전라권`, `구미_경북권`, `대전_충청권`
- 지정된 값 외 입력 차단

4. 목록 카드 UX
- 카드 클릭 시 상세로 이동
- 삭제 기능은 목록에서 제거하고 상세 페이지로 이동
- 카드 경계선 가시성 개선(테두리/구분선/hover 대비 강화)

## DetailView 변경
1. 상세 조회 API 연동
- `GET /api/posts/{id}` 사용
- 로딩/에러/404 상태 분기 처리

2. 수정 기능
- 수정 모드 진입 시 기존 레이아웃을 유지한 채 텍스트 표시 영역이 입력 요소로 전환
  - 카테고리: badge -> select
  - 제목: text -> input
  - 본문: text -> textarea
- 저장 시 `PUT /api/posts/{id}` 호출
- 수정 확정 전 비밀번호 필수 입력

3. 삭제 기능
- 상세 카드 우측 하단에 삭제 버튼 배치
- 삭제 버튼 클릭 시 모달 오픈
- 모달에서 비밀번호 입력 후 확인 시 `DELETE /api/posts/{id}` 호출

## API 베이스 URL
- `VITE_API_BASE_URL` 우선 사용
- 미설정 시 `http://127.0.0.1:8000` 기본값 사용

## 검증
- FE 빌드 통과 (`npm run build`)
