FROM python:3.12-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    xvfb \
    x11vnc \
    novnc \
    websockify \
    x11-utils \
    ca-certificates \
    fonts-liberation \
    fonts-noto-color-emoji \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/anthares-brouser
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py novnc_gateway.py profile_store.py start.sh qa40_render.py kwai_runtime_probe.py pid1.sh ./
RUN chmod +x /opt/anthares-brouser/start.sh /opt/anthares-brouser/qa40_render.py /opt/anthares-brouser/kwai_runtime_probe.py /opt/anthares-brouser/pid1.sh && mkdir -p /data/chrome-profile

EXPOSE 8080
VOLUME ["/data"]

# Keep graceful profile backup, but never let a stuck Chromium child block a
# Render replacement indefinitely. pid1.sh caps shutdown at 20 seconds.
CMD ["/opt/anthares-brouser/pid1.sh"]
