FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TZ=Asia/Shanghai

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY wait-for-db.sh /app/wait-for-db.sh
RUN chmod +x /app/wait-for-db.sh

COPY . .

EXPOSE 8000

CMD ["/app/wait-for-db.sh", "gunicorn", "--preload", "-w", "4", "-b", "0.0.0.0:8000", "run:app"]
