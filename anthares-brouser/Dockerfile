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
COPY app.py novnc_gateway.py profile_store.py start.sh qa40_render.py kwai_runtime_probe.py pid1.sh migration_app.py migration_capsule.py migration_oidc.py migration_oidc_reserva.py ./
RUN mv /opt/anthares-brouser/app.py /opt/anthares-brouser/base_app.py \
    && mv /opt/anthares-brouser/migration_app.py /opt/anthares-brouser/app.py \
    && chmod +x /opt/anthares-brouser/start.sh /opt/anthares-brouser/qa40_render.py /opt/anthares-brouser/kwai_runtime_probe.py /opt/anthares-brouser/pid1.sh \
    && mkdir -p /data/chrome-profile

EXPOSE 8080
VOLUME ["/data"]

CMD ["/opt/anthares-brouser/pid1.sh"]
