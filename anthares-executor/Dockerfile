FROM python:3.12-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8080
RUN apt-get update && apt-get install -y --no-install-recommends chromium ca-certificates fonts-liberation fonts-noto-color-emoji tini curl && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY executor.py controller_client.py profile_store.py kwai_probe.py ./
RUN useradd -m -u 10001 anthares && mkdir -p /data/profile /data/state && chown -R anthares:anthares /data /app
USER anthares
EXPOSE 8080
ENTRYPOINT ["/usr/bin/tini","--"]
CMD ["sh","-c","exec gunicorn --workers 1 --threads 4 --timeout 90 --graceful-timeout 15 --bind 0.0.0.0:${PORT:-8080} executor:app"]
