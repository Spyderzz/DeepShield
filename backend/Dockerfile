# Base image with Python 3.10 (Explicitly using Bookworm to avoid unstable Trixie repos)
FROM python:3.10-slim-bookworm

# Keeps Python from buffering stdout/stderr (important for HF Spaces logs)
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Tell HuggingFace where to cache downloaded models (ViT, BERT)
ENV HF_HOME=/app/.cache/huggingface

# Set working directory
WORKDIR /app

# ── System dependencies ───────────────────────────────────────────────────────
# Pinning to stable repos and adding --fix-missing for robustness
RUN apt-get update && apt-get install -y --no-install-recommends --fix-missing \
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
# Handle case where UID 1000 already exists (common in some base images)
RUN if ! id -u 1000 >/dev/null 2>&1; then \
        useradd -m -u 1000 appuser; \
    else \
        useradd -m appuser || true; \
    fi && \
    chown -R 1000:1000 /app
USER 1000

# HF Spaces requires port 7860
EXPOSE 7860

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]