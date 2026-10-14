FROM python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=10000

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates fonts-liberation fonts-noto-color-emoji \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir flask requests "psycopg[binary]" cryptography gunicorn playwright \
    && python -m playwright install --with-deps chromium \
    && useradd --create-home --uid 10001 ara

COPY infra/ /app/
RUN chown -R ara:ara /app

USER ara
EXPOSE 10000

CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:${PORT} --workers 1 --threads 4 --timeout 240 northflank_combined_app:app"]
