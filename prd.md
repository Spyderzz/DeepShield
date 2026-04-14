# DeepShield — Product Requirements Document (PRD)

## Product Overview

**Product Name:** DeepShield
**Product Type:** Explainable AI-based multimodal misinformation detection web platform

DeepShield is a lightweight web-based system that detects whether images, videos, screenshots, and news articles are authentic or manipulated using pretrained AI models and explainable verification pipelines. The platform prioritizes transparency, usability, and evidence-backed verification.

This system is designed as:

* A public-facing verification tool
* A portfolio-grade AI application
* A college minor project demonstrating multimodal AI integration

---

## Objectives

The system enables users to:

* Upload suspicious media
* Analyze authenticity using pretrained AI models
* View explainable evidence signals
* Observe processing pipeline visualization
* Cross-check trusted Indian news sources
* Download authenticity verification reports

---

## Target Users

### General Public

Needs:

* simple authenticity verdicts
* easy upload workflow
* trust-support guidance

### Students and Researchers

Needs:

* confidence scoring
* explainability indicators
* transparency of processing pipeline

### Social Media Users

Needs:

* screenshot verification
* claim validation
* trusted-source matching

---

## Supported Media Types (Version 1)

### Image Detection

System provides:

* authenticity classification
* confidence score (0–100%)
* manipulation heatmap overlay
* artifact detection indicators

### Video Detection

Pipeline:

Upload video → extract key frames → analyze frames → aggregate signals → generate timeline visualization

System outputs:

* suspicious frame markers
* frame confidence timeline
* final authenticity verdict

### Fake News Text Detection

System provides:

* credibility classification
* linguistic manipulation indicators
* sensationalism scoring
* authenticity confidence score

### Social Media Screenshot Detection

Pipeline:

Upload screenshot → OCR extraction → credibility scan → layout anomaly detection → authenticity scoring

Outputs:

* highlighted suspicious phrases
* manipulation likelihood
* authenticity verdict

---

## Core Features

### Multimodal Upload Interface

Supports:

* image upload
* video upload
* screenshot upload
* article text paste

Unified dashboard entry point.

---

### Explainable AI Detection Engine

Image signals include:

* GAN artifact detection
* facial boundary inconsistencies
* compression irregularities

Video signals include:

* frame-level authenticity scoring
* landmark stability tracking
* suspicious timeline visualization

Text signals include:

* sensationalism detection
* manipulation indicators
* credibility classification

Screenshot signals include:

* OCR extraction
* layout integrity scan
* credibility scoring

---

### Processing Pipeline Visualization

Displays structured animation before results appear.

Duration:

3–5 seconds

Example stages:

Upload received → preprocessing → detection stage → artifact scanning → scoring → verdict generation

Purpose:

* improve transparency
* increase trust
* demonstrate inference workflow

---

### Authenticity Score System

Displays:

**Numerical confidence score (0–100%)**

Example:

Authenticity Score: 82%

**Trust interpretation meter**

Score ranges:

0–20 Very Likely Fake
21–40 Likely Fake
41–60 Possibly Manipulated
61–80 Likely Real
81–100 Very Likely Real

Color mapping:

Red → Amber → Green

---

### Visual Explainability Indicators

Image outputs:

* manipulation heatmaps
* artifact regions

Video outputs:

* suspicious frame timeline

Text outputs:

* highlighted misleading phrases

Screenshot outputs:

* OCR-based suspicious phrase detection
* layout anomaly indicators

---

### Trusted Source Evidence Panel (India-Focused)

Pipeline:

Extract headline → keyword extraction → trusted-source matching → verified link display

Supported sources include:

* PIB India
* The Hindu
* Indian Express
* Reuters India
* BBC India
* ANI News
* NDTV
* Alt News
* Boom Live
* Factly

Displayed as clickable evidence cards.

---

### Contradicting Evidence Detection

If claim appears false:

System displays contradicting verification sources.

Example:

Alt News fact-check
Boom Live verification

---

### Authenticity Report Generator (PDF Export)

Report includes:

* media type
* authenticity score
* verdict classification
* detected indicators
* suspicious signals
* supporting source links
* verification recommendations

Supports:

* academic submission
* sharing verification results
* portfolio demonstration

---

### Optional User Accounts

Guest Mode:

* upload media
* analyze instantly
* download report

Logged-in Mode:

* saved report history
* verification archive
* dashboard access

---

### Responsible AI Guidance Layer

System displays:

Cross-check with trusted sources before sharing

Includes uncertainty disclaimer messaging.

---

## UI/UX Requirements

Design philosophy:

Minimal Material-style interface
Light theme default
Complementary accent colors
Trust-focused layout
No futuristic gradients

Primary color:

Material Blue

Accent color:

Material Amber

Semantic colors:

Green = Real
Amber = Warning
Red = Fake

Typography:

Roboto or Inter

---

## Processing Animation UX

Displayed before results load.

Duration:

3–5 seconds

Example status messages:

Preparing image
Detecting facial regions
Scanning compression patterns
Analyzing GAN artifacts
Generating authenticity score

Video example:

Extracting frames
Tracking landmarks
Analyzing frame consistency
Generating verdict

Screenshot example:

Extracting text
Analyzing layout structure
Evaluating credibility signals

---

## Results Dashboard Layout

Displays:

Prediction verdict card
Authenticity score meter
Trust interpretation scale
Explainability indicator cards
Processing summary
Verified source evidence panel
Contradicting evidence panel
Download report button

---

## Model Strategy

Uses pretrained models from Hugging Face ecosystem.

Model categories:

* image deepfake detection
* vision transformers
* BERT fake-news classifiers
* OCR pipelines

Advantages:

lightweight
fast inference
research-grade capability
strong portfolio value

---

## Security Considerations

Temporary upload storage
Optional authentication protection
User-controlled report downloads
No permanent raw media retention

Future upgrade:

Encrypted storage layer

---

## Performance Strategy

Video optimization:

Key-frame extraction instead of full-frame scanning

Pipeline visualization:

Hybrid real + simulated transitions

---

## Deployment Strategy

Frontend:

Material-style web interface

Backend:

Inference API server

Model source:

Hugging Face pretrained pipelines

Hosting options:

local deployment
university server
cloud inference

---

## Future Expansion (Phase 2)

Browser extension
Audio deepfake detection
Multilingual support
URL-based verification
Real-time monitoring
Mobile application
Community reporting layer
Encrypted storage
