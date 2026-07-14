# 2026-07-14 Render Free Tier 디스크 이슈 수정

## 작업 개요

Render Free 플랜에서 `disk` 설정이 지원되지 않아 배포가 실패하는 문제를 수정했습니다.

## 변경 파일

- `render.yaml`
- `BE/docs/07_render_cicd.md`

## 상세 변경

1. `render.yaml`
- `disk` 블록 제거
- `DATABASE_URL` 변경
  - 이전: `sqlite+aiosqlite:////var/data/localhub.db`
  - 변경: `sqlite+aiosqlite:////tmp/localhub.db`

2. `BE/docs/07_render_cicd.md`
- Free 플랜 디스크 미지원 제약 명시
- `/tmp` 기반 SQLite 경로 사용 안내
- 데이터 비영속성(재배포/재시작 시 유실 가능) 명시
- 영속 저장이 필요할 때 유료 플랜 + disk 사용 안내 추가

## 결과

- Render Blueprint 파싱/적용 시 Free 플랜 제약 충돌 제거
- 문서와 실제 배포 설정 일치
