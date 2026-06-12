#!/bin/sh
set -e
alembic upgrade head
python -m backend.seed_demo
exec uvicorn backend.main:app --host 0.0.0.0 --port 8080
