#!/usr/bin/env bash
set -euo pipefail

# Init DB script: copy seed DB into persistent DATA_DIR if DB not present.
# Usage: DATA_DIR=/data ./BE/scripts/init_db.sh

DATA_DIR="${DATA_DIR:-/data}"
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SEED_DB_PATH="$REPO_DIR/data/localhub_filled.db"
DB_PATH="$DATA_DIR/localhub.db"

mkdir -p "$DATA_DIR"

# Always copy seed DB on startup to ensure seed data is applied
if [ -f "$SEED_DB_PATH" ]; then
  cp -f "$SEED_DB_PATH" "$DB_PATH"
  echo "Copied seed DB to $DB_PATH (overwritten)"
else
  echo "No seed DB found at $SEED_DB_PATH; leaving empty DB to be created by app"
fi

# Ensure permissions
chmod 644 "$DB_PATH" || true

exit 0
