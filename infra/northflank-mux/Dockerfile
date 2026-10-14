FROM python:3.12-slim-bookworm
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    PORT=10000
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium ca-certificates fonts-liberation fonts-noto-color-emoji \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY infra/ /app/
RUN mkdir -p /ms-playwright \
    && pip install --no-cache-dir flask gunicorn requests "psycopg[binary]" cryptography playwright \
    && python -m playwright install chromium \
    && useradd --create-home --uid 10001 ara \
    && chown -R ara:ara /app /ms-playwright
USER ara
EXPOSE 10000
CMD ["sh","-c","set -eu; expected=$(python -c 'from playwright.sync_api import sync_playwright; p=sync_playwright().start(); print(p.chromium.executable_path); p.stop()'); if [ ! -x \"$expected\" ] && [ -x /usr/bin/chromium ]; then mkdir -p \"$(dirname \"$expected\")\"; ln -sf /usr/bin/chromium \"$expected\"; fi; exec gunicorn --bind 0.0.0.0:${PORT} --workers 1 --threads 4 --timeout 240 northflank_mux:app"]
