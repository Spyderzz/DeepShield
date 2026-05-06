<div align="center">

# 🛡️ DeepShield

**Explainable AI-Powered Multimodal Misinformation Detection Platform**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![JavaScript](https://img.shields.io/badge/JavaScript-ES6+-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)
[![React](https://img.shields.io/badge/React-18.3-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://reactjs.org)
[![Vite](https://img.shields.io/badge/Vite-5.4-646CFF?style=for-the-badge&logo=vite&logoColor=white)](https://vitejs.dev)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.4-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)](https://pytorch.org)
[![Hugging Face](https://img.shields.io/badge/Hugging_Face-Spaces-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black)](https://huggingface.co)
[![Gemini](https://img.shields.io/badge/Google_Gemini-1.5_Flash-8E75B2?style=for-the-badge&logo=googlegemini&logoColor=white)](https://deepmind.google/technologies/gemini/)
[![Supabase](https://img.shields.io/badge/Supabase-Postgres-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)](https://supabase.com)
[![Vercel](https://img.shields.io/badge/Vercel-Frontend-000000?style=for-the-badge&logo=vercel&logoColor=white)](https://vercel.com)
[![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
[![OpenCV](https://img.shields.io/badge/OpenCV-Vision-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)](https://opencv.org)


*Detect deepfakes, fake news, and manipulated media with transparency-backed AI verdicts*

</div>

---

## 📖 Overview

**DeepShield** is a production-ready, full-stack web platform designed to combat the rising threat of synthetic media. It accepts **images, videos, news text, audio, and social media screenshots**, subjecting them to a rigorous, multi-model forensic analysis. 

Moving beyond simple "real or fake" probability scores, DeepShield provides **human-readable LLM explanations, granular component breakdowns, temporal video analysis, and trusted-source cross-referencing**. 

It is built with a highly optimized decoupled architecture combining state-of-the-art **Vision Transformers (ViT), BERT NLP classifiers, and Gemini-powered Explainable AI** to create an end-to-end misinformation detection pipeline that doesn't just give a verdict — it shows you exactly *why* in plain, jargon-free English.

---

## ✨ Features & Capabilities

### 🔍 Multimodal Deepfake Detection
* **Image Forensics:** Utilizes a fine-tuned Vision Transformer (ViT) and EfficientNet trained on FaceForensics++ to detect pixel noise and compression anomalies via Grad-CAM++ and Error Level Analysis (ELA).
* **Video Frame Analysis:** Performs keyframe extraction, per-frame ViT analysis, and optical flow temporal consistency tracking to spot deepfakes and unnatural movement.
* **Audio Voice Cloning Detection:** Extracts acoustic features using Wav2Vec2/WavLM and applies signal heuristics (spectral variance, RMS consistency) to identify AI voice cloning across any language.
* **Fake News Verification:** Employs a Multilingual BERT classifier (English & Hindi) for sensationalism scoring, Named Entity Recognition (NER), and truth-override via trusted-source cross-referencing.
* **Screenshot Forensics:** Uses EasyOCR for text extraction and performs layout anomaly detection to catch manipulated social media posts.

### 🧠 Explainable AI (XAI)
* **Gemini 1.5 Flash Integration:** Asynchronous LLM streaming (typewriter effect) generates plain-English narrative summaries and granular Visual Language Model (VLM) component-score breakdowns.
* **Artifact Highlighting:** Explicitly points out manipulated regions, unusual compression artifacts, and synthetic noise patterns.

### ⚡ Premium Engineering
* **Ultra-Fast Frontend Performance:** Built with Vite and React 18, utilizing `React.lazy`, Suspense boundary code-splitting, and deferred 3D asset loading for an instant First Contentful Paint (FCP).
* **Glassmorphism UI:** Features a premium interface with Apple-style 3D processing animations and highly polished, jargon-free data visualization.
* **PDF Report Generation:** Downloadable, professional verification reports via WeasyPrint with full evidence breakdowns and embedded metadata.
* **Secure Cloud Persistence:** JWT-authenticated user accounts and stateless analysis history backed by a production-ready **Supabase** PostgreSQL database.

---

## 🏗️ System Architecture

DeepShield uses a robust, microservice-inspired architecture designed for high concurrency and stateless inference.

```mermaid
graph TD;
    Client[React 18 + Vite SPA] -->|HTTPS / REST| API[FastAPI Gateway]
    
    subgraph Backend Services
        API --> Auth[JWT & Auth Service]
        API --> Upload[SHA-256 Storage Cache]
        API --> Inference[AI Inference Layer]
        API --> DB[(Supabase PostgreSQL)]
    end
    
    subgraph AI Inference Engines
        Inference --> Image[ViT + EfficientNet]
        Inference --> Text[Multilingual BERT]
        Inference --> Audio[Wav2Vec2]
        Inference --> OCR[EasyOCR]
        Inference --> LLM[Gemini 1.5 Flash]
    end
```

---

## 🤖 Detection Pipelines

* **🖼️ Image Pipeline:** `Upload` → `SHA-256 Cache Check` → `ViT Classification` → `Generate Evidence Map (Grad-CAM++)` → `Tampering Check (ELA)` → `Metadata Trace` → `VLM Breakdown` → `Verdict`
* **🎬 Video Pipeline:** `Upload` → `Extract Frames` → `Analyze Individual Frames` → `Unnatural Movement Check` → `Audio Extraction & Deepfake Detection` → `Aggregate Signals` → `Verdict`
* **📰 Text Pipeline:** `Paste Article` → `Scan for Sensationalism` → `NLP Classification` → `Fact-Checking (Trusted Sources)` → `Async LLM Summary` → `Verdict`
* **📱 Screenshot Pipeline:** `Upload` → `Text Extraction (EasyOCR)` → `NLP Credibility Scan` → `Layout Tampering Detection` → `Source Cross-Reference` → `Verdict`
* **🎙️ Audio Pipeline:** `Upload` → `Preprocess Audio` → `Extract Vocal Patterns` → `Detect Synthetic Voice Cloning` → `Analyze Acoustic Signals` → `Verdict`

---

## 📈 Authenticity Scoring

DeepShield uses a standardized **Deepfake Probability score** alongside a 0–100 confidence scale, reinforced by a component breakdown.

| Score Range | Verdict | Indicator | Meaning |
|:------------|:--------|:----------|:--------|
| **81–100** | ✅ Very Likely Real | 🟢 Green | High confidence authentic |
| **61–80** | ✅ Likely Real | 🟢 Light Green | Probably authentic |
| **41–60** | ⚠️ Possibly Manipulated | 🟡 Amber | Uncertain — cross-check recommended |
| **21–40** | ❌ Likely Fake | 🟠 Orange | Probable manipulation detected |
| **0–20** | ❌ Very Likely Fake | 🔴 Red | Strong manipulation signals |

---

## ⚙️ Installation & Deployment

DeepShield is built to run locally for development and is fully containerized for deployment on platforms like Hugging Face Spaces.

### Prerequisites
* **Python** 3.10+
* **Node.js** 18+
* **Gemini API Key** (from Google AI Studio)
* **Supabase Database Connection String**

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

# Install dependencies
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

# Database
DATABASE_URL=postgresql://postgres.xxx:password@aws-0-region.pooler.supabase.com:6543/postgres

# AI Models & Explainability
LLM_PROVIDER=gemini
LLM_API_KEY=your_gemini_api_key_here
LLM_MODEL=gemini-2.0-flash

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
*(API Documentation will be available at `http://localhost:8000/docs`)*

### 5️⃣ Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
*(Open `http://localhost:5173` to view the application)*

---

## 🛡️ Security Features
* **Stateless Analysis:** Uploaded files are cached via SHA-256 for fast retrieval but safely stored without permanent coupling unless explicitly saved to history.
* **Rate Limiting:** IP and User-ID based `slowapi` limiters across endpoints to protect system resources and prevent API abuse.
* **Route Guards:** Authenticated endpoints with mandatory UUID token validation to prevent unauthorized record enumeration.
* **Supabase Cloud DB:** Production-ready PostgreSQL persistence with Row Level Security (RLS) support.

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
