# LocalHub Backend Docs

이 디렉토리는 LocalHub 백엔드(FastAPI + SQLite + SQLAlchemy 2.0 + Pydantic v2) 프로젝트의 생성/개발 가이드를 담습니다.

## 문서 맵

- [01 프로젝트 생성 가이드](./01_project_setup.md)
- [02 아키텍처 및 디렉토리 규칙](./02_architecture.md)
- [03 데이터베이스 및 마이그레이션](./03_database_and_migration.md)
- [04 API 구현 가이드 (posts/chat)](./04_api_implementation.md)
- [05 보안 및 운영 제약 체크리스트](./05_security_and_constraints.md)
- [06 개발 워크플로우 및 배포](./06_workflow_and_deploy.md)

## MVP 원칙

- 단순성 우선: 익명 서비스, 최소 기능으로 빠른 운영 가능 상태 달성
- 비동기 우선: `async def`, `await`, `AsyncSession` 중심 구현
- 제약 준수: 환경 변수, 비용 제한, 인증 단순화 규칙 엄수
