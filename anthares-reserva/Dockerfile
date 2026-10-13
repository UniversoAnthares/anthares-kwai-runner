FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /opt/anthares-reserva
COPY anthares-reserva/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY anthares-reserva/provider_router.py ./provider_router.py
RUN mkdir -p /data
ENV PORT=8080 ANTHARES_RESERVA_DB=/data/anthares-reserva.sqlite3
EXPOSE 8080
HEALTHCHECK --interval=20s --timeout=3s --start-period=5s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health',timeout=2)" || exit 1
CMD ["sh","-c","uvicorn provider_router:app --host 0.0.0.0 --port ${PORT:-8080} --no-access-log"]
