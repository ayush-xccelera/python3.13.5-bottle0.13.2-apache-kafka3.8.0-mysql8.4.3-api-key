#!/usr/bin/env bash
set -e

export PORT="${PORT:-20823}"

pip install -r requirements.txt

alembic upgrade head

exec gunicorn --bind 0.0.0.0:"$PORT" app.main:app
