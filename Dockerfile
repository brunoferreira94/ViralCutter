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
    locales \
    && rm -rf /var/lib/apt/lists/*

# Configure and generate pt_BR locale so processes inside the container
# default to pt_BR.UTF-8 (helps tools like yt-dlp choose pt-BR subtitles)
RUN sed -i 's/# pt_BR.UTF-8 UTF-8/pt_BR.UTF-8 UTF-8/' /etc/locale.gen || true \
    && locale-gen pt_BR.UTF-8 \
    && update-locale LANG=pt_BR.UTF-8

COPY requirements.txt requirements.core.txt requirements.cpu.txt ./

RUN python -m pip install --upgrade pip setuptools wheel && \
    python -m pip install -r requirements.cpu.txt

COPY . .

EXPOSE 7860

CMD ["python", "webui/app.py"]
ENV LANG=pt_BR.UTF-8 \
    LC_ALL=pt_BR.UTF-8 \
    LANGUAGE=pt_BR:pt
