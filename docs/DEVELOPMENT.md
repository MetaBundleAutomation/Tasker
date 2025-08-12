# Tasker Development Guide

This doc covers running Tasker locally and via Docker. Stack: FastAPI + HTMX. Single image. No Node.

## Local (Python) Dev
- Create a virtualenv (recommended) and install deps:
  ```bash
  python -m venv .venv
  .venv\Scripts\activate  # PowerShell: . .venv/Scripts/Activate.ps1
  pip install -r requirements.txt
  ```
- Run the server:
  ```bash
  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
  ```
- Open http://localhost:8000

## Docker
- Build:
  ```bash
  docker build -t tasker:dev .
  ```
- Run:
  ```bash
  docker run --rm -it -p 8000:8000 tasker:dev
  ```
- Open http://localhost:8000

## Project Structure
```
app/            # FastAPI backend
  main.py
static/
  css/
    styles.css
templates/      # Jinja2 templates
  base.html
  index.html
  partials/
    board.html
    analysis.html
Dockerfile
requirements.txt
```

## Future-proofing for FE/BE split
- HTML uses HTMX now; JSON API exposed under `/api/*` for future separate frontend.
- Add CORS config as needed when a separate frontend origin is used.

## Health check
- GET `/healthz` returns `{ "status": "ok" }`.
