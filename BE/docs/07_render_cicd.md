# 07. Render CI/CD 준비 가이드

## 1) 추가된 파일

- `render.yaml` (레포 루트)
- `.gitlab-ci.yml` (레포 루트)

## 2) Render Blueprint 설정

`render.yaml` 기준으로 다음이 자동 구성됩니다.

- 서비스 타입: Python Web Service
- 서비스 루트: `BE`
- Build Command: `pip install -r src/requirements.txt`
- Start Command: `python -m uvicorn app.main:app --app-dir src --host 0.0.0.0 --port $PORT`
- Health Check Path: `/health`
- Persistent Disk:
  - mount path: `/var/data`
  - DB 경로: `sqlite+aiosqlite:////var/data/localhub.db`

## 3) GitLab CI/CD 파이프라인

`.gitlab-ci.yml`은 아래 두 단계를 수행합니다.

1. `test` 단계
- `BE/src/requirements.txt` 설치
- Python 컴파일 체크(`compileall`)
- 앱 import 스모크 테스트

2. `deploy` 단계
- 조건: `main` 브랜치 + 관련 파일 변경
- Render Deploy Hook 호출

## 4) GitLab 변수 설정

프로젝트 CI/CD Variables에 아래를 추가하세요.

- `RENDER_DEPLOY_HOOK_URL` : Render 서비스의 Deploy Hook URL

선택 변수(운영 환경):
- `OPENAI_API_KEY`
- `CORS_ORIGINS`

## 5) Render 환경 변수 확인

`render.yaml`에 기본값이 있지만, 운영에서는 Render Dashboard에서 재확인 권장:

- `DATABASE_URL`
- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `OPENAI_MAX_TOKENS`
- `OPENAI_TIMEOUT_SECONDS`
- `CHAT_MAX_QUERY_LENGTH`
- `CHAT_MAX_REFERENCES`

## 6) 배포 흐름

1. `main` 브랜치에 BE 변경사항 머지
2. GitLab CI `test` 통과
3. CI에서 Render Deploy Hook 호출
4. Render가 새 이미지/코드 배포
5. `/health` 체크 성공 시 서비스 활성화

## 7) 트러블슈팅

- 배포가 안 되면:
  - GitLab 변수 `RENDER_DEPLOY_HOOK_URL` 설정 여부 확인
  - Render Blueprint가 `render.yaml`을 읽는지 확인
  - Render 로그에서 build/start command 에러 확인
- DB 초기화 이슈:
  - 디스크 mount path(`/var/data`)와 `DATABASE_URL` 일치 여부 확인
