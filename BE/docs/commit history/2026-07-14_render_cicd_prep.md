# 2026-07-14 Render CI/CD 준비

## 작업 개요

Render 배포 자동화와 SSAFY GitLab CI 연동을 위한 기본 파일과 문서를 추가했습니다.

## 변경 파일

- `render.yaml`
- `.gitlab-ci.yml`
- `BE/docs/07_render_cicd.md`
- `BE/docs/README.md`

## 상세 변경

1. `render.yaml` 추가
- Render Blueprint 기반 서비스 정의
- `rootDir: BE`
- Build: `pip install -r src/requirements.txt`
- Start: `python -m uvicorn app.main:app --app-dir src --host 0.0.0.0 --port $PORT`
- Health Check: `/health`
- Persistent Disk(`/var/data`) 및 SQLite 경로(`/var/data/localhub.db`) 설정
- 운영 환경변수 기본값/필수값 정의

2. `.gitlab-ci.yml` 추가
- `test` 스테이지:
  - 의존성 설치
  - `compileall` 문법 체크
  - FastAPI 앱 import 스모크 테스트
- `deploy` 스테이지:
  - `main` 브랜치 조건에서 실행
  - `RENDER_DEPLOY_HOOK_URL`로 Render 배포 트리거

3. 문서 추가
- `BE/docs/07_render_cicd.md`에 Render/GitLab 변수/배포 흐름/트러블슈팅 정리
- `BE/docs/README.md`에 07번 문서 링크 추가

## 운영 체크포인트

- GitLab CI/CD Variables에 `RENDER_DEPLOY_HOOK_URL` 등록 필요
- Render Dashboard에서 `OPENAI_API_KEY`, `CORS_ORIGINS` 값 확인 필요
- `main` 브랜치 머지 후 test/deploy 파이프라인 동작 확인 필요
