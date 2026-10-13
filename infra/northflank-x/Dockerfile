FROM python:3.12-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=10000

RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium ca-certificates fonts-liberation fonts-noto-color-emoji \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir flask gunicorn playwright requests cryptography \
    && python -m playwright install chromium

EXPOSE 10000
CMD ["sh","-c","gunicorn --workers 1 --threads 4 --timeout 180 --bind 0.0.0.0:${PORT} --chdir infra x_render_worker_v3:app"]
