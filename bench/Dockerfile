FROM mcr.microsoft.com/playwright/python:v1.56.0-noble
WORKDIR /app
COPY bench/render_server.py /app/render_server.py
RUN apt-get update -qq && apt-get install -y -qq ffmpeg && rm -rf /var/lib/apt/lists/* && pip install --no-cache-dir playwright==1.56.0 yt-dlp yt-dlp-ejs
CMD ["python","/app/render_server.py"]
