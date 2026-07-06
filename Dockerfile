# ─── STAGE 1: builder ───────────────────────────────────
FROM python:3.13-slim AS builder
WORKDIR /build

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ─── STAGE 2: production ────────────────────────────────
FROM python:3.13-slim AS production

LABEL org.opencontainers.image.source="https://github.com/alonsodon/monitored-api"

WORKDIR /app

COPY --from=builder /install /usr/local
COPY alembic.ini .
COPY alembic/ ./alembic/
COPY app/ ./app/

RUN adduser --disabled-password --gecos '' appuser
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

