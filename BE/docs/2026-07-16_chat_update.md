# 2026-07-16 — Chat endpoint updates

변경 요약:

- 파일: `BE/src/app/routers/chat.py`
  - OpenAI 추출 프롬프트를 단 5개의 canonical 권역(광주_전라권, 구미_경북권, 대전_충청권, 부산, 서울)으로 제한함.
  - `_map_to_allowed_region` 개선: OpenAI가 canonical 키(예: `광주_전라권`)를 반환해도 올바르게 매핑하도록 허용.
  - 클라이언트 응답 단순화: API `answer`는 상세 데이터 대신 간단한 확인 문장("네, {권역}의 {카테고리} 정보를 알려드릴게요.")만 반환하도록 변경. 상세한 장소 목록은 `references`에 유지.

테스트:

- 로컬 서버에서 `/api/chat`에 POST 요청으로 `{"query":"서울 레포츠 추천해 줘"}`를 호출해 동작 확인.
- 응답: `answer`가 간단한 문장으로 나오고, `references`에 장소 목록(10개)이 포함됨.

추가 메모:

- 변경 사항은 커밋되어 원격 브랜치로 푸시됨.
- 필요하면 `answer` 문구, `references` 개수 제한, 또는 category 정규화 추가 작업을 진행할 수 있음.
