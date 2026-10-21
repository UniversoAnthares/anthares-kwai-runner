FROM python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    PORT=10000

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates fonts-liberation fonts-noto-color-emoji \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /ms-playwright \
    && pip install --no-cache-dir flask requests "psycopg[binary]" cryptography gunicorn playwright \
    && python -m playwright install --with-deps chromium \
    && useradd --create-home --uid 10001 ara \
    && chown -R ara:ara /ms-playwright

COPY infra/ /app/
COPY tools/x_publication_safety.py /app/tools/x_publication_safety.py
RUN chown -R ara:ara /app

USER ara
EXPOSE 10000

# The vault-backed Anthares Browser uses Playwright's synchronous API and keeps
# one browser/context alive across requests. Keep all accesses on one Gunicorn
# thread; the runtime mesh already serializes browser mutations with its lease.
CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:${PORT} --workers 1 --threads 1 --timeout 240 northflank_combined_app:app"]
