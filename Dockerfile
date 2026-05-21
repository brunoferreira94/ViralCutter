FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    build-essential \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements.core.txt requirements.cpu.txt ./

RUN python -m pip install --upgrade pip setuptools wheel && \
    python -m pip install -r requirements.cpu.txt

COPY . .

EXPOSE 7860

CMD ["python", "webui/app.py"]
