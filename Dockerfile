FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY www.youtube.com_cookies.txt .
COPY templates/ templates/
COPY static/ static/

RUN mkdir -p /downloads

EXPOSE 5000

CMD ["python", "app.py"]
