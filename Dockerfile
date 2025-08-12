# syntax=docker/dockerfile:1
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps (optional minimal)
RUN apt-get update -y && apt-get install -y --no-install-recommends \
    build-essential \
  && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

# App
COPY app /app/app
COPY templates /app/templates
COPY static /app/static

EXPOSE 8000

# Enable uvicorn reload with env toggle
ENV UVICORN_HOST=0.0.0.0 \
    UVICORN_PORT=8000 \
    UVICORN_RELOAD=false

CMD ["sh", "-c", "uvicorn app.main:app --host ${UVICORN_HOST} --port ${UVICORN_PORT} ${UVICORN_RELOAD:+--reload}"]
