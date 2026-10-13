FROM python:3.13-slim
WORKDIR /app
COPY anthares-control-plane/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY anthares-control-plane/app.py ./app.py
ENV PORT=8080
EXPOSE 8080
CMD ["sh", "-c", "gunicorn --workers 2 --threads 4 --timeout 60 --bind 0.0.0.0:${PORT} app:app"]
