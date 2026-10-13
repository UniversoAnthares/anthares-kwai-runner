FROM python:3.12-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends chromium ca-certificates fonts-liberation tini && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY executor.py .
RUN useradd -m -u 10001 anthares && mkdir -p /data/profile /data/state && chown -R anthares:anthares /data
USER anthares
EXPOSE 8080
ENTRYPOINT ["/usr/bin/tini","--"]
CMD ["python","executor.py"]
