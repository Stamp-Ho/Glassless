# Render 배포 가이드 (영구 DB 및 시드 복사)

이 문서는 Render 무료 플랜에서 앱을 배포할 때, 매번 초기화되더라도 시작 시점에 샘플 데이터가 들어있도록 설정하는 절차입니다.

1. 영구 디스크 추가
- Render 서비스에서 Persistent Disk를 추가합니다.
- 마운트 경로로 `/data`를 사용합니다.

2. 환경 변수 설정
- `DATABASE_URL`을 다음 값으로 설정합니다:
  - `sqlite+aiosqlite:////data/localhub.db`
- (선택) `DATA_DIR`를 `/data`로 설정합니다.

3. 시드 DB 파일
- 저장소에는 `BE/data/localhub_filled.db`(샘플 데이터 포함)가 있습니다.
- `init_db.sh` 스크립트는 배포 컨테이너에서 `/data/localhub.db`가 없으면 이 파일을 복사합니다.

4. Start Command
- Render의 서비스 Start Command를 아래처럼 설정하세요:

```
/bin/bash BE/scripts/init_db.sh && uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers
```

(만약 가상환경을 사용하거나 다른 런처를 원하면 uvicorn 실행 부분을 적절히 변경하세요.)

5. 동작 원리
- 컨테이너가 시작될 때 `init_db.sh`가 실행되어 `/data/localhub.db`가 없으면 리포지토리의 `BE/data/localhub_filled.db`를 복사합니다.
- 이후 앱이 `DATABASE_URL`로 지정된 DB를 사용하므로, 매번 초기화되는 런타임에서도 기본 데이터가 들어있게 됩니다.

6. 주의사항
- Render 무료 플랜에서는 인스턴스 재생성 시 파일시스템이 초기화될 수 있습니다. 영구 디스크는 유지되지만, 서비스 설정에 따라 차이가 있을 수 있으니 Render의 영구 디스크 동작을 확인하세요.
- seed DB에 민감 정보가 포함되지 않도록 주의하세요.

7. 추가 개선 제안
- seed 과정을 idempotent SQL 마이그레이션/시드 스크립트로 교체
- SQLite 대신 Postgres 사용 권장(동시성/안정성)
