# 06. 개발 워크플로우 및 배포

## 1) 개발 순서 (권장)

1. `core/config.py`, `core/database.py` 작성
2. `models` 정의 및 테이블 생성
3. `schemas` 작성
4. `posts` 라우터 구현 및 테스트
5. `migrate.py`로 `Location` 데이터 적재
6. `chat` 라우터 + OpenAI 연동
7. 통합 테스트 및 Render 배포

## 2) 최소 테스트 시나리오

- Posts
  - 생성 -> 조회 -> 수정(성공/실패) -> 삭제(성공/실패)
- Chat
  - 정상 질의 응답
  - 빈 질의/초과 길이 질의 거부
  - OpenAI 타임아웃/실패 처리

## 3) Render 배포 메모

- Start Command 예시:

```bash
uvicorn src.app.main:app --host 0.0.0.0 --port $PORT
```

- Environment Variables 설정:
  - `DATABASE_URL`
  - `OPENAI_API_KEY`
  - `OPENAI_MODEL`
  - `OPENAI_MAX_TOKENS`
  - `OPENAI_TIMEOUT_SECONDS`

## 4) 운영 체크포인트

- 로그에 민감정보 출력 금지
- 에러 응답 메시지 표준화
- 타임아웃/재시도 정책 명확화

## 5) 다음 확장 후보 (MVP 이후)

- 지역별 캐싱
- 검색 품질 개선(토큰화/동의어)
- 관리자 데이터 갱신 도구
