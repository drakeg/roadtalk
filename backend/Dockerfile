# syntax=docker/dockerfile:1.12
FROM python:3.12-slim@sha256:423ed6ab25b1921a477529254bfeeabf5855151dc2c3141699a1bfc852199fbf AS builder
WORKDIR /build
COPY backend/pyproject.toml backend/README.md ./
COPY backend/app ./app
RUN python -m venv /opt/venv && /opt/venv/bin/pip install --no-cache-dir .

FROM python:3.12-slim@sha256:423ed6ab25b1921a477529254bfeeabf5855151dc2c3141699a1bfc852199fbf
ENV PATH="/opt/venv/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN groupadd --system roadtalk && useradd --system --gid roadtalk --home /app roadtalk
WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY backend/alembic.ini ./
COPY backend/migrations ./migrations
COPY deploy/field-test /opt/roadtalk/deploy
USER roadtalk
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/live', timeout=2)"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
