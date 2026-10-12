FROM mcr.microsoft.com/playwright/python:v1.56.0-noble
WORKDIR /app
COPY bench/render_server.py /app/render_server.py
RUN pip install --no-cache-dir playwright==1.56.0
CMD ["python","/app/render_server.py"]
