FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_PORT=8501 \
    TORCH_HOME=/app/temp/cache/torch \
    XDG_CACHE_HOME=/app/temp/cache \
    HF_HOME=/app/temp/cache/huggingface \
    HUGGINGFACE_HUB_CACHE=/app/temp/cache/huggingface/hub \
    TRANSFORMERS_CACHE=/app/temp/cache/huggingface/transformers \
    PYTHONPYCACHEPREFIX=/app/temp/cache/pycache

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    ffmpeg \
    git \
    libgomp1 \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-docker.txt .
RUN python -m pip install --upgrade pip setuptools wheel \
    && python -m pip install torch==2.2.2+cpu torchaudio==2.2.2+cpu --index-url https://download.pytorch.org/whl/cpu \
    && python -m pip install -r requirements-docker.txt

COPY . .

RUN python scripts/install_argos_en_hi.py

RUN mkdir -p input output temp assets \
    temp/cache/torch \
    temp/cache/huggingface \
    temp/cache/pycache \
    && chmod -R 777 input output temp assets

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://127.0.0.1:8501/_stcore/health || exit 1

CMD ["python", "-m", "streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
