FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg espeak-ng && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY scripts/anthares_microcut_v2.py /app/anthares_microcut_v2.py
COPY scripts/generate_microcut_fixture.py /app/generate_microcut_fixture.py
COPY infra/x-e2e-render/app.py /app/app.py
RUN pip install --no-cache-dir "faster-whisper==1.2.1" "av==14.4.0" flask gunicorn
ENV ANTHARES_WHISPER_MODEL=small ANTHARES_PAUSE_SECONDS=0.58 ANTHARES_PAUSE_KEEP_SECONDS=0.14 ANTHARES_FILLER_MIN_SECONDS=0.30 ANTHARES_MAX_REMOVAL_RATIO=0.32 ANTHARES_MIN_FINAL_SECONDS=25 ANTHARES_MIN_REMOVED_SECONDS=0.18
CMD ["python", "-u", "/app/app.py"]
