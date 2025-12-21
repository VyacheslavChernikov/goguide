ARG PYTHON_VERSION=3.11-slim

# ---------- builder ----------
FROM python:${PYTHON_VERSION} AS builder
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app

# system deps for build (removed in final image)
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# ---------- runtime ----------
FROM python:${PYTHON_VERSION} AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=go_guide.settings \
    PORT=8000 \
    WORKERS=3 \
    THREADS=4 \
    TIMEOUT=30
WORKDIR /app

# create non-root user
RUN adduser --disabled-password --gecos "" appuser

# install wheels only (no build deps)
COPY --from=builder /wheels /wheels
RUN pip install --no-cache /wheels/* && rm -rf /wheels

# copy project
COPY . /app

# collect static at build time (no DB needed)
RUN python manage.py collectstatic --noinput || true

USER appuser
EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]

