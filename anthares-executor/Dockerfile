FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
 && apt-get install -y --no-install-recommends chromium ca-certificates dumb-init \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/anthares-executor
COPY anthares-executor/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY anthares-executor/app.py ./app.py
COPY anthares-executor/supervisor.sh ./supervisor.sh
COPY anthares-brouser/profile_store.py ./profile_store.py
RUN chmod 0755 ./supervisor.sh \
 && mkdir -p /data/chrome-profile /run/anthares-executor

ENV CHROME_PROFILE_DIR=/data/chrome-profile PORT=8080 CDP_PORT=9222
EXPOSE 8080
HEALTHCHECK --interval=20s --timeout=3s --start-period=25s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health',timeout=2)" || exit 1
ENTRYPOINT ["/usr/bin/dumb-init","--"]
CMD ["/opt/anthares-executor/supervisor.sh"]
