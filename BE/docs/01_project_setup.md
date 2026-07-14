# 01. 프로젝트 생성 가이드

## 1) 목표

LocalHub 백엔드 MVP를 빠르게 실행 가능한 상태로 초기화합니다.

## 2) 권장 디렉토리 구조

```text
BE/
├── src/
│   ├── app/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── routers/
│   │   └── main.py
│   ├── scripts/
│   │   └── migrate.py
│   ├── .env.example
│   ├── .gitignore
│   └── requirements.txt
├── data/
│   ├── SCHEMA.md
│   ├── SOURCE.md
│   └── *.json
└── docs/
```

## 3) Python 환경

- Python 3.10+
- 가상환경 생성 후 의존성 설치

```bash
python -m venv .venv
source .venv/Scripts/activate  # Windows Git Bash 기준
pip install -U pip
```

## 4) requirements.txt 초안

```txt
fastapi
uvicorn[standard]
sqlalchemy>=2.0
aiosqlite
pydantic>=2
pydantic-settings
httpx
python-dotenv
```

## 5) .env.example

```env
APP_NAME=LocalHub API
APP_ENV=dev
APP_HOST=0.0.0.0
APP_PORT=8000
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

DATABASE_URL=sqlite+aiosqlite:///./localhub.db
OPENAI_API_KEY=YOUR_OPENAI_API_KEY
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=500
OPENAI_TIMEOUT_SECONDS=15
CHAT_MAX_QUERY_LENGTH=500
```

## 6) .gitignore 핵심 규칙

```gitignore
# Python
__pycache__/
*.py[cod]
.venv/

# Env
.env

# DB
*.db
*.sqlite3

# IDE
.vscode/
```

## 7) 실행 명령

```bash
uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000
```

Swagger 문서: `/docs`
