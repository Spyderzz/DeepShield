# Base image with Python 3.10
FROM python:3.10-slim

# Keeps Python from buffering stdout/stderr (important for HF Spaces logs)
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Tell HuggingFace where to cache downloaded models (ViT, BERT)
# /app/.cache persists better than the default home dir on HF Spaces
ENV HF_HOME=/app/.cache/huggingface
ENV TRANSFORMERS_CACHE=/app/.cache/huggingface

# Set working directory
WORKDIR /app

# ── System dependencies ───────────────────────────────────────────────────────
# libgl1 + libglib2.0-0  → OpenCV
# libcairo2-dev          → WeasyPrint (cairo backend)
# libpango-1.0-0 + pango-related → WeasyPrint text rendering (YOU WERE MISSING THESE)
# libgdk-pixbuf2.0-0     → WeasyPrint image support (YOU WERE MISSING THIS)
# libffi-dev             → cffi (WeasyPrint dep)
# fonts-liberation       → Fallback fonts so WeasyPrint PDFs don't break
# libgomp1               → Required by PyTorch CPU ops (YOU WERE MISSING THIS)
# ffmpeg                 → Video keyframe extraction (needed for your video pipeline)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    libcairo2-dev \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    fonts-liberation \
    fonts-dejavu-core \
    build-essential \
    pkg-config \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# ── Python dependencies ───────────────────────────────────────────────────────
COPY requirements.txt .

# Install PyTorch CPU-only FIRST (avoids pulling the massive CUDA build)
# CPU-only torch is ~250MB vs ~2.5GB for the default — critical for HF free tier
RUN pip install --no-cache-dir \
    torch==2.4.1 \
    torchvision==0.19.1 \
    --index-url https://download.pytorch.org/whl/cpu

# Install everything else
RUN pip install --no-cache-dir -r requirements.txt

# ── App code ──────────────────────────────────────────────────────────────────
COPY . .

# Create runtime directories
RUN mkdir -p /app/temp_uploads /app/.cache/huggingface

# ── Security: run as non-root (HF Spaces best practice) ──────────────────────
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# HF Spaces requires port 7860
EXPOSE 7860

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]