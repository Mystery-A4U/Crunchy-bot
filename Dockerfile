FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    git \
    wget \
    ffmpeg \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY . .

RUN pip3 install --no-cache-dir -r requirements.txt

CMD ["python3", "tg.py"]
