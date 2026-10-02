# WhatsApp support bot - HTTP server (main_http.py)
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 \
    PORT=3000 \
    SUPPORT_DB_PATH=/data/support.db

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run as a non-root user; /data holds the database - mount a persistent volume there
RUN useradd --create-home --uid 10001 app && mkdir -p /data && chown app:app /data
USER app
VOLUME ["/data"]

EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
    CMD python -c "import os, urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"PORT\", \"3000\")}/health', timeout=4)"

CMD ["python", "main_http.py"]
