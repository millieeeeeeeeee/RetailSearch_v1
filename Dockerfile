FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8080

# Gunicorn 啟動 Flask app
CMD ["gunicorn", "-b", "0.0.0.0:8080", "main:app", "--workers", "1", "--threads", "8"]
