#!/usr/bin/env bash
set -e

URL=${1:-http://localhost:3000/api/health}

echo "[INFO] Checking $URL"

if curl -fsS "$URL" >/dev/null; then
  echo "[OK] API healthy"
  exit 0
else
  echo "[ERROR] API not responding"
  exit 1
fi
