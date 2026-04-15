# DeepShield — Setup & Deployment Guide

Step-by-step instructions to run DeepShield locally or deploy to production.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start (Development)](#quick-start-development)
- [Backend Setup (Detailed)](#backend-setup-detailed)
- [Frontend Setup (Detailed)](#frontend-setup-detailed)
- [Environment Variables](#environment-variables)
- [AI Model Downloads](#ai-model-downloads)
- [Database](#database)
- [Running in Production](#running-in-production)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

| Software | Version | Purpose |
|:---------|:--------|:--------|
| **Python** | 3.10+ (3.11 recommended) | Backend runtime |
| **Node.js** | 18+ (LTS) | Frontend build/dev |
| **npm** | 9+ | Package management |
| **Git** | 2.x | Version control |

### Optional
| Software | Purpose |
|:---------|:--------|
| **CUDA toolkit** | GPU acceleration (if you have an NVIDIA GPU) |
| **NewsData.io API key** | Trusted source cross-referencing |

---

## Quick Start (Development)

```bash
# 1. Clone the repository
git clone https://github.com/Spyderzz/DeepShield.git
cd DeepShield

# 2. Backend setup
cd backend
python -m venv .venv

# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

# Install PyTorch CPU (do this first)
pip install torch==2.4.1 torchvision==0.19.1 --index-url https://download.pytorch.org/whl/cpu

# Install remaining dependencies
pip install -r requirements.txt

# Create environment file
cp ../.env.example .env
# Edit .env with your settings (see Environment Variables section)

# Start backend
python main.py
# → Server running at http://localhost:8000
# → API docs at http://localhost:8000/docs

# 3. Frontend setup (new terminal)
cd frontend
npm install
npm run dev
# → App running at http://localhost:5173
```

> **First run:** The AI models (~1.5 GB) will be downloaded automatically on first API call.
> Subsequent runs use the cached models from `~/.cache/huggingface/`.

---

## Backend Setup (Detailed)

### Step 1: Create Virtual Environment

```bash
cd backend
python -m venv .venv

# Activate:
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Windows CMD:
.venv\Scripts\activate.bat
# macOS/Linux:
source .venv/bin/activate
```

### Step 2: Install PyTorch (CPU)

PyTorch must be installed from the CPU index **before** `requirements.txt` to avoid downloading the 2GB CUDA version:

```bash
pip install torch==2.4.1 torchvision==0.19.1 --index-url https://download.pytorch.org/whl/cpu
```

**For GPU (NVIDIA CUDA 12.1):**
```bash
pip install torch==2.4.1 torchvision==0.19.1 --index-url https://download.pytorch.org/whl/cu121
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

**Full dependency list:**

| Package | Version | Purpose |
|:--------|:--------|:--------|
| fastapi | 0.115.0 | Web framework |
| uvicorn | 0.32.0 | ASGI server |
| pydantic | 2.9.2 | Data validation |
| pydantic-settings | 2.6.0 | Config from env |
| SQLAlchemy | 2.0.35 | Database ORM |
| transformers | 4.44.2 | HuggingFace models |
| torch | 2.4.1 | Deep learning runtime |
| opencv-python | 4.10.0 | Video frame extraction |
| grad-cam | 1.5.4 | Heatmap generation |
| mediapipe | 0.10.14 | Face detection |
| easyocr | 1.7.2 | OCR text extraction |
| httpx | 0.27.2 | Async HTTP (news API) |
| bcrypt | 4.2.0 | Password hashing |
| python-jose | 3.3.0 | JWT tokens |
| xhtml2pdf | 0.2.16 | PDF report generation |
| Jinja2 | 3.1.4 | PDF template rendering |
| loguru | 0.7.2 | Structured logging |

### Step 4: Configure Environment

```bash
# Copy the example file
cp ../.env.example .env

# Edit .env - at minimum, change:
# JWT_SECRET_KEY=your-random-secret-here
# NEWS_API_KEY=your-newsdata-io-key (optional)
```

### Step 5: Run the Server

```bash
python main.py
```

The server will:
1. Create the SQLite database (`deepshield.db`) if it doesn't exist
2. Preload AI models (if `PRELOAD_MODELS=true`)
3. Start the report cleanup background task
4. Listen on `http://0.0.0.0:8000`

**Interactive API docs:** `http://localhost:8000/docs` (Swagger UI)

---

## Frontend Setup (Detailed)

### Step 1: Install Dependencies

```bash
cd frontend
npm install
```

### Step 2: Run Development Server

```bash
npm run dev
```

The Vite dev server starts at `http://localhost:5173` with:
- Hot Module Replacement (HMR)
- Automatic proxy of `/api` requests to `http://localhost:8000`

### Step 3: Production Build (Optional)

```bash
npm run build
# Output: frontend/dist/
# Serve with any static file server
```

---

## Environment Variables

Create a `.env` file in the `backend/` directory:

| Variable | Default | Description |
|:---------|:--------|:------------|
| `APP_HOST` | `0.0.0.0` | Server bind address |
| `APP_PORT` | `8000` | Server port |
| `DEBUG` | `false` | Enable debug mode |
| `CORS_ORIGINS` | `["http://localhost:5173"]` | Allowed CORS origins |
| `DATABASE_URL` | `sqlite:///./deepshield.db` | Database connection string |
| `MAX_UPLOAD_SIZE_MB` | `100` | Maximum file upload size |
| `UPLOAD_DIR` | `./temp_uploads` | Temporary upload directory |
| `FILE_RETENTION_SECONDS` | `300` | Auto-delete uploaded files after (seconds) |
| `IMAGE_MODEL_ID` | `prithivMLmods/Deep-Fake-Detector-v2-Model` | HuggingFace image model |
| `TEXT_MODEL_ID` | `jy46604790/Fake-News-Bert-Detect` | HuggingFace text model |
| `DEVICE` | `cpu` | Inference device (`cpu` or `cuda`) |
| `PRELOAD_MODELS` | `true` | Preload models at startup |
| `NEWS_API_KEY` | *(empty)* | [NewsData.io](https://newsdata.io) API key |
| `NEWS_API_BASE_URL` | `https://newsdata.io/api/1/news` | News API endpoint |
| `REPORT_DIR` | `./temp_reports` | PDF report output directory |
| `REPORT_TTL_SECONDS` | `3600` | Report expiry time (seconds) |
| `JWT_SECRET_KEY` | `change-me-in-production` | **Change this!** JWT signing secret |
| `JWT_ALGORITHM` | `HS256` | JWT algorithm |
| `JWT_EXPIRATION_MINUTES` | `1440` | Token expiry (24 hours) |

---

## AI Model Downloads

Models are downloaded automatically on first use from HuggingFace Hub and cached at `~/.cache/huggingface/`.

| Model | Size | First Load |
|:------|:-----|:-----------|
| ViT Deepfake Detector | ~350 MB | ~30s (broadband) |
| BERT Fake News Classifier | ~440 MB | ~40s (broadband) |
| EasyOCR models | ~100 MB | ~15s (broadband) |
| MediaPipe FaceMesh | ~10 MB | Bundled with package |

**Total first-run download:** ~900 MB

**To pre-download models manually:**
```python
from transformers import AutoModelForImageClassification, AutoImageProcessor, pipeline

# Image model
AutoModelForImageClassification.from_pretrained("prithivMLmods/Deep-Fake-Detector-v2-Model")
AutoImageProcessor.from_pretrained("prithivMLmods/Deep-Fake-Detector-v2-Model")

# Text model
pipeline("text-classification", model="jy46604790/Fake-News-Bert-Detect")
```

---

## Database

DeepShield uses **SQLite** — zero configuration, file-based database.

- **Location:** `backend/deepshield.db` (auto-created)
- **Tables:** `users`, `analysis_records`, `reports`
- **ORM:** SQLAlchemy 2.x with declarative models in `db/models.py`

No migrations needed for initial setup. The database is created by SQLAlchemy on first run.

---

## Running in Production

### Option 1: Direct Deployment

```bash
# Backend
cd backend
pip install gunicorn
gunicorn main:app -w 1 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Frontend (build and serve static files)
cd frontend
npm run build
# Serve dist/ with nginx, caddy, or any static file server
```

> **Note:** Use `-w 1` (single worker) because ML models are loaded in-process. Multiple workers would duplicate model memory (~2GB per worker).

### Option 2: Railway / Render (Free Tier)

1. Push to GitHub
2. Connect to Railway/Render
3. Set environment variables in dashboard
4. Backend: Python buildpack, start command `python main.py`
5. Frontend: Static site, build command `npm run build`, publish directory `dist`

> **Warning:** Free tiers typically have 512MB memory limits. ML models require ~2GB. Consider paid tiers or CPU-optimized model variants.

### Nginx Reverse Proxy Example

```nginx
server {
    listen 80;
    server_name deepshield.example.com;

    # Frontend static files
    location / {
        root /var/www/deepshield/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # API proxy
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        client_max_body_size 100M;
        proxy_read_timeout 300s;  # Long timeout for video analysis
    }
}
```

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|:------|:---------|
| `torch` installs CUDA version (2GB+) | Install from CPU index first: `pip install torch --index-url https://download.pytorch.org/whl/cpu` |
| `ModuleNotFoundError: mediapipe` | Ensure `.venv` is activated; MediaPipe requires Python ≤ 3.12 |
| EasyOCR `UnicodeEncodeError` on Windows | Fixed: EasyOCR initialized with `verbose=False` |
| `bcrypt` / `passlib` AttributeError | Fixed: Using `bcrypt==4.2.0` directly instead of passlib wrapper |
| CORS errors in browser | Check `CORS_ORIGINS` in `.env` matches your frontend URL |
| `xhtml2pdf` import errors | Ensure `pip install xhtml2pdf==0.2.16` (pure Python, no system deps) |
| Model download hangs | Check internet connection; models are ~900MB total on first run |
| Video analysis timeout | Increase Axios timeout in frontend; default is 300s for video |
| `JWT_SECRET_KEY` warning | Set a strong random value in `.env` for production |
| SQLite locked error | Ensure only one backend process is running |

### Verifying Installation

```bash
# Backend health check
curl http://localhost:8000/api/v1/health
# Expected: {"status":"ok"}

# Quick image analysis test
curl -X POST http://localhost:8000/api/v1/analyze/image \
  -F "file=@test_image.jpg"
# Expected: JSON with verdict, score, heatmap

# Frontend
curl http://localhost:5173
# Expected: HTML response (React SPA)
```

### Log Files

Backend uses `loguru` for structured logging. All logs output to `stderr` by default. Model loading, analysis timing, and errors are logged with context.

```
2026-04-15 12:00:00 | INFO | Loading image model: prithivMLmods/Deep-Fake-Detector-v2-Model
2026-04-15 12:00:03 | INFO | Image model loaded
2026-04-15 12:00:05 | INFO | Saved AnalysisRecord id=1 score=49 verdict=Possibly Manipulated
```
