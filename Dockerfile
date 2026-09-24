# syntax=docker/dockerfile:1

FROM python:3.13.5-slim AS builder

WORKDIR /build

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.13.5-slim

RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

COPY --from=builder /install /usr/local
COPY . .

ENV PORT=20823
EXPOSE 20823

USER appuser

CMD ["sh", "-c", "alembic upgrade head && gunicorn --bind 0.0.0.0:${PORT:-20823} app.main:app"]
