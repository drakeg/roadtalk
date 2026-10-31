# syntax=docker/dockerfile:1.28
FROM scratch AS browser-assets
ADD --checksum=sha256:a77a2f4c363e93099d7c135721c9ec81d6c5bacc691796dad799222e33cbfb31 \
    https://cdn.jsdelivr.net/npm/livekit-client@2.21.0/dist/livekit-client.umd.js \
    /livekit-client.umd.js

FROM python:3.14-slim@sha256:cd89c30eda26ee911a4611b18680086e0ea42e6f5f8cbe653d07fa7958c9cec8 AS builder
WORKDIR /build
COPY backend/pyproject.toml backend/README.md ./
COPY backend/app ./app
RUN python -m venv /opt/venv && /opt/venv/bin/pip install --no-cache-dir .

FROM python:3.14-slim@sha256:cd89c30eda26ee911a4611b18680086e0ea42e6f5f8cbe653d07fa7958c9cec8
ENV PATH="/opt/venv/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN python -m pip install --no-cache-dir --upgrade "setuptools>=78.1.1" \
    && apt-get update \
    && apt-get upgrade --no-install-recommends -y \
    && apt-get install --only-upgrade --no-install-recommends -y \
      libssl3t64 \
      openssl \
      openssl-provider-legacy \
      util-linux \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system roadtalk \
    && useradd --system --gid roadtalk --home /app roadtalk
WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
RUN /opt/venv/bin/pip install --no-cache-dir --upgrade \
      "setuptools>=78.1.1" \
      "msgpack>=1.2.3" \
      "urllib3>=2.8.0"
COPY --from=browser-assets /livekit-client.umd.js /opt/roadtalk/web/livekit-client.umd.js
COPY backend/alembic.ini ./
COPY backend/migrations ./migrations
COPY deploy/field-test /opt/roadtalk/deploy
USER roadtalk
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/live', timeout=2)"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
