# syntax=docker/dockerfile:1
# Multi-stage build for the GOD MODE AI backend.

# ----------------------------------------------------------------------------- builder
FROM python:3.12-slim AS builder
WORKDIR /app
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
COPY requirements.txt .
RUN pip install --prefix=/install -r requirements.txt

# ----------------------------------------------------------------------------- runtime
FROM python:3.12-slim AS runtime
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_ENV=production \
    USE_IN_MEMORY_BACKENDS=false
WORKDIR /app

# Non-root user.
RUN groupadd --system app && useradd --system --gid app --home /app app

# Python deps from the builder layer.
COPY --from=builder /install /usr/local

# Application code.
COPY backend ./backend
COPY docker/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh && chown -R app:app /app

USER app
EXPOSE 8000

# Container-level health probe hits the API health endpoint.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health').status==200 else 1)"

ENTRYPOINT ["entrypoint.sh"]
# Production: Gunicorn managing Uvicorn workers.
CMD ["gunicorn", "backend.api.main:app", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--workers", "4", "--bind", "0.0.0.0:8000", \
     "--timeout", "120", "--graceful-timeout", "30", "--access-logfile", "-"]
