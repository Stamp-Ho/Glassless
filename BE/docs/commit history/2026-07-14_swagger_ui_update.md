# 2026-07-14 Swagger UI 경로 추가

## 작업 개요

FastAPI 기본 문서 경로(`/docs`) 외에 별도 Swagger UI 접근 경로(`/swagger-ui`)를 추가했습니다.

## 변경 파일

- `BE/src/app/main.py`
- `BE/README.md`

## 상세 변경

1. `main.py`
- `get_swagger_ui_html`를 import
- `GET /swagger-ui` 엔드포인트 추가 (`include_in_schema=False`)
- OpenAPI 스키마는 기존 `app.openapi_url`(`/openapi.json`)을 재사용

2. `BE/README.md`
- API 문서 경로 안내에 `/docs`, `/swagger-ui` 명시

## 검증 결과

- `GET /docs` -> `200`
- `GET /swagger-ui` -> `200`
- `GET /openapi.json` -> `200`

## 비고

- 기본 FastAPI Swagger 경로(`/docs`)는 유지됩니다.
- `/swagger-ui`는 동일 OpenAPI 스키마를 사용하는 별칭 UI 경로입니다.
