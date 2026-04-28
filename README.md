---
title: DeepShield
emoji: 🛡️
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
---

<div align="center">

# 🛡️ DeepShield

**Explainable AI-Powered Multimodal Misinformation Detection Platform**

*Detect deepfakes, fake news, and manipulated media with transparency-backed AI verdicts*

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18.3-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![PyTorch](https://img.shields.io/badge/PyTorch-2.4-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini-Flash_3.1-4A90E2?style=for-the-badge&logo=google&logoColor=white)
![Neon](https://img.shields.io/badge/Neon-Serverless_Postgres-00E599?style=for-the-badge&logo=postgresql&logoColor=black)
![Vite](https://img.shields.io/badge/Vite-5.4-646CFF?style=for-the-badge&logo=vite&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

</div>

---

## 📋 Overview

**DeepShield** is a full-stack web platform that accepts **images, videos, news text, and social media screenshots** — then returns transparency-backed authenticity verdicts. Moving beyond simple probability scores, DeepShield provides **human-readable LLM explanations, granular component breakdowns, temporal video analysis, and trusted-source cross-referencing**. 

Built with a **decoupled architecture** (React frontend + FastAPI backend + dedicated AI inference layer), DeepShield combines state-of-the-art Vision Transformers (ViT), BERT NLP classifiers, and Gemini-powered Explainable AI to create an end-to-end misinformation detection pipeline that doesn't just give a verdict — it **shows you why**. 

The platform features a **premium glassmorphism UI** with Apple-style 3D processing animations, optimized for an engaging user experience, and is robustly backed by a **Neon Serverless Postgres** database for deployment on **Hugging Face Spaces**.

> 🎓 *Designed for both real-world deployment and academic submission (college minor project with viva-ready documentation).*

---

## 🚀 Key Capabilities

🔍 **Image Deepfake Detection** — Fine-tuned Vision Transformer (ViT) trained on FaceForensics++ combined with Grad-CAM++ heatmap explainability and Error Level Analysis (ELA).

🎬 **Video Deepfake Detection** — Keyframe extraction, per-frame ViT analysis, optical flow temporal consistency tracking, and **audio deepfake detection** (WavLM/wav2vec2) with async job processing.

🎙️ **Standalone Audio Deepfake Detection** — Acoustic feature extraction, WavLM/wav2vec2 voice ML models, and signal heuristics (spectral variance, RMS consistency) for independent audio analysis.

📰 **Fake News Text Detection** — Multilingual BERT classifier (English & Hindi) with sensationalism scoring, NER-based keyword extraction, and truth-override via cosine similarity.

📱 **Screenshot Verification** — EasyOCR text extraction, layout anomaly detection, and credibility analysis.

🧠 **Gemini-Powered Explainability** — Integrates Gemini Flash for LLM plain-English narrative summaries and granular VLM component-score breakdowns (facial symmetry, skin texture, lighting, etc.).

🗺️ **Manipulation Heatmaps & Metadata** — Grad-CAM++ powered visual explanations, ELA blending, and automated EXIF metadata anomaly extraction.

🔗 **Trusted Source Cross-Referencing** — India-focused evidence panel matching claims against PIB, The Hindu, Reuters India, Alt News, and more.

📊 **Authenticity Score System** — 0-100 confidence scale with color-coded trust interpretation (Red → Amber → Green).

📃 **PDF Report Generation** — Downloadable professional verification reports via WeasyPrint with full evidence breakdown and embedded metadata.

👤 **User Accounts & History** — JWT-authenticated accounts backed by Neon Postgres with saved analysis history and verification archive.

✨ **Premium Interface** — Mesh gradients, glassmorphism panels, and 3D staggered LayerStack animations for real-time inference visualization.

---

## 🏗️ System Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                      CLIENT (Browser)                        │
│   React 18 + Vite 5 SPA (Glassmorphism, 3D Animations)       │
│   ┌──────────┐ ┌──────────┐ ┌─────────┐ ┌──────────────┐   │
│   │  Upload   │ │ Pipeline │ │ Results │ │   Reports    │   │
│   │  Module   │ │Animation │ │Dashboard│ │  & History   │   │
│   └──────────┘ └──────────┘ └─────────┘ └──────────────┘   │
│                        │ HTTPS / REST                        │
└────────────────────────┼─────────────────────────────────────┘
                         │
┌────────────────────────┼─────────────────────────────────────┐
│                 BACKEND (FastAPI Server)                     │
│  ┌─────────────────────┼─────────────────────────────────┐   │
│  │              API Gateway Layer                        │   │
│  │  /upload   /analyze   /report   /auth   /history   /stats/recent │   │
│  ├───────────────────────────────────────────────────────┤   │
│  │              Service Layer                            │   │
│  │  ImageSvc VideoSvc TextSvc AudioSvc LLMSvc ReportSvc  │   │
│  ├───────────────────────────────────────────────────────┤   │
│  │            AI Inference Layer                         │   │
│  │  ViT Deepfake │ BERT NLP │ EasyOCR │ Gemini VLM/LLM   │   │
│  ├───────────────────────────────────────────────────────┤   │
│  │           Data / Storage Layer                        │   │
│  │  Neon Postgres (Users/History) │ SHA-256 Object Cache │   │
│  └───────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Technology Stack

### Backend
- **Framework:** FastAPI, Uvicorn, Pydantic
- **Database:** SQLAlchemy, Neon Serverless Postgres, Alembic
- **Auth & Security:** JWT (JSON Web Tokens), bcrypt, slowapi (Rate Limiting)

### Machine Learning & AI
- **Core ML:** PyTorch, Hugging Face Transformers
- **Computer Vision:** OpenCV, MediaPipe, Grad-CAM++, EasyOCR
- **Generative AI:** Google Gemini API (LLM Summaries & VLM Breakdowns)
- **Audio Analysis:** librosa, WavLM / wav2vec2

### Frontend
- **Core:** React 18, Vite 5, React Router 6
- **Styling:** CSS Modules, Tailwind-inspired tokens, Glassmorphism
- **Animations:** Framer Motion (3D LayerStacks, Liquid transitions)
- **Data Viz:** Recharts

### Utilities
- **PDF Generation:** WeasyPrint, Jinja2 Templates
- **Logging:** Loguru
- **Testing:** Pytest, Vitest

---

## 🤖 AI Models & Inference Pipeline

| Model | Architecture | Task | Source |
|:------|:-------------|:-----|:-------|
| **DeepShield-ViT** | Vision Transformer | Image deepfake classification | Fine-tuned on FaceForensics++ |
| **Fake News Multilingual**| XLM-RoBERTa / BERT | Text credibility classification | Custom / HuggingFace |
| **Audio Deepfake** | WavLM / wav2vec2 | Audio authenticity classification| ASVspoof trained |
| **Gemini Flash** | LLM / VLM | Explanations & Granular scoring | Google AI Studio |
| **EasyOCR Engine** | CRAFT + CRNN | Screenshot text extraction | EasyOCR (en + hi) |

### 🔄 Detection Pipelines

**Image Pipeline:**
```
Upload → SHA-256 Cache Check → ViT Classification → Grad-CAM++ & ELA → EXIF Extraction → Gemini VLM Breakdown & Summary → Verdict
```

**Video Pipeline:**
```
Upload → Extract Keyframes → Per-Frame ViT → Temporal Optical Flow Check → Audio Extraction & Detection → Aggregate Signals → Gemini Summary → Verdict
```

**Text Pipeline:**
```
Paste Article → NER Keyword Extraction → BERT Classification → Truth-Override (Trusted Sources Cosine Sim) → Gemini Summary → Verdict
```

**Screenshot Pipeline:**
```
Upload → EasyOCR Extraction → BERT Credibility Scan → Layout Anomaly Detection → Source Cross-Reference → Verdict
```

**Audio Pipeline:**
```
Upload → Preprocess Audio → Acoustic Feature Extraction → Voice ML Classification → Signal Heuristics → Gemini Summary → Verdict
```

---

## ⚙️ Local Installation & Cloud Deployment

DeepShield is built to run locally for development and is configured for deployment on **Hugging Face Spaces** connected to **Neon Postgres**.

### Prerequisites
- **Python** 3.10+
- **Node.js** 18+
- **Gemini API Key** (from Google AI Studio)
- **Neon Database Connection String** (for Postgres)

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/Spyderzz/DeepShield.git
cd DeepShield
```

### 2️⃣ Backend Setup
```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# Install dependencies (CPU PyTorch recommended for local)
pip install torch==2.4.1 torchvision==0.19.1 --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
```

### 3️⃣ Environment Configuration
Create a `.env` file in the root directory:
```env
# Server
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=true
CORS_ORIGINS=["http://localhost:5173", "https://your-huggingface-space.hf.space"]

# Database (Neon Postgres)
DATABASE_URL=postgresql://user:pass@ep-cool-name.neon.tech/deepshield?sslmode=require

# AI Models & Explainability
LLM_PROVIDER=gemini
LLM_API_KEY=your_gemini_api_key_here
LLM_MODEL=gemini-1.5-flash

# Auth
JWT_SECRET_KEY=generate_a_secure_random_key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440
```

### 4️⃣ Start the Backend
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
> API Docs available at `http://localhost:8000/docs`

### 5️⃣ Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
> Open `http://localhost:5173` to view the application.

---

## 📈 Deepfake Probability & VLM Breakdown

DeepShield uses a standardized **Deepfake Probability score** (computed as `100 - Authenticity Score`) alongside a **0–100 confidence scale**, reinforced by a Gemini VLM component breakdown.

| Score Range | Verdict | Color | Meaning |
|:------------|:--------|:------|:--------|
| 81–100 | ✅ Very Likely Real | 🟢 Green | High confidence authentic |
| 61–80 | ✅ Likely Real | 🟢 Light Green | Probably authentic |
| 41–60 | ⚠️ Possibly Manipulated | 🟡 Amber | Uncertain — cross-check recommended |
| 21–40 | ❌ Likely Fake | 🟠 Orange | Probable manipulation detected |
| 0–20 | ❌ Very Likely Fake | 🔴 Red | Strong manipulation signals |

The **Detailed Breakdown Card** evaluates sub-components (Facial Symmetry, Lighting Consistency, Background Coherence, etc.) to explicitly point out artifacts.

---

## 🛡️ Security Features
- **Stateless Analysis:** Uploaded files cached via SHA-256 for fast retrieval but safely stored without permanent coupling unless explicitly saved to history.
- **Rate Limiting:** IP and User-ID based `slowapi` limiters across endpoints to protect system resources and prevent API abuse.
- **Route Guards & Report Security:** Authenticated `/history` and `/stats/recent` endpoints, with mandatory UUID token validation on `/report` access to prevent unauthorized record enumeration.
- **Neon Cloud DB:** Production-ready PostgreSQL persistence.

---

## 📄 Documentation

| Document | Description |
|:---------|:------------|
| [`BUILD_PLAN.md`](BUILD_PLAN.md) | Original MVP implementation plan |
| [`BUILD_PLAN2.md`](BUILD_PLAN2.md) | Detailed Phase 11-22 plan (Hardening & UX Overhaul) |
| [`ISSUES.md`](ISSUES.md) | Bug tracker and technical debt documentation |
| [`FRONTEND_REDESIGN.md`](FRONTEND_REDESIGN.md) | Specs for the glassmorphism and 3D LayerStack overhaul |

---

## 📄 License
This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 👤 Author
[![GitHub](https://img.shields.io/badge/GitHub-Spyderzz-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/Spyderzz)

<div align="center">
⭐ **If this project helps you, consider giving it a star!** ⭐

*Built with ❤️ using AI/ML for a safer digital world*
</div>
