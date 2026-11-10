#!/bin/sh
set -e
if [ "${KAGGLE_SYNC_ON_START:-0}" = "1" ]; then
  python sync_kaggle.py || echo "Kaggle sync failed; API will start with existing/local samples."
fi
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
