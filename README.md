<div align="center">

# 🛡️ DeepShield

**Explainable AI-Powered Multimodal Misinformation Detection Platform**

*Detect deepfakes, fake news, and manipulated media with transparency-backed AI verdicts*

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18.3-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![PyTorch](https://img.shields.io/badge/PyTorch-2.4-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)
![HuggingFace](https://img.shields.io/badge/HuggingFace-Transformers-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black)
![Vite](https://img.shields.io/badge/Vite-5.4-646CFF?style=for-the-badge&logo=vite&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

</div>

---

## 📋 Overview

**DeepShield** is a full-stack web platform that accepts **images, videos, news text, and social media screenshots** — then returns transparency-backed authenticity verdicts with evidence signals, manipulation heatmaps, confidence scores, trusted-source cross-referencing, and downloadable PDF reports.

Built with a **decoupled architecture** (React frontend + FastAPI backend + dedicated AI inference layer), DeepShield combines state-of-the-art Vision Transformers (ViT), BERT NLP classifiers, and Explainable AI (Grad-CAM) to create an end-to-end misinformation detection pipeline that doesn't just give a verdict — it **shows you why**.

> 🎓 *Designed for both real-world deployment and academic submission (college minor project with viva-ready documentation).*

---

## 🚀 Key Capabilities

🔍 **Image Deepfake Detection** using Vision Transformer (ViT) with Grad-CAM heatmap explainability.

🎬 **Video Deepfake Detection** with keyframe extraction, per-frame analysis, and temporal consistency tracking.

📰 **Fake News Text Detection** using BERT classifier with sensationalism scoring and manipulation indicators.

📱 **Screenshot Verification** via EasyOCR text extraction, layout anomaly detection, and credibility analysis.

🗺️ **Manipulation Heatmaps** — GradCAM-powered visual explanations highlighting exactly where manipulation was detected.

🔗 **Trusted Source Cross-Referencing** — India-focused evidence panel matching claims against PIB, The Hindu, Reuters India, Alt News, and more.

📊 **Authenticity Score System** — 0-100 confidence scale with color-coded trust interpretation (Red → Amber → Green).

📃 **PDF Report Generation** — Downloadable professional verification reports via WeasyPrint with full evidence breakdown.

👤 **User Accounts & History** — Optional JWT-authenticated accounts with saved analysis history and verification archive.

🧠 **Processing Pipeline Visualization** — Animated real-time inference stages for full transparency.

---

## 🏗️ System Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                      CLIENT (Browser)                        │
│   React 18 + Vite 5 SPA (Material Design, CSS Modules)      │
│   ┌──────────┐ ┌──────────┐ ┌─────────┐ ┌──────────────┐   │
│   │  Upload   │ │ Pipeline │ │ Results │ │   Reports    │   │
│   │  Module   │ │Animation │ │Dashboard│ │  & History   │   │
│   └──────────┘ └──────────┘ └─────────┘ └──────────────┘   │
│                        │ HTTPS / REST                        │
└────────────────────────┼─────────────────────────────────────┘
                         │
┌────────────────────────┼─────────────────────────────────────┐
│                 BACKEND (FastAPI Server)                      │
│  ┌─────────────────────┼─────────────────────────────────┐   │
│  │              API Gateway Layer                         │   │
│  │  /upload   /analyze   /report   /auth   /history      │   │
│  ├───────────────────────────────────────────────────────┤   │
│  │              Service Layer                             │   │
│  │  ImageSvc  VideoSvc  TextSvc  ScreenshotSvc  ReportSvc│   │
│  ├───────────────────────────────────────────────────────┤   │
│  │            AI Inference Layer                          │   │
│  │  ViT Deepfake │ BERT NLP │ EasyOCR │ Grad-CAM │ OpenCV   │
│  ├───────────────────────────────────────────────────────┤   │
│  │           Data / Storage Layer                         │   │
│  │  SQLite (Users/History)  │  Temp Storage  │  PDF Cache │   │
│  └───────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Technology Stack

### Backend

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)
![Uvicorn](https://img.shields.io/badge/Uvicorn-0.32-2C2C2C?style=flat-square&logo=uvicorn&logoColor=white)
![Pydantic](https://img.shields.io/badge/Pydantic-2.9-E92063?style=flat-square&logo=pydantic&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=flat-square&logo=sqlalchemy&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?style=flat-square&logo=sqlite&logoColor=white)
![JWT](https://img.shields.io/badge/JWT-Auth-000000?style=flat-square&logo=jsonwebtokens&logoColor=white)

### Machine Learning & AI

![PyTorch](https://img.shields.io/badge/PyTorch-2.4-EE4C2C?style=flat-square&logo=pytorch&logoColor=white)
![HuggingFace](https://img.shields.io/badge/🤗_Transformers-4.44-FFD21E?style=flat-square)
![OpenCV](https://img.shields.io/badge/OpenCV-4.10-5C3EE8?style=flat-square&logo=opencv&logoColor=white)
![GradCAM](https://img.shields.io/badge/Grad--CAM-1.5-FF6F61?style=flat-square)
![EasyOCR](https://img.shields.io/badge/EasyOCR-1.7-4B8BBE?style=flat-square)
![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10-0097A7?style=flat-square&logo=google&logoColor=white)

### Frontend

![React](https://img.shields.io/badge/React-18.3-61DAFB?style=flat-square&logo=react&logoColor=black)
![Vite](https://img.shields.io/badge/Vite-5.4-646CFF?style=flat-square&logo=vite&logoColor=white)
![React Router](https://img.shields.io/badge/React_Router-6.27-CA4245?style=flat-square&logo=reactrouter&logoColor=white)
![Framer Motion](https://img.shields.io/badge/Framer_Motion-11-0055FF?style=flat-square&logo=framer&logoColor=white)
![Recharts](https://img.shields.io/badge/Recharts-2.13-22B5BF?style=flat-square)
![Axios](https://img.shields.io/badge/Axios-1.7-5A29E4?style=flat-square&logo=axios&logoColor=white)
![CSS Modules](https://img.shields.io/badge/CSS_Modules-Scoped-1572B6?style=flat-square&logo=css3&logoColor=white)

### Utilities

![WeasyPrint](https://img.shields.io/badge/WeasyPrint-PDF_Gen-3E4348?style=flat-square)
![Jinja2](https://img.shields.io/badge/Jinja2-Templates-B41717?style=flat-square&logo=jinja&logoColor=white)
![Loguru](https://img.shields.io/badge/Loguru-Logging-00C7B7?style=flat-square)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker&logoColor=white)

---

## 🤖 AI Models & Inference Pipeline

| Model | Architecture | Task | Source |
|:------|:-------------|:-----|:-------|
| **Deep-Fake-Detector-v2** | Vision Transformer (ViT) | Image deepfake classification | [`prithivMLmods/Deep-Fake-Detector-v2-Model`](https://huggingface.co/prithivMLmods/Deep-Fake-Detector-v2-Model) |
| **Fake News Detection** | BERT-base | Text credibility classification | [`GonzaloA/fake-news-detection-small`](https://huggingface.co/GonzaloA/fake-news-detection-small) |
| **EasyOCR Engine** | CRAFT + CRNN | Screenshot text extraction | [EasyOCR](https://github.com/JaidedAI/EasyOCR) (en + hi) |
| **Grad-CAM** | Class Activation Mapping | Heatmap explainability | [pytorch-grad-cam](https://github.com/jacobgil/pytorch-grad-cam) |
| **MediaPipe Face Mesh** | BlazeFace + FaceMesh | Facial landmark tracking | [MediaPipe](https://developers.google.com/mediapipe) |

### 🔄 Detection Pipelines

**Image Pipeline:**
```
Upload → Validate → Preprocess (224×224) → ViT Classification → Grad-CAM Heatmap → Artifact Detection → Score & Verdict
```

**Video Pipeline:**
```
Upload → Validate → Extract Keyframes (10-30) → Per-Frame ViT Analysis → Landmark Stability Check → Aggregate Signals → Timeline + Verdict
```

**Text Pipeline:**
```
Paste Article → Validate → Preprocess → BERT Classification → Sensationalism Analysis → Manipulation Indicator Scan → Keywords → Score & Verdict
```

**Screenshot Pipeline:**
```
Upload → Validate → EasyOCR Extraction → BERT Credibility Scan → Layout Anomaly Detection → Suspicious Phrase Mapping → Score & Verdict
```

---

## 📊 Datasets Used

| Dataset | Source | Type | Size | Usage |
|:--------|:-------|:-----|:-----|:------|
| **FaceForensics++ (C23)** | [Kaggle](https://www.kaggle.com/datasets/xdxd003/ff-c23) | Video (6 manipulation methods) | ~17 GB / 7,000 videos | Video pipeline benchmarking |
| **DeepFakeFace (DFF)** | [HuggingFace](https://huggingface.co/datasets/OpenRL/DeepFakeFace) | Image (diffusion-generated) | Varies | Robustness testing vs modern fakes |

**FaceForensics++** includes 6 manipulation techniques: Deepfakes, Face2Face, FaceSwap, FaceShifter, NeuralTextures, and DeepFakeDetection — covering both GAN-based and graphics-based face manipulation.

**DeepFakeFace** focuses on **diffusion-model-generated** fakes (Stable Diffusion V1.5, SD Inpainting, InsightFace) — testing robustness against next-generation deepfakes that traditional detectors struggle with.

---

## 📁 Project Structure

```
DeepShield/
├── 📄 README.md                    # This file
├── 📄 BUILD_PLAN.md                # 20-section implementation plan
├── 📄 prd.md                       # Product Requirements Document
├── 📄 .env.example                 # Environment variable template
├── 📄 .gitignore
│
├── 🐍 backend/                     # Python FastAPI backend
│   ├── main.py                     # App entry point + lifespan
│   ├── config.py                   # Pydantic settings from .env
│   ├── requirements.txt            # Python dependencies
│   │
│   ├── api/                        # Route layer
│   │   ├── router.py               # Main API router aggregator
│   │   └── v1/
│   │       ├── analyze.py          # /analyze endpoints (all media types)
│   │       ├── report.py           # /report endpoints (generate + download)
│   │       ├── auth.py             # /auth endpoints (register, login)
│   │       ├── history.py          # /history endpoints (list, detail)
│   │       └── health.py           # /health endpoint
│   │
│   ├── models/                     # AI model loading & inference
│   │   ├── model_loader.py         # Singleton loader (ViT, BERT, OCR, Face)
│   │   ├── image_detector.py       # ViT deepfake classifier
│   │   ├── text_classifier.py      # BERT fake news classifier
│   │   ├── heatmap_generator.py    # Grad-CAM heatmap generation
│   │   ├── ocr_engine.py           # EasyOCR wrapper
│   │   └── face_detector.py        # MediaPipe face detection
│   │
│   ├── services/                   # Business logic layer
│   │   ├── image_service.py        # Image deepfake orchestration
│   │   ├── video_service.py        # Video frame-level analysis
│   │   ├── text_service.py         # Fake news text analysis
│   │   ├── screenshot_service.py   # Screenshot OCR + credibility
│   │   ├── source_service.py       # Trusted source verification
│   │   ├── report_service.py       # PDF report generation
│   │   └── auth_service.py         # Authentication logic
│   │
│   ├── schemas/                    # Pydantic request/response models
│   ├── db/                         # SQLAlchemy ORM + SQLite
│   ├── utils/                      # File handling, scoring, preprocessing
│   ├── templates/                  # Jinja2 report templates
│   └── tests/                      # pytest test suite
│
├── ⚛️ frontend/                    # React + Vite SPA
│   ├── index.html                  # SPA entry point
│   ├── vite.config.js              # Vite config + API proxy
│   ├── package.json
│   │
│   └── src/
│       ├── App.jsx                 # Root component + router
│       ├── index.css               # Design system tokens
│       │
│       ├── components/
│       │   ├── layout/             # Navbar, Footer, PageContainer
│       │   ├── upload/             # UploadZone, MediaTypeSelector
│       │   ├── pipeline/           # PipelineVisualizer (animated stages)
│       │   ├── results/            # VerdictCard, ScoreMeter, HeatmapOverlay
│       │   ├── sources/            # SourcePanel, ContradictionPanel
│       │   ├── report/             # ReportDownload
│       │   ├── auth/               # LoginForm, RegisterForm
│       │   └── common/             # Button, Card, Modal, Tooltip
│       │
│       ├── pages/                  # Route pages
│       │   ├── HomePage.jsx        # Landing + upload entry
│       │   ├── AnalyzePage.jsx     # Upload → Pipeline → Results
│       │   ├── ResultsPage.jsx     # Full results dashboard
│       │   ├── HistoryPage.jsx     # Past analyses (authenticated)
│       │   ├── LoginPage.jsx       # Login
│       │   ├── RegisterPage.jsx    # Register
│       │   ├── AboutPage.jsx       # Project info & methodology
│       │   └── NotFoundPage.jsx    # 404
│       │
│       ├── hooks/                  # useAnalysis, useAuth, useFileUpload
│       ├── services/               # Axios API client layer
│       ├── context/                # AuthContext (JWT provider)
│       └── utils/                  # Constants, validators, formatters
│
└── 📚 docs/                        # Documentation
    ├── API_REFERENCE.md
    ├── MODEL_CARDS.md
    └── SETUP_GUIDE.md
```

---

## ⚙️ Local Installation

### Prerequisites

- **Python** 3.10+ ([Download](https://www.python.org/downloads/))
- **Node.js** 18+ ([Download](https://nodejs.org/))
- **Git** ([Download](https://git-scm.com/))
- **4 GB+ RAM** (for AI model preloading)

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/Spyderzz/DeepShield.git
cd DeepShield
```

### 2️⃣ Backend Setup

```bash
# Create and activate virtual environment
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

# Install PyTorch (CPU version)
pip install torch==2.4.1 torchvision==0.19.1 --index-url https://download.pytorch.org/whl/cpu

# Install remaining dependencies
pip install -r requirements.txt
```

### 3️⃣ Environment Configuration

```bash
# From the project root
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# Server
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=true
CORS_ORIGINS=["http://localhost:5173"]

# Database
DATABASE_URL=sqlite:///./deepshield.db

# AI Models
IMAGE_MODEL_ID=prithivMLmods/Deep-Fake-Detector-v2-Model
TEXT_MODEL_ID=GonzaloA/fake-news-detection-small
DEVICE=cpu

# News API (optional — get free key at newsdata.io)
NEWS_API_KEY=your_api_key_here

# Auth
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440
```

### 4️⃣ Start the Backend

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

> 📍 Backend runs at `http://localhost:8000`
> 📍 API docs at `http://localhost:8000/docs` (Swagger UI)

### 5️⃣ Frontend Setup

```bash
# Open a new terminal
cd frontend
npm install
npm run dev
```

> 📍 Frontend runs at `http://localhost:5173`
> 📍 API calls auto-proxy to backend via Vite config

### 6️⃣ Verify Installation

```bash
# Health check
curl http://localhost:8000/api/v1/health
# Expected: {"status": "healthy", ...}
```

Open `http://localhost:5173` in your browser — you should see the DeepShield landing page.

---

## 🌐 API Endpoints

| Method | Endpoint | Description |
|:-------|:---------|:------------|
| `GET` | `/api/v1/health` | Health check and model status |
| `POST` | `/api/v1/analyze/image` | Analyze image for deepfake manipulation |
| `POST` | `/api/v1/analyze/video` | Analyze video with keyframe extraction |
| `POST` | `/api/v1/analyze/text` | Analyze news article text for fake news |
| `POST` | `/api/v1/analyze/screenshot` | Analyze social media screenshot via OCR |
| `POST` | `/api/v1/report/generate` | Generate PDF verification report |
| `GET` | `/api/v1/report/{id}/download` | Download generated PDF report |
| `POST` | `/api/v1/auth/register` | Register new user account |
| `POST` | `/api/v1/auth/login` | Login and receive JWT token |
| `GET` | `/api/v1/history` | Get analysis history (authenticated) |

Full API documentation available at `/docs` (Swagger UI) when backend is running.

---

## 📈 Authenticity Score System

DeepShield uses a **0–100 confidence scale** with color-coded trust interpretation:

| Score Range | Verdict | Color | Meaning |
|:------------|:--------|:------|:--------|
| 81–100 | ✅ Very Likely Real | 🟢 Green | High confidence authentic |
| 61–80 | ✅ Likely Real | 🟢 Light Green | Probably authentic |
| 41–60 | ⚠️ Possibly Manipulated | 🟡 Amber | Uncertain — cross-check recommended |
| 21–40 | ❌ Likely Fake | 🟠 Orange | Probable manipulation detected |
| 0–20 | ❌ Very Likely Fake | 🔴 Red | Strong manipulation signals |

---

## 🔗 Trusted Source Evidence Panel

India-focused cross-referencing against verified news sources:

| Source | Type |
|:-------|:-----|
| 🏛️ PIB India | Government press bureau |
| 📰 The Hindu | National newspaper |
| 📰 Indian Express | National newspaper |
| 🌍 Reuters India | International wire service |
| 🌍 BBC India | International broadcaster |
| 📡 ANI News | Wire service |
| 📺 NDTV | Television network |
| 🔍 Alt News | Fact-checking organization |
| 🔍 Boom Live | Fact-checking organization |
| 🔍 Factly | Fact-checking organization |

---

## 🛡️ Security Features

- 🔒 **No Permanent Media Storage** — Uploaded files auto-deleted after analysis (configurable retention: default 5 min)
- 🔑 **JWT Authentication** — Stateless token-based auth with bcrypt password hashing
- ✅ **Input Validation** — MIME type + magic byte + file size validation on all uploads
- 🛡️ **CORS Protection** — Strict origin whitelisting
- 🧹 **Temp File Cleanup** — Automated cleanup of expired temporary files
- 📝 **Structured Logging** — Loguru-based audit trail

---

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend tests (when configured)
cd frontend
npm test
```

### Benchmark Datasets

Run model benchmarks against the included test datasets:

```bash
# Benchmark against FaceForensics++ C23 (requires dataset download)
python scripts/benchmark_ff.py

# Benchmark against DeepFakeFace diffusion-generated images
python scripts/benchmark_dff.py
```

---

## 📄 Documentation

| Document | Description |
|:---------|:------------|
| [`BUILD_PLAN.md`](BUILD_PLAN.md) | 20-section implementation plan with full architecture specs |
| [`prd.md`](prd.md) | Product Requirements Document |
| [`docs/API_REFERENCE.md`](docs/API_REFERENCE.md) | Complete API endpoint documentation |
| [`docs/MODEL_CARDS.md`](docs/MODEL_CARDS.md) | AI model details, citations, and performance metrics |
| [`docs/SETUP_GUIDE.md`](docs/SETUP_GUIDE.md) | Detailed deployment instructions |

---

## 🗺️ Development Roadmap

| Phase | Description | Status |
|:------|:------------|:-------|
| Phase 0 | Project Setup — FastAPI + React + Design System | ✅ Complete |
| Phase 1 | Image Detection Pipeline — ViT + Grad-CAM + API | 🔄 In Progress |
| Phase 2 | Video Detection Pipeline — Keyframe + Timeline | ⏳ Planned |
| Phase 3 | Text Classification Pipeline — BERT + Sensationalism | ⏳ Planned |
| Phase 4 | Screenshot Pipeline — EasyOCR + Layout Analysis | ⏳ Planned |
| Phase 5 | Trusted Source Verification — News API + Evidence | ⏳ Planned |
| Phase 6 | Processing Pipeline Animation | ⏳ Planned |
| Phase 7 | PDF Report Generation — WeasyPrint + Jinja2 | ⏳ Planned |
| Phase 8 | Authentication & History — JWT + User Accounts | ⏳ Planned |
| Phase 9 | Polish & Integration — Responsive + E2E Testing | ⏳ Planned |
| Phase 10 | Documentation & Submission | ⏳ Planned |

---

## 📚 References & Citations

```bibtex
@inproceedings{roessler2019faceforensicspp,
    title={FaceForensics++: Learning to Detect Manipulated Facial Images},
    author={Roessler, Andreas and Cozzolino, Davide and Verdoliva, Luisa
            and Riess, Christian and Thies, Justus and Niessner, Matthias},
    booktitle={International Conference on Computer Vision (ICCV)},
    year={2019}
}

@misc{song2023robustness,
    title={Robustness and Generalizability of Deepfake Detection:
           A Study with Diffusion Models},
    author={Haixu Song and Shiyu Huang and Yinpeng Dong and Wei-Wei Tu},
    year={2023},
    eprint={2309.02218},
    archivePrefix={arXiv},
    primaryClass={cs.CV}
}
```

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 👤 Author

[![GitHub](https://img.shields.io/badge/GitHub-Spyderzz-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/Spyderzz)

---

<div align="center">

⭐ **If this project helps you, consider giving it a star!** ⭐

*Built with ❤️ using AI/ML for a safer digital world*

</div>
