2026-07-16 — Fix merge conflicts and missing model

Summary:
- Removed leftover git merge conflict markers in `app/core/config.py` and `app/routers/locations.py`.
- Added missing `LocationRating` model (`app/models/location_rating.py`) required by `app/routers/chat.py`.
- Exported `LocationRating` from `app/models/__init__.py`.
- Verified application imports and started the server; `/health` returns `{"status": "ok"}`.

Files changed:
- BE/src/app/core/config.py
- BE/src/app/routers/locations.py
- BE/src/app/models/location_rating.py (new)
- BE/src/app/models/__init__.py

Notes:
- Installed Python dependencies in the project's venv before verification.
- Recommend running full test suite and CI pipeline after merging.
