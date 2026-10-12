FROM python:3.12-slim
WORKDIR /app
RUN apt-get update -qq && apt-get install -y -qq ffmpeg && rm -rf /var/lib/apt/lists/*
COPY . /app
RUN pip install --no-cache-dir 'yt-dlp[default]' yt-dlp-ejs faster-whisper
ENV PYTHONUNBUFFERED=1 PYTHONUTF8=1 X_SOURCE_CHANNEL=https://www.youtube.com/@UniversoAnthares/streams X_SCAN_START=600 X_SCAN_SECONDS=300 X_MIN_SOURCE_SECONDS=1200 X_WHISPER_MODEL=base
CMD ["python","render-x-real/server.py"]
