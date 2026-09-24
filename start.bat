@echo off
if not defined PORT set PORT=20823

pip install -r requirements.txt

alembic upgrade head

waitress-serve --host=0.0.0.0 --port=%PORT% app.main:app
